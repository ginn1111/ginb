---
name: map-gl-overlay-integration
description: "Integrate third-party WebGL rendering engines (L7, Deck.gl, Three.js) as non-native overlays on MapLibre/Mapbox maps. Covers scene lifecycle, map adapter wiring, type pitfalls, and data-update patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [map, gl-overlay, l7, deckgl, threejs, maplibre, react]
---

# Map GL Overlay Integration

Use this when wiring a third-party GL rendering library (AntV L7, Deck.gl, Three.js custom layers, etc.) as a visual overlay on an existing MapLibre or Mapbox GL map in a React app.

---

## General pattern

Every GL-overlay-on-map integration follows the same lifecycle:

1. **Mount a container div** absolute-positioned inside the map container, `pointer-events-none` to pass clicks through to the map.
2. **Create a Scene/Renderer** that wraps the existing map instance (not a new map).
3. **Add layers** after the scene emits its `loaded` event.
4. **Update data** via the library's layer-setData equivalent.
5. **Destroy** on unmount.

```
┌─────────────────────┐
│    MapLibre map      │
│  ┌───────────────┐  │
│  │ GL overlay div │  │  ← pointer-events-none
│  │  (L7 / etc.)   │  │
│  └───────────────┘  │
└─────────────────────┘
```

---

## Pitfalls

### 1. Chainable methods lose concrete type

L7 PointLayer/HeatmapLayer chain methods (`.source().shape().size().color().style()`) return `ILayer`, **not** the concrete class. Any ref typed as `HeatmapLayer | null` fails assignment.

```ts
// ❌ TS error — .source() returns ILayer, not HeatmapLayer
const heatRef = useRef<HeatmapLayer | null>(null);
heatRef.current = new HeatmapLayer().source(data).shape('heatmap'); // Type 'ILayer' not assignable

// ✅ Use ILayer for refs
import type { ILayer } from '@antv/l7';
const heatRef = useRef<ILayer | null>(null);
```

Same for `PointLayer`, `LineLayer`, etc.

### 2. Scene init before data arrives

The scene's `loaded` callback fires asynchronously — data may arrive before or after. Use a ref to track latest data:

```ts
const dataRef = useRef<FeatureCollection | null>(data);
useEffect(() => { dataRef.current = data; }, [data]);

// Inside scene.on('loaded'):
const latest = dataRef.current ?? []; // always fresh
```

### 3. Destroy is mandatory

Failing to call `scene.destroy()` on unmount leaks WebGL resources and event listeners. Always return a cleanup from the init effect.

### 4. Recreate vs update

Destroying and recreating the whole scene on every data poll causes visible flash. Prefer a two-effect pattern:

- `useEffect #1` — scene init (depends only on `map` instance, runs once)
- `useEffect #2` — data update (depends on `data`, calls `layer.setData()`)

Gate effect #2 with a `readyRef` that flips to `true` inside `loaded`.

### 5. Overlay lives outside react-map-gl `<Map>` component

L7 creates its own WebGL canvas on top of the map. Do NOT render the L7 container div as a child of react-map-gl's `<Map>` component. Place it as a **sibling** of `<Map>` inside the map shell div, with `absolute inset-0 pointer-events-none`.

```tsx
<div className=\"relative min-h-0 flex-1\">
  <Map ...>
    {/* MapLibre-native Source/Layer children go here */}
    <MapLayersStack />
  </Map>

  {/* L7 overlay — sibling of <Map>, positioned absolutely */}
  <MyL7Overlay mapRef={mapRef} />

  {/* Other UI overlays */}
  <MapPanelToolbar />
</div>
```

### 6. SSR guard — dynamic import with `ssr: false`

L7 accesses `window` and `document` at import time. In Next.js App Router, always import the overlay component via `next/dynamic`:

```tsx
import dynamic from 'next/dynamic';

const MyOverlay = dynamic(() => import('./MyOverlay'), { ssr: false });
```

The component file itself must start with `'use client'`.

### 7. Canvas animation performance budget

For 2D canvas overlays on top of MapLibre, treat every per-frame operation as hot-path code. Avoid drawing every data point at full refresh rate.

Recommended defaults:
- Cap animated points to the highest-signal subset (e.g. top 50-100 by magnitude/severity), not the full feed.
- Throttle animation to ~24fps (`1000 / 24`) unless smooth particle motion truly needs 60fps.
- Cap DPR around `1`-`1.25` for full-screen overlays; high DPR multiplies fill work.
- Use viewport culling before arcs/strokes.
- Avoid per-point gradients and shadows in the frame loop. Use simple strokes/fills, or pre-render sprites if glow is required.
- Reduce ring count before reaching for workers/offscreen canvas. One or two rings usually reads well; three rings across hundreds of points is expensive.

If a user reports map lag after adding a canvas expression layer, first cut point count, FPS, DPR, shadows/gradients, and ring count before changing architecture.

### 8. Map instance from react-map-gl + Redux layer toggle pattern

When the map is managed by `react-map-gl` and layer state comes from Redux:

```tsx
// In MaplibreViewer parent:
import { useRef, useState } from 'react';
import type { MapRef } from 'react-map-gl/maplibre';

const mapRef = useRef<MapRef>(null);
const [rawMap, setRawMap] = useState<maplibregl.Map | null>(null);

<Map
  ref={mapRef}
  onLoad={() => setRawMap(mapRef.current?.getMap() ?? null)}
>
```

```tsx
// In overlay component:
import { useAppSelector } from '@/store/hooks';
import { getActiveLayerById, getLayerQuerySelector } from '@/store/map-layer';
import { useDomainGeoJSON } from '@/hooks/query/maps/useDomainGeoJson';

const isActive = useAppSelector((s) => getActiveLayerById(s, 'my_layer_key'));
const layerQuery = useAppSelector((s) => getLayerQuerySelector(s, 'my_layer_key'));
const { data } = useDomainGeoJSON(layerQuery, { enabled: isActive });

const geoJSON = data?.geoJSON ?? null;

// Resolve raw map instance from ref (may not be ready at first render):
const [map, setMap] = useState<maplibregl.Map | null>(null);
useEffect(() => {
  if (!isActive) return;
  const m = mapRef.current?.getMap();
  if (m) { setMap(m); return; }
  const id = setInterval(() => {
    const m2 = mapRef.current?.getMap();
    if (m2) { setMap(m2); clearInterval(id); }
  }, 100);
  setTimeout(() => clearInterval(id), 3000);
  return () => clearInterval(id);
}, [isActive, mapRef]);

if (!isActive) return null;
return <MyL7Overlay map={map} data={geoJSON} />;
```

---

## Canvas 2D overlay on MapLibre

Use this when a layer is visual-only, high-frequency, or needs trail/fade effects (wind particles, animated flow lines) and does not need MapLibre hit-testing.

**Wire pattern:** create a normal DOM `<canvas>` inside `map.getContainer()`, position it over the map, and set `pointer-events: none` so MapLibre still receives drag/hover/click events.

```ts
const map = mapRef.current?.getMap();
const container = map.getContainer();

const canvas = document.createElement('canvas');
canvas.style.position = 'absolute';
canvas.style.inset = '0';
canvas.style.pointerEvents = 'none';
container.appendChild(canvas);
```

**Reuse pattern (avoid duplicate canvases on effect re-run):** when the canvas effect may run multiple times (e.g. React Strict Mode, dependency changes), check for an existing canvas by id before creating a new one:

```ts
const CANVAS_ID = 'my-overlay';

let canvas = container.querySelector(`#${CANVAS_ID}`) as HTMLCanvasElement | null;
if (!canvas) {
  canvas = document.createElement('canvas');
  canvas.id = CANVAS_ID;
  canvas.style.position = 'absolute';
  canvas.style.inset = '0';
  canvas.style.pointerEvents = 'none';
  container.insertBefore(canvas, container.querySelector('.maplibregl-control-container'));
}
rippleCanvasRef.current = canvas;
```

The cleanup function should still `canvas.remove()` — the id‑based query ensures the next effect run finds the element rather than creating a new one.

**Projection bridge:** keep simulation state in geographic coordinates, draw in screen pixels, then convert back.

```ts
const start = map.project([particle.lng, particle.lat]); // lng/lat -> x/y
const nextX = start.x + vx * stepPx;
const nextY = start.y + vy * stepPx;
ctx.moveTo(start.x, start.y);
ctx.lineTo(nextX, nextY);
const next = map.unproject([nextX, nextY]); // x/y -> lng/lat
particle.lng = next.lng;
particle.lat = next.lat;
```

**Pure-canvas interaction replacement:** if the user asks to remove Deck.gl / third-party picking, or if native MapLibre clustering does not match the custom canvas visual clustering, keep the canvas `pointer-events: none` and add MapLibre event listeners on the map instead of making the canvas interactive. Hit-test against the **same screen-space points the canvas draws** when interaction must match custom grouping; otherwise hit-test the full data set for per-point hover/click.

```ts
const findNearest = (map: maplibregl.Map, data: Datum[], point: maplibregl.Point) => {
  let nearest: Datum | null = null;
  let best = HIT_RADIUS_PX * HIT_RADIUS_PX;

  for (const item of data) {
    const p = map.project([item.longitude, item.latitude]);
    const dx = p.x - point.x;
    const dy = p.y - point.y;
    const d2 = dx * dx + dy * dy;
    if (d2 <= best) {
      nearest = item;
      best = d2;
    }
  }

  return nearest;
};

map.on('mousemove', (event) => {
  const item = findNearest(map, data, event.point);
  map.getCanvas().style.cursor = item ? 'pointer' : '';
  // Dispatch existing hover entity shape here.
});

map.on('click', (event) => {
  const item = findNearest(map, data, event.point);
  if (!item) return;
  // Dispatch existing selected entity shape here.
});
```

Use the full data set for hit-testing if popup/hover should work on all points; keep the animated draw set capped separately for performance. But if canvas compresses / merges points visually (earthquake swarms, dense pulses), do **not** also enable MapLibre source clustering for interaction: native supercluster membership will differ from the custom screen-space compression. In that case, store the latest drawn compressed points in a ref, hit-test those points on `mousemove` / `click`, and resolve the chosen compressed point's representative id back to the original datum for popup details.

**Mercator:** this is a strong fit. Rebuild any screen-space lookup grid after move/zoom/resize/style changes, and clear/reseed particles when map interaction settles instead of trying to transform old trails.

**Globe:** same `project`/`unproject` calls work, but the canvas remains a flat screen overlay. It has no depth test, no automatic horizon/backside clipping, and can draw over empty space near the globe limb. For clean globe output, add explicit visible-hemisphere / globe-disc clipping, or use a real MapLibre custom WebGL layer when particles must hug the globe surface with true occlusion.

For canvas point overlays in MapLibre globe mode, wrap projection in a helper and use it in **both** drawing and pure-canvas hit testing. Native `map.project([lng, lat])` gives screen coordinates, but you must skip backside points yourself:

```ts
const HORIZON_COSINE_PADDING = -0.08;
const toRadians = (degree: number) => (degree * Math.PI) / 180;
const isGlobeProjection = (map: maplibregl.Map) => map.getProjection()?.type === 'globe';

const isOnVisibleGlobeHemisphere = (map: maplibregl.Map, item: { latitude: number; longitude: number }) => {
  if (!isGlobeProjection(map)) return true;

  const center = map.getCenter();
  const centerLat = toRadians(center.lat);
  const itemLat = toRadians(item.latitude);
  const deltaLng = toRadians(item.longitude - center.lng);
  const cosine =
    Math.sin(centerLat) * Math.sin(itemLat) +
    Math.cos(centerLat) * Math.cos(itemLat) * Math.cos(deltaLng);

  return cosine >= HORIZON_COSINE_PADDING;
};

const projectOverlayPoint = (map: maplibregl.Map, item: { latitude: number; longitude: number }) => {
  if (!isOnVisibleGlobeHemisphere(map, item)) return null;
  const point = map.project([item.longitude, item.latitude]);
  if (!Number.isFinite(point.x) || !Number.isFinite(point.y)) return null;
  return point;
};
```

If a layer only wants animated pulses for high-signal events, filter animation data separately from interaction data. Example: draw only earthquakes with `magnitude >= 5`, but keep full earthquake data for hover/click so non-pulsing events remain selectable.

For map-layer query hooks that return GeoJSON artifacts (`{ geoJSON, mapById }`), prefer `mapById` as the canonical source row store for canvas overlay builders and hover/selected payloads. Build render/hit-test data from `Array.from(data.mapById.values())`, then when hover finds a nearest screen-space datum, resolve the original row with `data.mapById.get(item.id)` before dispatching tooltip properties. This keeps hover/selected details aligned with the same IDs used by generated GeoJSON features and avoids stale shape drift from parallel raw-query hooks.

For a lightweight glow on pulsing canvas points, prefer one cheap filled halo circle around the core with low alpha instead of `shadowBlur` or radial gradients in the frame loop. Example: draw `coreRadius * 2.4` at `0.18` alpha, then the solid core. Add a second filled halo only when visual specs require a stronger glow and perf remains acceptable.

For severity-coded ripple patterns, map the semantic level to ring count instead of hardcoding one count for every point. Keep the animation dataset separate from hit-testing data: draw only points that should visibly pulse, but allow hover/click against the full feed if needed. Example earthquake mapping: level 1 / moderate (`3 <= magnitude < 5`) → 1 ring, level 2 / strong (`5 <= magnitude < 7`) → 2 rings, level 3 / major (`magnitude >= 7`) → 3 rings. Use `ringDelay = RIPPLE_DURATION_MS / ringCount` so rings are evenly phased over the animation cycle. Guard against accidental high ring counts (e.g. `10`) because ring count is hot-path draw work.

**Hybrid interaction — MapLibre Source/Layer + canvas visuals.** When a layer needs animated canvas effects (ripples, particles, pulses) but also needs native MapLibre hover/click/popup, prefer rendering **invisible circle layers as children of `<Source>`** inside `<Map>` for interaction, while keeping the canvas purely visual with `pointer-events: none`. This avoids manual `findNearest` hit-testing math and gets native globe projection handling for free.

Important: when the canvas layer does its own screen-space compression/grouping, keep the MapLibre hit `<Source>` **unclustered**. Do not add `cluster` to the invisible hit source unless you intentionally want cluster hover/click. MapLibre supercluster and custom canvas compression use different merge radii/projection timing, so their grouped positions/counts can mismatch. Register only the invisible hit layer id as interactive; do not register the cluster layers.

```tsx
// In the layer component (child of <Map>):
import { Layer, Source } from 'react-map-gl/maplibre';

<Source id="my-layer" type="geojson" data={geoJSON}>
  {/* Invisible hit circles — MapLibre handles hover/click via queryRenderedFeatures */}
  <Layer
    id="my-layer-hit"
    type="circle"
    filter={['!', ['has', 'point_count']]}
    paint={{
      'circle-radius': 12,
      'circle-color': 'rgba(255, 255, 255, 0.01)',
      'circle-opacity': 0.01,
    }}
  />
</Source>
```

Pair this with a separate useEffect that creates a `<canvas>` inside `map.getContainer()` for visual animation. The parent component's global `handleMouseMove` (which calls `queryRenderedFeatures`) automatically dispatches `setHoveredEntity`/`setSelectedEntity` for features in these invisible layers — no per-layer mouse event handlers needed.

Key rules:
- Canvas stays `pointer-events: none` so it never blocks MapLibre interaction.
- Register the hit layer ids in the interactive layer selector (`selectInteractiveLayerIds`) gated behind `activeLayers.my_layer`.
- The layer ids must be present in the parent's `INTERACTIVE_LAYER_IDS` list (or the selector gates them directly as literal strings).
- If replacing or overlaying an older native layer with canvas visuals, keep any existing interactive native ids gated behind `activeLayers.my_layer` too; do not leave them always-on in `selectInteractiveLayerIds`. Add the new invisible hit id beside them.
- Prefer one generic invisible hit layer (e.g. `my-layer-hit`) over making every visual/ripple layer interactive. Let global `handleMouseMove` / `handleMapClick` read feature properties (`id`, `type`, coordinates) and drive existing tooltip/selection popup flow.
- Filter the invisible circles by magnitude/severity to create separate hit zones per level only when hit radius or payload must differ; otherwise a single unclustered hit layer is enough.
- Radius of invisible circles can vary by level (larger for stronger quakes) to improve click targeting on important features.
- Canvas animation data and hit-testing data are now decoupled: canvas draws only animated subset, interaction works on the full feed via MapLibre's native query.
- For globe projection, MapLibre's `queryRenderedFeatures` handles backside occlusion natively — the invisible layers are automatically not returned for backside features, unlike the manual canvas `projectEarthquake` helper.

Prefer this pattern over manual `map.on('mousemove')` + `findNearest` canvas hit-testing when the map already has a global `queryRenderedFeatures`-based hover handler (common in react-map-gl setups). It is less code, more robust, and globe-safe.

**Screen-space compression for dense canvas overlays:** when many data points cluster close together on screen (e.g. earthquake swarms), drawing individual ripples/pulses for each wastes GPU fill and creates visual noise. Compress them into a single visual at the centroid before each frame using a simple greedy screen-space cluster:

```ts
const CLUSTER_MERGE_RADIUS_PX = 48;

type CompressedPoint = {
  x: number;
  y: number;
  magnitude: number;
  depth: number;
  id: string;
  weightedCount: number;
};

const median = (values: number[]): number => {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
};

const compressScreenSpace = (
  map: maplibregl.Map,
  items: EarthquakeDeckDatum[],
): CompressedPoint[] => {
  // Project all items to screen coords
  const projected = [];
  for (const item of items) {
    const p = projectOverlayPoint(map, item);
    if (!p) continue;
    projected.push({ ...item, px: p.x, py: p.y });
  }

  const radiusSq = CLUSTER_MERGE_RADIUS_PX ** 2;
  const assigned: number[] = new Array(projected.length).fill(-1);
  const groups: number[][] = [];

  // Greedy clustering: for each unassigned point, find all neighbors within radius
  for (let i = 0; i < projected.length; i += 1) {
    if (assigned[i] !== -1) continue;
    const group: number[] = [i];
    assigned[i] = groups.length;
    for (let j = i + 1; j < projected.length; j += 1) {
      if (assigned[j] !== -1) continue;
      const dx = projected[i].px - projected[j].px;
      const dy = projected[i].py - projected[j].py;
      if (dx * dx + dy * dy <= radiusSq) {
        group.push(j);
        assigned[j] = groups.length;
      }
    }
    groups.push(group);
  }

  return groups.map((group) => {
    const members = group.map((idx) => projected[idx]);
    return {
      x: members.reduce((s, m) => s + m.px, 0) / members.length,
      y: members.reduce((s, m) => s + m.py, 0) / members.length,
      magnitude: median(members.map((m) => m.magnitude)),
      depth: median(members.map((m) => m.depth).filter(d => d != null)),
      id: members[0].id,
      weightedCount: members.length,
    };
  });
};

// In draw loop:
const compressed = compressScreenSpace(map, rippleData);
for (const point of compressed) drawRipple(point, time);
```

Key rules:
- Run compression **each frame** (points move relative to viewport on pan/zoom).
- Cluster radius (`CLUSTER_MERGE_RADIUS_PX`) sets the visual merge threshold. Tune per layer: 24px works for earthquake swarms on a full-screen map; larger for sparse layers or smaller viewports.
- Use **median** for aggregated values (magnitude, depth) to avoid outliers dominating the cluster visual.
- Compression runs before viewport culling — projected points already clipped to visible hemisphere are naturally excluded.
- The `projectEarthquake` helper (including globe hemisphere guard) must be reused from the existing projection helper, not duplicated.
- `weightedCount` is available for rendering a count badge or scaling visual size by cluster density. When scaling core radius, use a logarithmic factor so a cluster of 10 doesn't look 10× bigger than a single point — e.g. `1 + Math.log2(Math.max(weightedCount, 1)) * 0.35`, capped to a reasonable max (e.g. `Math.min(18, baseRadius * scale)`). Scale only the core dot area — do NOT scale ring/max radius, or rings will expand unnaturally on clusters.
- Count badge should be centered inside the core circle (textAlign=`center`, textBaseline=`middle`) at `(x, y)`.
- Canvas text font must inherit from the app's font-family: `getComputedStyle(document.documentElement).fontFamily`. Never hardcode `monospace` for UI labels — the app's body font reflects the design system.

**Cache compression output to skip recompute on unchanged viewport.** `compressScreenSpace` projects all points and clusters them — expensive at high point counts. Cache the raw result between frames when map viewport hasn't changed significantly:

```ts
const compressedCacheRef = useRef<{ key: string; raw: CompressedPoint[] }>({ key: '', raw: [] });

// In draw loop:
const center = map.getCenter();
const zoom = map.getZoom();
// Round to 1 decimal so tiny pans don't invalidate
const cacheKey = `${rippleData.length}:${center.lat.toFixed(1)}:${center.lng.toFixed(1)}:${zoom.toFixed(1)}`;

let raw: CompressedPoint[];
if (compressedCacheRef.current.key === cacheKey) {
  raw = compressedCacheRef.current.raw;                   // reuse
} else {
  raw = compressScreenSpace(map, rippleData);              // compute
  compressedCacheRef.current = { key: cacheKey, raw };
}
```

Key rules:
- Include data length in the key — if new points arrived, recompute even if viewport is same.
- Round map center and zoom to 1 decimal so sub‑threshold jitter doesn't flush the cache every frame.
- The lerp smoothing (next section) still runs on the cached raw result each frame, so visual motion from pan/zoom that barely misses the cache threshold remains smooth.
- Reset the cache when the canvas effect unmounts by letting the ref be garbage-collected with the component.
- This is purely visual — it does not affect `queryRenderedFeatures` or interaction (which remains on the full feed via MapLibre Source/Layer). Interaction and canvas visuals are fully decoupled.

**Frame-to-frame smoothing.** Raw compression snaps when cluster membership changes (points entering/exiting the merge radius on pan/zoom). Smooth the visual by lerping compressed points from the previous frame toward the current frame, keyed by `id`:

```ts
const prevCompressedRef = useRef<Map<string, CompressedPoint>>(new Map());

// In draw loop:
const raw = compressScreenSpace(map, rippleData);
const prev = prevCompressedRef.current;
const lerpFactor = 0.2; // higher = faster convergence

const compressed: CompressedPoint[] = raw.map((cur) => {
  const old = prev.get(cur.id);
  if (!old) return cur;
  return {
    x: old.x + (cur.x - old.x) * lerpFactor,
    y: old.y + (cur.y - old.y) * lerpFactor,
    magnitude: old.magnitude + (cur.magnitude - old.magnitude) * lerpFactor,
    depth: old.depth + (cur.depth - old.depth) * lerpFactor,
    id: cur.id,
    weightedCount: cur.weightedCount,
  };
});
prevCompressedRef.current = new Map(compressed.map((p) => [p.id, p]));
```

Rules:
- Use a **`Map<string, Т>`** (not an array) for O(1) lookup — the per-frame `.find()` over an array burns time as point count grows.
- Match by `id` (the same stable id from the source data, or the first member's id for cluster centroids). When a cluster splits, the main point retains the same id — the other split-off points don't match a previous entry and snap in cleanly.
- Lerp factor `0.2` converges in ~5 frames at 24fps (≈200ms). Tune per layer: smaller for smoother but laggy motion, larger for snappy but possible pop.
- Store the **smoothed** result (not the raw result) in the ref, so each frame continues from the last drawn position rather than jumping back to the true position — this ensures the visual never backtracks.
- The lerp runs on every frame regardless of cluster membership change, so it also smooths normal earthquake motion during map pan/zoom.

**Canvas resize in draw loop (lighter than ResizeObserver):** instead of adding a ResizeObserver, check `clientWidth`/`clientHeight` + `devicePixelRatio` at the top of the draw loop and only re-allocate the canvas buffer when dimensions actually change. This avoids the observer lifecycle and works well when the draw loop already runs at 24fps:

```ts
let width = 0, height = 0, dpr = 1;
const syncCanvasSize = () => {
  const nextW = Math.max(container.clientWidth, 1);
  const nextH = Math.max(container.clientHeight, 1);
  const nextDpr = Math.min(window.devicePixelRatio || 1, DPR_CAP);
  if (nextW === width && nextH === height && nextDpr === dpr) return;
  width = nextW; height = nextH; dpr = nextDpr;
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
};
```

Call `syncCanvasSize()` once before the first frame and once per draw loop iteration. Return early if unchanged — no-op is free.

**Documentation artifacts:** if asked to summarize this pattern into an HTML explainer, produce a standalone local HTML file, include Tailwind CDN when requested, and verify it opens with the expected title.

## Library-specific notes

### AntV L7 — package & adapter

| Concern | Detail |
|---------|--------|
| Core | `@antv/l7` — re-exports Scene, all layer types |
| MapLibre adapter | `@antv/l7-maps/maplibre` (NOT `@antv/l7-maplibre` — that package doesn't exist in npm) |
| Export name | `MapLibre` (not `Map`) |
| Config | `new MapLibre({ mapInstance: existingMaplibreGlMap })` |
| Scene | `new Scene({ id: 'div-id', map: mapLibreAdapter, logoVisible: false })` |

**Type import path**: `import type { ILayer } from '@antv/l7';`

**Layer types available**: `HeatmapLayer`, `PointLayer`, `LineLayer`, `PolygonLayer`, `RasterLayer`, `ImageLayer`, `CanvasLayer`, `CityBuildingLayer`, `GeometryLayer`, `MaskLayer`, `WindLayer`, `TileLayer`.

### Deck.gl — MapLibre/Mapbox overlay approach

For Deck.gl on an existing `react-map-gl/maplibre` / MapLibre map, prefer `MapboxOverlay` from `@deck.gl/mapbox` over creating a separate `Deck` canvas. This reuses the map WebGL context and avoids duplicate overlay canvases.

### Hybrid Deck picking + DOM canvas expression overlay

When a map point layer needs richer animated visual expression (ripples, particles, pulses) but already has working Deck.gl picking/click/popup behavior, keep Deck.gl for interaction and add a separate native 2D canvas overlay for visuals. This is less risky than replacing Deck with pure canvas because hit testing, hover dispatch, and selected-entity popup flow stay unchanged.

Pattern:
- Add a `<canvas>` programmatically to `map.getContainer()` as an absolute overlay before `.maplibregl-control-container`, with `pointerEvents = 'none'`, transparent background, and optional `mixBlendMode = 'screen'` for glow effects.
- Use `map.project([lng, lat])` on every animation frame so ripples follow pan/zoom without custom transform math.
- Size canvas with DPR cap (`Math.min(window.devicePixelRatio || 1, 2)`) and `ResizeObserver`; clean up with `cancelAnimationFrame`, `resizeObserver.disconnect()`, and `canvas.remove()`.
- Cap rendered points before drawing (e.g. top N by magnitude/severity and threshold minor events) to avoid per-frame loops over large feeds.
- Keep popup/hover in Deck (`pickable`, `onHover`, `onClick`) and leave canvas `pointer-events: none` so it never steals map interaction.
- Reuse existing layer color helpers where possible (`getDepthColor`, severity palettes, theme config) instead of inventing new color maps.


```tsx
import { ScatterplotLayer } from '@deck.gl/layers';
import { MapboxOverlay } from '@deck.gl/mapbox';
import type maplibregl from 'maplibre-gl';

const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
map.addControl(overlay as unknown as maplibregl.IControl);

// Data/filter updates — do not recreate overlay.
overlay.setProps({ layers });

// Unmount cleanup — prevents duplicate layers after remount.
map.removeControl(overlay as unknown as maplibregl.IControl);
```

Pattern:
- Init effect: wait for `map` and `map.isStyleLoaded()`, create one `MapboxOverlay({ interleaved: true, layers: [] })`, `map.addControl(...)`.
- Update effect: derive Deck layers from current data/filters and call `overlay.setProps({ layers })`.
- Cleanup: `map.removeControl(overlay)` in `try/catch` and clear refs.
- Type pitfall: MapLibre and Mapbox control types do not line up exactly; cast the overlay to `maplibregl.IControl` at `addControl`/`removeControl` boundaries.
- For globe safety, keep globe-compatible point/vector layers such as `ScatterplotLayer`; avoid aggregation/screen-grid/heatmap layers unless verified in MapLibre globe.
- If integrating hover/click into an existing MapLibre tooltip system, Deck `onHover`/`onClick` can dispatch the same hovered/selected entity shape instead of adding a second popup system.

### Three.js (react-three-fiber / custom)

- Create a `THREE.WebGLRenderer` with `alpha: true`, position it over the map
- Synchronise camera with MapLibre's `on('move', ...)` — this is the hard part
- Use `MapLibre's` `lngLatToWorld` / mercator projection to position objects

---

## Reference files

- `references/l7-maplibre.md` — L7-specific recipes: imports, types, data-update pattern, race-condition handling
