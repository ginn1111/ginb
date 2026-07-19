---
name: aioz-map-layer
description: "AIOZ World Deck map layer operations: add, migrate/rename, and add type filters. All files, registry entries, and patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [aioz, map-layer, map, registry, filter, migration]
---

# AIOZ World Deck — Map Layer Operations

Use this when building, renaming, or adding filters to a map layer in the AIOZ World Deck project.

---

## Project conventions

- Layer keys: **snake_case** (`military_tracker`, `emerg_squawks`, `vessels_ais`)
- Layer IDs in Maplibre: **kebab-case** (`military-tracker-layer`, `emerg-squawks-clusters`)
- Icon sprite IDs: **kebab-case** prefixed `icon-` (`icon-military-tracker`, `icon-emerg-squawks`)
- SVG icon exports: prefix `svgLayer` + PascalName (`svgLayerMilitaryTracker`)
- Filter files: `<LayerName>Filters.tsx` (camelCase domain, PascalCase component)
- All text sizes use `src/styles/theme-fonts.css` utilities — no `text-[Npx]`

### File locations

| Concern | Path |
|---------|------|
| Layer keys / categories | `src/constants/mapLayers.ts` |
| Layer appearance config | `src/constants/mapLayerConfig.ts` |
| Layer component registry | `src/store/map-layer-registry.ts` |
| Layer filter component registry | `src/store/map-filter-layer-registry.ts` |
| Store initial query state | `src/store/map-layer/index.ts` |
| Store query type constants | `src/store/map-layer/constants.ts` |
| Interactive layer IDs | `src/store/map/index.ts` (INTERACTIVE_LAYER_IDS) |
| Interactive layer selectors | `src/store/map-layer/selector.ts` |
| SVG layer icons | `src/assets/icons/LayerIcons.ts` |
| Icon sprite loader | `src/hooks/useMapImageLoader.ts` |
| Component files | `src/components/widget/MaplibreViewer/<LayerName>Layer.tsx` |
| Filter component files | `src/components/widget/MapLayersFilter/<LayerName>Filters.tsx` |
| Layer hook (GeoJSON) | `src/hooks/query/maps/use<Domain>GeoJson.ts` |
| Layer counts | `src/hooks/query/useLayerCounts.ts` |
| Map layers query | `src/hooks/query/useMapLayers.ts` |
| Default preset layers | `src/features/layout-manager/model/defaultMapLayers.ts` |
| Hook query keys | `src/hooks/hook-keys.ts` |
| Docs | `docs/data/map-layers.md` |

---

## Operation 1: Add a new map layer

Touch ALL of these files:

1. **`src/constants/mapLayers.ts`** — add key to one of the `*_MAP_LAYERS` arrays (or `LEGACY_MAP_LAYERS` if placeholder)
2. **`src/constants/mapLayerConfig.ts`** — add `layer_key: { cluster: bool, color: '#hex' }`
3. **`src/store/map-layer/index.ts`** — add `layer_key: { limit: -1, ...filterParams }` to `initialState.layerQuery`
4. **`src/store/map-layer-registry.ts`** — add `const layer_key = lazy(() => import(...))` + entry in `LAYER_COMPONENT_MAP`
5. **`src/store/map/index.ts`** — add `'layer-key-layer'` and `'layer-key-clusters'` to `INTERACTIVE_LAYER_IDS`
6. **`src/store/map-layer/selector.ts`** — add `activeLayers.layer_key && INTERACTIVE_LAYER_IDS_MAP['layer-key-layer']` and cluster variant
7. **`src/components/widget/MaplibreViewer/<LayerName>Layer.tsx`** — create the component
8. **`src/hooks/query/maps/use<Domain>GeoJson.ts`** — create the GeoJSON hook
9. **`src/assets/icons/LayerIcons.ts`** — add `svgLayer<Name>` export
10. **`src/hooks/useMapImageLoader.ts`** — add `['icon-layer-name', svgLayer<Name>]` sprite entry
11. **`src/hooks/query/useLayerCounts.ts`** — add count entry
12. **`src/hooks/query/useMapLayers.ts`** — add `layer_key: true` (or false)
13. **`src/features/layout-manager/model/defaultMapLayers.ts`** — add to relevant preset
14. **`docs/data/map-layers.md`** — add row to table

### Layer component skeleton

```tsx
'use client';

import { memo } from 'react';
import { Layer, Popup, Source } from 'react-map-gl/maplibre';

import { CLUSTER_BUBBLE_DEFAULTS, getMapClusterSourceProps } from '@/constants/mapCluster';
import { getClusterColor } from '@/constants/mapLayerConfig';
import { use<Domain>GeoJSON } from '@/hooks/query/maps/use<Domain>GeoJson';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { INTERACTIVE_LAYER_IDS_MAP, setSelectedEntity } from '@/store/map';
import { getActiveEntitySelector, getActiveLayerById, getLayerQuerySelector } from '@/store/map-layer';
import { LiquidBadge, POPUP_INTERACTIVE_CLASS, PopupCard, PopupContent, PopupField, PopupHeader } from './MapPopupCard';

const <LayerName>Layer = () => {
  const dispatch = useAppDispatch();
  const isActive = useAppSelector((state) => getActiveLayerById(state, '<layer_key>'));
  const layerQuery = useAppSelector((state) => getLayerQuerySelector(state, '<layer_key>'));
  // ...use<Domain>GeoJSON, Source/Layer/Popup...
};

export default memo(<LayerName>Layer);
```

---

## Operation 2: Safe-migrate / rename a layer

Replace an old layer key with a new one. **Two-phase:** add new, then deprecate old.

### Phase 1 — Add new key

Same files as Operation 1, but:
- The new component/hook is a copy of the old one with all internal refs renamed
- The old key stays in its category for now
- `pnpm type-check` after every file

### Phase 2 — Deprecate old key

1. Move old key from its category to `LEGACY_MAP_LAYERS` in `src/constants/mapLayers.ts`
2. Wire old key to `PLACEHOLDER` in `src/store/map-layer-registry.ts`
3. Remove old key from `initialState.layerQuery` in `src/store/map-layer/index.ts`
4. Remove old key from `src/store/map-layer/selector.ts` (interactive layer entries)
5. Remove old key from `src/store/map/index.ts` (INTERACTIVE_LAYER_IDS entries)
6. Remove old key from `src/constants/mapLayerConfig.ts`
7. Remove old key from `src/hooks/query/useLayerCounts.ts`
8. Remove old key from `src/hooks/query/useMapLayers.ts`

### Phase 3 — Clean up dead files

- Delete old component `.tsx`
- Delete old GeoJSON hook `.ts`
- Delete old service files if no other consumers
- Delete old standalone hook (e.g., `useEmergencySquawk.ts`)
- Remove orphaned query keys from `src/hooks/hook-keys.ts`
- Update `docs/data/map-layers.md`
- Run `pnpm type-check` and `pnpm build` to verify

---

## Operation 3: Add a type filter to a layer

Follow `docs/how-to-impl-map-layer-filter.md`. Exact files:

1. **`src/store/map-layer/constants.ts`** — add default types array (e.g., `MILITARY_TRACKER_DEFAULT_TYPES`)
2. **`src/store/map-layer/index.ts`** — reference the constant in `initialState.layerQuery[layer]` as `types: DEFAULT_TYPES`
3. **`src/components/widget/MapLayersFilter/<LayerName>Filters.tsx`** — create filter component
4. **`src/store/map-filter-layer-registry.ts`** — add lazy import + registry entry

### Filter component template

```tsx
import { Get<Domain>Data } from '@/__generated__/api';
import { IMapLayerFilter } from '@/constants/mapLayerFilter';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { getLayerQuerySelector, setLayerQuery } from '@/store/map-layer';
import { DEFAULT_TYPES } from '@/store/map-layer/constants';
import { ExtractQuery } from '@/types';
import LayerFilterGrid from './LayerFilterGrid';

const COMMON_VALUE = { limit: -1 };
type FilterParams = ExtractQuery<Get<Domain>Data>;

const OPTIONS: IMapLayerFilter<FilterParams>[] = [
  { key: 'type_a', label: 'Type A', value: { ...COMMON_VALUE, types: ['type_a'] } },
  { key: 'type_b', label: 'Type B', value: { ...COMMON_VALUE, types: ['type_b'] } },
];

const isMatchOption = (query: Nullish<FilterParams>, params: FilterParams) =>
  query?.types?.some((t) => params.types?.includes(t));

const <LayerName>Filters = () => {
  const queryLayer = useAppSelector<Nullish<FilterParams>>((state) =>
    getLayerQuerySelector(state, '<layer_key>'),
  );
  const dispatch = useAppDispatch();

  const handleSetFilter = (opt: FilterParams, isActive: boolean) => {
    const newQueryLayer = { ...queryLayer, types: [...(queryLayer?.types || [])] };
    if (opt.types) {
      if (isActive) {
        newQueryLayer.types = newQueryLayer.types.filter((t) => !opt.types?.includes(t));
      } else {
        newQueryLayer.types.push(...opt.types);
      }
    }
    if (newQueryLayer.types.length === 0) newQueryLayer.types = DEFAULT_TYPES;
    dispatch(setLayerQuery({ layer: '<layer_key>', query: newQueryLayer }));
  };

  return <LayerFilterGrid options={OPTIONS} queryLayer={queryLayer} isMatchOption={isMatchOption} onToggle={handleSetFilter} />;
};

export default <LayerName>Filters;
```

### Hook must read types from store, not hardcode

```ts
// ✅ Good — types come from store layerQuery, fall back to a default constant
const internalQuery = useMemo(() => ({
  ...query,
  types: query?.types ?? DEFAULT_TYPES,
}), [query]);

// ❌ Bad — types hardcoded in hook
const internalQuery = useMemo(() => ({
  ...query,
  types: ['some_type'],
}), [query]);
```

### Scalar single-select filters (non-array query params)

Not every layer filter is a `types: string[]` multi-select. For scalar backend params like `suspicion_level`, keep the pattern simpler:

1. First inspect `src/__generated__/api/types.gen.ts` and `src/__generated__/api/zod.gen.ts` for the query field. If codegen exposes a real enum/union, use that as the source of truth.
2. If codegen only exposes `string`, do **not** invent enum members from the field name alone. Narrow from authoritative evidence: generated comments, current repo usage, or observed API/domain values.
3. Keep session-specific value findings in a skill reference file, not as a broad repo constant, unless the repo already has a shared domain enum for that field.
4. Build `IMapLayerFilter` options where each chip writes one scalar value.
5. `isMatchOption` should compare equality (`query?.suspicion_level === params.suspicion_level`).
6. `onToggle` should set the scalar when inactive and clear it back to `undefined` when active.
7. `onAllChange` should reset the scalar field to `undefined` rather than inventing an "all" backend value.
8. Keep other query fields intact (`interval`, `limit`, existing defaults).
9. If the hook already forwards unknown query fields to the SDK/API, no hook change is needed; only update the filter UI + store query state.

Example shape:

```tsx
type FilterParams = ExtractQuery<GetNuclearTestData> & {
  interval?: LayerInterval;
};

const OPTIONS = [
  { key: 'none', label: 'None', value: { limit: -1, suspicion_level: 'None' } },
  { key: 'high', label: 'High', value: { limit: -1, suspicion_level: 'High' } },
] satisfies IMapLayerFilter<FilterParams>[];

const isMatchOption = (query: Nullish<FilterParams>, params: FilterParams) =>
  query?.suspicion_level === params.suspicion_level;

const handleSetFilter = (opt: FilterParams, isActive: boolean) => {
  dispatch(
    setLayerQuery({
      layer: 'nuclear_tests',
      query: {
        ...queryLayer,
        suspicion_level: isActive ? undefined : opt.suspicion_level,
      },
    }),
  );
};
```

Reference: `references/nuclear-tests-suspicion-filter.md`.

### Pitfall — generated field is `string`, not enum

For `nuclear_tests.suspicion_level`, codegen may only emit `string` even when product/domain uses a small set of values. In that case:
- do **not** create a fake enum constant in `src/store/map-layer/constants.ts` just to make the filter feel typed
- do **not** assume extra values from DTO comments alone
- prefer current repo/domain evidence and keep the narrowed list close to the filter implementation or in a skill reference
- if backend/OpenAPI later upgrades the field to a real enum, switch the filter to that generated enum/union and delete the local narrowing

---

## Operation 4: Weather raster time-series tiles

Use this when implementing animated/live weather raster tiles in `src/components/widget/MaplibreViewer/WeatherLayer`.

- Weather raster playback is driven by changing the raster `Source` URL template; MapLibre fetches visible viewport tiles again when the source `key` changes.
- Backend contract for weather time-series tiles: query param is `time=<unix_seconds>`.
- Frame timestamps should be Unix seconds, spaced by **1 hour**. Round the base timestamp down to the current hour before applying hour offsets so tile cache keys are stable within the hour.
- Example URL shape:
  ```txt
  /weather/map?map=temp_new&z={z}&x={x}&y={y}&time=1782115200
  ```
- Use `requestAnimationFrame` for playback timing, not `setInterval`, so animation pauses/throttles with the browser frame loop and matches existing map layer staging style.
- Force source refresh with a key containing both active weather layer and frame id:
  ```tsx
  <Source key={`${activeLayer}-${currentFrame.id}`} type="raster" tiles={[weatherTileUrl]}>
  ```
- Keep timeline controls rendered only when the weather map/layer is active (`mapStyleId === MapStyle.WEATHER_MAP`) in `MapControlsOverlay`.
- If the timeline also has a toolbar button, add it to `src/components/widget/MaplibreViewer/MapPanelToolbar/index.tsx` but filter it by current map style:
  ```ts
  const mapStyle = useAppSelector((state) => state.map.mapStyle);
  const items =
    mapStyle === MapStyle.WEATHER_MAP
      ? TOOLBAR_ITEMS
      : TOOLBAR_ITEMS.filter((item) => item.id !== 'weather_timeline');
  ```
- Model the weather timeline as a map panel: add `weather_timeline` to `MapPanelId` / `initialState.open`, wire toolbar toggle via `togglePanel`, and close from the panel with `setPanelOpen({ id: 'weather_timeline', open: false })`.
- Prefer the shared `DraggablePanel` wrapper for map UI panels instead of raw `Rnd`. Extend `DraggablePanel` when needed instead of duplicating drag/resize state in the feature component.
- For bottom-left placement matching screenshot specs, let `DraggablePanel` accept `defaultPosition={{ left: 28, bottom: 64 }}` and resolve bottom/right against measured parent size.
- For autoplay, pass `disabled={isPlaying}` to `DraggablePanel` so dragging and resizing turn off while playback runs, while play/pause remains usable.
- For timeline-only resize, pass per-panel `enableResizing` with only `right: true`; do not change global panel resize defaults just for this one panel.
- Put range inputs inside `data-no-drag` and also stop pointer propagation on `onPointerDown` so slider drags do not start panel drags.
- For date-group cells, use shared `LiquidTooltip`/`LiquidTooltipProvider` and show full date (`dddd, MMM D, YYYY`) while keeping the visible cell label short.
- Put time-series helpers under `src/components/widget/MaplibreViewer/WeatherLayer/weatherTimeline.ts`; keep rendering in `WeatherTimeSeriesLayer.tsx` and playback in `useWeatherTimeline.ts`.
- If `useWeatherTimeline` is consumed from both the raster layer and overlay UI, do **not** keep source-tile loading state in local hook `useState`; each hook call owns a separate state instance. Put shared loading in Redux (`state.map.weatherFrameLoading`) and expose it from the hook.
- Track raster source inflight state by setting loading true when `activeWeatherLayer` or `activeWeatherFrameIndex` changes, then polling `mapRef.getSource(WEATHER_SOURCE_ID) && mapRef.isSourceLoaded(WEATHER_SOURCE_ID)` with `requestAnimationFrame` until loaded.
- Loading spinner must not cause layout shift: always render the spinner slot and toggle `opacity-100` / `opacity-0` inside a fixed/min-width time cell.
- Remove all debug `console.*` while touching weather/map viewer code; project logging rules ban direct console calls.

## Operation 5: Convert a map panel or popover into a side drawer

Use this when moving an existing floating map surface like `DraggablePanel` or a popover into a left/right drawer while preserving feature logic.

### Goal

Keep the content subtree and Redux panel state the same. Swap only the container behavior.

### Source patterns

See `references/map-viewer-controls.md` for session-derived notes on left-overlay positioning, z-index ordering with `UnifiedSearchControl`, drawer dismissal pitfalls, and duplicate trigger cleanup.

- Left/right drawer shell references:
  - `src/components/widget/MaplibreViewer/WeatherCityMarkersLayer/WeatherForecastDrawer.tsx`
  - `src/components/widget/MaplibreViewer/FlightsLayer/FlightDetailDrawer.tsx`
- Shared primitive:
  - `src/components/ui/liquid/drawer.tsx`
- Toolbar trigger style reference:
  - `src/components/widget/MaplibreViewer/MapPanelToolbar/index.tsx`

### Preferred implementation shape

1. Keep the existing feature body component unchanged if possible.
2. Mount the drawer into `#maplibre-viewer-shell`:
   ```ts
   const drawerContainer =
     typeof document === 'undefined'
       ? undefined
       : (document.getElementById('maplibre-viewer-shell') ?? undefined);
   ```
3. Use `LiquidDrawer` + `LiquidDrawerContent` with `overlay={false}`.
4. Flatten the edge touching the viewport with `advancedRadius`.
5. If the panel needs to stay available while closed, do **not** `return null` for the whole component. Render the trigger outside the drawer and gate only `open` state.
6. When cloning the toolbar button to a new left/right map position, copy the exact `LiquidButton` sizing, tooltip, active-state style, and icon weight behavior from `MapPanelToolbar` instead of approximating it.
7. Preserve existing panel state wiring such as `togglePanel('layers_filter')` and `setPanelOpen({ id: 'layers_filter', open: false })`.

### Critical pitfall — map interaction can auto-close Vaul drawers

When a side drawer sits over MapLibre and the user should be able to click or drag the map **without hiding the drawer**, set:

```tsx
<LiquidDrawer dismissible={false} ...>
```

Why:
- Vaul treats map canvas clicks and drags as outside interactions by default.
- That fires `onOpenChange(false)` and closes the drawer even though the user only meant to pan/select on the map.
- Symptom: clicking or dragging the map hides the drawer.

Use explicit close affordances instead:
- close button inside the drawer header
- panel toggle button cloned from `MapPanelToolbar`

### Suggested shell details

- Header with visible title + explicit close button
- `LiquidDrawerTitle` remains for accessibility, even when the visible header duplicates the title
- For grouped filter UIs, if sticky section headers visually disappear into the drawer chrome, add `rounded-lg` + light border/padding to the sticky header wrapper rather than rewriting section logic

## Operation 6: Boundary selection and search-driven active state

Use this when a map workflow selects an area/boundary from search, chips, or any non-click path and the UI must show the country/boundary highlight.

### Core distinction

In AIOZ map viewer, **Redux selection state alone is not enough** for visible boundary highlight.

Two things exist:
1. store state: `state.map.selectedCountry`
2. map feature-state on `COUNTRY_HOVER_SOURCE_ID`:
   - `hover: true|false`
   - `selected: true|false`

`CountryHoverLayer.tsx` paints from **feature-state**, not Redux directly. So a flow that only dispatches `setSelectedCountry(...)` updates state but may show **no visible active border/fill**.

### Source files

- `src/components/widget/MaplibreViewer/CountryHoverLayer.tsx`
  - source id: `country-hover-source`
  - fill layer id: `country-hover-fill-layer`
  - border layer id: `country-hover-border-layer`
  - rendering uses `['feature-state', 'selected']` and `['feature-state', 'hover']`
- `src/components/widget/MaplibreViewer/useCountrySelection.tsx`
  - owns `setFeatureState(...)` synchronization for country hover/selection
- `src/components/widget/MaplibreViewer/index.tsx`
  - mounts `useCountrySelection({ mapRef, mapStyleId })`

### Required rule

If you add a new selection entrypoint for bounded places/areas (for example `UnifiedSearchControl`), verify **end-to-end wiring**:

1. Does it update `selectedCountry`?
2. Does that state reach `useCountrySelection` or another sync path that calls `map.setFeatureState({ source: COUNTRY_HOVER_SOURCE_ID, id }, { selected: true })`?
3. Does the selected id actually match a feature id in `CountryHoverLayer` source data?

Missing any one of these means “state wired” but “visual active layer not wired”.

### Preferred pattern

Keep one synchronization owner in `useCountrySelection.tsx`.

- click path can continue to call local helper `setSelectedCountryState(...)`
- non-click path should either:
  - reuse that hook’s sync effect by updating `state.map.selectedCountry`, or
  - explicitly call a shared exported sync helper if refactoring demands it

Avoid duplicating raw `map.setFeatureState(...)` logic across unrelated components.

#### Search-driven country activation — preferred implementation

When `UnifiedSearchControl` or another search surface activates a bounded place/country:

1. **Do not** store the geocoder id (for example Nominatim `place_id`) as `selectedCountry.id`.
2. Add the reusable resolver to `useCountrySelection.tsx`, not to the search component:
   - read `COUNTRY_HOVER_SOURCE_ID`
   - scan source `FeatureCollection`
   - normalize and match canonical country name from source properties (`name`, `ADMIN`, `name_en`, `NAME`)
   - build the final `{ id, name, properties, latitude, longitude, bbox }` payload from the matched source feature
3. Thread that resolver down into the search UI (`MaplibreViewer` → `MapControlsOverlay` → `UnifiedSearchControl`) and dispatch `setSelectedCountry(resolvedSelection)` only after resolving into the country source's id space.
4. Candidate country name from geocoder result should prefer:
   - `address.country`
   - else normalized place `name`
   - else fallback label
5. Keep manual map click selection disabled when product says search-only, but leave `CountryHoverLayer` mounted so store-driven selection still paints.

This keeps one class-level owner for country selection logic and prevents each search/control surface from inventing its own country-id mapping.

#### Render-path pitfall — source mounted vs state wired

For visible country highlight, all three must be true:
- `CountryHoverLayer` is mounted in `MapLayersStack`
- `selectedCountry` store updates are synced into `feature-state.selected`
- `selectedCountry.id` matches the feature id domain of `country-hover-source`

A common failure mode is fixing only one or two of these and believing the layer is "wired" because Redux state changes.

### Common pitfall — wrong id domain

Geocoder / search results often carry ids like Nominatim `place_id`. `CountryHoverLayer` uses GeoJSON feature ids from `generateId` or source feature ids. These ids are usually **not the same**.

So even after store→feature-state sync exists, highlight still fails when:
- `selectedCountry.id` is a geocoder id
- `COUNTRY_HOVER_SOURCE_ID` features use different ids

When highlight matters, map the selection onto the country source’s id space, or switch to name/bbox-based lookup before calling `setFeatureState`.

### Verification checklist for this class of task

After implementing search-driven or programmatic boundary selection, verify all four:

- [ ] selecting bounded result updates `state.map.selectedCountry`
- [ ] `useCountrySelection` (or equivalent) syncs store state into `feature-state.selected`
- [ ] selected id matches a real feature in `country-hover-source`
- [ ] visible fill/border highlight appears in browser, not just store state

### Fast diagnosis

Symptom: map zooms to area, Redux state looks right, but no active country highlight.

Check in order:
1. Did the flow only dispatch `setSelectedCountry(...)`? If yes, add/confirm feature-state sync.
2. Is `CountryHoverLayer` mounted? If no, no highlight source exists.
3. Does `selectedCountry.id` belong to the same id domain as `country-hover-source`? If no, map the id or derive match by bbox/name.

## Verification

After any layer operation:

```bash
pnpm type-check    # Must pass with 0 new errors
pnpm build         # Must succeed (if feasible)
```

Check in browser:
- Layer appears in `MapLayersFilter` under the correct category
- Toggling layer on/off shows/hides markers
- Clusters render and are clickable
- Popup shows correct data on click
- Filters (if added) update the map on toggle
