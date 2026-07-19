# Gas Estimation Flow Diagram Reference

## Overview
Interactive architecture diagram visualizing the gas estimation flow in aioz-wallet-mobile:
`GasSimulator` → `GasConfig` → `FeeConfig` → UI Components

## Files
- **Diagram**: `/home/aioz/workspace/aioz-wallet-mobile/gas-estimation-flow.html`
- **Source modules**:
  - `packages/hooks/src/tx/gas-simulator.ts` — simulation loop, KVStore caching, gas estimation
  - `packages/hooks/src/tx/gas.ts` — GasConfig observable wrapper
  - `packages/hooks/src/tx/fee.ts` — FeeConfig, fee computation, EIP-1559 integration
  - `apps/extension/src/widgets/fee-picker/model/fee.ts` — FeePicker UI model (has reactivity bug)

## Key Flow (4 phases)

### 1. Init & Cache Load
- GasSimulator autorun loads `initialGasEstimated` from KVStore
- Sets `isInitialized=true`

### 2. Simulation Loop
- Triggered when enabled + initialized + any reactive dependency changes
- `simulateGasFn()` → `tx.simulate(fee)` → `gasUsed`
- Updates `recentGasEstimated` if >2% change
- Persists to KVStore

### 3. GasConfig Update
- **Critical link**: GasSimulator autorun watches `gasEstimated`
- Computes `adjusted = gasEstimated * gasAdjustment` (default 1.3×)
- Calls `gasConfig.setValue(adjusted)` → updates `GasConfig._value`
- `gasConfig.gas` getter now returns new value

### 4. Fee Recalculation
- `getFeeTypePrettyForFeeCurrency(currency, type)` reads `gasConfig.gas` (reactive)
- Calls `getGasPriceForFeeCurrency()` — handles Osmosis, Initia, EVM fee-market, EIP-1559
- For EIP-1559: `getEIP1559TxFees(type)` → `maxFeePerGas`
- Returns `CoinPretty(gasPrice × gas + l1DataFee)`

## Known Reactivity Bug
**FeePicker** (`apps/extension/src/widgets/fee-picker/model/fee.ts:48-62`) uses `autorun` that only tracks `feeConfig.getFeeTypePrettyForFeeCurrency()`. Since `FeeConfig.gasConfig` is not `@observable` and `gasConfig.gas` is a plain getter, the autorun doesn't re-run when `gasConfig.gas` changes.

**Fix options:**
1. Add `@observable gasConfig: IGasConfig` to FeeConfig class
2. Use `reaction(() => feeConfig.gasConfig.gas, () => { /* update feeInUIs */ })` in FeePicker
3. Make `GasConfig.gas` a `@computed` on observable `_value` (already true) and ensure FeeConfig observes it

## Diagram Features
- 4 flow chips: Init, Simulate, Update, Fee
- Clickable nodes with detail panel
- Animated edge highlighting
- Dark/light theme with localStorage persistence
- Responsive (cards stack on mobile)