# TxChainSetter chainId Null-Safety — Full Analysis

## Session Context

- File: `aioz-wallet-mobile/apps/extension/src/pages/bridge/index.tsx`
- Branch: `feat/bridge-ibc` (keplr wallet extension)

## Trace

1. **`chainGetter.getChain("")`** at `packages/stores/src/chain/base.ts:855`
   - Calls `ChainIdHelper.parse("")` → returns `{ identifier: "", version: 0 }`
   - Lookup in `chainInfoMap` for `""` key — no chain registered with empty identifier
   - Throws `new Error("Unknown chain info: ")`

2. **`TxChainSetter.chainInfo`** at `packages/hooks/src/tx/chain.ts:18-21`
   - MobX `@computed` getter → calls `this.chainGetter.getChain(this.chainId)`
   - `@computed` defers: constructing/`setChain("")` stores the empty string, never reads chainInfo

3. **Deferred crash on first consumer read:**
   - `bridgeSummary` memo at line 242-244 reads `bridgeConfigs.feeConfig.fees`
   - `FeeConfig.selectableFeeCurrencies` (line 196) reads `this.chainInfo.bip44.coinType`
   - MobX evaluates `@computed` chainInfo → `getChain("")` → 💥

## Three Call Sites Fixed

### 1. bridge/index.tsx

```tsx
// Before (line 150-159):
const bridgeConfigs = useSendMixedIBCTransferConfig(
    chainStore,
    queriesStore,
    bridgeChainId ?? "",
    ...
);
// useGasSimulator also had bridgeChainId || "" at line 204

// After:
const safeBridgeChainId =
    bridgeChainId && chainStore.hasChain(bridgeChainId)
      ? bridgeChainId
      : chainStore.chainInfos[0]?.chainId ?? "";
```

Same pattern applied in `use-send-bridge.ts` and `use-bridge-tx-config.ts`.

## Why Not Fix in the Library

`@keplr-wallet/hooks` and `@keplr-wallet/stores` are consumed as pre-built packages (npm). We can't patch the throw in `getChain()`. The guard must live at the application call site.

## Related Chains

- `ethereumAccountStore.getAccount("")` — also used with `bridgeChainId || ""` in the same files, though it may not throw (depends on implementation)
- `GasSimulator` also extends `TxChainSetter` but does NOT read `this.chainInfo` — safe for now
