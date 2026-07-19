# MapLibre animated image markers: per-feature color via finite image variants

Context: earthquake markers moved from full-screen canvas overlay to `map.addImage` animated images. The user then wanted marker color by quake depth while keeping magnitude-based ring animation.

## Pattern

MapLibre `icon-color` is not a safe fit for arbitrary animated canvas images unless using a true SDF icon. For canvas-rendered pulse/ring markers, generate a small finite set of pre-colored images instead:

1. Define semantic depth buckets and colors once:
   - unknown: orange
   - shallow `< 70km`: red/orange
   - intermediate `70–300km`: yellow
   - deep `> 300km`: purple
2. Define magnitude levels to match the actual layer filter thresholds, not arbitrary representative values:
   - level1: magnitude `2` for `mag < 3`
   - level2: magnitude `3` for `3 <= mag < 5`
   - level3: magnitude `5` for `mag >= 5`
3. Register images for every `magnitude level × depth bucket` pair.
4. Add the source property the expression needs (`depth`) into GeoJSON feature properties.
5. In the symbol layer `icon-image`, use a nested `case` expression:
   - first choose magnitude level (`>=5`, `>=3`, fallback)
   - inside each branch choose depth bucket (`unknown`, `<70`, `<=300`, fallback deep)

## Legend panel

When adding a map-only legend for this visual encoding:

- Reuse `MaplibreViewer/DraggablePanel`, not raw `react-rnd`.
- Render only when the owning map layer is active (`getActiveLayerById(state, 'earthquakes')`).
- Add a `MapPanelId` for persisted layout.
- Keep text compact and use theme font utilities (`text-caption`, `text-body-03`), not arbitrary font sizes.
- Use same exported color constants as marker image registration so legend and map cannot drift.

## Pitfalls

- Do not keep one generic image ID per magnitude when color must vary per feature; all features using that image will share color.
- Do not add static concentric circles and animated rings for same marker unless explicitly requested; they muddy the pulse.
- If ring animation reaches image bounds, the transparent canvas still clips square. Either increase image canvas size or reduce `maxRadius` so expanded rings stay inside the transparent margin.
