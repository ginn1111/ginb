# Send and bridge form pitfalls

## Query-param recipient restore not marked dirty
Files seen:
- `src/hooks/use-send-standard-query-string.ts`
- `src/hooks/use-tx-config-query-string.ts`
- `src/pages/send-v2/index.tsx`
- `src/components/ui-v2/send/send-v2-form.tsx`

Pattern:
- query restore reader calls page callback
- page callback updated config recipient only, or updated RHF without `shouldDirty` / `shouldTouch`
- visible recipient restored, but dirty-state logic stayed false

Fix pattern:
- in restore callback, set config/store value
- then call `form.setValue("recipient", value, { shouldDirty: true, shouldTouch: true })`

## Asset change must clear recipient
File seen:
- `src/pages/send-v2/send-v2-page.tsx`

Pattern:
- token/asset change cleared chain, denom, amount
- recipient left stale

Fix pattern:
- clear recipient in same token/asset selection handler

## Bridge amount handler validation
Files seen:
- `src/features/bridge-ibc/hooks/use-bridge-amount.ts`
- `src/features/bridge-ibc/lib/utils.ts`
- `src/features/bridge-ibc/lib/utils.test.ts`

Patterns:
- invalid decimals like `1..2`, `0.1.2`, `12.34.56` must be rejected before display/form/config writes
- requested leading-zero cleanup regex: `/^0{1,}(\d{1,})/g`
- `.5` normalization still handled after cleanup

Verification examples:
- asset change clears recipient
- query restore marks recipient dirty/touched
- malformed decimal tests pass

## Fee config error gap in bridge IBC
Files seen:
- `src/features/bridge-ibc/hooks/use-send-ibc.ts` (hook)
- `src/features/bridge-ibc/hooks/use-send-ibc-effects.ts` (extracted hook)
- `src/components/send/send-ibc.tsx` (standalone component — second case)

Pattern:
- `recipientConfig`, `amountConfig`, `memoConfig` each had `useEffect` syncing `uiProperties.error` → RHF `setError`
- `feeConfig.uiProperties.error` had NO such effect — `InsufficientFeeError` was silently swallowed
- `feeConfig.uiProperties.error` is computed at `packages/hooks/src/tx/fee.ts:1245-1247` but was only consumed in sign page, never in bridge IBC send form
- The gap existed in BOTH the hook (`use-send-ibc.ts`) and the standalone component (`send-ibc.tsx`) — two independent consumers of the same `sendConfigs`

Fix:
- extract `useBridgeFeeErrorSync({ feeConfig, setError })` to `use-send-ibc-effects.ts`
- call from hook: one-liner `useBridgeFeeErrorSync({ feeConfig: sendConfigs.feeConfig, setError })`
- call from component: same one-liner alongside existing `useTxConfigsValidate`
- guard both `handleSendIbc` and component `onSubmit` with `txConfigsValidate.interactionBlocked`
- using `UseFormSetError<any>` not `UseFormSetError<Record<string, any>>` for the interface — TS covariance quirk with typed form data

Takeaway: when checking which config errors are shown, verify ALL consumers (hook + component) not just one. Extract shared logic into custom hook to avoid copy-paste drift.
