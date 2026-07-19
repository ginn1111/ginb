# Webpack extension + ts-loader + React Fast Refresh notes

Session pattern:
- Repo had webpack-based browser extension app.
- Config used `webpack-ext-reloader` plus `watch: true` in development.
- Source config did not contain React Fast Refresh wiring even though old `dist/` files showed refresh runtime strings.

Applied changes:
- Added dev deps:
  - `@pmmmwh/react-refresh-webpack-plugin`
  - `react-refresh`
  - `react-refresh-typescript`
- Patched webpack config to:
  - require refresh plugin + transformer
  - enable `webpack.HotModuleReplacementPlugin()` in development
  - add dev-only `ts-loader` custom transformer via `ReactRefreshTypeScript()`
  - set `transpileOnly: isEnvDevelopment`
  - inject page-only bootstrap entry `./src/dev/react-refresh-hmr.ts` into React page entries
  - keep background/content/injected entries on normal reload path
- Added dev bootstrap that:
  - calls `hot.accept()`
  - polls `hot.check(true)` every second when status is `idle`
  - reloads page on `abort` / `fail`

Verification evidence used:
- `yarn install --mode=skip-build` succeeded
- dev webpack compile emitted bundles with:
  - `react-refresh/runtime.js`
  - `__webpack_require__.$Refresh$`
  - refresh registration/signature markers

Verification blockers encountered:
- global compile still failed on unrelated existing TS error:
  - `apps/extension/src/utils/accounts-management.ts:75`
  - `TS2345` around `BlobOptions`
- lint also failed on unrelated existing formatting issues
- second dev compile hit `EADDRINUSE` on `webpack-ext-reloader` port 9090 after first server already bound it

Practical lesson:
- In extension repos using `webpack-ext-reloader`, prove Fast Refresh by source config + emitted refresh markers, but state clearly that full verification may still be blocked by unrelated repo errors.
- When re-running dev compile in same session, watch for reloader port collisions from previous run.
