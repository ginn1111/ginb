---
name: network-graph-visualization
title: Network / Force-Directed Graph Visualization
description: Build interactive network and force-directed graphs in React/Next.js with React Flow, D3, or react-force-graph-2d. Covers library selection, type safety, custom node rendering, SSR handling, and rapid preview.
tags: [react-flow, xyflow, d3, network-graph, visualization, nextjs, force-graph]
category: software-development
---

# Network / Force-Directed Graph Visualization

## When to use

- Building node-link diagrams for threat intelligence, dependency graphs, relationship mapping
- Interactive graph with drag, zoom, pan
- Custom node rendering with entity-type-specific labels, badges, metadata

## Library decision

| Need | Library | Notes |
|---|---|---|
| **Production React graph (recommended)** | `@xyflow/react` (React Flow) | Clean React components for nodes/edges. TypeScript-friendly. Built-in controls, minimap, background. Best for maintainable production code. |
| Quick canvas-based graph | `react-force-graph-2d` | Wraps force-graph. Canvas renderer, good perf. **Cannot pass custom node type** — use `any` + cast in callbacks. Harder to maintain. |
| Full D3 control | `d3-force` + raw SVG/Canvas | More boilerplate but full flexibility. |
| Minimal static graph | D3 SVG directly | Lighter, no React binding. |

**Prefer React Flow for new work.** It's declarative, easier to style, and avoids canvas rendering pitfalls.

## Project setup

### React Flow (preferred)

```bash
pnpm add @xyflow/react
```

Import stylesheet in component or layout:

```tsx
import '@xyflow/react/dist/style.css';
```

### react-force-graph-2d (legacy)

```bash
pnpm add react-force-graph-2d force-graph
```

## SSR guard

Both libraries use browser APIs. Must be excluded from SSR:

### React Flow

Not needed — React Flow renders SVG, not canvas. Dynamic import only needed if using `client-only` features:

```tsx
// No SSR guard needed for basic usage
import { ReactFlow, Background, Controls } from '@xyflow/react';
```

Canvas/WebGL features like `<MiniMap>` work fine client-side without dynamic import in Next.js App Router (`'use client'` is sufficient).

### react-force-graph-2d

Canvas-based. Must use dynamic import:

```tsx
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
});
```

## React Flow patterns

### Component structure

```
src/components/widget/<WidgetName>/
├── CampaignGraph.tsx        // Graph view component
├── nodes/
│   └── CampaignNode.tsx     // Custom node component(s)
└── index.tsx                // View-switching container
```

### Custom node component

```tsx
import { Handle, Position, type NodeProps } from '@xyflow/react';

type NodeDatum = {
  name: string;
  entityType: string;
  color: string;
  metadata: Record<string, string>;
};

const CampaignNode = ({ data }: NodeProps) => {
  const d = data as unknown as NodeDatum;  // Cast at boundary
  return (
    <div className="group relative">
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      {/* Entity badge */}
      <div
        className="absolute left-1/2 -translate-x-1/2 rounded px-1.5 text-[10px] font-semibold uppercase text-white"
        style={{ top: '-18px', backgroundColor: d.color }}
      >
        {d.entityType}
      </div>
      {/* Node body */}
      <div
        className="rounded-lg border-2 px-3 py-2 shadow-lg backdrop-blur-sm"
        style={{ backgroundColor: `${d.color}15`, borderColor: `${d.color}50` }}
      >
        <p className="text-center font-medium">{d.name}</p>
        {/* Metadata rows */}
        {d.metadata && Object.entries(d.metadata).map(([k, v]) => (
          <div key={k} className="text-muted-foreground/70 flex items-center justify-between gap-2 text-[10px]">
            <span className="font-mono">{k}</span>
            <span className="text-white/80">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const nodeTypes = { campaignNode: CampaignNode };
export default nodeTypes;
```

### Main graph component

```tsx
import { Background, Controls, ReactFlow, useEdgesState, useNodesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import nodeTypes from './nodes/CampaignNode';

type NodeDatum = { name: string; entityType: string; color: string; metadata: Record<string, string> };

// Build a React Flow node with type-safe data
const buildNode = (id: string, x: number, y: number, data: NodeDatum): Node => ({
  id, type: 'campaignNode', position: { x, y },
  data: data as unknown as Record<string, unknown>,  // Cast at boundary
});

const Graph = ({ campaignId }: { campaignId: string }) => {
  const initialNodes = useMemo(() => [
    buildNode('center', 400, 300, { name: 'Campaign', entityType: 'Campaign', color: '#ef4444', metadata: {} }),
    // ... satellite nodes with circular layout
  ], []);

  const initialEdges = useMemo<Edge[]>(() => [
    {
      id: 'e1', source: 'center', target: 'sat1',
      label: 'uses', type: 'smoothstep',
      style: { stroke: '#64748b', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#64748b' },
      animated: true,
    },
  ], []);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="flex-1">
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView minZoom={0.2} maxZoom={3} colorMode="dark"
      >
        <Background variant="dots" gap={24} size={1} color="rgba(148,163,184,0.15)" />
        <Controls position="bottom-right" />
      </ReactFlow>
    </div>
  );
};
```

### Circular satellite layout

```tsx
const satellites = [
  { id: 'vuln-1', name: 'CVE-2021-28372', entityType: 'Vulnerability', color: '#ec4899' },
  { id: 'tool-1', name: 'TeamViewer', entityType: 'Tool', color: '#06b6d4' },
  // ...
];

const centerX = 400, centerY = 300, radius = 180;
const satNodes = satellites.map((e, i) => {
  const angle = (2 * Math.PI * i) / satellites.length - Math.PI / 2;
  return buildNode(e.id, centerX + radius * Math.cos(angle) - 70, centerY + radius * Math.sin(angle) - 20, {
    name: e.name, entityType: e.entityType, color: e.color, metadata: e.metadata,
  });
});
```

### Type safety with React Flow

React Flow expects `Node<Record<string, unknown>>` by default. **Don't fight the generics.** The data flows through `NodeProps.data` as `unknown`. Cast at two boundaries:

1. **Building nodes**: cast `data as unknown as Record<string, unknown>` in a `buildNode()` helper
2. **Consuming in custom node**: cast `data as unknown as NodeDatum` at the top of the component

This matches React Flow's internal API and avoids complex type gymnastics that break on library updates.

### Node type union inference

When metadata keys differ per entity type, TypeScript infers a union `{MITRE ID: string; Tactic: string} | {Score: string; Type: string} | ...`. This fails `Record<string, string>` since each variant has optional keys from other variants. Fix with explicit cast per metadata object:

```tsx
metadata: { 'MITRE ID': 'T1190', Tactic: 'Initial Access' } as Record<string, string>
```

Or define `NodeDatum` with `Record<string, string> | Record<string, never>` and cast at construction.

## react-force-graph-2d patterns (legacy)

### Type safety pattern

The library's `GraphNode` / `GraphLink` generics are index-signature-based and won't accept your typed nodes. **Do not fight the type system** — use `any` parameters in render callbacks and cast inside:

```tsx
type MyNode = {
  id: string;
  name: string;
  entityType: string;
  val?: number;
  color?: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
};

type MyLink = {
  source: string;
  target: string;
  relationshipType: string;
  color?: string;
};

const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D) => {
  const n = node as MyNode;
  const x = n.x ?? 0;
  const y = n.y ?? 0;
  // ... draw with ctx
}, []);

const paintLink = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
  const l = link as MyLink;
  ctx.strokeStyle = l.color ?? '#64748b';
  ctx.lineWidth = 2;
  ctx.globalAlpha = 0.6;
}, []);
```

### Canvas custom rendering pattern

For `react-force-graph-2d`, use `nodeCanvasObject` + `linkCanvasObject`:

```tsx
<ForceGraph2D
  graphData={{ nodes, links }}
  nodeCanvasObject={paintNode}
  linkCanvasObject={paintLink}
  linkDirectionalArrowLength={6}
  linkDirectionalArrowRelPos={1}
  linkCurvature={0.15}
/>
```

### Entity-type label + metadata rendering (canvas)

```tsx
const badgeHeight = 16;
const labelHeight = 20;
const metaY = labelY + labelHeight + 8;

// Entity type badge (above node)
ctx.font = '10px Inter, sans-serif';
ctx.fillStyle = nodeColor;
ctx.fillRect(badgeX, badgeY, badgeWidth, badgeHeight);
ctx.fillStyle = '#fff';
ctx.fillText(label, x, badgeY + badgeHeight / 2);

// Name label (below node)
ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
ctx.fillRect(labelX, labelY, labelWidth, labelHeight);
ctx.fillStyle = '#f1f5f9';
ctx.fillText(nodeName, x, labelY + labelHeight / 2);

// Metadata (stacked below name)
Object.entries(metadata).forEach(([key, value], i) => {
  const metaText = `${key}: ${value}`;
  ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
  ctx.fillRect(metaX, metaY + i * 14, metaWidth, 12);
  ctx.fillStyle = '#cbd5e1';
  ctx.fillText(metaText, x, metaY + i * 14 + 8);
});
```

## Layout tuning

### React Flow (fixed positions)

React Flow doesn't use force simulation. Position nodes explicitly (circular, hierarchical, dagre). For force-directed layout, compute positions with `dagre` or D3 on the server before rendering.

```tsx
// Circular layout for star-like graphs
const angle = (2 * Math.PI * i) / items.length - Math.PI / 2;
const x = centerX + radius * Math.cos(angle) - offsetX;
const y = centerY + radius * Math.sin(angle) - offsetY;
```

### react-force-graph-2d (simulation)

```tsx
<ForceGraph2D
  cooldownTicks={100}
  d3AlphaDecay={0.02}     // Lower = more settling time
  d3VelocityDecay={0.3}    // Higher = less jitter
/>
```

D3 raw equivalents:
```
d3.forceLink().distance(200)
d3.forceManyBody().strength(-400)
d3.forceCollide(60)
```

## Widget view-switch pattern

For in-widget graph mode (like Campaigns list → graph):

```tsx
const [viewMode, setViewMode] = useState<'list' | 'graph'>('list');
const [selectedId, setSelectedId] = useState<string | null>(null);

if (viewMode === 'graph' && selectedId) {
  return <CampaignGraph campaignId={selectedId} onBack={() => {
    setViewMode('list');
    setSelectedId(null);
  }} />;
}

// Else render the list view
```

### Widget integration checklist

1. **Component file** — `src/components/widget/<WidgetName>/<Component>.tsx`
2. **Component registry** — add to `LAYOUT_COMPONENTS_REGISTRY` in layout-manager index
3. **Widget catalogue** — add entry in `src/constants/widgets.ts` under correct `WidgetCategory`

## Rapid prototyping: standalone HTML preview

When the app requires auth (blocking fast iteration), create a standalone HTML file in `public/` with raw D3.js loaded from CDN:

```html
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
  // Same data structure as your React component
  // Same rendering logic, ported to D3 API
  // Access at http://localhost:3000/preview-<name>.html
</script>
```

This lets the user see the graph layout, colors, labels, and interactions immediately without any auth/login flow. Delete the file when the real component is verified.

## Legend pattern

Always add an entity-type legend when nodes have multiple types:

```tsx
<div className="absolute bottom-4 left-4 rounded-lg border border-border/40 bg-card/90 p-3">
  <div className="text-caption font-medium mb-2">Entity Types</div>
  {Object.entries(TYPE_MAP).map(([type, label]) => (
    <div key={type} className="flex items-center gap-2">
      <div className="h-3 w-3 rounded-full" style={{ backgroundColor: COLORS[type] }} />
      <span className="text-caption text-muted-foreground">{label}</span>
    </div>
  ))}
</div>
```

## Reference files

- `references/stix-threat-intel-graph-mapping.md` — STIX campaign data → graph node/link mapping for cybersecurity threat intel dashboards. Entity types, relationship types, OpenCTI GraphQL shape, display priorities per entity type.

## Pitfalls

### React Flow

- **Type errors on `nodeTypes`**: React Flow's `Node<Record<string, unknown>>` constraint won't accept your typed data. Cast at two boundaries: `data as unknown as Record<string, unknown>` when building nodes, and `data as unknown as NodeDatum` in custom nodes. This is by design.
- **Union metadata keys break `Record<string, string>`**: When different entity types have different metadata fields (`{MITRE ID, Tactic}` vs `{Score, Type}`), TypeScript infers a union with optional keys that fails index signature checks. Cast each metadata object with `as Record<string, string>` or use `as const` on the data.
- **`@xyflow/react` styles**: Import `@xyflow/react/dist/style.css` once. Missing this causes invisible nodes and missing connection handles.
- **ESLint `unused-var` on mock props**: Prefix unused props with underscore: `({ campaignId: _campaignId, onBack })`. Pre-commit hooks enforce this.

### react-force-graph-2d (legacy)

- **Type errors on `nodeCanvasObject`**: Library's generic constraints are too loose. Use `(node: any, ctx)` + cast. This is the library's fault, not yours. Do not spend time trying to type it perfectly.
- **SSR crash**: `force-graph` needs `window`, `canvas`, and `requestAnimationFrame`. Always `dynamic(() => import(...), { ssr: false })`.
- **Null `x`/`y` on initial render**: Force simulation hasn't settled. Default to 0 with `??` in paint callbacks.
- **`fx`/`fy` type with `null`**: Library sets to `null` on drag release but types say `number | undefined`. Remove `null` from your type — omit it or use `number` only.

### General

- **Preview file stale**: Delete `public/preview-*.html` once the real component is verified, or it becomes dead code.
- **Force layout infinite page limit**: Set `getNextPageParam` to return `undefined` when `nextOffset >= total` or infinite queries will spin forever.
