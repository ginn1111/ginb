# Gas Simulator → Fee/Gas Config Flow

## Overview
How the `GasSimulator` class coordinates with `GasConfig` and `FeeConfig` via MobX autoruns.

**File:** `packages/hooks/src/tx/gas-simulator.ts`

---

## Flow Summary

```
simulateGasFn() 
    → state.setRecentGasEstimated(gasUsed)
    → gasEstimated getter returns recentGasEstimated (or initialGasEstimated from KVStore)
    → autorun: gasConfig.setValue(gasEstimated * gasAdjustment)
    → gasConfig.gas updates
    → FeeConfig.getFeeTypePrettyForFeeCurrency() reads this.gasConfig.gas
    → fee amount = gasPrice * gas + l1DataFee
    → CoinPretty displayed in UI
```

---

## Key Code Locations

### GasSimulator init (lines 305-468)
```typescript
// 1. Load persisted estimate from KVStore
autorun(() => {
  kvStore.get(key).then(saved => state.setInitialGasEstimated(saved));
});

// 2. Run simulation when enabled + initialized
autorun(() => {
  const tx = simulateGasFn();
  const fee = feeConfig.toStdFee();
  // Only re-simulate when fee goes zero↔non-zero
  if (needsSimulation) {
    state.refreshTx(tx);
    state.refreshStdFee(fee);
  }
});

// 3. Execute simulation + persist
autorun(() => {
  const promise = state.tx.simulate(state.stdFee);
  promise.then(({ gasUsed }) => {
    if (meaningfulChange) state.setRecentGasEstimated(gasUsed);
    kvStore.set(key, gasUsed);
  });
});

// 4. **Critical**: Push adjusted gas into GasConfig
autorun(() => {
  if (enabled && gasEstimated != null) {
    gasConfig.setValue(gasEstimated * gasAdjustment);  // default 1.3x
  }
});
```

### FeeConfig.getFeeTypePrettyForFeeCurrency (fee.ts:591-603)
```typescript
readonly getFeeTypePrettyForFeeCurrency = computedFn(
  (feeCurrency, feeType) => {
    const gas = this.gasConfig.gas;              // ← reads adjusted gas
    const gasPrice = this.getGasPriceForFeeCurrency(feeCurrency, feeType);
    const feeAmount = gasPrice.mul(new Dec(gas)).add(this.l1DataFee ?? new Dec(0));
    return new CoinPretty(feeCurrency, feeAmount.roundUp()).maxDecimals(feeCurrency.coinDecimals);
  }
);
```

---

## Chain of Reactivity

| Change | Propagates To |
|--------|---------------|
| `gasEstimated` (simulation result) | `gasConfig.setValue()` |
| `gasConfig.gas` | `FeeConfig.getFeeTypePrettyForFeeCurrency()` |
| `feeConfig.type` / `feeConfig.currency` | `getFeeTypePrettyForFeeCurrency()` re-evaluates |
| `gasAdjustmentValue` (user input) | `gasConfig.setValue()` → fee recalc |

---

## L1 Data Fee

Added in `FeeConfig.getFeeTypePrettyForFeeCurrency` (line 597):
```typescript
.add(this.l1DataFee ?? new Dec(0))
```

**Purpose:** Accounts for rollup L1 calldata cost (Arbitrum/Optimism). Without it, fee estimate would be too low on L2 chains.

Stored via `FeeConfig.setL1DataFee(fee: Dec)` — set externally when L1 fee oracle available.

---

## EIP-1559 Path

`FeeConfig.getGasPriceForFeeCurrency` (line 761-765) calls:
```typescript
if (this.canEIP1559TxFeesAndReady()) {
  const { maxFeePerGas, gasPrice } = this.getEIP1559TxFees(feeType);
  return maxFeePerGas ?? gasPrice;
}
```

`FeeConfig.getEIP1559TxFees` (fee.ts:777-822) queries:
- `ethereumQueries.queryEthereumBlock` → `baseFeePerGas`
- `ethereumQueries.queryEthereumFeeHistory` → priority fee percentiles
- Returns `{ maxFeePerGas, maxPriorityFeePerGas, gasPrice? }`

**Note:** `maxFeePerGas = baseFeePerGas * multiplier + maxPriorityFeePerGas`. Used as effective gas price for fee display.

---

## Persistence

- `KVStore` key: `${chainIdentifier}/${key}` (default key from hook init)
- On app restart: `initialGasEstimated` loaded instantly → `gasConfig` set → fee shown immediately
- Fresh simulation runs async and may update to a slightly different value

---

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Fee shows 0 initially | `gasEstimated` is undefined until simulation completes | Show "Estimating..." or use `initialGasEstimated` |
| Fee jumps after a moment | Initial KVStore value differs from fresh simulation | Expected — 1.3x adjustment + fresh sim |
| L2 fee too low | `l1DataFee` not set | Call `feeConfig.setL1DataFee(l1Fee)` from chain-specific logic |
| GasConfig not updating | `gasAdjustmentValue` is `""` or invalid → `gasAdjustment` returns 0 | Validate input in `setGasAdjustmentValue` |

---

## Related Files

- `packages/hooks/src/tx/fee.ts` — FeeConfig, getEIP1559TxFees, getFeeTypePrettyForFeeCurrency
- `packages/hooks/src/tx/types.ts` — IGasConfig, IFeeConfig interfaces
- `packages/hooks/src/tx/chain.ts` — TxChainSetter base class