# Bridge page fee subtraction verification note

Session pattern:
- Changed file: `apps/extension/src/pages/bridge-v2/index.tsx`
- Change: pass `subtractFee` into `useBridgeAmount` only when fee denom matches selected token denom; otherwise `undefined`.

Verification sequence that worked:
1. `yarn workspace @keplr-wallet/extension build:noop` → passed
2. `yarn workspace @keplr-wallet/extension test --passWithNoTests` → passed
3. Explicit root verification required afterward:
   - `yarn run build` → passed
   - `yarn run test` → failed outside touched package

Root test failure shape:
- failing task: `@aioz-ui/icon-react:test`
- symptom in root output: nested workspace expects `pnpm` because `packages/aioz-ui/package.json` has `packageManager` field
- interpretation: ambient monorepo/workspace-runner issue, not evidence against bridge page diff when extension-scoped checks already pass

Reuse:
- When explicit root verification is demanded, run it.
- When root failure lands in unrelated workspace, preserve both truths:
  - changed package verified
  - repo root not fully green due unrelated blocker
