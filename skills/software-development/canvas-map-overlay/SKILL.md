---
name: canvas-map-overlay
category: software-development
description: >-
  Canvas animation overlay on MapLibre GL. Screen-space clustering, 
  ripple effects, click/hover discrimination, transition smoothing, 
  and interaction delegation via hit layers + canvas dual approach.
---

# Canvas Map Overlay

Techniques for rendering animated visual effects on a `<canvas>` overlaid on a MapLibre map, with screen-space clustering for performance.

## Canvas Lifecycle

```tsx
// Inside component
const canvasRef = useRef<HTMLCanvasElement | null>(null);

useEffect(() => {
  const map = mapRef.current;  // maplibregl.Map
  if (!map) return;
  const container = map.getContainer();

  // REUSE existing canvas by id — don't create new each mount
  let canvas = container.querySelector('#my-overlay') as HTMLCanvasElement | null;
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.id = 'my-overlay';
    canvas.style.position = 'absolute';
    canvas.style.inset = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    // Insert before maplibregl controls so controls stay clickable
    const controls = container.querySelector('.maplibregl-control-container');
    container.insertBefore(canvas, controls ?? null);
  }

  const dpr = Math.min(window.devicePixelRatio, DP_CAP);  // cap for perf
  canvas.width = Math.floor(container.clientWidth * dpr);
  canvas.height = Math.floor(container.clientHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Animation loop with frame rate throttle
  let lastTime = 0;
  const draw = (time: number) => {
    if (time - lastTime < TARGET_MS) {
      frameId = requestAnimationFrame(draw);
      return;
    }
    lastTime = time;
    syncCanvasSize();
    ctx.clearRect(0, 0, w, h);
    // ... render ...
    frameId = requestAnimationFrame(draw);
  };
  frameId = requestAnimationFrame(draw);

  return () => {
    cancelAnimationFrame(frameId);
    canvas.remove();
  };
}, [deps]);
```

⚠ **Canvas removal pitfall**: If the effect re-runs (dependency changes), `canvas.remove()` in cleanup deletes the DOM element. Next mount creates a new one — brief flash. To avoid this, skip `remove()` when reusing:
```ts
const isReused = container.querySelector('#my-overlay');
// ... in cleanup:
if (!isReused) canvas.remove();
```

## Screen-Space Clustering

Group points by pixel proximity before drawing to reduce draw calls and visually compress dense swarms.

```ts
const CLUSTER_MERGE_RADIUS_PX = 48;

type Projected = { px: number; py: number; magnitude: number; depth: number; id: string };

function compressScreenSpace(map: maplibregl.Map, data: EarthquakeDeckDatum[]): CompressedPoint[] {
  // 1. Project each datum to screen coords
  const projected: Projected[] = [];
  for (const item of data) {
    const p = map.project([item.longitude, item.latitude]);
    projected.push({ ...item, px: p.x, py: p.y });
  }

  // 2. Greedy cluster: if unassigned point is within radius of existing group, join it
  const radiusSq = CLUSTER_MERGE_RADIUS_PX ** 2;
  const assigned: number[] = new Array(projected.length).fill(-1);
  const groups: number[][] = [];

  for (let i = 0; i < projected.length; i++) {
    if (assigned[i] !== -1) continue;
    const g: number[] = [i];
    assigned[i] = groups.length;
    for (let j = i + 1; j < projected.length; j++) {
      if (assigned[j] !== -1) continue;
      const dx = projected[i].px - projected[j].px;
      const dy = projected[i].py - projected[j].py;
      if (dx * dx + dy * dy <= radiusSq) {
        g.push(j);
        assigned[j] = groups.length;
      }
    }
    groups.push(g);
  }

  // 3. Each group → single compressed point with median values
  const median = (arr: number[]) => {
    const s = [...arr].sort((a, b) => a - b);
    return s[Math.floor(s.length / 2)];
  };

  return groups.map((group) => {
    const members = group.map((idx) => projected[idx]);
    return {
      x: members.reduce((s, m) => s + m.px, 0) / members.length,
      y: members.reduce((s, m) => s + m.py, 0) / members.length,
      magnitude: median(members.map((m) => m.magnitude)),
      depth: median(members.map((m) => m.depth).filter((d): d is number => d != null)),
      id: members[0].id,
      weightedCount: members.length,
    };
  });
}
```

**Cache the result** — add a `compressedCacheRef` keyed on `dataLen + center.lat.toFixed(1) + center.lng.toFixed(1) + zoom.toFixed(1)` to skip recompute when map hasn't moved.

## Frame-to-Frame Lerp Smoothing

Avoid pop when points enter/exit clusters. **Use `Map<string, T>` for O(1) lookup** (array `.find()` is O(n) and grows with point count).

```ts
const prevRef = useRef<Map<string, CompressedPoint>>(new Map());
// In draw:
const prev = prevRef.current;
const lerpFactor = 0.2;  // speed: 0.08=slow, 0.2=medium, 0.5=fast

const smoothed: CompressedPoint[] = raw.map((cur) => {
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
prevRef.current = new Map(smoothed.map((p) => [p.id, p]));
```

## Click / Hover Discrimination (Standalone vs Cluster)

**Default approach** (preferred): Add the invisible hit layers to the map's global `interactiveLayerIds` so the map's built-in `onClick` handler dispatches selection for all features — including clusters. Simple, no per-frame `queryRenderedFeatures` overhead.

```ts
// in selector.ts — add hit layer ids when the layer is active
activeLayers.earthquakes && EarthquakeMapLayerIds.eq_level1,
activeLayers.earthquakes && EarthquakeMapLayerIds.eq_level2_inner,
activeLayers.earthquakes && EarthquakeMapLayerIds.eq_level3_inner,
```

**When cluster discrimination is needed** (block clicks on compressed groups): Remove the hit layers from `interactiveLayerIds` and handle clicks manually via map event listeners using `queryRenderedFeatures` with a bounding box of `CLUSTER_MERGE_RADIUS_PX`. Only 1 feature within radius = standalone → dispatch; ≥2 = cluster → no-op.

```ts
map.on('click', (e: maplibregl.MapMouseEvent) => {
  const box: [[number, number], [number, number]] = [
    [e.point.x - RADIUS, e.point.y - RADIUS],
    [e.point.x + RADIUS, e.point.y + RADIUS],
  ];
  const nearby = map.queryRenderedFeatures(box, { layers: HIT_LAYER_IDS });
  if (nearby.length !== 1) return;  // 0=nothing, >1=cluster — ignore
  // dispatch setSelectedEntity with first feature's properties
});
```

⚠ **Cursor hover**: Adding a per-frame `mousemove` listener that calls `queryRenderedFeatures` on every move is expensive — avoid it. Let MapLibre's native `MouseEnter`/`MouseLeave` on interactive layers handle cursor changes. If cluster discrimination is used, accept default cursor on clusters.

## Layer Pair (Invisible Hit + Canvas Visual)

- **Invisible MapLibre Layer**: opacity 0.001 circles, radius 6-14, for interaction via `queryRenderedFeatures`
- **Canvas overlay**: visual rendering (ripples, dots, clusters) — `pointer-events: none`
- Dual approach gives interaction precision of MapLibre with visual freedom of canvas

## Migrating Overlay Draws to MapLibre Images

When user asks to migrate canvas drawing into `map.addImage`, preserve existing visual semantics first. Do **not** replace domain-specific visuals with a generic pulsing-dot helper unless explicitly requested. See `references/maplibre-static-image-plus-overlay-animation.md` for a concrete static-marker + old-overlay-animation migration pattern. See `references/maplibre-depth-colored-images-and-legend.md` for finite pre-colored animated images plus a draggable legend when marker color must vary by feature property.

Pattern:
1. Read existing canvas draw function and copy its geometry/colors/opacity into a separate image factory.
2. Register one stable image id per semantic level/type (`level1`, `level2`, `level3`, etc.).
3. Render static glyphs through MapLibre `Source` + `Layer type="symbol"` using those image IDs.
4. Keep existing overlay animation if user says “keep old animation” — only move marker glyphs/static cores to `addImage`.
5. If user says remove the overlay, move the pulse/ripple math into the MapLibre image object's `render()` method and call `map.triggerRepaint()` there. Do not keep a full-screen DOM canvas or any leftover overlay lifecycle/hit-test code.
6. Preserve the old domain animation parameters inside the image factory: `duration`, `ringCount`, `ringDelay`, magnitude scaling, alpha falloff, and line width. Encode these per semantic image/level when the image no longer receives per-feature data.
6. Preserve the old domain animation parameters inside the image factory: `duration`, `ringCount`, magnitude scaling, alpha falloff, and line width. Encode these per semantic image/level when the image no longer receives per-feature data.
7. When moving an overlay ring animation into `map.addImage`, do not keep both static concentric `circles` and animated rings unless the user explicitly wants a filled dot. Static circles and `ringCount` often duplicate the same visual purpose and create muddy/boomerang-like markers. Prefer one-way outward rings: `progress = (time / duration + ring / ringCount) % 1`, eased outward radius, squared alpha fade, and no delayed reverse/bounce phase.
8. Keep marker geometry separated: small **core** dot, optional faint **halo** circle, animated **ring** outside the halo. If the user says “minimum must be the core/halo,” start the animated ring at `haloRadius` (or `coreRadius` if no halo), not at zero; draw the core/halo once after rings. Decrease core by changing `coreRadius`, not by scaling the whole image.
9. If the image layer needs clustering, do the full MapLibre cluster contract: spread `getMapClusterSourceProps(featureCount)` on the `Source`, add both cluster bubble and cluster count layers filtered by `['has', 'point_count']`, filter the symbol/image layer with `['!', ['has', 'point_count']]`, add the cluster circle layer id to `INTERACTIVE_LAYER_IDS`, and gate it in `selectInteractiveLayerIds` with the layer active flag.
10. When image visuals must vary by per-feature data (e.g. earthquake depth color), don't assume one `addImage` can recolor dynamically. `icon-color` only reliably recolors SDF-style icons; for animated canvas images, pre-register one stable image id per semantic bucket (e.g. magnitude level × depth bucket), put the bucket-driving value into GeoJSON `properties`, then choose the image with a MapLibre `case` expression. Keep each image option's representative magnitude aligned with the same thresholds used by the symbol-layer filter/expression (`<3`, `>=3 && <5`, `>=5` → representative `2`, `3`, `5`) so animation radius/ring count matches the rendered level.
11. If static glyphs moved to symbol images but overlay remains, remove duplicate static core drawing from the animation canvas so overlay owns only rings/ripples.
11. Keep generic focus/pulsing images separate from domain images; shared helper only okay for truly shared math, not shared behavior.
12. Verify no edited-file TypeScript errors with `pnpm type-check 2>&1 | grep '<edited paths>' || true` when repo has unrelated failures.
13. If per-feature color is needed on animated canvas images, do not assume `icon-color` can tint them. Register one image per visual bucket (for example magnitude level × depth bucket) and select with a MapLibre `icon-image` expression. Add the driving property (for example `depth`) into GeoJSON properties in the hook, and keep thresholds shared/aligned with the layer filters.
14. For layer-specific legends, add a registry (layer key → panel id/title/icon/theme/component metadata) and make both the toolbar button and the legend panel depend on that registry plus the layer active state. Unregistered layers should show no legend affordance and mount no legend panel.

## DPR for map.addImage

For `map.addImage`, DPR must be applied in two places — canvas size and `pixelRatio` — to keep logical icon size consistent across displays:

```ts
const dpr = Math.max(window.devicePixelRatio ?? 1, 1);
map.addImage(id, imageFactory(24 * dpr, map, opts), { pixelRatio: dpr });
```

The canvas renders at `24 * dpr` actual pixels, and `pixelRatio: dpr` tells MapLibre to display it at `(24 * dpr) / dpr = 24` logical CSS px. Without this, icons are sharp on standard displays but blurry on retina. This is different from the canvas-overlay DPR approach (where `ctx.setTransform(dpr,…)` handles scaling) — `map.addImage` needs `pixelRatio` because MapLibre manages image scaling internally.

To ensure pixelRatio always produces a usable value, clamp with `Math.max(dpr, 1)` to guard against edge cases where `devicePixelRatio` is 0.

### Pitfall: removing magnitude from radius formulas

When image visuals (ring size, core dot) should be constant across all features, but the factory still receives a `magnitude` parameter, check for `Math.min()` caps that always win:

```ts
// Dead: cap always wins at current size/mag values
const maxRadius = Math.min(size * 0.15, size * (0.08 + magnitude * 0.1));
// → Just: const maxRadius = size * 0.15;
```

If magnitude no longer affects the rendered image, remove it from the radius formulas. The parameter can stay in the options bag for `ringCount` selection if that still varies by magnitude level.

Pitfall: if old animation was disabled behind a temporary `ringCount = 0`/TODO, restoring "old animation" means re-enabling the original computed ring count, not reusing another pulsing animation. If the animation moves into a static map image, carry that ring-count logic into the image options (`level1/2 → 1 ring`, strong/major levels → original high ring count) instead of hardcoding a generic 2-ring pulse.

## Performance Constants Template

```ts
const DP_CAP = 1.25;         // max devicePixelRatio for canvas
const TARGET_FPS = 24;       // frame throttling
const TARGET_MS = 1000 / TARGET_FPS;
const VIEWPORT_PADDING = 80; // px — cull off-screen entities
const MAX_POINTS = 90;       // soft cap to keep frame budget
```

## Canvas Opacity on Map Move

Hide the canvas overlay during map interaction to avoid visual misalignment (canvas is stale while map moves underneath). Restore on move end.

```ts
const defaultOpacity = canvas.style.opacity || '0.95';
const onMoveStart = () => { canvas.style.opacity = '0'; };
const onMoveEnd = () => { canvas.style.opacity = defaultOpacity; };
map.on('movestart', onMoveStart);
map.on('moveend', onMoveEnd);

// Cleanup in effect return:
map.off('movestart', onMoveStart);
map.off('moveend', onMoveEnd);
```

This pairs well with the render loop — drawing continues during move but the canvas is invisible, so the first frame after moveend already has correct positions.
