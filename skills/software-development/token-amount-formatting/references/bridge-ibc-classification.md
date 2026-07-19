# Bridge/IBC Token Classification — Keplr Wallet

## Token Type Detection

Bridge-eligible tokens need **two** checks, not just `coinDenom`:

```ts
function isBridgeToken(tokens: ViewToken[]): boolean {
  const token = tokens[0].token;

  // Check 1: denom matches known bridge currencies
  const denomMatch = BRIDGE_CURRENCY_DENOMS.includes(
    token.currency.coinDenom as BridgeCurrency
  );

  // Check 2: at least one variant's chain maps to a known bridge network
  const chainValid = tokens.some(
    (v) => getNetworkIdFromChainId(v.chainInfo.chainId) != null
  );

  return !isIbcToken && denomMatch && chainValid;
}
```

**Why both?** Both ETH (mainnet) and Sepolia ETH have `coinDenom: "ETH"`. But only mainnet Ethereum (chainId `eip155:1`) resolves via `getNetworkIdFromChainId` → `"ETH"` because only chainId 1 is in `BRIDGE_NETWORK_CHAIN_ID_MAP`. Sepolia goes unmatched → correctly excluded from bridge tokens.

## Available "To" Networks Resolution

`getAvailableToNetworks(fromNetwork)` expects a **bridge network ID** (`"ETH"`, `"BSC"`, `"AIOZ"`), not a chain ID (`"eip155:1"`). Always convert first:

```ts
// BAD — chainId won't match swap direction from_network values
getAvailableToNetworks(getViewTokenChainId(fromNetworkData))

// GOOD — convert to bridge network ID first
const bridgeNetworkId = getNetworkIdFromChainId(
  getViewTokenChainId(fromNetworkData)
);
getAvailableToNetworks(bridgeNetworkId) // → ["AIOZ", "BSC", ...]
```

## BRIDGE_NETWORK_CHAIN_ID_MAP

```ts
// apps/extension/src/constants/bridge-networks.ts
export const BRIDGE_NETWORK_CHAIN_ID_MAP: Record<string, number> = {
  AIOZ: 168,     // aioz-evm chainId
  ETH: 1,        // ethereum mainnet
  BSC: 56,       // binance smart chain
};
```

Any token with an EVM chainId not in this map (e.g. Sepolia `11155111`, Goerli `5`) is **not** bridge-eligible, even if its `coinDenom` matches `BRIDGE_CURRENCY_DENOMS`.

## Resetting To-Recipient on Token/Network Change

When changing the token or "From" network, always reset both:

```ts
setToAddress("");
setToNetworkData(null);
form.setValue("toNetwork", "");
```

Applies to both IBC (recipient address) and BRIDGE (destination network) types.

## Key Files

| File | Purpose |
|---|---|
| `apps/extension/src/constants/bridge-networks.ts` | Bridge network config, chainId mapping, `getNetworkIdFromChainId` |
| `apps/extension/src/features/bridge-ibc/config/constants.ts` | `BRIDGE_CURRENCY_DENOMS` |
| `apps/extension/src/features/bridge-ibc/hooks/use-ibc-bridge-tokens.ts` | Token classification (IBC vs BRIDGE) |
| `apps/stores-internal/src/aioz-bridge/swap-directions.ts` | `getAvailableToNetworks` (expects bridge network IDs) |
| `apps/extension/src/pages/bridge-v2/index.tsx` | Bridge page wiring |
