# WDS + extension CSP + publicPath notes

Session findings in webpack-based browser extension popup/sidepanel flow:

- `webpack-dev-server` can be installed and `webpack serve` can start successfully, while `package.json` dev script still uses plain `webpack` and therefore does not actually use `devServer`.
- `devServer.client.webSocketURL` controls websocket event transport only.
- `output.publicPath` controls where webpack runtime fetches split chunks and hot-update JSON/JS.
- In extension pages, setting dev `publicPath` to `http://127.0.0.1:8080/` makes runtime request remote chunk files such as `popup-*.bundle.js` and hot-update files from localhost.
- Even after adding MV3 `content_security_policy.extension_pages`, extension pages can still emit CSP errors like:
  - `Loading the script 'http://127.0.0.1:8080/....bundle.js' violates the following Content Security Policy directive: "script-src 'self'"`
- Practical lesson: localhost websocket signaling may work while remote script execution still fails.
- Safer dev fallback for extension pages:
  - keep scripts/chunks loaded from extension origin (`script-src 'self'`)
  - allow localhost only in `connect-src`
  - use custom websocket client to trigger full page reload on rebuild success
  - avoid remote `publicPath` unless browser/runtime behavior is explicitly proven acceptable in target environment

Useful CSP shape for reload-only dev signaling:

```json
"content_security_policy": {
  "extension_pages": "script-src 'self'; object-src 'self'; connect-src 'self' ws://127.0.0.1:8080 http://127.0.0.1:8080"
}
```

Caution:
- Adding `http://127.0.0.1:8080` to `script-src` may still not make remote extension-page bundles viable under MV3 policy.
- Treat remote `publicPath` in extension pages as experimental and browser-policy constrained, not a normal HMR setup.
