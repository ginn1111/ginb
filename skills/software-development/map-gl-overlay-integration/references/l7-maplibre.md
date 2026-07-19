# AntV L7 + MapLibre — Integration Reference

## Packages

```json
"@antv/l7": "latest"         // Core — Scene, layers, types
"@antv/l7-maps": "latest"    // Map adapter — subpath export for maplibre
```

`@antv/l7-maps/maplibre` is NOT `@antv/l7-maplibre` — that npm package does not exist.

The `@antv/l7-maps` package must be a **direct** dependency, not transitive. pnpm does not hoist subpath exports of transitive deps.

## Imports

```ts
import { HeatmapLayer, PointLayer, Scene } from '@antv/l7';
import type { ILayer } from '@antv/l7';
import { MapLibre } from '@antv/l7-maps/maplibre';
```

## L7 layers for earthquake-style data

| Layer | Shape | Sizing | Colouring | Notes |
|-------|-------|--------|-----------|-------|
| `HeatmapLayer` | `.shape('heatmap')` | `.size('mag', [0, 30])` | auto (density) | `style: { intensity: 2, radius: 20, opacity: 0.35 }` |
| `PointLayer` | `.shape('circle')` | `.size('mag', [3, 25])` | `.color('depth', ramp[])` | `.active(true)` enables hover highlight |

## Typical component skeleton

```tsx
'use client';

import { useEffect, useRef } from 'react';

import type { ILayer } from '@antv/l7';
import { HeatmapLayer, PointLayer, Scene } from '@antv/l7';
import { MapLibre } from '@antv/l7-maps/maplibre';
import type { FeatureCollection } from 'geojson';
import type { Map as MaplibreMap } from 'maplibre-gl';

interface Props {
  map: MaplibreMap | null;
  data: FeatureCollection | null;
}

const MyOverlay = ({ map, data }: Props) => {
  const sceneRef = useRef<Scene | null>(null);
  const pointRef = useRef<ILayer | null>(null);
  const heatRef = useRef<ILayer | null>(null);
  const dataRef = useRef<FeatureCollection | null>(data);
  const readyRef = useRef(false);
  const id = useRef(`l7-${Math.random().toString(36).slice(2, 9)}`).current;

  // Keep data ref current so 'loaded' callback gets latest.
  useEffect(() => { dataRef.current = data; }, [data]);

  // Bootstrap L7 scene once.
  useEffect(() => {
    if (!map || sceneRef.current) return;

    const scene = new Scene({
      id,
      map: new MapLibre({ mapInstance: map }),
      logoVisible: false,
    });

    scene.on('loaded', () => {
      const src = dataRef.current ?? ([] as unknown as FeatureCollection);

      const heat = new HeatmapLayer()
        .source(src, { parser: { type: 'geojson' } })
        .shape('heatmap')
        .size('mag', [0, 30])
        .style({ intensity: 2, radius: 20, opacity: 0.35 });

      const points = new PointLayer()
        .source(src, { parser: { type: 'geojson' } })
        .shape('circle')
        .size('mag', [3, 25])
        .color('depth', ['#fca5a5', '#f87171', '#ef4444', '#dc2626', '#991b1b'])
        .style({ opacity: 0.7, strokeWidth: 1, stroke: '#ffffff' })
        .active(true);

      scene.addLayer(heat);
      scene.addLayer(points);

      heatRef.current = heat;
      pointRef.current = points;
      readyRef.current = true;
    });

    sceneRef.current = scene;

    return () => {
      scene.destroy();
      sceneRef.current = null;
      pointRef.current = null;
      heatRef.current = null;
      readyRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map]);

  // Update data without recreate.
  useEffect(() => {
    if (!readyRef.current || !data) return;
    pointRef.current?.setData(data);
    heatRef.current?.setData(data);
  }, [data]);

  return <div id={id} className="pointer-events-none absolute inset-0" aria-hidden />;
};

export default MyOverlay;
```

## Type pitfalls

| Pitfall | Fix |
|---------|-----|
| Chain methods return `ILayer`, not `HeatmapLayer` | Type refs as `ILayer \| null` |
| `MapLibre` not `Map` import | `from '@antv/l7-maps/maplibre'` |
| GeoJSON source needs explicit parser | `.source(data, { parser: { type: 'geojson' } })` |
| `@antv/l7-maps` not found at runtime | Add as direct dep — pnpm doesn't hoist transitive subpath exports |

## Placement relative to react-map-gl `<Map>`

L7 renders its own WebGL canvas over the map. The container div must be a **sibling** of the `<Map>` component, NOT a child:

```tsx
{/* ✅ Correct */}
<div className="relative min-h-0 flex-1">
  <Map ref={mapRef} ... />
  <div id="l7-container" className="pointer-events-none absolute inset-0" />
</div>

{/* ❌ Wrong — inside <Map> children */}
<Map ...>
  <div id="l7-container" />  {/* L7 canvas gets clipped/mispositioned */}
</Map>
```

## Next.js / SSR setup

```tsx
// Parent imports the overlay dynamically:
import dynamic from 'next/dynamic';

const L7Layer = dynamic(() => import('./L7Layer'), { ssr: false });

// In render:
<L7Layer map={mapInstance} data={geoJSON} />
```

The overlay component file itself must start with `'use client'` — L7 imports browser globals.

## Redux layer toggle pattern

For existing AIOZ World Deck layers, gate the overlay with Redux state:

```tsx
import { useAppSelector } from '@/store/hooks';
import { getActiveLayerById, getLayerQuerySelector } from '@/store/map-layer';
import { useDomainGeoJSON } from '@/hooks/query/maps/useDomainGeoJson';

const isActive = useAppSelector((s) => getActiveLayerById(s, 'earthquakes'));
const layerQuery = useAppSelector((s) => getLayerQuerySelector(s, 'earthquakes'));
const { data } = useDomainGeoJSON(layerQuery, { enabled: isActive });
```

## Map instance acquisition

The raw MapLibre instance may not be available at first render (react-map-gl `onLoad` hasn't fired yet). Resolve it reactively:

```tsx
const [rawMap, setRawMap] = useState<maplibregl.Map | null>(null);

useEffect(() => {
  if (!isActive) return;
  const m = mapRef.current?.getMap();
  if (m) { setRawMap(m); return; }
  // Poll briefly — resolves within a frame or two.
  const id = setInterval(() => {
    const m2 = mapRef.current?.getMap();
    if (m2) { setRawMap(m2); clearInterval(id); }
  }, 100);
  setTimeout(() => clearInterval(id), 3000);
  return () => clearInterval(id);
}, [isActive, mapRef]);
```

Alternatively, use a global map registry pattern (existing in AIOZ World Deck at `src/components/widget/MaplibreViewer/mapController.ts`):

```ts
import { getMapInstance } from '@/components/widget/MaplibreViewer/mapController';
const map = getMapInstance(); // non-reactive — call inside a polling effect or store subscriber
```

## Key differences from MapLibre native layers

| Concern | ML native (react-map-gl Source/Layer) | L7 overlay |
|---------|----------------------------------------|------------|
| Rendering | MapLibre's style pipeline | L7's own WebGL canvas overlay |
| Click handling | Built-in map interaction | `.active(true)` for hover, manual `.on('click')` for selection |
| Clustering | Native supercluster | L7 cluster layer or manual |
| Popups | react-map-gl `<Popup>` | L7 Popup API or separate React component |
| Container | Inline in `<Source>` children | Sibling of `<Map>`, absolute-positioned |
| SSR | Works with react-map-gl SSR | Requires `dynamic(..., { ssr: false })` |
