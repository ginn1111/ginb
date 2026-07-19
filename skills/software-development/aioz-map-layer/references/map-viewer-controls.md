# Map viewer controls and drawer pitfalls

Applies to AIOZ World Deck map-side controls mounted inside `MaplibreViewer`.

## Left-side layer filter drawer migration

When moving `MapLayersFilter` from a floating `DraggablePanel` into a left `LiquidDrawer`:

- Keep `MapLayersFilter` content and Redux `layers_filter` state unchanged.
- Change only outer container behavior in `src/components/widget/MapLayersFilter/popover.tsx`.
- Mount the drawer into `#maplibre-viewer-shell`.
- Reuse the existing map drawer shell pattern from `WeatherForecastDrawer` / `FlightDetailDrawer`.

## Persistent trigger rule

If the drawer needs its own map-side trigger, do **not** gate the whole component on `isOpen`.
The trigger must remain rendered while the drawer is closed.

Pattern:
- always render trigger control
- render drawer with `open={isOpen}`
- use existing `togglePanel('layers_filter')` / `setPanelOpen(...)` state flow

## Toolbar-clone trigger pattern

If product wants the new trigger to match `MapPanelToolbar`, clone these traits from `src/components/widget/MaplibreViewer/MapPanelToolbar/index.tsx`:

- `LiquidButton size="icon-xs"`
- `variant={isOpen ? 'secondary' : 'ghost'}`
- `createActiveControlStyle(theme)` when open
- `liquidOptions` with `borderLight`, `blur: 2`, `brightness: 50`
- same icon weight flip: `fill` when active, `regular` when inactive
- wrap with `LiquidTooltip`

## Positioning pitfall

Do **not** absolutely position the cloned left-side trigger with hardcoded `top/left` if the page already has a left overlay stack such as `UnifiedSearchControl`.

Instead:
- place the trigger inside the same left overlay cluster in `MapControlsOverlay`
- let the parent overlay own absolute positioning
- use vertical stacking when search and trigger should not overlap

## Z-index pitfall with unified search

When `UnifiedSearchControl` can expand its own floating panel, the layer-filter toggle must stay visually behind search.

Rules:
- do not give the cloned trigger its own stronger local z-index
- prefer the parent left overlay stack z-index
- if search and trigger share a cluster, search should render before the toggle in DOM order

## Drawer dismissal pitfall

`LiquidDrawer` / Vaul treats map canvas interaction as outside interaction by default.
If users must drag/pan/click the map while keeping the drawer open, set:

- `dismissible={false}` on the drawer

Otherwise map clicks can fire outside-dismiss and hide the drawer even though the map interaction itself never touched `layers_filter` Redux state.

## Duplication cleanup

If a new left-side trigger replaces an older right-side toolbar trigger, remove the old `layers_filter` item from `MapPanelToolbar` to avoid duplicate entry points.
