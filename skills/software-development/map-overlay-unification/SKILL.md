---
name: map-overlay-unification
description: Consolidate multiple floating map overlay panels (legends, controls, timelines) into a single anchored tabbed panel
category: software-development
tags: [maplibre, overlay, panel, legend, control, unified, draggable-panel]
---

# Unified Map Overlay Panel Pattern

## When to Use

Consolidating multiple floating/draggable map overlay panels (legends, controls, timelines, configs) into a single **anchored, non-draggable panel** with a flat tab list. Applies when:
- Multiple active map layers each render their own `DraggablePanel`
- Weather/map controls create separate overlays
- Visual clutter from overlapping panels confuses users
- Need consistent theming and behavior across all map overlays

## Core Pattern

### 1. Registry with Kind + Order

Extend or create a registry that includes both legends and controls:

```ts
// src/components/widget/MaplibreViewer/mapLayerLegendRegistry.ts
export type PanelKind = 'control' | 'legend';

export type MapPanelRegistryItem = {
  layer: MapLayer;
  panelId: MapPanelId;
  title: string;
  icon: Icon;
  themeKey: WidgetKey;
  kind: PanelKind;      // 'control' or 'legend'
  order: number;        // controls < legends, then by order
};

export const MAP_PANEL_REGISTRY: Partial<Record<MapLayer, MapPanelRegistryItem>> = {
  earthquakes: {
    layer: 'earthquakes',
    panelId: 'earthquake_depth_legend',
    title: 'Quake depth',
    icon: PulseIcon,
    themeKey: 'earthquake_tracker',
    kind: 'legend',
    order: 100,
  },
  // Weather controls added dynamically in panel component
};
```

### 2. Anchored Panel Component

```tsx
// src/components/widget/MaplibreViewer/UnifiedLegendControlPanel.tsx
const UnifiedLegendControlPanel = () => {
  // Build tabs from registry + dynamic entries (weather controls)
  const tabs = useMemo((): UnifiedTab[] => {
    const result: UnifiedTab[] = [];
    
    // Registry-based tabs (legends)
    for (const [layerKey, entry] of Object.entries(MAP_PANEL_REGISTRY)) {
      if (!activeLayers[layerKey]) continue;
      result.push({ ...entry, kind: entry.kind, order: entry.order });
    }
    
    // Dynamic controls (weather) - only when active
    if (mapStyle === MapStyle.WEATHER_MAP && activeWeatherLayer) {
      result.push({ id: 'weather_layer', kind: 'control', order: 20, ... });
    }
    
    // Sort: kind (controls first), then order
    return result.sort((a, b) => KIND_ORDER[a.kind] - KIND_ORDER[b.kind] || a.order - b.order);
  }, [activeLayers, mapStyle, activeWeatherLayer]);

  // Lazy mount: only render selected tab content
  const getTabContent = (tab: UnifiedTab) => {
    switch (tab.id) {
      case 'earthquake_depth_legend': return <EarthquakeDepthLegend />;
      case 'weather_layer': return <WeatherLayerConfigPanel />;
      default: return null;
    }
  };

  return (
    <div className="pointer-events-none absolute bottom-4 left-4 z-30">
      <div className="pointer-events-auto">
        {/* Tab bar - LiquidButton tabs */}
        <LiquidContainer className="rounded-t-lg">...</LiquidContainer>
        {/* Content panel - lazy mounted */}
        {activeTabId && <LiquidContainer className="rounded-b-lg">{getTabContent(activeTab)}</LiquidContainer>}
      </div>
    </div>
  );
};
```

### 3. Strip DraggablePanel from Content Components

Content components (`EarthquakeDepthLegend`, `WeatherLayerConfigPanel`) render **inline content only** — no `DraggablePanel` wrapper. They read `isOpen` from Redux (`state.mapPanels.open[panelId]`) and return `null` when closed.

### 4. Wire into MapControlsOverlay

```tsx
// MapControlsOverlay.tsx
return (
  <>
    <MapPanelToolbar />           {/* Toolbar buttons (map select, news, etc.) */}
    <MapSelect />
    <UnifiedLegendControlPanel /> {/* Single anchored panel for legends + controls */}
    <UnifiedSearchControl />
    <MapLayersFilterPopover />
  </>
);
```

### 5. Update Toolbar

Remove individual toolbar items for panels now in unified panel (e.g., `weather_timeline`, `weather_layer`). Keep only global tools (`map_select`, `news_list`) + legend tabs from registry.

## Key Decisions from This Project
## Key Decisions from This Project

| Decision | Rationale |
|----------|-----------|
| **Position**: bottom-right anchored (`bottom-4 right-4`) | Fixed position, no drag, predictable location (user override from original bottom-left) |
| **Tab order**: controls first, then legends | Controls are actionable; legends are reference |
| **Lazy mount**: `getTabContent()` switch on active tab | Only mount heavy content when selected |
| **Redux sync**: read `state.mapPanels.open`, dispatch `setPanelOpen` | Single source of truth for open/close |
| **Weather timeline**: kept separate (own DraggablePanel) | User preference: timeline stays floating |
| **Weather layer config**: included in unified panel | User preference: config tab in unified panel |
| **Theme**: `LiquidContainer` + `WIDGET_THEME_REGISTRY[themeKey]` + `createActiveControlStyle()` | Consistent with MapPanelToolbar |
| **Spec file created**: `docs/unified-map-legend-panel-spec.md` | Documents requirements, acceptance criteria, rollback plan |

## Pitfalls

- **Don't forget to update registry imports** — old `MAP_LAYER_LEGEND_REGISTRY` references will break TypeScript
- **Type the registry access** — `MAP_PANEL_REGISTRY[layer as keyof typeof MAP_PANEL_REGISTRY]` for TS safety
- **Theme key cast** — `WIDGET_THEME_REGISTRY[themeKey as keyof typeof WIDGET_THEME_REGISTRY]`
- **Weather controls are dynamic** — not in registry; added in component based on `activeWeatherLayer`
- **MapLayerLegend bottom-center bar** — keep separate for `conflict_zones` (whitelisted), not in unified panel
- **Don't force weather timeline into unified panel** — user preference: keep it separate as DraggablePanel
- **Revert if user says "revert changes"** — `git restore .` + `rm UnifiedLegendControlPanel.tsx` returns to cleanly

## Verification

```bash
pnpm type-check   # Must pass
pnpm run build    # Must pass
```

## References

- `references/unified-panel-implementation.md` — Full implementation notes from this session
- `references/registry-pattern.md` — Registry type definitions and usage