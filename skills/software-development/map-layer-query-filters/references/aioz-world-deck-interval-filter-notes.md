# AIOZ World Deck interval-filter rollout notes

## Durable lessons

### 1. Raw query state vs backend request state
For map-layer interval filters, Redux `layerQuery` should keep semantic state like:
- `interval: '3d'`
- `interval: '7d'`
- `interval: '30d'`

Hooks should translate that semantic state into backend params only inside fetch logic.

### 2. Query key rule
Use raw `query` / `layerQuery` directly in `queryKey`.

Bad:
- `queryKey` built from derived `start_date` / `end_date` / `since` / `until`

Good:
- `queryKey: queryKeys.getLayerGeoJSON(layer, query)`
- `queryKey: ['getNews', query]` or project-specific layer-key namespace if appropriate

### 3. API regen review pattern
After regenerating API spec, re-check generated query params before trusting earlier wiring.

Observed mapping from this session:
- `GetNewsData['query']` -> `start_date`, `end_date`
- `GetConflictMilitaryTrackerData['query']` -> `start_date`, `end_date`
- `GetNuclearTestData['query']` -> `since`, `until`
- `GetWeatherLandslideData['query']` -> `start_date`, `end_date`
- `GetWeatherSevereWeatherData['query']` -> `start_date`, `end_date`
- `GetCyberIntelligenceIodaOutageData['query']` -> `since`, `until`
- `GetMaritimeWarningData['query']` -> `since`, `until`

### 4. Layer-key alias pitfall
`live_news` is real map-layer key. Stale `news` refs can remain in:
- selectors
- config maps
- query key namespaces

### 5. Bulk-refactor pitfall
When mass-replacing date helper calls, formatting can degrade badly even if type-check still passes. Always do a readability pass after bulk edits.
