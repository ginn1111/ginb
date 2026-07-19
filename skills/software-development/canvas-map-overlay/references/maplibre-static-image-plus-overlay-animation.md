# MapLibre static image markers + canvas overlay animation

Session lesson from AIOZ World Deck earthquake layer work.

User intent distinction:
- "add quake like a static image using canvas" = generate marker glyphs with an offscreen canvas and register them via `map.addImage`, then render through MapLibre symbol layers.
- "keep styling and animation" = preserve old marker look and existing overlay/ripple animation. Do not swap in a generic pulsing-dot animation.

Good migration shape:
1. Extract existing static marker geometry (core fill, outer fill/stroke, opacity/colors) into a dedicated canvas image factory.
2. Register stable semantic image IDs, e.g. `earthquake-level-1`, `earthquake-level-2`, `earthquake-level-3`.
3. Add/keep MapLibre `Source` + `Layer type="symbol"` entries using those image IDs and magnitude/level filters.
4. Leave overlay canvas responsible only for animation/ripples. Remove duplicated static core drawing from overlay if symbol images now own marker glyphs.
5. If old animation was disabled by a temporary `ringCount = 0`, restore original computed ring count (`getRingCount(mag)`) instead of borrowing another animation helper.

Pitfall:
- Generic helpers like `pulsingDotFactory` are tempting, but wrong when the user asks to preserve domain-specific styling. Keep focus/pulse images and domain marker images separate unless visuals truly match.

Verification pattern when repo has unrelated type errors:
```bash
pnpm exec eslint src/components/widget/MaplibreViewer/mapController.ts src/components/widget/MaplibreViewer/EarthquakeLayer.tsx
pnpm type-check 2>&1 | grep -E 'src/components/widget/MaplibreViewer/(EarthquakeLayer|mapController)' || true
```
