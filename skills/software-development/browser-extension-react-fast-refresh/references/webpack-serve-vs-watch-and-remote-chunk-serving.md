# webpack serve vs watch and remote popup chunk serving

Use when debugging webpack-dev-server in browser-extension repos with React Fast Refresh or custom reload clients.

## Durable lessons

- `webpack serve` plus top-level `watch: true` is a bad combo. `webpack-cli` warns: `No need to use the 'serve' command together with '{ watch: true | false }'`. For clean dev-server validation, run `webpack serve ... --no-watch` or make top-level watch conditional so serve mode owns rebuilds.
- If popup main bundle is `200 text/javascript` but split popup chunks are `404 text/html`, dev-server is not serving emitted split chunks at remote `publicPath` even though runtime URL generation is correct.
- In this repo class, reliable remote popup chunk serving needed:
  - `output.publicPath` set to dev-server origin in development
  - `devServer.static.directory = dist`
  - `devServer.static.publicPath = "/"`
  - `devServer.historyApiFallback = false`
  - `devServer.devMiddleware.publicPath = "/"`
  - `devServer.devMiddleware.writeToDisk = true`
- Verify exact failing chunk URL with `curl -I`. If it returns `200 text/javascript`, MIME serving is fixed. If it returns `404 text/html`, browser strict MIME failure is expected and CSP is not root cause yet.
- For extension pages, even after MIME serving is fixed, remote chunk execution may still hit MV3/CSP browser policy. Distinguish server MIME failures from browser policy failures.

## Useful verification sequence

1. Start dev server with serve mode, not plain webpack build:
   - `webpack serve --config webpack.config.js --host 127.0.0.1 --port 8080 --no-watch`
2. Check main popup bundle MIME:
   - `curl -I http://127.0.0.1:8080/popup.bundle.js`
3. Check exact failing split chunk MIME:
   - `curl -I http://127.0.0.1:8080/<exact-chunk-name>.bundle.js`
4. If split chunk is 404 but file exists in `dist/`, align `devServer.static` + `devMiddleware.writeToDisk`.
5. Only after MIME is fixed, investigate CSP / MV3 remote code limits.
