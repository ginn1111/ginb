# AIOZ Wallet Mobile — bridge-v2 picker ordering

## Session lesson

Bridge-v2 token and network pickers needed same product rule:
- prioritize `aioz_168-1` first
- then sort by balance descending
- compare with `Dec`, not `number`
- move sort logic out of component bodies

## Good placement

Shared comparator lives in:
- `apps/extension/src/features/bridge-ibc/hooks/use-ibc-bridge.ts`

Consumers:
- `apps/extension/src/widgets/network-picker-sheet/network-picker-sheet.tsx`
- `apps/extension/src/widgets/token-picker-sheet/token-picker-sheet.tsx`

## Good comparator shape

- `AIOZ_NETWORK_CHAIN_ID = "aioz_168-1"`
- `isAiozNetworkChainId(chainId)`
- `compareDecDesc(a: Dec, b: Dec)` using `equals` + `gt`
- `compareBridgePickerNetworks(a, b)`
- `compareBridgePickerTokens(a, b)`

## Concrete pitfall caught by verification

`Dec.eq` does not exist in this repo's unit type.
Use `Dec.equals(...)`.

## Verification used

- `yarn workspace @keplr-wallet/extension test`
- `yarn workspace @keplr-wallet/extension build:noop`
- `yarn workspace @keplr-wallet/extension build`

## Why save

Same mistake likely repeats in:
- send-v2 token/network pickers
- bridge destination selectors
- any wallet asset selector with promoted-chain business rule
