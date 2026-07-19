# NetworkPickerSheet: Balance formatting (unified)

## Architecture (post-refactor)

Single `NetworkPickerSheet` at `@/widgets/network-picker-sheet/`. No dual variants.

**How balance is computed** — via `formatBalance(token: CoinPretty, chainId?: string)` from `@/features/bridge-ibc/lib/utils.ts`:

```ts
export const formatBalance = (token: CoinPretty, chainId?: string) => {
  const denomHelper = new DenomHelper(token.currency.coinMinimalDenom);
  const fmtCoinPretty = formatTokenLabel(token);

  if (denomHelper.type === "native" && denomHelper.denom.startsWith("ibc/")) {
    return `${fmtCoinPretty.hideIBCMetadata(true).toString()}-IBC`;
  }
  if (denomHelper.type === "native") return fmtCoinPretty.toString();
  if (denomHelper.type === "cw20") {
    return `${fmtCoinPretty.hideDenom(true).toString()} ${denomHelper.denom}-CW20`;
  }
  if (denomHelper.type === "erc20") {
    const isBEP20 = chainId === EIP_BSC_CHAIN_ID;
    return `${fmtCoinPretty.hideDenom(true).toString()} ${token.denom}-${
      isBEP20 ? "BEP20" : "ERC20"
    }`;
  }
  return formatTokenLabel(token).toString();
};
```

## Token type classification

| `denomHelper.type` | Condition | Display format |
|---|---|---|
| `native` + starts with `ibc/` | IBC-wrapped native | `"1,234.56 ATOM-IBC"` |
| `native` | Plain native | `"1,234.56 ATOM"` |
| `cw20` | CosmWasm token | `"1,234.56 CONTRACT_ADDR-CW20"` |
| `erc20` + BSC chainId | BEP-20 on BSC | `"1,234.56 TOKEN-BEP20"` |
| `erc20` + other chainId | ERC-20 on Ethereum/etc | `"1,234.56 TOKEN-ERC20"` |
| fallback | Anything else | `formatTokenLabel(token).toString()` |

## Related imports

- `DenomHelper` from `@keplr-wallet/common` — classifies token type
- `formatTokenLabel` from `../hooks/use-ibc-bridge` — applies `maxDecimals(6).shrink(true).trim(true)` and returns a `CoinPretty` (or `IntPretty`)
- `CoinPretty` from `@keplr-wallet/unit` — the token amount object
- `EIP_BSC_CHAIN_ID` from `@/constants/bridge-networks` — "eip155:56"
