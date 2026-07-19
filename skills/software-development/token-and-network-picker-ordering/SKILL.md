---
name: token-and-network-picker-ordering
description: Order wallet token/network pickers with shared comparators, chain priority rules, and exact balance comparisons.
---

# Token and Network Picker Ordering

Use when changing sort order for wallet token pickers, network pickers, bridge pickers, or send/receive asset selectors.

## Core rules

1. Put ordering logic outside UI components.
2. Keep comparator functions in shared model/hook/util layer near data shaping.
3. Compare balances with exact domain units (`Dec`, `CoinPretty`, existing money types), not `parseFloat`, `Number(...)`, or subtraction on formatted strings.
4. UI component should consume pre-sorted data or import shared comparator only.
5. If product wants a promoted chain first (for example AIOZ mainnet), make that an explicit priority branch before balance comparison.

## Recommended pattern

- Define `PROMOTED_CHAIN_ID` constant once.
- Add `isPromotedChainId(...)` helper.
- Add `compareDecDesc(a, b)` helper using domain methods like `equals`, `gt`, `lt`.
- Add class-level comparators such as:
  - `compare...Networks(a, b)`
  - `compare...Tokens(a, b)`
- Sort token summaries at data-assembly time.
- Sort per-token network variants with same shared comparator.
- Remove duplicate inline `.sort(...)` logic from picker components.

## Pitfalls

- Do not use `Dec.eq`; use real supported methods (`equals`, `gt`, `lt`) from current unit type.
- Do not convert balances to `number` only to compare sort order.
- Do not keep one comparator in data layer and another slightly different comparator in component layer.
- Do not leave a component-local fallback sort after moving logic outward.

## Verification

1. Run package-scoped tests.
2. Run package-scoped typecheck/noop build.
3. If full package build is expected for confidence, run it too and separate existing warnings from new failures.

## AIOZ-specific note

For AIOZ wallet bridge pickers, `aioz_168-1` is promoted ahead of pure balance ordering.

## Support files

- `references/aioz-wallet-mobile-bridge-v2.md` — concrete repo example for bridge-v2 token/network picker ordering.
