---
name: map-layer-query-filters
description: Implement and review map-layer filter plumbing in AIOZ World Deck, especially temporal/interval filters and layerQuery -> hook -> API param translation.
---

# Map Layer Query Filters

## When to use
- Adding or changing a map-layer filter in AIOZ World Deck
- Wiring `layerQuery` state into a map hook
- Implementing interval / temporal filters for map layers
- Reviewing cache-key behavior for map-layer queries
- Auditing stale layer-key aliases like `news` vs `live_news`

## Core rule
Keep **UI/state query shape** and **backend request shape** separate.

- `layerQuery` in Redux stores semantic UI state, e.g. `interval: '7d'`
- hook translates semantic state into backend params, e.g. `start_date`, `end_date`, `since`, `until`
- **queryKey must use raw `layerQuery` directly**, not a derived request object
- derived backend params belong in fetch request only

## Standard flow
1. Add or update default `layerQuery` state in `src/store/map-layer/index.ts`
2. Add or update per-layer filter UI in `src/components/widget/MapLayersFilter/`
3. Register filter component in `src/store/map-filter-layer-registry.ts`
4. In hook, destructure `interval` from `query`
5. Build backend request params from `getDateRangeFromInterval(interval)` inside fetch logic (or a local derived request object)
6. Keep `queryKey` based on raw `query` / `layerQuery`, not translated dates
7. Run `pnpm type-check`

## Temporal filter rules
Use `getDateRangeFromInterval()` as source of truth.

- start bound: `getDateRangeFromInterval(interval)[0]?.toISOString()`
- end bound: `getDateRangeFromInterval(interval)[1]?.toISOString()`
- do not re-introduce `getIntervalStartDate` / `getIntervalEndDate`

## Query-key pitfall
Do **not** do this:

```ts
queryKey: queryKeys.getLayerGeoJSON('water_alerts', {
  ...query,
  start_date,
  end_date,
})
```

Do this instead:

```ts
queryKey: queryKeys.getLayerGeoJSON('water_alerts', query)
```

and translate dates only in the request:

```ts
const { interval, ...rest } = (query ?? {}) as Query & { interval?: string };
const [start, end] = getDateRangeFromInterval(
  (interval as SinceInterval | undefined) ?? 'all',
);

const apiQuery = {
  ...rest,
  start_date: start?.toISOString(),
  end_date: end?.toISOString(),
};
```

Reason: cache key should follow source-of-truth `layerQuery`, not duplicate transform logic.

**Namespace change for `live_news`**: The `useNewsGeoJson` hook previously used `['getNews', query]` as its query key. After aligning with the layer key `live_news`, it now uses `queryKeys.getLayerGeoJSON('live_news', query)`. This changes the cache namespace. If anything elsewhere in the app invalidates or depends on the old `getNews` key, behavior will change. Audit before merging.

## Endpoint mapping checklist
After API regen, re-check generated query types before wiring params.

Typical mappings seen in this repo:
- `start_date` / `end_date` for `live_news`, `military_tracker`, `landslides`, severe-weather layers, `earthquakes`
- `since` / `until` for `nuclear_tests`, `net_outages`, `maritime_warnings`
- endpoint-specific scalar filters like `mag_from` / `mag_to` for `earthquakes`
- endpoint-specific scalar filters like `severity` for `net_outages`

Never assume old param names survived regen. Re-open generated `Get...Data['query']` types and align hook mapping.

### When product asks for backend filters that are missing from generated query types
Sometimes UI/product asks for backend params (for example `speed_min` / `speed_max` or `gust_min` / `gust_max` on `wind_field`) before the generated OpenAPI query type exposes them.

Use this temporary pattern:

1. Keep Redux `layerQuery` semantic and raw as usual.
2. Add the filter UI and store values in `layerQuery`.
3. In the hook, define a **local extended query type**:
   ```ts
   type WindFieldQuery = GetWeatherGlobalWindData['query'] & {
     speed_min?: number;
     speed_max?: number;
     gust_min?: number;
     gust_max?: number;
   };
   ```
4. Accept that local extended type in the hook and pass it through to the SDK call.
5. Register the filter UI normally in `MAP_FILTER_LAYERS_REGISTRY`.
6. Call out clearly in the final report that codegen/spec still needs alignment if the generated type does not yet include those params.

Important: this is a **bridge**, not a permanent substitute for regen. Prefer `pnpm generate:api` and official generated query fields whenever available.

## Layer-key pitfall
Check actual map-layer key before wiring selectors and config.

Known example:
- map layer key is `live_news`, not `news`

Audit these places together when fixing a stale alias:
- `getActiveLayerById(...)`
- `getLayerQuerySelector(...)`
- map layer visual config key
- hook query key namespace if layer-specific

## Review checklist
## Review checklist
- raw `queryKey` uses `query` / `layerQuery` directly
- fetch request translates interval to backend params
- generated query type matches actual param names after API regen
- layer key matches registry/constants (`live_news` vs stale alias)
- interval defaults are set intentionally for each layer
- formatting remains readable after any bulk refactor
- when user asks for bounded numeric filters (for example `mag_from` / `mag_to` on earthquakes), do **not** add interval unless explicitly requested
- when user asks for a categorical backend filter already present in generated query types (for example `severity` on `net_outages`), prefer extending existing layer filter UI over creating a new custom component pattern
- for single-value categorical filters, use shared `LayerFilters` pills in single-select mode: active pill click clears back to `undefined`, and "All" clears filter state
- for single-select categorical filters, header should show active label beside title (`Severity (Critical)`, `Severity (All)`) instead of active counts like `(1/2)`; counts remain better for multi-select filters
- single-select active label beside title should use the same text color as the title itself; do not mute it with `text-muted-foreground` or lower-opacity text classes
- before adding categorical options, verify actual backend/domain values from generated query types, existing layer rendering, or payload examples; do not invent extra buckets (`high`/`medium`/`low`) when layer only exposes real values like `normal` and `critical`
- if the generated query field is only `string` (not a literal union / enum), still derive the filter state type from the generated query field (`NonNullable<Get...Data['query']>['field']`) and source the concrete option list from real backend data such as response `counts` / `full_counts` maps or payload examples; do not hand-maintain category lists for backend-owned filters
- when the filter maps cleanly to existing visual buckets on the layer, prefer shared horizontal pill filters (`LayerFilters`) with predefined ranges over freeform numeric inputs

## Numeric-range filter rule
Keep bounded numeric filters aligned with the layer's visual semantics.

Example: earthquakes already render three magnitude buckets on map (`<3`, `3–5`, `5+`). When user asks for `mag_from` / `mag_to` filtering, the filter UI should usually expose those same predefined ranges as horizontal pills instead of raw min/max inputs. Wire each pill to a concrete backend query shape:

- `Minor <3` -> `{ mag_to: 3 }`
- `Moderate 3–5` -> `{ mag_from: 3, mag_to: 5 }`
- `Strong 5+` -> `{ mag_from: 5 }`
- `All` clears both bounds back to `undefined`

This keeps filter UX consistent with what user already sees on map and avoids overbuilding custom input controls for a discrete range model.

## Verification
- `pnpm type-check`
- if repo has unrelated red baseline, grep output for touched files and confirm no new errors

**Type-check baseline strategy**: When the repo has pre-existing type errors, run `pnpm type-check` and grep only for the specific files you changed. Example:
```bash
pnpm type-check 2>&1 | rg -n "useNewsGeoJson|useWaterAlertsGeoJson|useNuclearTestsGeoJson|..."
```
If the grep returns nothing, your changes introduced no new type errors — the full output failures are from unrelated pre-existing issues.

## Commit hygiene for filter work
When a session touches more than one layer/domain, split commits by scope before staging.

- shared filter-framework changes in one commit (for example `LayerFilters` behavior)
- per-layer UI changes in their own commit when they are the main task (`net_outages`, `earthquakes`, etc.)
- unrelated layer work already present in worktree (for example `nuclear_tests`, `live_satellites`) stays out of your commit unless user explicitly asks to bundle it

Before committing:
1. run `git status --short`
2. inspect diffs for every touched filter/layer file
3. stage only files for one scope
4. if pre-commit hooks fail on unrelated red baseline, call that out explicitly before using `--no-verify`

Reason: map-layer work often lands in parallel across several layers; bundling them hides review intent and fights user-requested split commits.

## References
- `references/aioz-world-deck-interval-filter-notes.md` — session notes, param mappings, pitfalls, and examples from interval-filter rollout
- `references/earthquakes-magnitude-filter.md` — earthquake-specific pattern for combining interval translation with `mag_from` / `mag_to`
- `references/net-outages-severity-filter.md` — pattern for adding scalar categorical filters alongside interval filters on map layers
