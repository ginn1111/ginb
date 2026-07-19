---
name: form-state-sync-and-restoration
description: Keep form state, config mirrors, query-param restore, and dependent field resets consistent in React Hook Form flows.
version: 0.1.0
author: Hermes Agent
license: MIT
---

# Form State Sync and Restoration

Use when a page has:
- React Hook Form state plus mirrored config/store state
- query-string or session-storage restore
- dependent fields like token/network/recipient/amount
- bugs where visible UI, form dirtiness, and config state drift apart

## Core rules

1. **User event updates both owners once.**
   - If form and config both own a field, update both in same handler.
   - Do not rely on a later sync effect for routine typing.

2. **Restore paths must mark RHF state correctly.**
   - Query/session restore that behaves like prefilled user input should usually call:
     - `form.setValue(name, value, { shouldDirty: true, shouldTouch: true })`
   - If config/store also owns the value, update that in same restore callback.

3. **Parent selection changes reset dependent fields in event handler.**
   - Token/asset/network changes can invalidate recipient or amount.
   - Clear stale dependent fields directly in the selection handler, not later in a reactive cleanup effect.

4. **Validate amount shape before any write.**
   - Character allow-list alone is not enough.
   - After cleanup/normalization, reject malformed decimals before writing form/config/display state.

## Known good patterns

### Restore recipient from query params
Bad:
- restore only config recipient
- call `form.setValue("recipient", value)` without dirty/touch flags

Good:
- update config recipient
- call `form.setValue("recipient", value, { shouldDirty: true, shouldTouch: true })`

### Asset or token change
When token/asset changes:
- clear network if tied to prior token
- clear amount if denom/balance changed
- clear recipient if address format or target asset context may differ

### Config error sync into RHF
Each config type (`recipientConfig`, `amountConfig`, `memoConfig`, `feeConfig`) exposes `uiProperties.error` that may hold validation errors (e.g. `InsufficientFeeError`). These must be synced to RHF so the form displays them.

Pattern — one effect per config:
```ts
useEffect(() => {
  const err = config.uiProperties.error;
  if (err) {
    setError("fieldName", { type: "manual", message: err.message });
    return;
  }
  // optional: clearErrors("fieldName") on no error — skip if submit handler
  // re-validates inline anyway
}, [config.uiProperties.error, setError]);
```

When adding a new config type (e.g. `feeConfig`), check ALL existing effects for sibling configs — if they all have one, the new one needs it too. Gap signal: a config error exists on `uiProperties.error` but is never forwarded to RHF in the hook.

### Validation guard before submit
Some Keplr hooks expose `useTxConfigsValidate` returning `{ interactionBlocked }`. This is `true` when **any** config has an error or `loading-block` state. Guard submit early:

```ts
const handleSubmit = form.handleSubmit(async () => {
  if (txConfigsValidate.interactionBlocked) return;
  // ... rest of submit
});
```

This replaces manual inline checks for each individual config's `uiProperties.error` in submit — the guard covers all of them at once. Use it when the hook already has `txConfigsValidate` computed; don't rederive the same logic.

### Extract shared error-sync hooks into reusable custom hooks
When a pattern repeats across a hook (`use-send-ibc.ts`) and a standalone component (`send-ibc.tsx`), extract the RHF-sync effect into its own custom hook (e.g. `useBridgeFeeErrorSync`) in a shared effects file (`use-send-ibc-effects.ts`). Both consumers then call it as a one-liner:

```ts
useBridgeFeeErrorSync({ feeConfig: sendConfigs.feeConfig, setError });
```

This avoids copy-paste drift and makes the error-sync behavior testable independently.

### "Two cases" rule
When adding or fixing an error-sync path (config `uiProperties.error` → RHF `setError`), always check sibling usage. If the same config type (`feeConfig`) is used in both a hook-level flow AND a standalone component, both need the same effect. The gap signal is: config error exists on `uiProperties.error` but is never forwarded to RHF in one of the consumers.

### `setError` type quirk with custom hooks
When a custom hook accepts `setError` as a parameter, using `UseFormSetError<Record<string, any>>` as the interface type does NOT work — a caller with a typed form (e.g. `UseFormSetError<SendIBCFormData>`) is not assignable to it because TypeScript checks `name` parameter variance strictly.

**Fix:** use `UseFormSetError<any>` instead of `UseFormSetError<Record<string, any>>`. This accepts any typed `setError` without complaints.

```ts
interface IUseBridgeFeeErrorSync {
  feeConfig: FeeConfig;
  setError: UseFormSetError<any>;  // not UseFormSetError<Record<string, any>>
}
```

## Pitfalls

### Inline callbacks in effect deps = render loop

When a custom hook accepts callback parameters (`setError`, `clearErrors`, `clearAmountError`, etc.) and lists them in a `useEffect` dependency array, **passing inline arrow functions creates a new reference every render**, which fires the effect every render, which calls `setError(...)`, which triggers another render — infinite loop freeze.

```ts
// BAD — inline arrow, new ref every render
useBridgeAmountValidation({
  clearAmountError: () => clearErrors("amount"),
  setAmountError: (message) => setError("amount", { type: "manual", message }),
});

// GOOD — useCallback, stable ref
const clearAmountError = useCallback(() => clearErrors("amount"), [clearErrors]);
const setAmountError = useCallback(
  (message: string) => setError("amount", { type: "manual", message }),
  [setError]
);
useBridgeAmountValidation({ clearAmountError, setAmountError });
```

**Checklist to detect this class of bug:**
1. Custom hook accepts callback parameter(s) that end up in a `useEffect` dep array
2. Call site passes an inline arrow / anonymous function
3. Effect calls `setError`, `setState`, or any setter that triggers re-render
4. → pull each inline callback into `useCallback` before passing

**Scan for sibling call sites** — when one call site in a file is fixed, check other calls to the same custom hook in the same file or sibling files. They often have the same pattern.

### Query restore updates config but not form dirtiness
Symptom:
- input shows restored recipient
- UI logic checking dirty/touched acts like field untouched

Fix:
- make restore callback update both config and RHF with `shouldDirty` + `shouldTouch`

### Controller `fieldState` drifts when custom handler bypasses `field.onChange`
Symptom:
- `Controller` render uses `fieldState.isTouched` / `fieldState.error`
- input `onChange` calls a custom action that uses `form.setValue(...)`
- visible value updates, but `fieldState` in render lags or disagrees with `form.formState`

Fix:
- if custom action owns updates, read touched/error from `form.formState` for that field
- or restore full `Controller` ownership by calling `field.onChange` and deriving side effects from there
- do not mix `fieldState` display with an external write path and assume they stay aligned

### Reset lives in wrong layer
Symptom:
- one page variant clears recipient on asset change
- another page variant leaves stale recipient because page-level handler skipped reset

Fix:
- put reset in exact source event handler for that page variant
- verify all variants, not only old page

### Leading-zero and malformed-decimal drift
Symptom:
- amount field accepts `1..2` or stale zero-prefixed values
- downstream parse/display logic diverges

Fix:
- cleanup input
- apply exact leading-zero regex if requested by product
- full-shape validate before writing state
- if minus sign should be excluded, remove it in first sanitizer before validation and keep a regression test for `-12.5 -> 12.5` or whatever product expects

## Verification checklist

- Change token/asset -> recipient cleared if dependency exists
- Restore recipient from query/session -> field visible and RHF dirty/touched true
- Invalid decimals never enter display/form/config state
- Leading-zero normalization matches requested regex behavior

## References
- `references/send-and-bridge-form-pitfalls.md` — concrete wallet send/bridge examples: query restore dirty-state bug, asset-change recipient reset, malformed decimal guard
- `references/mobx-computed-deferred-errors.md` — mobx `@computed` defers config-class errors (e.g. empty-chainId throw) until first consumer reads `chainInfo`.  Diagnostic tips, file map.
