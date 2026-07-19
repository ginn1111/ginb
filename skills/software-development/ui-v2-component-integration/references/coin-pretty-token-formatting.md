# CoinPretty token amount formatting

`@keplr-wallet/unit` — specifically `CoinPretty` — is the standard way token amounts are carried and displayed in this codebase.

## How CoinPretty works internally

```ts
// Constructor (coin-pretty.ts:53-67)
constructor(currency, amount) {
  this.intPretty = new IntPretty(
    amount.quoTruncate(
      DecUtils.getTenExponentNInPrecisionRange(currency.coinDecimals)
    )
  ).maxDecimals(currency.coinDecimals);
}
```

**Key:** CoinPretty divides the input `amount` by `10^coinDecimals`. It expects amounts in **minimal denom** (smallest unit). It stores the **display value** internally.

| Input | coinDecimals | Internal display value |
|---|---|---|
| 555795781258283355997 | 18 | 555.795781258283355997 |
| 1000000 | 6 | 1.0 |

## The formatting chain

```ts
coinPretty
  .maxDecimals(6)    // cap decimal places
  .trim(true)        // strip trailing zeros: "1.500000" → "1.5"
  .shrink(true)      // reduce decimals when integer part is large
  .toString();
```

### trim (`DecUtils.trim` — `dec-utils.ts:5`)

Removes trailing `0` chars after the decimal point, then the `.` itself if nothing remains.

```
"1.5000"  → "1.5"
"100.00"  → "100"
"0.00100" → "0.001"
```

### shrink (`CoinUtils.shrinkDecimals` — `coin-utils.ts:117`)

Dynamically reduces decimal precision based on integer magnitude:

```
actualDecimals = max(maxDecimals - integerDigits + 1, 0)
```

With `maxDecimals=6`:

| Value | Integer digits | Effective decimals | Output |
|---|---|---|---|
| 1234.567890 | 4 | 6 - 4 + 1 = **3** | `1,234.568` |
| 1.234567 | 1 | 6 - 1 + 1 = **6** | `1.234567` |
| 12345678.123 | 8 | 6 - 8 + 1 = **0** | `12,345,678` |

### maxDecimals

Hard cap on decimal digits shown. Without it, defaults to `coinDecimals` (often 18).

## Common pitfall: wrong multiplier when converting display ↔ minimal denom

**Symptoms:** CoinPretty produces a very small number (like `5.5e-16`) when fed a display-ready Dec.

**Root cause:** using `coinDecimals` (e.g. `18`) instead of `10^coinDecimals` (e.g. `10^18`) when converting from display value to minimal denom.

```ts
// ❌ WRONG — multiplies by 18
.mul(new Dec(token.currency.coinDecimals))

// ✅ CORRECT — multiplies by 10^18 (ten-to-the-power-of-coinDecimals)
.mul(DecUtils.getTenExponentN(token.currency.coinDecimals))
```

**Why:** `DecUtils.getTenExponentN(18)` returns `10^18` as a `Dec`. `new Dec(18)` returns `18`. The difference is 17 orders of magnitude.

## How to sum CoinPretty amounts across chains

When you have multiple `CoinPretty` instances for the same token on different chains and want a combined total label:

```ts
import { CoinPretty, Dec, DecUtils } from "@keplr-wallet/unit";

const zeroDec = new Dec(0);

const totalDec = tokens.reduce(
  (sum, t) =>
    sum.add(
      t.token
        .toDec()                                                       // display value (e.g. 555.7957)
        .mul(DecUtils.getTenExponentN(t.token.currency.coinDecimals))  // back to minimal denom
    ),
  zeroDec
);

const totalLabel = new CoinPretty(token.currency, totalDec)
  .maxDecimals(6)
  .trim(true)
  .shrink(true)
  .toString();
```

Or skip the round trip entirely when you just need display totals:

```ts
const totalDisplay = tokens.reduce(
  (sum, t) => sum.add(t.token.toDec()),
  zeroDec
);

const totalLabel = new IntPretty(totalDisplay)
  .maxDecimals(6)
  .trim(true)
  .shrink(true)
  .toString();
```

## When NOT to use CoinPretty

If you already have a display-ready `Dec` (e.g. from parsing a JSON response), use `IntPretty` directly instead of creating a fake currency with `coinDecimals: 0`:

```ts
import { IntPretty, Dec } from "@keplr-wallet/unit";

new IntPretty(new Dec("555.795781"))
  .maxDecimals(6)
  .trim(true)
  .shrink(true)
  .toString();
// → "555.795781"
```
