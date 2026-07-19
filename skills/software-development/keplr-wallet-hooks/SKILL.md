---
name: keplr-wallet-hooks
description: "Patterns and pitfalls for integrating @keplr-wallet/hooks, @keplr-wallet/stores, and TxChainSetter-based config objects in React/TS wallet extensions."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [keplr, cosmos, wallet, hooks, mobx, stores]
    related_skills: [token-amount-formatting, systematic-debugging]
---

# Keplr Wallet Hooks Integration

## Overview

This skill covers patterns for working with `@keplr-wallet/hooks` and `@keplr-wallet/stores` — the class hierarchy of `TxChainSetter`, the config-oriented hook methods (`useSendMixedIBCTransferConfig`, `useIBCTransferConfig`, `useSendTxConfig`, etc.), and the MobX `@computed` evaluation model that defers errors.

Applies to any Cosmos/Keplr wallet extension or mobile app.

## TxChainSetter chainId Null-Safety

### The Bug

`TxChainSetter.chainInfo` (`packages/hooks/src/tx/chain.ts`) is a MobX `@computed` that calls:

```ts
get chainInfo(): IChainInfoImpl {
  return this.chainGetter.getChain(this.chainId);
}
```

`chainGetter.getChain(chainId)` (`packages/stores/src/chain/base.ts`) does a map lookup keyed by `ChainIdHelper.parse(chainId).identifier`. If the chain isn't registered:

```ts
throw new Error(`Unknown chain info: ${chainId}`);
```

When `chainId` is `""`, `ChainIdHelper.parse("")` returns `{ identifier: "", version: 0 }` → map miss → **throw**.

### Why It's Tricky

- `@computed` defers evaluation — the hook call (e.g. `useSendMixedIBCTransferConfig(chainStore, queriesStore, "", ...)`) succeeds silently.
- Error fires later when a MobX consumer reads `feeConfig.fees`, `feeConfig.selectableFeeCurrencies`, `recipientConfig.bech32Prefix`, `amountConfig.sendableCurrencies` — any computed that dereferences `this.chainInfo`.
- In bridge page: `bridgeSummary` memo reads `feeConfig.fees` → crash.

### Config Classes That Read `chainInfo`

| Config | Properties that hit `this.chainInfo` |
|---|---|
| `FeeConfig` | `selectableFeeCurrencies`, fee calculations, `uiProperties` |
| `AmountConfig` | `sendableCurrencies`, `canUseCurrency` |
| `RecipientConfig` | bech32 prefix, address validation |
| `MemoConfig` | *(none — only reads `this._value`)* |
| `GasConfig` | *(none — only reads `this._value`)* |
| `SenderConfig` | *(none — empty `uiProperties`)* |
| `GasSimulator` | *(none — no `chainInfo` reads)* |

### All Classes That `extends TxChainSetter` (potential crash surface)

`AmountConfig`, `StakedAmountConfig`, `RecipientConfig`, `GasSimulator`, `MemoConfig`, `SenderConfig`, `GasConfig`, `FeeConfig`, `UnbondingAmountConfig` (+ variants in hooks-bitcoin, hooks-starknet).

### Fix Pattern

React hooks can't be conditional, so guard at the call site with a fallback to a known-valid chainId:

```ts
const safeBridgeChainId =
  bridgeChainId && chainStore.hasChain(bridgeChainId)
    ? bridgeChainId
    : chainStore.chainInfos[0]?.chainId ?? "";
```

Pass `safeBridgeChainId` to both `useSendMixedIBCTransferConfig` and `useGasSimulator`.

### Call Sites Repaired (aioz-wallet-mobile)

- `apps/extension/src/pages/bridge/index.tsx` — 3 occurrences
- `apps/extension/src/features/bridge-ibc/hooks/use-send-bridge.ts` — 3 occurrences
- `apps/extension/src/features/bridge-ibc/model/use-bridge-tx-config.ts` — 3 occurrences

### Gas Simulator → Fee/Gas Config Flow

See `references/gas-simulator-fee-flow.md` for full details on how `GasSimulator` pushes adjusted gas into `GasConfig`, which then feeds `FeeConfig.getFeeTypePrettyForFeeCurrency()` for fee display.

### Broader Rule

Any project using `@keplr-wallet/hooks` / `@keplr-wallet/stores` `TxChainSetter` subclass will have this gap. When integrating tx configs before chain info is guaranteed resolved, always `hasChain()`-guard the chainId before passing to hook configs.

## References

- `references/keplr-txchainsetter-chainid-null.md` — Full session transcript and file paths for the chainId null-safety fix
- `references/gas-simulator-fee-flow.md` — Detailed flow docs (gas-simulator → gas-config → fee-config)
- `../../../workspace/aioz-wallet-mobile/gas-estimation-flow.html` — **Interactive SVG diagram** of the full flow with animated chips (Init, Simulate, Update, Fee). Open in browser.

## FeePicker Reactivity Bug (Discovered 2026-07-08)

**File:** `apps/extension/src/widgets/fee-picker/model/fee.ts` lines 48-62

**Problem:** `FeePicker.init()` uses `autorun` that only tracks `feeConfig.getFeeTypePrettyForFeeCurrency()`. Since `FeeConfig.gasConfig` is not `@observable` and `gasConfig.gas` is a plain getter, the autorun doesn't re-run when `gasConfig.gas` changes (via simulation or manual edit).

```typescript
// FeePicker.init() - BROKEN
autorun(() => {
  this._feeTypes.forEach((type) => {
    this._feeInUIs.set(type, formatBalance(
      this.feeConfig.getFeeTypePrettyForFeeCurrency(this._feeCurrency, type)
    ));
  });
});
```

**Fix options:**
1. Add `@observable gasConfig: IGasConfig` to FeeConfig class
2. Use `reaction(() => feeConfig.gasConfig.gas, () => { /* update feeInUIs */ })` in FeePicker
3. Make `GasConfig.gas` a `@computed` on observable `_value` (already true) and ensure FeeConfig observes it

**Impact:** Fee selector UI shows stale fee amounts after gas estimation completes or user changes gas adjustment.
