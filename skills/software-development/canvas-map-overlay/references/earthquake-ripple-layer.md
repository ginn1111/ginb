# Reference: Earthquake Ripple Layer

Implementation: `src/components/widget/MaplibreViewer/EarthquakeLayer.tsx`

## Pipeline

GeoJSON hook → `toEarthquakeDeckData()` → `getVisibleRippleData()` (filters by mag bounds + horizon clip)

## Canvas

Overlay `<canvas>` with `mixBlendMode: 'screen'`, `pointer-events: none`. Reuses existing by id `#earthquake-ripple-overlay` instead of creating each mount.

## Hit Layers

MapLibre Source + 3 invisible circle Layers filtered by mag threshold:
- `eq-level1`: mag < 3, radius 10
- `eq-level2-inner`: mag >= 3 && < 5, radius 12  
- `eq-level3-inner`: mag >= 5, radius 14

All at `circle-opacity: 0.01`, `circle-color: 'rgba(255,255,255,0.01)'`. These layers ARE in `interactiveLayerIds` via `selectInteractiveLayerIds` — global map click handler dispatches selection for all quakes (clusters included). Manual click discrimination was attempted and reverted; preference is to keep layers interactive globally.

## Constants

| Constant | Value | Purpose |
|---|---|---|
| `CLUSTER_MERGE_RADIUS_PX` | 48 | Screen-space cluster threshold |
| `RIPPLE_DURATION_MS` | 2400 | One ripple cycle |
| `RIPPLE_TARGET_FRAME_INTERVAL_MS` | 41.67 | 24fps throttle |
| `RIPPLE_CANVAS_MAX_DPR` | 1.25 | Perf cap |
| `RIPPLE_VIEWPORT_PADDING_PX` | 80 | Cull off-screen |
| `MAX_RIPPLE_POINTS` | 90 | Soft cap |
| `HORIZON_COSINE_PADDING` | -0.08 | Globe clip margin |

## Cluster Dot Scaling

```ts
const baseCoreRadius = Math.min(9, 2.5 + mag * 0.7);
const countScale = 1 + Math.log2(Math.max(weightedCount, 1)) * 0.35;
const coreRadius = Math.min(18, baseCoreRadius * countScale);  // dot grows with cluster
const maxRadius = Math.min(72, 18 + mag * 8);  // rings stay fixed
```

## Globe Horizon Clip

```ts
const cosDist = Math.sin(lat) * Math.sin(center.lat) +
  Math.cos(lat) * Math.cos(center.lat) * Math.cos((lng - center.lng) * DEG_TO_RAD);
if (cosDist < -0.08) continue;
```

## Selected Entity Popup

Condition: `selectedEntity?.layer === 'earthquakes'`. Uses `<Popup>` with `POPUP_INTERACTIVE_CLASS`. Content via `PopupCard`: id, location, time, magnitude, depth.
