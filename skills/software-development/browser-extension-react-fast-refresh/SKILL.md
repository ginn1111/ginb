---
name: browser-extension-react-fast-refresh
description: Add or troubleshoot React Fast Refresh / hot reload in webpack-based browser extensions, especially ts-loader setups without webpack-dev-server.
---

# Browser Extension React Fast Refresh

Use when:
- User wants React component hot reload / Fast Refresh in a webpack-based browser extension.
- Extension already uses `webpack-ext-reloader` or plain webpack watch instead of `webpack-dev-server`.
- App compiles TS/TSX with `ts-loader` and needs React Fast Refresh without switching whole build pipeline.

Do not assume:
- `webpack-ext-reloader` alone gives real Webpack HMR. It usually gives extension/page reload, not Fast Refresh state-preserving updates.
- Built `dist/` artifacts prove current source config is correct. Always inspect source webpack config and package manifest.

## Core approach

1. Inspect webpack source config, not only emitted bundles.
2. Confirm whether project uses `ts-loader`, `babel-loader`, or both.
3. For `ts-loader` path, add dev-only deps:
   - `@pmmmwh/react-refresh-webpack-plugin`
   - `react-refresh`
   - `react-refresh-typescript`
4. Make `ts-loader` dev-only Fast Refresh aware:
   - `transpileOnly: true` in development
   - `getCustomTransformers().before = [ReactRefreshTypeScript()]` in development
5. Enable webpack HMR in development:
   - `new webpack.HotModuleReplacementPlugin()`
   - dev-only hot update filenames if needed
6. Add `ReactRefreshWebpackPlugin` in development only.
7. Inject HMR bootstrap only into React extension-page entries (popup/options/register/etc), not background/content/injected scripts unless they truly render React UI.
8. If setup does not use `webpack-dev-server` or hot middleware socket client, add a tiny dev bootstrap that:
   8. If setup uses a custom dev bootstrap for extension pages, choose transport behavior based on actual runtime behavior, not theory:
      - use `import.meta.webpackHot` (or equivalent runtime handle) instead of redeclaring `module` in TS ESM files
      - parse webpack-dev-server websocket payloads (`hash`, `ok`, `still-ok`, `warnings`, `errors`, `invalid`, `static-changed`) instead of treating every reconnect/message as a reload signal
      - do **not** assume a `content-changed` event exists; standard webpack-dev-server commonly does not emit it in this setup
      - if HMR via `hot.check(true)` causes reconnect/reload loops or feels one tick behind, simplify to pure full-page reload mode
      - for pure reload mode, ignore first `ok` after initial connect, then reload on subsequent `ok` only
      - do **not** assume a `content-changed` event exists; standard webpack-dev-server commonly emits `hash` then `ok` / `still-ok`
      - ignore `still-ok`, `hash`, `warnings`, `errors`, and `invalid` in pure reload mode
      - be careful with `static-changed`; in extension pages it can create reconnect → reload loops, so default to ignoring it unless proven safe
      - gate reload with a one-shot boolean so one rebuild cannot trigger multiple reloads
      - do **not** call `window.location.reload()` on socket reconnect by default in extension pages; this can create a reconnect → reload → reconnect loop
      - `module.hot.dispose()` runs only during real HMR replacement/removal, not during full `window.location.reload()`; do not rely on it to preserve state in reload-only mode
      - for state that must survive full page reloads, use `sessionStorage` / browser storage or server-side state keyed by a client id; module-scope variables die on reload
      - if using real HMR in TS ESM files, prefer `import.meta.webpackHot` over `module.hot` to avoid `Property 'hot' does not exist on type 'Module'` errors
      - remote websocket origin and remote hot-update asset origin are different knobs: `devServer.client.webSocketURL` affects event transport, while `output.publicPath` affects where `hot.check()` fetches `*.hot-update.{json,js}` and split chunks
      - browser-extension MV3 pages can usually allow remote websocket/http via `connect-src`, but remote JS/chunk/hot-update execution is still constrained by extension-page CSP and browser policy; updating `publicPath` to localhost can trigger CSP or MIME failures even when socket works
      - if remote chunk loads fail with `MIME type ('text/html') is not executable`, dev server is returning HTML fallback / not-found for the chunk path; align `webpack serve`, `output.publicPath`, `devServer.devMiddleware.publicPath`, and disable `historyApiFallback` while debugging
      - for extension pages, `0.0.0.0` may be used as a bind address for the server but is a poor browser target; prefer a concrete client-reachable host such as `127.0.0.1` for websocket/chunk URLs unless the environment proves otherwise
      - reserve full reload for truly non-HMR assets only, and even then verify it does not loop in the extension environment
   9. Verify by compiling development bundle and searching emitted JS for:

      - separate CSP concerns clearly: `connect-src` can allow websocket/http signaling to localhost, but `script-src` still governs remote JS chunk execution; allowing localhost under CSP may still not make remote extension-page scripts viable in MV3
      - when testing remote publicPath on extension pages, expect console errors like `violates the following Content Security Policy directive: "script-src 'self'"`; safest fallback is local packaged scripts + remote websocket reload signal only
   9. Verify by compiling development bundle and searching emitted JS for:

      - for browser-extension pages, do **not** point `output.publicPath` at `http://127.0.0.1:<port>/` (or any localhost origin) just to make `hot.check()` fetch from dev server: MV3/MV2 extension CSP blocks remote script/chunk execution, so hot-update JS and split chunks must still load from extension origin (`'self'`)
      - if you need localhost only for signaling, keep scripts on extension origin and allow localhost only in `connect-src` (e.g. websocket/http to dev server); remote script loading and remote chunk publicPath are a dead end for extension popup/side-panel pages under normal CSP
   9. Verify by compiling development bundle and searching emitted JS for:

      - reserve full reload for truly non-HMR assets only, and even then verify it does not loop in the extension environment
   9. Verify by compiling development bundle and searching emitted JS for:

   - extension repos may have `webpack-dev-server` installed and a valid `devServer` block, but `package.json` dev script can still be plain `webpack`
   - for custom websocket bootstrap, connect to `ws://<current-host>:<port>/ws`; do not use `0.0.0.0` as browser websocket host unless the user explicitly insists and has proven it reachable from the browser
   - when a standalone local HTML page, `file://` page, or another foreign origin hits `webpack-dev-server` and you see `[webpack-dev-server] Invalid Host/Origin header`, add a dev-only `devServer.allowedHosts` rule (often `"all"` for local debugging) in addition to `host`, `client.webSocketURL`, and `output.publicPath`; this guard is separate from websocket/publicPath wiring
   - websocket host and HMR fetch host are separate knobs: `devServer.client.webSocketURL` controls the socket, while `output.publicPath` controls where `hot.check()` fetches hot-update assets
   - if `hot.check()` fetches from the extension/page origin, set a dev-only absolute `output.publicPath` such as `http://127.0.0.1:8080/`
   - when returning from HMR experiments back to pure reload mode, remove stray `module.hot` code from the bootstrap; TypeScript ESM files commonly error on `module.hot` and stale HMR code can silently reintroduce wrong behavior
   - in TypeScript with strict index-signature checks, access env keys as `process.env["WDS_SOCKET_PORT"]` / `process.env["WDS_SOCKET_PATH"]`
10. Verify by compiling development bundle and searching emitted JS for:
   - `react-refresh/runtime.js`
   - `__webpack_require__.$Refresh$`
   - component registration/signature markers
10. Report separately:
   - whether Fast Refresh wiring exists
   - whether full repo build is blocked by unrelated pre-existing lint/type errors

## ts-loader pattern

Typical dev-only loader shape:

- exclude `node_modules`
- `transpileOnly: isEnvDevelopment`
- `getCustomTransformers: () => ({ before: isEnvDevelopment ? [ReactRefreshTypeScript()] : [] })`

Keep production path clean: no refresh plugin, no HMR plugin, no injected refresh bootstrap.

## Entry strategy

Good targets:
- popup page
- options page
- onboarding/register page
- side panel page
- any HTML-rendered React extension page

Avoid by default:
- background worker/service worker
- content scripts
- injected page scripts

Reason: those paths usually need extension reload semantics, not React Fast Refresh.

## Verification rules

- Fresh compile required before claiming setup works.
- If repo has unrelated type/lint errors, say verification is blocked globally and provide narrower evidence from emitted dev bundle markers.
- Distinguish:
  - full page reload
  - extension auto reload
  - real React Fast Refresh wiring

## Pitfalls

- Running webpack from wrong working directory can break relative asset reads inside config.
- `webpack-ext-reloader` may bind its own port and still not provide true HMR transport.
- React Refresh plugin docs prefer `babel-loader`; `ts-loader` route is community-supported, so keep implementation minimal and isolated to development.
- If using custom HMR bootstrap, make it page-only and fail-safe: fallback to `window.location.reload()` on HMR abort/fail.
- Do not claim success solely because old `dist/` files already contain refresh runtime strings.
- MV3 extension pages are hostile to remote HMR assets. `connect-src` can allow websocket / fetch to localhost, but remote `script-src` for `http://127.0.0.1:8080/...` chunks may still be blocked by browser policy even if the manifest CSP string includes localhost. Prefer websocket-triggered full reload with extension-local bundles unless remote chunk execution is explicitly proven in that browser.
- If you experiment with remote `output.publicPath`, verify the exact failing chunk URL with `curl -I`. `200 text/javascript` means dev-server serving is correct; `404 text/html` means the browser is getting an HTML error page and strict MIME checking will fail before CSP becomes the next blocker.
- For webpack-dev-server to serve split popup chunks reliably in this repo class, `devServer.static` should point at `dist`, `historyApiFallback` should stay `false`, and `devMiddleware.writeToDisk` may be needed so the chunk path requested by the extension exists on disk as well as in memory.

## Pitfalls

- Running webpack from wrong working directory can break relative asset reads inside config.
- `webpack-ext-reloader` may bind its own port and still not provide true HMR transport.
- React Refresh plugin docs prefer `babel-loader`; `ts-loader` route is community-supported, so keep implementation minimal and isolated to development.
- If using custom HMR bootstrap, make it page-only and fail-safe: fallback to `window.location.reload()` on HMR abort/fail.
- Do not claim success solely because old `dist/` files already contain refresh runtime strings.
- MV3 extension pages are hostile to remote HMR assets. `connect-src` can allow websocket / fetch to localhost, but remote `script-src` for `http://127.0.0.1:8080/...` chunks may still be blocked by browser policy even if the manifest CSP string includes localhost. Prefer websocket-triggered full reload with extension-local bundles unless remote chunk execution is explicitly proven in that browser.
- If you experiment with remote `output.publicPath`, verify the exact failing chunk URL with `curl -I`. `200 text/javascript` means dev-server serving is correct; `404 text/html` means the browser is getting an HTML error page and strict MIME checking will fail before CSP becomes the next blocker.
- For webpack-dev-server to serve split popup chunks reliably in this repo class, `devServer.static` should point at `dist`, `historyApiFallback` should stay `false`, and `devMiddleware.writeToDisk` may be needed so the chunk path requested by the extension exists on disk as well as in memory.
- `connect-src` and `script-src` solve different failures: widening `connect-src` only unblocks websocket/fetch/XHR. Remote chunks from `http://127.0.0.1:8080/...` still need `script-src` allowance and may still be constrained by MV3 policy.
- MIME `text/html` for remote chunk usually means dev-server serving fallback/404, not CSP. Verify exact chunk URL with `curl -I` before blaming HMR runtime or browser policy.
- if `popup.bundle.js` is `200 text/javascript` but split chunks are `404 text/html`, webpack-dev-server is not serving emitted split chunks at remote `publicPath`; serve `dist/` explicitly and write emitted files to disk.
- in this repo class, a working remote-chunk recipe was: `devServer.static = { directory: path.resolve(__dirname, "dist"), publicPath: "/", watch: false }`, `historyApiFallback: false`, `devMiddleware.publicPath = "/"`, `devMiddleware.writeToDisk = true`, plus remote `output.publicPath` and `headers["Access-Control-Allow-Origin"] = "*"`.
- `withReactRefreshEntry()` helpers are easy to accidentally leave as no-ops; verify the development branch really injects the custom bootstrap (e.g. `./src/dev/dev-reload.ts`) and that the main popup entry uses the helper too.
- only inject refresh/bootstrap into React extension-page entries (popup/register/ledger/onboarding/side-panel). Keep background, content scripts, and injected scripts on plain entries unless you have a proven HMR story for them.
- when webpack aborts with `is not accepted` for a React page module (for example `./src/pages/main/index.tsx -> ./src/index.tsx`), add an accept boundary at the root entry with `import.meta.webpackHot?.accept([...], () => root.render(<App />));` rather than relying only on the custom websocket bootstrap.
- if you declare `ImportMeta.webpackHot` in more than one file, the declarations must be compatible. Prefer one shared shape broad enough for `accept`, `check`, `status`, and `addStatusHandler`, or avoid redeclaring a narrower shape in another entry file.
- `module.hot` typing may fail in TS extension repos; prefer `import.meta.webpackHot` with a small local interface when repo lacks `webpack/module` typings.

## Support files

- `references/extension-ts-loader-fast-refresh.md` — notes from real session applying this pattern in a webpack extension repo using `webpack-ext-reloader`.
- `references/wds-extension-reload-client.md` — websocket event patterns and pure reload-mode rules for webpack-dev-server in browser-extension pages.
- `references/extension-custom-wds-client.md` — custom webpack-dev-server websocket client notes for extension pages, including loop-avoidance rules for `hot.check(true)` vs full reload.
- `references/wds-extension-csp-and-publicpath.md` — notes on `publicPath`, websocket transport, and MV3 CSP limits when trying to load remote dev-server chunks in extension pages.
- `references/remote-popup-chunk-serving.md` — remote popup split-chunk serving recipe: CSP distinctions, `publicPath`, webpack-dev-server `static`/`devMiddleware` alignment, and MIME-check workflow.
- `references/webpack-serve-vs-watch-and-remote-chunk-serving.md` — durable notes on avoiding `webpack serve` + top-level `watch` conflicts and fixing `200 main bundle / 404 split chunk` dev-server behaviour in extension popup flows.
- `references/wds-invalid-host-origin-header.md` — standalone HTML / foreign-origin `Invalid Host/Origin header` diagnosis: why `allowedHosts` matters separately from websocket URL, publicPath, and CSP.
- `references/react-cross-package-ref-mismatch.md` — TS2322 cross-package React ref type mismatch from duplicate `@types/react` copies. Narrow `React.ComponentProps<'div'>` to `React.HTMLAttributes<HTMLDivElement>` when component doesn't need `ref`.
