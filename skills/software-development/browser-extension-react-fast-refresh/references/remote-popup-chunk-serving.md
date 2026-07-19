# Remote popup chunk serving for webpack-dev-server

Condensed notes from AIOZ Wallet extension session.

## Symptom pattern

Browser popup requests a remote split chunk such as:

`http://127.0.0.1:8080/popup-node_modules_formatjs_intl_lib_src_create-intl_js-node_modules_ethersproject_abi_lib_es-802039.bundle.js`

Browser error:
- `Refused to execute script ... because its MIME type ('text/html') is not executable`

## What this usually means

Not primarily CSP. First suspect dev-server pathing.

If the chunk URL returns `text/html`, webpack-dev-server is serving:
- 404 HTML page, or
- HTML fallback

instead of JS.

## Quick proof steps

1. Check popup root bundle:
   - `curl -I http://127.0.0.1:8080/popup.bundle.js`
2. Check exact failing split chunk:
   - `curl -I http://127.0.0.1:8080/<failing-split-chunk>.bundle.js`
3. Inspect local dist for same file:
   - chunk existing in `dist/` but 404 from dev server means serving config mismatch.

Expected good result:
- `HTTP/1.1 200 OK`
- `Content-Type: text/javascript` (or equivalent JS MIME)

Bad result seen in session before fix:
- `HTTP/1.1 404 Not Found`
- `Content-Type: text/html; charset=utf-8`

## Working config pattern

When experimenting with remote popup chunk loading from `http://127.0.0.1:8080/`:

- `output.publicPath = "http://127.0.0.1:8080/"` in development
- `devServer.client.webSocketURL` points to same host/port/path
- `devServer.historyApiFallback = false`
- `devServer.static.directory = path.resolve(__dirname, "dist")`
- `devServer.static.publicPath = "/"`
- `devServer.static.watch = false`
- `devServer.devMiddleware.publicPath = "/"`
- `devServer.devMiddleware.writeToDisk = true`
- optional `Access-Control-Allow-Origin: *` header for cross-origin loading experiments

Why `writeToDisk: true` mattered here:
- popup root bundle was available from dev-server memory
- split chunk was not reachable remotely until dev-server aligned with on-disk `dist/` output

## CSP distinction

Do not mix these up:
- `connect-src` => websocket / fetch / XHR
- `script-src` => remote JS chunks

Widening `connect-src` alone does **not** fix remote chunk execution.

## TS runtime note

For custom client bootstrap in TS repos, `module.hot` typings may be absent. Use `import.meta.webpackHot` with a local interface instead of fighting repo-global typings.
