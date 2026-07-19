# Interval Styling Migration — 2026-06-10

## What was done

Standardized three patterns across all 11 map GeoJSON hooks and 6 filter
components:

### 1. Hook interval type: `string` → `SinceInterval`

**Before:**
```ts
const { interval, ...rest } = (query ?? {}) as SomeQuery & {
  interval?: string;
};
const [startDate, endDate] = getDateRangeFromInterval(
  (interval as SinceInterval | undefined) ?? 'all',
);
```

**After:**
```ts
const { interval, ...rest } = (query ?? {}) as SomeQuery & {
  interval?: SinceInterval;
};
const [startDate, endDate] = getDateRangeFromInterval(interval);
```

Changes:
- `interval?: string` → `interval?: SinceInterval`
- `(interval as SinceInterval | undefined) ?? 'all'` → `interval` (type already correct, `?? 'all'` was dead code)

Files: useAvalanchesGeoJson.ts (already done), useFloodsGeoJson.ts,
useHeatColdGeoJson.ts, useLandslidesGeoJson.ts, useMaritimeWarningsGeoJson.ts,
useMilitaryTrackerGeoJson.ts, useNetOutagesGeoJson.ts, useNewsGeoJson.ts,
useNuclearTestsGeoJson.ts, useTornadoesGeoJson.ts, useWaterAlertsGeoJson.ts.

### 2. Filter component: toggle-ternary → direct interval

Removed the toggle-off ternary from `handleSetFilterInterval` in all filter
components. The "All" button in `LayerIntervalFilters` already handles
toggling off via `onChange(undefined)`.

**Files:** FloodFilters, TornadoFilters, HeatColdFilters, IntervalLayerFilters,
NuclearTestsFilters, MilitaryTrackerFilters, AvalancheFilters.

### 3. GeoJSON hook: inline `getDateRangeFromInterval` calls → destructured variable

Extracted duplicate `getDateRangeFromInterval(...)[0]` / `[1]` inline calls
into a single `const [x, y] = getDateRangeFromInterval(interval)`.

**Files:** All 11 GeoJSON hooks (same set as #1).
