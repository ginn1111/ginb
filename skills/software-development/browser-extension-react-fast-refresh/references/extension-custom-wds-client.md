# Custom webpack-dev-server websocket client for browser extension pages

Session pattern:
- User wanted custom `src/dev/dev-reload.ts` websocket client for extension React pages.
- Initial bootstrap used forced `window.location.reload()` on dev-server events.
- This created risk of deadloop in browser extension page context: page reload -> websocket reconnect -> message -> page reload.

Working pattern:
- Use `import.meta.webpackHot` in TS/ESM bootstrap instead of redeclaring `module`.
- Read socket config from compile-time env accessors already available in bundle (`process.env["WDS_SOCKET_PORT"]`, `process.env["WDS_SOCKET_PATH"]`).
- Parse webpack-dev-server websocket payloads rather than string-matching only one event.
- Track:
  - `lastHash`
  - `updateInFlight`
- Call `hot.check(true)` only when:
  - hot runtime exists
  - status is `idle`
  - no update already in flight
- Do not force `window.location.reload()` on reconnect, `ok`, or `content-changed` for extension page HMR.
- For `static-changed`, prefer logging/ignoring first until a safe non-looping full reload strategy is proven.

Practical pitfall found:
- Hardcoding websocket host to `0.0.0.0` may satisfy a user's local setup, but this is normally a server bind address, not a browser client destination. Use only when explicitly requested.

Verification evidence from session:
- `npx tsc -p tsconfig.json --noEmit --pretty false` -> exit 0
- `npx cross-env NODE_ENV=development webpack --config webpack.config.js --no-watch` -> exit 0
- Remaining webpack warning was unrelated (`@protobufjs/inquire` critical dependency)
