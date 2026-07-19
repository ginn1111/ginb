# Earthquakes magnitude filter pattern

Use when map layer needs interval filter plus earthquake magnitude bounds.

## Files touched
- `src/components/widget/MapLayersFilter/EarthquakeFilters.tsx`
- `src/store/map-filter-layer-registry.ts`
- `src/store/map-layer/index.ts`
- `src/hooks/query/maps/useEarthquakesGeoJson.ts`

## Pattern
- Redux `layerQuery` stores UI state: `interval`, `mag_from`, `mag_to`
- hook keeps raw `query` in `queryKey`
- hook strips `interval` before SDK call
- hook translates `interval -> start_date/end_date` with `getDateRangeFromInterval(interval)`
- hook passes `mag_from` / `mag_to` through unchanged to `getWeatherEarthquake`
- filter UI uses two numeric inputs for min/max magnitude and writes `undefined` when cleared

## Reason
Earthquake endpoint supports both temporal bounds and scalar magnitude bounds. Interval plumbing must not drop endpoint-native filters while translating UI-only state.

## Verification note
Repo-wide `pnpm type-check` was blocked by pre-existing generated-file errors in `src/__generated__/api/zod.gen.ts`. Touched files produced no targeted type-check hits.
