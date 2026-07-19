# Net outages severity filter

## Use case
Map layer `net_outages` needs categorical severity filter plus existing interval filter.

## Backend shape
Generated query type `GetCyberIntelligenceIodaOutageData['query']` includes:
- `severity?: string`
- `country?: string`
- `since?: string`
- `until?: string`

Hook `useNetOutagesGeoJSON` already translates `interval` from layerQuery into `since` / `until`, so UI-only change can add severity without hook refactor.

## UI pattern
For this layer, severity options are:
- `normal`
- `critical`

Implementation pattern:
- keep `LayerIntervalFilters`
- add `LayerFilters` beneath it
- use single-select categorical behavior:
  - click inactive pill -> set `severity`
  - click active pill -> clear to `undefined`
  - `All` button clears `severity`
- compare case-insensitively when matching active option

## Header rule
Because severity here is single-select, show active label next to title:
- `Severity (Normal)`
- `Severity (Critical)`
- `Severity (All)`

Do not show multi-select count UI like `(1/2)` for this case.

## Files touched in session pattern
- `src/components/widget/MapLayersFilter/NetOutagesFilters.tsx`
- `src/components/widget/MapLayersFilter/LayerFilters.tsx`

## Reusable lesson
When a map-layer categorical filter is mutually exclusive and semantically one-of-N, extend shared `LayerFilters` with an optional header label override instead of building custom one-off header markup in the layer component.
