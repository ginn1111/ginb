# Bridge V2 Infinite Render Loop — Debug Trace

**File**: `apps/extension/src/pages/bridge-v2/index.tsx`
**Symptom**: page freezes / CPU 100% — infinite render loop

## Call Chain

1. `BridgePageV2Content` renders → `useBridgeAmount()` called
2. `useBridgeAmount` calls `form.watch("amount")` and `form.watch("displayAmount")` → live subscriptions
3. `BridgePageV2Content` calls `useSendIbc({...})` → inside `useSendIbc`:

```ts
useBridgeAmountValidation({
  amountValue,
  availableBalanceDec,
  chainId,
  clearAmountError: () => clearErrors("amount"),       // NEW FN every render
  feeConfig: sendConfigs.feeConfig,
  feeCurrencyBalance,
  isERC20,
  setAmountError: (message) =>                          // NEW FN every render
    setError("amount", { type: "manual", message }),
  token,
});
```

4. `useBridgeAmountValidation` in `use-send-ibc-effects.ts` has these deps:

```ts
useEffect(() => {
  // ... validates amount ...
  if (error) setAmountError(message);   // calls setError("amount", ...)
  else clearAmountError();               // calls clearErrors("amount")
}, [
  amountValue,
  availableBalanceDec,
  chainId,
  clearAmountError,     // ← new ref every render
  feeConfig,
  feeConfig.fees,
  feeConfig.selectableFeeCurrencies,
  feeConfig.uiProperties.loadingState,
  feeCurrencyBalance,
  isERC20,
  setAmountError,       // ← new ref every render
  token,
]);
```

5. Effect fires on every render because `clearAmountError` / `setAmountError` are new arrows each time.
6. If validation succeeds → `clearErrors("amount")` → RHF state update → re-render → goto 5
7. If validation fails → `setError("amount", ...)` → RHF state update → re-render → goto 5

Either path loops infinitely.

## Fix

`use-send-ibc.ts`: hoist both callbacks to `useCallback`:

```ts
const clearAmountError = useCallback(() => clearErrors("amount"), [clearErrors]);
const setAmountError = useCallback(
  (message: string) => setError("amount", { type: "manual", message }),
  [setError]
);
```

Then pass them by reference:

```ts
useBridgeAmountValidation({
  clearAmountError,
  setAmountError,
  // ... rest same
});
```

## Related files

- `apps/extension/src/features/bridge-ibc/hooks/use-send-ibc.ts` — call site
- `apps/extension/src/features/bridge-ibc/hooks/use-send-ibc-effects.ts` — effect definition (lines 153-271)
