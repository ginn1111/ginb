---
name: map-layer-temporal-filters
description: Add or extend interval/temporal filters for map layers in AIOZ World Deck.
---

# Map Layer Temporal Filters

## When to use
- User wants interval/date filters for map layers.
- Need decide which map layers should expose temporal filtering.
- Need wire map-layer filter UI to backend query params or client-side date filtering.
- Need align semantic meaning of layer with what interval means to user on map.

## Core rule
Implement temporal filtering only for layers where time window has clear user meaning on map.

Good fit:
- event/history layers
- warnings/alerts with issue window
- incident feeds
- article/event streams

Bad fit:
- static infrastructure
- current snapshot layers where interval would imply history that UI does not show
- layers belonging to excluded semantic groups

## Required workflow
1. Confirm scope by map-layer group before coding.
   - Ask which group(s) are in scope when user says exclude another group.
   - Do not assume `news` vs `live_news`; verify actual map-layer key in code.
2. Inspect existing layer state and registry.
   - `src/constants/mapLayers.ts`
   - `src/store/map-layer/index.ts`
   - `src/store/map-filter-layer-registry.ts`
3. Inspect existing filter UI and hook plumbing.
   - Filter UI lives under `src/components/widget/MapLayersFilter/`
   - Map hooks live under `src/hooks/query/maps/`
4. Determine temporal transport pattern per endpoint.
   - Some APIs use `since` / `until`
   - Some APIs use `start_date` / `end_date`
   - Some layers need client-side post-filtering because API has no time params
   - If API spec/codegen was regenerated during task, re-open generated query types before finalizing. Do not trust earlier assumptions about param names or cardinality; subtle changes like adding `until` beside `since` are easy to miss.
5. Add default interval in `src/store/map-layer/index.ts` only for in-scope layers.
6. Add or register filter UI.
   - Reuse shared interval component when layer only needs interval.
   - For mixed filters, render interval above existing type chips.
7. Translate `interval` out of Redux query state before API call.
   - Never send raw UI-only `interval` field to SDK endpoint.
   - Convert to backend query params in map hook.
8. After editing `.ts` / `.tsx`, run `pnpm type-check`.
9. Separate new errors from pre-existing repo errors before reporting status.

## Implementation patterns

### Shared interval utilities
Keep date math in `src/utils/intervalFilter.ts`.
Useful helpers:
- `SinceInterval` type — `'3d' | '7d' | '30d' | '90d' | '180d' | '1y' | 'all'`
- `getDateRangeFromInterval(interval: Nullish<SinceInterval>)` returning `[start, end]`
- client-side `isDateWithinInterval()` for feeds without backend time params

**Type discipline for interval**: Always type the `interval` field as `SinceInterval` (or the UI export `LayerInterval`) in the intersection type, never `string`. The old pattern of `interval?: string` with an `as SinceInterval` cast is dead — the type system should enforce the domain directly.

**`?? 'all'` default is dead code**: `getDateRangeFromInterval` already handles `null`/`undefined` natively (returns `[null, null]`), same as passing `'all'`. The `?? 'all'` fallback is a no-op that adds visual noise. Drop it:

```ts
// ✅ correct
const [start, end] = getDateRangeFromInterval(interval);

// ❌ noisy — ?? 'all' is redundant
const [start, end] = getDateRangeFromInterval(
  (interval as SinceInterval | undefined) ?? 'all',
);
```

Prefer a single destructured call over inline tuple indexing. If user asks to simplify temporal plumbing, remove one-off `getIntervalStartDate` / `getIntervalEndDate` helpers and use:
```ts
const [start, end] = getDateRangeFromInterval(interval);
// then start?.toISOString(), end?.toISOString()
```
This keeps all interval math in one source of truth, avoids helper drift during API-spec regeneration, and eliminates the redundant second function call.

**End-boundary semantics**: `getDateRangeFromInterval` uses `dayjs().add(1, 'day').startOf('day')` for the end bound (not `startOf('day')`). This means a `'30d'` interval includes the **entire current day** up to midnight tonight, not just up to midnight last night. Confirm this is the intended behavior with the user before assuming. If it changes, it affects cache-key stability because the derived `end_date`/`until` value shifts at midnight.

### Interval-only filter UI
If layer only needs interval:
- create tiny wrapper component under `src/components/widget/MapLayersFilter/`
- read layer query from Redux
- write `interval` back directly (no toggle-ternary)
- register component in `src/store/map-filter-layer-registry.ts`

**`handleSetFilterInterval` — just set `interval` directly, no toggle.**

The old toggle-ternary pattern:
```ts
dispatch(setLayerQuery({ layer, query: { ...queryLayer, interval: queryLayer?.interval === interval ? undefined : interval } }));
```
was meant to let users toggle-off the same interval. But it breaks the UX contract: when a user clicks an interval, they expect to see data for that interval. The toggle-off is handled by the "All" button in `LayerIntervalFilters` (which calls `onChange(undefined)`). Keep `handleSetFilterInterval` simple:

```ts
const handleSetFilterInterval = (interval: Nullish<LayerInterval>) => {
  dispatch(
    setLayerQuery({
      layer: 'my_layer',
      query: { ...queryLayer, interval },
    }),
  );
};
```

Also simplify the `value` prop — no need for the `as { interval?: LayerInterval }` cast on `queryLayer` when the hook already typed the layer query correctly. Just pass `queryLayer?.interval` directly.

### Mixed filter UI
If layer already has chips/toggles:
- keep current chip logic
- add interval UI above chips
- preserve existing query keys like `event_types` or `types`
- if shared chip component supports `onAllChange`, wire it for warning/type groups so partial selections show an `All` reset back to default query values
- for semantic warning-level chips, do not use one shared active color. Extend `IMapLayerFilter` with per-option active styling (for example `activeStyle?: CSSProperties`) and feed `createBadgeStyleFromColor(WIDGET_THEME_REGISTRY.*)` per option so `Advisory` / `Watch` / `Warning` / `Flash` can carry distinct meaning

### Hook translation
Prefer `useMemo` for derived API params, not inline in `fetchRows`.

Call `getDateRangeFromInterval` once and destructure into variables rather than indexing the tuple inline twice. This avoids redundant computation and keeps intent clear:

```ts
const internalQuery = useMemo(() => {
  const { interval, ...rest } = (query ?? {}) as Query & { interval?: SinceInterval };
  const [startDate, endDate] = getDateRangeFromInterval(interval);
  return {
    ...rest,
    start_date: startDate?.toISOString(),
    end_date: endDate?.toISOString(),
  } satisfies Query;
}, [query]);

return useGeoJSONArtifacts<...>({
  queryKey: queryKeys.getLayerGeoJSON('layer_key', query), // raw query in key
  fetchRows: async () => {
    const { data } = await getXxx({ query: internalQuery }); // derived query at fetch
    // ...
  },
});
```

The same destructured pattern works when the translation is inside `fetchRows` (simpler hooks that don't need `useMemo`):

```ts
fetchRows: async () => {
  const { interval, ...rest } = (query ?? {}) as SomeQuery & { interval?: SinceInterval };
  const [startDate, endDate] = getDateRangeFromInterval(interval);
  const { data } = await getXxx({
    query: { ...rest, start_date: startDate?.toISOString(), end_date: endDate?.toISOString() },
  });
  // ...
},
```

For APIs that use `since`/`until` naming, destructure accordingly:

```ts
const [since, until] = getDateRangeFromInterval(interval);
// then use since?.toISOString(), until?.toISOString()
```

Avoid inlining the translation inside `fetchRows` when the derived params are also needed for cache-key stability — prefer `useMemo` for those cases. But when the hook is simple enough that `queryKey` uses the raw `query`, inlining inside `fetchRows` with destructured variables is acceptable and avoids useMemo overhead.

Patterns:
- `interval` -> `since`
- `interval` -> `since` + `until`
- `interval` -> `start_date` + `end_date`
- `interval` -> client-side `pubDate`/event-date filter after fetch

Concrete reminder from AIOZ map layers:
- `nuclear_tests` may require bounded RFC3339 window (`since` + `until`) after spec regeneration, not only `since`.
- `live_news` can drift in two different ways and both must be checked after API spec regeneration:
  1. query-shape drift — if `GetNewsData['query']` gains `start_date` / `end_date`, stop client-side `pubDate` filtering and send bounded backend params instead;
  2. layer-key drift — nearby files may still use stale `news` key even though actual map-layer key is `live_news`.
- For `live_news`, audit all three places together:
  - map hook query translation (`src/hooks/query/maps/useNewsGeoJson.ts`)
  - layer selectors / active checks in UI (`src/components/widget/MaplibreViewer/NewsLayer.tsx` or replacement layer component)
  - visual config / registry keys (`src/constants/mapLayerConfig.ts`, related registries)

Keep query key based on translated API query, not raw UI state, when interval changes affect fetch results.

## Weather raster tile time-series

When user asks for weather "time series tiles", "movement tiles", or live weather animation in AIOZ World Deck, treat each frame as a raster tile URL variant, not as GeoJSON animation.

Pattern:
- Keep `react-map-gl/maplibre` raster `<Source type="raster" tiles={[tileUrl]}>`.
- Build URL with backend frame param: `time=<unixHour>` unless backend contract says otherwise.
- Do **not** use a static `WEATHER_TIMELINE_FRAMES` array for live weather series. Generate frames at runtime from the current hour.
- Default live-weather playback range in AIOZ World Deck: hourly frames from `now - 48h` through `now` (49 frames total).
- Format timeline labels as `ddd DD - HH:mm` (example via dayjs: `dayjs.unix(unixTime).format('ddd DD - HH:mm')`), not relative labels like `-4h` / `Now`.
- Keep the raster `<Source>` stable. Do **not** change `key` per frame. A keyed remount removes/re-adds the source and causes the old tiles to disappear while the new time-series tiles load.
- Let `react-map-gl` update the existing source: its `Source` component deep-compares props and calls `source.setTiles(props.tiles)` when only `tiles` changes. This follows MapLibre's refresh/reload path and keeps current renderable tiles visible until new tiles arrive.
- Store playback state in map slice when it must be shared by layer + overlay: `weatherTimelinePlaying`, `activeWeatherFrameIndex`, `stepWeatherFrame({ frameCount, direction })`.
- Keep weather-layer code split small: pure `weatherTimeline.ts`, `useWeatherTimeline.ts`, `WeatherTimeSeriesLayer.tsx`, `WeatherTimelineOverlay.tsx`; keep `MaplibreViewer/index.tsx` as event orchestration only.
- Make timeline overlay draggable when user asks to move control over the map. Render it only while `MapStyle.WEATHER_MAP` is active, and stop pointer propagation during drag so MapLibre does not steal the gesture.
- When user asks for a weather time-series/range control, use a native `<input type="range">` with `step={1}` over frame index values. For hourly weather frames this means each slider step is one hour. Bind `min={0}`, `max={frameCount - 1}`. Keep a local `pendingFrameIndex` for instant thumb/label/day-strip feedback, and debounce the committed Redux frame index (for example with `useDebounceCallback(..., SEARCH_DEBOUNCE_MS)`) so tile requests do not fire on every drag event. Flush on pointer-up/blur so final selected hour loads immediately. Keep the visible label beside the slider in `ddd DD - HH:mm` format.
- When user asks for a calendar/timeline strip below the range, group contiguous frames by calendar date and render segmented cells under the slider. Use date group label format `ddd DD` (not full timestamp). Size/position each segment on the same scale as the range input: `rangeMax = frameCount - 1`, `left = group.start / rangeMax`, `width = (nextGroup.start - group.start) / rangeMax` (last group ends at `rangeMax`). Do not use `group.length / frameCount`; it drifts from slider thumb positions. Drive active day highlighting from `pendingFrameIndex ?? frameIndex`, not only the committed index, so UI stays responsive during debounced dragging.
- For floating timeline panels over map/weather imagery, favor contrast over glassiness: semantic `bg-background/95`, `border-border`, `text-foreground`, and a stronger shadow. Avoid low-contrast `bg-card/90`, `border-border/60`, or `text-muted-foreground` for primary timestamp/date text when the map is visible behind the panel.
- For the AIOZ weather timeline overlay, use the shared `DraggablePanel` component, not raw `react-rnd`, so panel behavior stays consistent with other map panels. If needed, minimally extend `DraggablePanel` itself with reusable props rather than bypassing it:
  - `defaultPosition` can accept `{ left, bottom }` so the panel starts at the screenshot-like bottom-left map position (`left: 28`, `bottom: 64`).
  - `disabled` can disable drag/resize while autoplay is running.
  - `enableResizing` can restrict resizing to the right edge for the timeline.
- Wire weather timeline visibility through `mapPanels.open.weather_timeline`: add the toolbar toggle in `MapPanelToolbar/index.tsx`, default it open in `src/store/map-panels/index.ts`, and close via `DraggablePanel onClose` using `setPanelOpen({ id: 'weather_timeline', open: false })`. The range input must use `data-no-drag` and stop pointer propagation so panel dragging does not steal slider gestures.
- Weather Timeline toolbar button must only render while `state.map.mapStyle === MapStyle.WEATHER_MAP`; filter it out of toolbar items for all other map styles.
- When the user hides the timeline, reset timeline state: cancel pending debounced frame commits, stop autoplay, set local pending frame index to `0`, and dispatch `setActiveWeatherFrameIndex(0)`.
- For weather source-tile inflight state, track `isFrameLoading` in `useWeatherTimeline` with `mapRef.getSource('weather-time-series-source') && mapRef.isSourceLoaded('weather-time-series-source')`. Set loading true when `activeWeatherLayer` or `activeWeatherFrameIndex` changes, poll with `requestAnimationFrame`, and render a small `SpinnerGapIcon` beside the timestamp while loading.
- For date-group cells under the weather range, add a tooltip per cell using shared `LiquidTooltip`; show full calendar date (for example `dddd, MMM D, YYYY`) while keeping the visible segment label compact (`ddd DD`).

Minimal tile flow:
```tsx
const weatherTileUrl = buildWeatherTileUrl({ layer: activeLayer, frame: currentFrame });

<Source
  id="weather-time-series-source"
  type="raster"
  tiles={[weatherTileUrl]}
  tileSize={256}
>
  <Layer id="weather-time-series-layer" type="raster" />
</Source>
```

Why no `key`: `react-map-gl` `Source` compares props and calls `source.setTiles()` for `tiles` changes. Keyed remount bypasses that and causes visible tile gaps.

Backend contract matters: if backend ignores `time`, MapLibre still reloads but visual frame is identical. Do not claim animation works until network/render check shows frame-specific tiles.

### Custom per-layer interval types (non-standard values)

Not every layer uses the standard `SinceInterval` (`'3d' | '7d' | '30d' | '90d' | '180d' | '1y' | 'all'`). Some layers need layer-specific values. Keep the values and labels explicit so typos like `feature` vs `future` cannot hide in string replacement logic.

**Pattern — define type + options array in the hook file, export both:**

```ts
// src/hooks/query/maps/useEarthquakesGeoJson.ts
export type EarthquakeInterval =
  | '1y'
  | '90d'
  | '30d'
  | '7d'
  | '7d-future'
  | '30d-future'
  | '90d-future'
  | '1y-future';

export const EARTHQUAKE_INTERVAL_OPTIONS: EarthquakeInterval[] = [
  '1y',
  '90d',
  '30d',
  '7d',
  '7d-future',
  '30d-future',
  '90d-future',
  '1y-future',
];
```

**Future suffix semantics belong in `getDateRangeFromInterval`.** `-future` means a forward-looking window, not featured/significant data:

```ts
// getDateRangeFromInterval('30d-future')
const start = dayjs();
const end = start.add(30, 'd');
```

The hook should pass the raw interval to the utility and only translate returned dates to the endpoint params:

```ts
const { interval, ...rest } = (query ?? {}) as QueryType & {
  interval?: EarthquakeInterval;
};
const [startDate, endDate] = getDateRangeFromInterval(interval);

const queryParams = {
  ...rest,
  ...(startDate && { start_date: startDate.toISOString() }),
  ...(endDate && { end_date: endDate.toISOString() }),
};
```

Do **not** add `mag_from` / significance filtering for `-future` values unless the user explicitly requests that separate filter.

**Display labels.** Use an explicit label map instead of suffix replacement:

```tsx
const EARTHQUAKE_INTERVAL_LABELS: Record<EarthquakeInterval, string> = {
  '1y': 'Last 1 Year',
  '90d': 'Last 90 Days',
  '30d': 'Last 30 Days',
  '7d': 'Last 7 Days',
  '7d-future': 'Next 7 Days',
  '30d-future': 'Next 30 Days',
  '90d-future': 'Next 90 Days',
  '1y-future': 'Next 1 Year',
};
```

Use title copy like `Time Window`, not raw `Interval`, when the filter mixes past and future ranges.

**Redux state.** Store the raw custom string (e.g. `'30d-future'`) in `layerQuery.interval`. The hook + interval utility own translation to API params — never send the raw string to the backend.

**Reference implementation:**
- `src/utils/intervalFilter.ts` — `FutureInterval` / `DateRangeInterval`, `-future` date math
- `src/hooks/query/maps/useEarthquakesGeoJson.ts` — `EarthquakeInterval` type/options and raw interval handoff
- `src/components/widget/MapLayersFilter/EarthquakeFilters.tsx` — `Time Window` UI with explicit label map + existing magnitude chips

## Pitfalls
- **User says "Try again" — fix, don't report.** If user says "Try again" or "do it" after you report session findings, they want the fix implemented immediately. Stop analyzing, start coding. This overrides analysis-first instincts.
- **Bulk-editing multiple similar hooks can corrupt files.** When rewriting the same interval-translation pattern across 10+ hook files, automated scripts (sed over multi-line patterns, Python regex replaces, terminal heredocs) can introduce line-number prefixes, broken indentation, or duplicate content. Prefer targeted `patch()` calls per file, or at minimum verify each output file parses after any mass edit. Use `pnpm type-check` with a targeted grep (not full output) to confirm all touched files are clean, because the repo may have a pre-existing error baseline that drowns new failures.
- **`live_news` query-key namespace changed.** The `useNewsGeoJson` hook went from `['getNews', query]` to `queryKeys.getLayerGeoJSON('live_news', query)`. If anything elsewhere invalidates the old `getNews` key, that cache invalidation silently stops working. Search the repo for `'getNews'` or `"getNews"` before merging.
- `news` may be stale naming in nearby files; active map-layer key can be `live_news`.
- User may ask to exclude layers from another group after docs/spec were drafted. Reconfirm scope before implementation.
- Do not broaden scope from one group to all semantic candidates unless user explicitly says so.
- If `pnpm type-check` fails, check whether failures come from touched files or unrelated pre-existing repo errors.
- Do not add synthetic map-layer keys to Redux state if not present in `MAP_LAYER_LIST`.
- **Bulk-editing multiple similar hooks**: When rewriting the same interval-translation pattern across 10+ hook files, automated edits can corrupt source (line-number prefixes, broken indentation, duplicate lines). Use targeted single-file patches instead of multi-file scripts. After any mass change, open each file and verify it parses.
- **Cache-key stability vs. end-boundary**: The `getDateRangeFromInterval` end bound uses `add(1, 'day').startOf('day')` for standard past intervals. If this changes, `end_date`/`until` values in fetch requests shift at midnight. If the `queryKey` is correctly based on raw `layerQuery`, the cache key stays stable — only the *request payload* changes. But if any code accidentally puts derived dates into the query key, midnight churn will cause unnecessary refetches.
- **`future` is not `feature`**: If a user says `7d-future` / `30d-future` / `90d-future` / `1y-future`, implement a forward-looking window: `start = dayjs()`, `end = start.add(days, 'd')`. Do not interpret it as "featured" data and do not add magnitude/significance params unless the user explicitly requests those separately.

## Verification
- `pnpm type-check`
- Confirm new filter components are registered in `MAP_FILTER_LAYERS_REGISTRY`
- Confirm in-scope hooks translate `interval` before SDK call
- Confirm default interval exists only for intended layers

## References
- `references/aioz-world-deck-interval-patterns.md` — concrete AIOZ patterns, affected files, and query-param mapping examples.
- `references/weather-timeline-range-control-2026-06-22.md` — session notes for weather raster time-series slider, date-strip alignment, debounce, and Source update behavior.
