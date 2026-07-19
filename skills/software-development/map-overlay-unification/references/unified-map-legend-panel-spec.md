# Unified Map Legend Panel Spec - Session Notes

This is a condensed copy of the spec created during the session. The full spec lives at `docs/unified-map-legend-panel-spec.md`.

## Registry Design

```
MAP_PANEL_REGISTRY (mapLayerLegendRegistry.ts)
- earthquakes → panelId: earthquake_depth_legend, kind: legend, order: 100
- weather (dynamic) → panelId: weather_layer, kind: control, order: 20
```

Weather timeline (`weather_timeline`) intentionally excluded — stays as floating DraggablePanel.

## Component Changes

| File | Change |
|------|--------|
| mapLayerLegendRegistry.ts | Rename MAP_LAYER_LEGEND_REGISTRY → MAP_PANEL_REGISTRY, add kind + order |
| UnifiedLegendControlPanel.tsx | New: anchored bottom-right, flat tabs, lazy mount |
| MapControlsOverlay.tsx | Remove individual panels, add UnifiedLegendControlPanel + WeatherTimelineOverlay |
| MapPanelToolbar/index.tsx | Remove weather_layer toolbar item |
| EarthquakeDepthLegend.tsx | Strip DraggablePanel, render inline |
| WeatherLayerConfigPanel.tsx | Strip DraggablePanel, render inline |
| WeatherTimelineOverlay.tsx | **Reverted** - keep DraggablePanel |

## Key Patterns

### Registry Access with TS Safety
```ts
const item = MAP_PANEL_REGISTRY[layer as keyof typeof MAP_PANEL_REGISTRY];
```

### Theme Key Cast
```ts
const theme = WIDGET_THEME_REGISTRY[themeKey as keyof typeof WIDGET_THEME_REGISTRY];
```

### Tab Sorting
```ts
const KIND_ORDER = { control: 0, legend: 1 };
tabs.sort((a, b) => KIND_ORDER[a.kind] - KIND_ORDER[b.kind] || a.order - b.order);
```

### Lazy Content Mount
```ts
const getTabContent = (tab) => {
  switch (tab.id) {
    case 'earthquake_depth_legend': return <EarthquakeDepthLegend />;
    case 'weather_layer': return <WeatherLayerConfigPanel />;
  }
};
```

### Redux Sync
```ts
const openPanels = useAppSelector(state => state.mapPanels.open);
const handleTabClick = (tab) => {
  if (tab.id === activeTabId) dispatch(setPanelOpen({ id: tab.panelId, open: false }));
  else { tabs.forEach(t => dispatch(setPanelOpen({ id: t.panelId, open: false })));
    dispatch(setPanelOpen({ id: tab.panelId, open: true })); }
};
```

## Verification Commands
```bash
pnpm type-check   # Must pass
pnpm run build    # Must pass
```

## Rollback
```bash
git restore .
rm src/components/widget/MaplibreViewer/UnifiedLegendControlPanel.tsx
```