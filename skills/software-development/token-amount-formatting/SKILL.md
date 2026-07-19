---
name: token-amount-formatting
description: Format token amounts with @keplr-wallet/unit (Dec, IntPretty, CoinPretty) — the correct formatting chain, multiplier pitfalls, IBC denom handling, and Dec→number conversion. Applies to any Cosmos/Keplr wallet project.
category: software-development
---

# Token Amount Formatting (Keplr Wallet Unit)

Formatting token amounts in a Cosmos wallet using `@keplr-wallet/unit`. Covers `Dec`, `IntPretty`, `CoinPretty`, `DecUtils`.

## Core Types

| Type | Purpose | Key methods |
|---|---|---|
| `Dec` | Arbitrary-precision decimal (big-integer backed, 18 decimal precision) | `.toString(prec?)`, `.add()`, `.sub()`, `.mul()`, `.quo()`, `.gt()`, `.lt()`, `.equals()` |
| `IntPretty` | Human-readable decimal display | `.maxDecimals()`, `.shrink()`, `.trim()`, `.toString()` |
| `CoinPretty` | Dec + currency denom pairing | All `IntPretty` methods + `.hideIBCMetadata()`, `.showRawCoinDenom()`, `.hideDenom()`, `.maxCoinDenomLength()` |
| `DecUtils` | Decimal utilities | `.getTenExponentN()`, `.trim()` |

## 🚨 CRITICAL Pitfalls

### 1. Defaults give 18 decimal places
`IntPretty`/`CoinPretty` default `maxDecimals` is 18. **Always** chain `.maxDecimals(6)` for display.

```ts
// BAD — shows "0.000000000000001234 ATOM"
new IntPretty(dec).toString()

// GOOD — shows "0.000001 ATOM"
new IntPretty(dec).maxDecimals(6).shrink(true).trim(true).toString()
```

### 2. Multiplier confusion: ×18 ≠ ×10¹⁸
`new Dec(n)` creates `n` (e.g., `new Dec(18)` = 18). To get exponent, use `DecUtils.getTenExponentN(n)`:

```ts
const coinDecimals = 18;

// BAD — gives ×18 not ×10¹⁸
dec.mul(new Dec(coinDecimals));

// GOOD — gives ×10¹⁸
dec.mul(DecUtils.getTenExponentN(coinDecimals));
```

### 3. CoinPretty divides amount by 10^coinDecimals
Constructor takes amount in **minimal denom**, divides by 10^coinDecimals internally.

```ts
// coinDecimals=18, passing 555.795781 → tiny number (re-divided)
new CoinPretty(currency, new Dec("555.795781")) // wrong

// Pass in minimal unit (e.g., wei/satoshi)
new CoinPretty(currency, new Dec("555795781000000000000")) // correct
```

To pass a display-ready `Dec` directly, fake `coinDecimals: 0` or use `IntPretty` alone.

## Formatting Chains

### Full CoinPretty chain
```ts
new CoinPretty(currency, amountInMinimalDenom)
  .hideIBCMetadata(true)    // show clean denom, not IBC hash
  .maxDecimals(6)            // limit decimal places
  .shrink(true)              // reduce decimals when int part is big
  .trim(true)                // strip trailing zeros
  .toString()
  // → "1,234.56 ATOM"
```

### Plain Dec (no currency)
```ts
new IntPretty(dec)
  .maxDecimals(6)
  .shrink(true)
  .trim(true)
  .toString()
// → "1,234.56"
```

### Dec → JS number (display only)
```ts
parseFloat(dec.toString())
// or
Number(dec.toString())
// ⚠️ loses precision beyond ~15 significant digits
```

## IBC Denom Handling

### hideIBCMetadata (preferred)
When IBC trace is resolved (`currency.originCurrency` exists):
```ts
coinPretty.hideIBCMetadata(true).toString()
// → "ATOM" instead of "ATOM (ibc/27394FB0...)"
```

### makeCoinDenomPretty (for raw IBC hashes)
Static utility that hex-decodes raw denom strings:
```ts
CoinPretty.makeCoinDenomPretty("ibc/27394FB092D2ECDCCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2")
// tries hex→UTF-8 decode
```

### Denom-only / Amount-only rendering
```ts
coinPretty.hideDenom(true).toString()    // "1,234.56" (just amount)
coinPretty.hideAmount(true).toString()   // "ATOM" (just denom)
```

Useful for `description` labels in picker triggers where denom is shown separately:
```tsx
description={`${fromNetworkData.token.hideIBCMetadata(true).hideDenom(true).toString()} available`}
// → "555.79 available"
```

### Currency type hierarchy
```ts
interface Currency {                     // Native chain token
  coinDenom, coinMinimalDenom, coinDecimals
}
interface IBCCurrency extends Currency {  // IBC-bridged token
  paths, originChainId,
  originCurrency: Currency | undefined   // Original source-chain currency
}
interface ERC20Currency extends Currency { // EVM token
  type: "erc20", contractAddress
}
interface CW20Currency extends Currency { // CosmWasm token
  type: "cw20", contractAddress
}
```

### Token type classification with DenomHelper

Use `DenomHelper` from `@keplr-wallet/common` to classify a token by its `coinMinimalDenom` at runtime (useful for branching on type in balance-formatting helpers):

```ts
import { DenomHelper } from "@keplr-wallet/common";

const denomHelper = new DenomHelper(currency.coinMinimalDenom);

denomHelper.type   // "native" | "cw20" | "erc20"
denomHelper.denom  // raw denom string (e.g. "ibc/27394F...", "uatom", contract address)
```

Common display suffixes per type (used in `formatBalance` helper):

| `denomHelper.type` | Condition | Display |
|---|---|---|
| `native` + starts with `ibc/` | IBC-wrapped native | `"ATOM-IBC"` |
| `native` | Plain native | `"ATOM"` |
| `cw20` | CosmWasm | `"CONTRACT-CW20"` |
| `erc20` | EVM | `"TOKEN-ERC20"` or `"TOKEN-BEP20"` (check `chainId === EIP_BSC_CHAIN_ID`)

### Explicit-label toggle pattern for bridge UI

When a formatter takes an `explicit` flag for bridge token labels, treat it as **suffix toggle**, not **amount toggle**.

Correct behavior:
- `explicit: false` → keep normal `CoinPretty` rendering (`amount + denom`), e.g. `"1.234567 ATOM"`, `"1.234567 USDT"`
- `explicit: true` → keep amount, but replace plain denom rendering with typed suffix label, e.g. `"1.234567 ATOM-IBC"`, `"1.234567 USDT-ERC20"`, `"1.234567 cw20:aioz1contract-CW20"`

Pitfall:
- Do **not** read `explicit` as “hide amount” or “return denom only”. User expectation in bridge picker/summary UI was amount beside coin denom in normal mode; `explicit` only adds protocol/type information.

Implementation pattern:
```ts
const normal = fmtCoinPretty.hideAmount(hideAmount).toString();
const label = fmtCoinPretty.hideDenom(true).hideAmount(hideAmount).toString();

return explicit ? `${label} ${token.denom}-ERC20` : normal;
```

For IBC native tokens, keep normal path as:
```ts
const normal = fmtCoinPretty.hideAmount(hideAmount).hideIBCMetadata(true).toString();
return explicit ? `${normal}-IBC` : normal;
```

**`currency` vs `currency.originCurrency`:** `currency` is the token's representation on the current chain. `originCurrency` (on `IBCCurrency` only) is the **original** source-chain currency — carries the native `coinMinimalDenom` (e.g. `"uatom"`) and `coinDecimals`. Non-IBC tokens have no `originCurrency` — check via `"originCurrency" in currency`.

### Key fields on ViewToken / Currency
| Field | What it holds |
|---|---|
| `currency.coinDenom` | Human-readable denom (e.g., "ATOM"), set by resolved IBC trace |
| `currency.coinMinimalDenom` | Raw chain denom (e.g., "ibc/27394FB0...", "uatom") |
| `currency.originCurrency` | The original IBC source currency — has the native `coinMinimalDenom` and `coinDecimals` |

## DecUtils Reference

```ts
DecUtils.getTenExponentN(n)  // returns Dec for 10^n (use as multiplier)
DecUtils.trim(dec)            // strips trailing zeros from a Dec string
```

## shrink() Formula

`IntPretty.shrink(true)` reduces `maxDecimals` when integer part is large: `maxDecimals - integerDigits + 1` (min 0). So with `maxDecimals(6)`:
- `1234.567890` → `1234.56789` (intDigits=4, maxDec=3)
- `12345678.90` → `12345678` (intDigits=8, maxDec=-1 → 0)

## CoinUtils
```ts
CoinUtils.shrinkDecimals(decStr, maxDec, intDigits)
// Same logic as shrink(), usable standalone on strings
```

## See Also
- `packages/unit/src/decimal.ts` — Dec class source
- `packages/unit/src/int-pretty.ts` — IntPretty formatting options
- `packages/unit/src/coin-pretty.ts` — CoinPretty + makeCoinDenomPretty
- `packages/unit/src/dec-utils.ts` — DecUtils.trim
- `packages/unit/src/coin-utils.ts` — CoinUtils.shrinkDecimals
- `references/bridge-ibc-classification.md` — Bridge token classification pitfalls (chain validation, To-network resolution)
