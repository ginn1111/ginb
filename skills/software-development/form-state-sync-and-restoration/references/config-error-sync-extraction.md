# Config Error Sync Hook Extraction (Bridge IBC)

## Problem

`use-send-ibc.ts` had 3 inline `useEffect`s syncing `recipientConfig/amountConfig/memoConfig.uiProperties.error` → RHF `setError`. A 4th (`feeConfig`) was added inline. The same pattern existed in `send-ibc.tsx` as inline submit-time checks.

## Extraction Target

Move all 4 effects into `use-send-ibc-effects.ts` as named hooks, consumed as one-liners from both files.

## Before

### In `use-send-ibc.ts` (3 inline effects + 1 new inline)

```ts
useEffect(() => {
  const recipientError = sendConfigs.recipientConfig.uiProperties.error;
  if (recipientError) {
    setError("recipient", { type: "manual", message: recipientError.message || "Invalid recipient address" });
    return;
  }
  clearErrors("recipient");
}, [clearErrors, sendConfigs.recipientConfig.uiProperties.error, setError]);

useEffect(() => {
  if (isAiozIbcErc20) { clearErrors("amount"); return; }
  const amountError = sendConfigs.amountConfig.uiProperties.error;
  if (amountError) {
    setError("amount", { type: "manual", message: amountError.message || "Invalid amount" });
    return;
  }
  clearErrors("amount");
}, [clearErrors, isAiozIbcErc20, sendConfigs.amountConfig.uiProperties.error, setError]);

useEffect(() => {
  const memoError = sendConfigs.memoConfig.uiProperties.error;
  if (memoError) {
    setError("memo", { type: "manual", message: memoError.message });
    return;
  }
  clearErrors("memo");
}, [clearErrors, sendConfigs.memoConfig.uiProperties.error, setError]);

useEffect(() => {
  const feeError = sendConfigs.feeConfig.uiProperties.error;
  if (feeError) {
    setError("amount", { type: "manual", message: feeError.message || "Insufficient fee" });
    return;
  }
}, [sendConfigs.feeConfig.uiProperties.error, setError]);
```

### In `send-ibc.tsx` (inline submit-time checks, no real-time sync)

No effects at all — errors only checked inside `onSubmit`.

## After

### In `use-send-ibc-effects.ts` (4 named hooks)

```ts
interface IUseBridgeFeeErrorSync {
  feeConfig: FeeConfig;
  setError: UseFormSetError<any>;  // NOT UseFormSetError<Record<string, any>>
}

export const useBridgeFeeErrorSync = ({ feeConfig, setError }) => {
  useEffect(() => {
    const err = feeConfig.uiProperties.error;
    if (err) {
      setError("amount", { type: "manual", message: err.message || "Insufficient fee" });
    }
  }, [feeConfig.uiProperties.error, setError]);
};
```

Same pattern for `useBridgeRecipientErrorSync` (adds `clearErrors("recipient")` on no-error), `useBridgeAmountErrorSync` (adds `isAiozIbcErc20` branch, clears `"amount"`), `useBridgeMemoErrorSync` (clears `"memo"`).

### In `use-send-ibc.ts` (4 one-liners)

```ts
useBridgeRecipientErrorSync({ recipientConfig: sendConfigs.recipientConfig, setError, clearErrors });
useBridgeAmountErrorSync({ amountConfig: sendConfigs.amountConfig, isAiozIbcErc20, setError, clearErrors });
useBridgeMemoErrorSync({ memoConfig: sendConfigs.memoConfig, setError, clearErrors });
useBridgeFeeErrorSync({ feeConfig: sendConfigs.feeConfig, setError });
```

### In `send-ibc.tsx` (same one-liners)

Import from `@/features/bridge-ibc/hooks/use-send-ibc-effects`.

## Type Lesson

`UseFormSetError<Record<string, any>>` is NOT assignable from `UseFormSetError<SendIBCFormData>` because TypeScript checks name parameter variance strictly. Use `UseFormSetError<any>` in the interface — it accepts any typed `setError`.

## Files Changed

- `apps/extension/src/features/bridge-ibc/hooks/use-send-ibc-effects.ts`
- `apps/extension/src/features/bridge-ibc/hooks/use-send-ibc.ts`
- `apps/extension/src/components/send/send-ibc.tsx`

## Related

- `txConfigsValidate.interactionBlocked` guard added in both hook and component.
- `useBridgeFeeErrorSync` does NOT `clearErrors("amount")` on no-error because amount may have errors from `useBridgeAmountValidation`.
