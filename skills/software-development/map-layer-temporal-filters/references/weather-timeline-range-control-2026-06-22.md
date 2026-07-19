# Weather timeline range control notes (2026-06-22)

Context: AIOZ World Deck `MaplibreViewer` weather raster tile time-series UI.

## Durable lessons
- Keep weather raster `<Source>` stable. Do not key by frame/layer. `react-map-gl` `Source` deep-compares props and calls `source.setTiles(props.tiles)` when `tiles` changes; keyed remount causes blank/gone source while new raster tiles load.
- Generate weather frames at runtime from current hour. Current contract: hourly frames from `now - 48h` through `now` (49 frames), URL query `time=<unixHour>`.
- Primary timestamp label format: `ddd DD - HH:mm`.
- Date strip label format: `ddd DD`.
- Range control: native `<input type="range">`, `min=0`, `max=frameCount - 1`, `step=1`; one step equals one hour.
- Debounce committed frame index so tile requests do not fire on every drag event. Keep local `pendingFrameIndex` for instant UI feedback; flush on pointer-up/blur.
- Date group strip must align to slider percentage, not equal cell counts. Use:
  - `rangeMax = frameCount - 1`
  - `left = group.start / rangeMax`
  - `width = (nextGroup.start - group.start) / rangeMax`
  - last group ends at `rangeMax`
- Use grid/fixed center column so slider and date strip share exact width/left edge. Example: controls column + `12rem` slider/date column + timestamp column; date strip `col-start-2 w-full`.
- Floating map overlay needs high contrast over colorful tiles: `bg-background/95`, `border-border`, `text-foreground`, strong shadow.

## Files involved
- `src/components/widget/MaplibreViewer/WeatherLayer/weatherTimeline.ts`
- `src/components/widget/MaplibreViewer/WeatherLayer/useWeatherTimeline.ts`
- `src/components/widget/MaplibreViewer/WeatherLayer/WeatherTimeSeriesLayer.tsx`
- `src/components/widget/MaplibreViewer/WeatherLayer/WeatherTimelineOverlay.tsx`
- `src/components/widget/MaplibreViewer/MapControlsOverlay.tsx`

## Verification pattern
- Targeted eslint for edited weather files.
- Full `pnpm type-check` may be blocked by unrelated generated Zod / map filter baseline errors; distinguish touched-file failures from pre-existing errors.
