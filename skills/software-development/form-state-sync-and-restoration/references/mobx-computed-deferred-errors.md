# MobX `@computed` Deferred Error Pattern

## The Pattern

Config classes using MobX `@computed` getters **defer errors** — the getter is not
evaluated until a consumer reads it.  Hook constructor (`new Config(...)`)
succeeds even when `chainId` is empty or missing.  The throw surfaces later,
at some unrelated render or effect.

## Common Path: `TxChainSetter.chainInfo`

All Keplr tx config classes (`SenderConfig`, `GasConfig`, `MemoConfig`,
`FeeConfig`, `IBCAmountConfig`, `IBCRecipientConfig`) extend `TxChainSetter`:

```
@computed
get chainInfo(): IChainInfoImpl {
  return this.chainGetter.getChain(this.chainId);
}
```

`chainGetter.getChain(chainId)` at `packages/stores/src/chain/base.ts`:

```
getChain(chainId: string): IChainInfoImpl<C> {
  const chainIdentifier = ChainIdHelper.parse(chainId);
  const chainInfo = this.chainInfoMap.get(chainIdentifier.identifier);
  if (!chainInfo) {
    throw new Error(`Unknown chain info: ${chainId}`);
  }
  return chainInfo;
}
```

## Empty-chainId Case

When `chainId = ""`:

1. `ChainIdHelper.parse("")` → `{ identifier: "", version: 0 }`
2. `chainInfoMap.get("")` → `undefined` (no chain with empty identifier)
3. Throws: `Error: Unknown chain info: `

## Caller Pattern

Common in bridge/v2 code — callers pass `bridgeChainId ?? ""` as chainId:

```ts
const bridgeConfigs = useSendMixedIBCTransferConfig(
  chainStore, queriesStore,
  bridgeChainId ?? "",          // ← empty when bridge chain unset
  senderAddress, ...
);
```

Hook call succeeds silently.  `Error: Unknown chain info:` surfaces only
when first consumer accesses `config.chainInfo` — e.g. a component rendering
`bridgeConfigs.gasConfig` or `bridgeConfigs.amountConfig`.

## Diagnostic Tips

1. **Error source is a mobx computed, not the hook** — if traceback points to
   `TxChainSetter.chainInfo` or `chainGetter.getChain`, the hook constructor
   already ran fine.  Bug is upstream: something that should set chainId
   before consumer reads.
2. **Trace @computed properties** — read the class hierarchy: `new Config()`
   stores chainId.  `setChain(id)` writes it.  `get chainInfo()` reads it.
   The timing gap is between set and first get.
3. **Check caller's `??` fallback** — `chainId ?? ""` masks the bug because
   empty string passes `ChainIdHelper.parse` and gets looked up as a valid
   key.  Guard: `if (!chainId) return null` before calling the hook.
4. **`setChain` does not re-validate** — `setChain(id)` only assigns
   `this._chainId = id`.  No map-check.  The throw comes on computed
   re-evaluation.
5. **Config memo key can mask it** — if a parent memoizes config objects and
   consumer reads `chainInfo` at render time, the error can appear and
   disappear depending on whether the consumer re-renders.

## Related Files

| File | Role |
|------|------|
| `packages/hooks/src/tx/chain.ts` | `TxChainSetter` — `@computed chainInfo` |
| `packages/stores/src/chain/base.ts` | `getChain()` — the throw site |
| `packages/cosmos/src/chain-id/cosmos.ts` | `ChainIdHelper.parse()` — `""` passes through |
| `packages/hooks/src/ibc/send-ibc-transfer.ts` | `useSendMixedIBCTransferConfig` — passes chainId through |
| `packages/hooks/src/tx/fee.ts` | `useFeeConfig` — consumer of chainInfo |
| `packages/hooks/src/tx/gas.ts` | `useGasConfig` — same |
| `packages/hooks/src/tx/memo.ts` | `useMemoConfig` — same |
| `packages/hooks/src/tx/sender.ts` | `useSenderConfig` — same |
