# Webpack dev server reload client notes for browser-extension pages

Session learnings:
- Standard webpack-dev-server message flow in this setup is usually `hash` then `ok` / `still-ok`; a `content-changed` event should not be assumed.
- Pure reload mode works better than `hot.check(true)` when extension pages hit reconnect loops or feel one build tick behind.
- Good pure reload rule:
  - ignore first `ok` after initial socket connect
  - reload on subsequent `ok`
  - ignore `still-ok`, `hash`, `warnings`, `errors`, `invalid`
  - treat `static-changed` as dangerous-by-default because it can produce reconnect → reload → reconnect loops in extension pages
- `module.hot.dispose()` only fires during real HMR replacement/removal; it does not help preserve state across `window.location.reload()`.
- To persist client state across full reloads, use `sessionStorage` / browser storage or server-side state keyed by a stable client id.
- In TS ESM files, `import.meta.webpackHot` is safer than `module.hot` to avoid `Property 'hot' does not exist on type 'Module'` errors.
- For webpack, websocket event origin and hot-update asset origin are separate:
  - `devServer.client.webSocketURL` controls the websocket endpoint
  - `output.publicPath` controls where split chunks and `*.hot-update.{json,js}` are fetched from
- In MV3 extension pages, allowing localhost in `connect-src` can enable websocket/http signaling, but remote script/chunk execution remains constrained by extension-page CSP and browser policy.
- If remote chunk fetches fail with MIME `text/html`, dev server is returning HTML fallback or a not-found page for the chunk path. Verify `webpack serve` is actually running and align:
  - `output.publicPath`
  - `devServer.devMiddleware.publicPath`
  - `historyApiFallback: false`
  - `static: false` during debugging
- `0.0.0.0` is a server bind address, not ideal browser target. Prefer `127.0.0.1` or another client-reachable host for websocket and chunk URLs unless the environment proves otherwise.
