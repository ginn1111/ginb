# AIOZ World Deck interval filter patterns

## Group/scope lesson
When user says exclude layers from another group, confirm exact `*_MAP_LAYERS` groups from `src/constants/mapLayers.ts` before coding.

Observed in session:
- `ENVIRONMENT_MAP_LAYERS`
- `SECURITY_AND_INTEL_MAP_LAYERS`
- `AVIATION_AND_MARITIME_MAP_LAYERS`
- `HUMANITARIAN_AND_CRISIS_MAP_LAYERS`

User then widened scope to all of these.

## Naming pitfall
Map docs/conversation may say `news`, but active map-layer key in code can be `live_news`.

Files that revealed mismatch:
- `src/constants/mapLayers.ts`
- `src/components/widget/MaplibreViewer/LiveNews/index.tsx`
- pre-existing repo errors also referenced stale `news` key in:
  - `src/components/widget/MaplibreViewer/NewsLayer.tsx`
  - `src/constants/mapLayerConfig.ts`

## Interval transport mappings used

### `since`
- `src/hooks/query/maps/useNuclearTestsGeoJson.ts`

### `since` + `until`
- `src/hooks/query/maps/useNetOutagesGeoJson.ts`
- `src/hooks/query/maps/useMaritimeWarningsGeoJson.ts`

### `start_date` + `end_date`
- `src/hooks/query/maps/useMilitaryTrackerGeoJson.ts`
- `src/hooks/query/maps/useWaterAlertsGeoJson.ts`
- `src/hooks/query/maps/useLandslidesGeoJson.ts`
- `src/hooks/query/maps/useFloodsGeoJson.ts`
- `src/hooks/query/maps/useTornadoesGeoJson.ts`
- `src/hooks/query/maps/useHeatColdGeoJson.ts`
- `src/hooks/query/maps/useAvalanchesGeoJson.ts`

### Client-side date filtering after fetch
- `src/hooks/query/maps/useNewsGeoJson.ts`
- reason: endpoint query shape inspected in generated types did not expose temporal params, so interval semantics implemented by filtering `pubDate`

## Reusable UI pattern
Created interval-only wrappers under `src/components/widget/MapLayersFilter/` for layers that need only interval:
- `IntervalLayerFilters.tsx`
- `LiveNewsFilters.tsx`
- `LandslidesFilters.tsx`
- `WaterAlertsFilters.tsx`
- `NetOutagesFilters.tsx`
- `MaritimeWarningsFilters.tsx`

For mixed chips + interval layers, render interval first, then existing chip controls:
- `FloodFilters.tsx`
- `TornadoFilters.tsx`
- `HeatColdFilters.tsx`
- `AvalancheFilters.tsx`
- existing `MilitaryTrackerFilters.tsx`
- existing `NuclearTestsFilters.tsx`

## Default interval seeds used
Set in `src/store/map-layer/index.ts`:
- `nuclear_tests`: `30d`
- `military_tracker`: `3d`
- `live_news`: `7d`
- `net_outages`: `7d`
- `landslides`: `30d`
- `water_alerts`: `30d`
- `maritime_warnings`: `30d`
- `floods`: `30d`
- `heat_cold`: `30d`
- `avalanches`: `30d`

## Custom per-layer interval types used

### Earthquake — `EarthquakeInterval` with past + `-future` suffix
- Project-owned doc: `docs/map-layer-temporal-filters.md` (also referenced from `AGENTS.md` decision table). Treat this as the durable source before profile-level notes.
- File: `src/hooks/query/maps/useEarthquakesGeoJson.ts`
- Options: `'1y' | '90d' | '30d' | '7d' | '3d' | '3d-future' | '7d-future' | '30d-future' | '90d-future' | '1y-future'`
- Transport: `start_date` + `end_date` via `getDateRangeFromInterval`
- `-future` is literal future, not “feature”: `30d-future` means from now to 30 days ahead.
- `getDateRangeFromInterval()` owns future handling. Do not slice suffixes in layer hooks; pass `interval` through and let the utility return `[now, now + N days]` for future options.
- Do **not** add magnitude/significance params for future intervals; future only changes date range.
- Layer key: `earthquakes`
- Default: `3d`
- UI: custom "Time Window" chips above magnitude chips in `EarthquakeFilters.tsx`; use explicit human labels (`Last 3 Days`, `Last 7 Days`, `Next 3 Days`, `Next 30 Days`), not raw option values.
- When adding a new interval, update both `EarthquakeInterval`/`EARTHQUAKE_INTERVAL_OPTIONS` and `EARTHQUAKE_INTERVAL_LABELS`, then run touched-file type-check grep because repo-wide generated zod errors may be pre-existing.

## Verification lesson
Run `pnpm type-check`, then separate:
- new errors caused by interval changes
- existing repo failures unrelated to work

In this session, repo had many pre-existing errors. New work also exposed pre-existing stale `news` references, but touched files themselves did not add fresh type-check failures after removing synthetic `news` state entry.
