# Unified Legend/Control Panel Implementation — Session Notes

## Context
User wanted to consolidate multiple floating legend/control panels into a single anchored panel with tabs.
Original state: `EarthquakeDepthLegend` (DraggablePanel), `WeatherTimelineOverlay` (DraggablePanel), `WeatherLayerConfigPanel` (DraggablePanel), `MapLayerLegend` (bottom-center bar).
Each panel rendered independently, causing overlap and confusion when multiple active.

## User Preferences Discovered
1. **Position**: bottom-right (initially asked bottom-left, then corrected to bottom-right)
2. **Tab order**: Controls first, then Legends
3. **Lazy mount**: Same pattern as layer lazy mounting — only render active tab content
4. **Weather timeline**: Keep as separate floating DraggablePanel (not in unified panel)
5. **Weather layer config**: Group in unified panel (Control tab)
6. **Earthquake legend**: Group in unified panel (Legend tab)

## Implementation Flow

### 1. Registry Update (`mapLayerLegendRegistry.ts`)
- Renamed `MAP_LAYER_LEGEND_REGISTRY` → `MAP_PANEL_REGISTRY`
- Added `kind: 'control' | 'legend'` and `order: number` fields
- Only `earthquakes` entry in registry (weather controls handled dynamically)

### 2. New Component (`UnifiedLegendControlPanel.tsx`)
- Anchored `bottom-4 right-4 z-30`
- Builds tabs from registry + dynamic weather config
- Sorts by `kind` (controls first) then `order`
- Reads `state.mapPanels.open` for sync, dispatches `setPanelOpen`
- Lazy content via `getTabContent()` switch on active tab ID

### 3. Wiring (`MapControlsOverlay.tsx`)
- Removed: `EarthquakeDepthLegend`, `MapLayerLegend`, `WeatherLayerConfigPanel`, `WeatherTimelineOverlay`
- Added: `UnifiedLegendControlPanel`
- Kept: `WeatherTimelineOverlay` conditional on weather map

### 4. Toolbar Cleanup (`MapPanelToolbar/index.tsx`)
- Removed `weather_timeline`, `weather_layer` from `TOOLBAR_ITEMS`
- Registry legend items filtered by `kind === 'legend'`

### 5. Panel Content Simplification
- `EarthquakeDepthLegend.tsx`: Removed `DraggablePanel` wrapper
- `WeatherLayerConfigPanel.tsx`: Removed `DraggablePanel` wrapper
- `WeatherTimelineOverlay.tsx`: **Reverted** — kept `DraggablePanel` (floating)

## TypeScript Patterns Used
```ts
// Registry access with type safety
const item = MAP_PANEL_REGISTRY[layer as keyof typeof MAP_PANEL_REGISTRY];

// Theme registry access
const theme = WIDGET_THEME_REGISTRY[themeKey as keyof typeof WIDGET_THEME_REGISTRY];
```

## Verification
```bash
pnpm type-check  # ✓
pnpm run build   # ✓
```

## Open Questions / Follow-ups
- Mobile responsive behavior for anchored panel
- Whether `MapLayerLegend` bottom-center bar for `conflict_zones` should eventually unify
- Keyboard navigation for tabs (currently mouse-only)