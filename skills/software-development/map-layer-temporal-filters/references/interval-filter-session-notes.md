# Session: Wire interval filters for 11 map layers

## What was done
Added interval-based date filtering across semantic map layers in AIOZ World Deck.
Filter state stores semantic interval (`'3d'|'7d'|'30d'|'all'`), hooks convert to
concrete API params (`start_date`/`end_date`/`since`/`until`) at fetch time.
Cache keys use raw `layerQuery` directly.

## Key refactors
- Removed `getIntervalStartDate` / `getIntervalEndDate` helpers — all callers inline
  `getDateRangeFromInterval(...)[N]?.toISOString()` directly
- `getDateRangeFromInterval` end bound changed: `startOf('day')` → `add(1, 'day').startOf('day')`
  (includes full current day, not just up to current midnight)
- Query keys moved from derived-date objects to raw `layerQuery`:
  - before: `queryKey: queryKeys.getLayerGeoJSON('water_alerts', { ...query, start_date, end_date })`
  - after: `queryKey: queryKeys.getLayerGeoJSON('water_alerts', query)`

## Files changed (33 total)

### Core utility
- `src/utils/intervalFilter.ts` — removed 2 helpers, added `SinceInterval` type, end-bound shift

### Config / store
- `src/constants/mapLayerConfig.ts` — `news` → `live_news`
- `src/constants/mapLayers.ts`
- `src/constants/mapLayerFilter/index.ts`
- `src/store/map-layer/index.ts` — interval defaults for 8 layers
- `src/store/map-filter-layer-registry.ts` — 5 new filter UIs registered

### Filter UI (new)
- `src/components/widget/MapLayersFilter/IntervalLayerFilters.tsx`
- `src/components/widget/MapLayersFilter/LiveNewsFilters.tsx`
- `src/components/widget/MapLayersFilter/LandslidesFilters.tsx`
- `src/components/widget/MapLayersFilter/WaterAlertsFilters.tsx`
- `src/components/widget/MapLayersFilter/NetOutagesFilters.tsx`
- `src/components/widget/MapLayersFilter/MaritimeWarningsFilters.tsx`

### Filter UI (extended)
- `src/components/widget/MapLayersFilter/FloodFilters.tsx`
- `src/components/widget/MapLayersFilter/TornadoFilters.tsx`
- `src/components/widget/MapLayersFilter/HeatColdFilters.tsx`
- `src/components/widget/MapLayersFilter/AvalancheFilters.tsx`
- `src/components/widget/MapLayersFilter/NuclearTestsFilters.tsx`

### Filter UI (infrastructure)
- `src/components/widget/MapLayersFilter/LayerFilters.tsx`
- `src/components/widget/MapLayersFilter/LayerIntervalFilters.tsx`
- `src/components/widget/MapLayersFilter/index.tsx`

### Layer components
- `src/components/widget/MaplibreViewer/NewsLayer.tsx` — `news` → `live_news`
- `src/components/widget/MaplibreViewer/LiveNews/ListNewsPopup.tsx`

### Hooks (11 files)
- `src/hooks/query/maps/useMilitaryTrackerGeoJson.ts`
- `src/hooks/query/maps/useNuclearTestsGeoJson.ts`
- `src/hooks/query/maps/useNewsGeoJson.ts`
- `src/hooks/query/maps/useWaterAlertsGeoJson.ts`
- `src/hooks/query/maps/useLandslidesGeoJson.ts`
- `src/hooks/query/maps/useFloodsGeoJson.ts`
- `src/hooks/query/maps/useTornadoesGeoJson.ts`
- `src/hooks/query/maps/useHeatColdGeoJson.ts`
- `src/hooks/query/maps/useAvalanchesGeoJson.ts`
- `src/hooks/query/maps/useNetOutagesGeoJson.ts`
- `src/hooks/query/maps/useMaritimeWarningsGeoJson.ts`

## Param mapping table

| Layer | Backend params | Condition |
|-------|---------------|-----------|
| `nuclear_tests` | `since`, `until` | was `since` only before spec regen |
| `military_tracker` | `start_date`, `end_date` | unchanged |
| `net_outages` | `since`, `until` | new |
| `maritime_warnings` | `since`, `until` | new |
| `live_news` | `start_date`, `end_date` | was client-side `pubDate` filter |
| `landslides` | `start_date`, `end_date` | new |
| `water_alerts` | `start_date`, `end_date` | new |
| `floods` | `start_date`, `end_date` | new |
| `tornadoes` | `start_date`, `end_date` | new |
| `heat_cold` | `start_date`, `end_date` | new |
| `avalanches` | `start_date`, `end_date` | new |

## Verification
- `pnpm type-check` — 290 total errors, all pre-existing (generated zod, unrelated widgets)
- Zero errors in any touched file from the interval rollout
- Targeted grep confirmed: `pnpm type-check 2>&1 | rg -n "use(WaterAlerts|Landslides|...|News)GeoJson"` → empty

## Review items flagged (not blockers)
1. End-boundary semantic change (`+1 day`)
2. `useNewsGeoJson` cache namespace changed (`['getNews', ...]` → `queryKeys.getLayerGeoJSON(...)`)
3. `tornadoes` still lacks default interval (siblings have `interval: '30d'`)
4. `nuclear_tests` now bounded (was open-ended `since`)
