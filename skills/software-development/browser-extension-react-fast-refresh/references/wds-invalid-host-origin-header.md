# Webpack Dev Server Invalid Host/Origin Header in Browser-Extension Debug Flows

Use when a standalone HTML playground, `file://` page, or another local origin loads code that talks to a webpack dev server and the browser console shows:

- `[webpack-dev-server] Invalid Host/Origin header`
- `HTTP/1.1 403 Forbidden`
- `Invalid Host header`

## Durable lesson

This failure is a separate guard from:

- `devServer.client.webSocketURL`
- `output.publicPath`
- extension CSP `connect-src`

If those are already correct, webpack dev server can still reject the request based on host/origin validation.

## Practical fix

For local-only debugging, add:

```js
devServer: {
  host: "127.0.0.1",
  allowedHosts: "all",
}
```

Safer alternative when exact origins are known: use an explicit host allowlist instead of `"all"`.

## Verification shape

1. Restart the old webpack dev server. Config changes do nothing until restart.
2. Probe with mismatched host/origin headers:

```bash
curl -i -H 'Host: evil.test' -H 'Origin: http://evil.test' http://127.0.0.1:8080/
```

3. Before fix: expect `403 Invalid Host header`.
4. After fix + restart: expect no `Invalid Host header` response.

## Notes

- In extension repos, an old server process commonly masks the fix; kill stale port owner first.
- If the new dev server cannot start because of file-watcher exhaustion (`ENOSPC`), that blocks runtime proof but does not invalidate the config diff itself.
- Keep this dev-only. Do not cargo-cult `allowedHosts: "all"` into production-facing configs.
