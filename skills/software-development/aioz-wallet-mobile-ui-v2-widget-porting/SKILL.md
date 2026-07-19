---
name: aioz-wallet-mobile-ui-v2-widget-porting
description: Port send-v2 UI pieces into aioz-wallet-mobile extension flows by cloning widgets, keeping state in hooks, and matching existing V2 button/layout patterns.
---

# When to use

Use when moving or reusing send-v2 UI in `aioz-wallet-mobile`, especially for extension flows like bridge-v2, send, recipient, amount, and submit actions.

# Core rules

1. Read source UI-v2 component first. Clone exact visual pattern before inventing anything.
2. If reused outside send-v2, prefer cloning into `apps/extension/src/widgets/` and import from widgets in target flow.
3. Keep widget components dumb. Put state, derived values, formatting, toggle state, and handlers in flow hook (`use-*`) and pass via props.
4. For bridge-v2 amount flow, `useBridgeAmount` owns amount display state, input mode state, conversion labels, max handling, and change handlers. `widgets/amount-field.tsx` should be presentational only.
5. For bridge-v2 recipient flow, show recipient field only when destination is not a bridge network.
6. For amount entry, disable input and MAX action until source chain is chosen (`networkConfirmed`).
7. When cloning send-v2 submit action, copy bottom fixed button styling exactly (`variant="danger"`, disabled opacity/cursor/pointer behavior, `Continue` label) but do not invent a submit handler. Wire visual button first; only attach behavior when real bridge flow exists.
8. In this repo, prefer shortest diff. Reuse existing hook outputs instead of adding local component state.

# Bridge-v2 checklist

- `apps/extension/src/pages/bridge-v2/index.tsx`
  - import widget component from `@/widgets/...`
  - derive state from bridge hooks, not component-local UI state
  - make form body scrollable when adding fixed bottom action
- `apps/extension/src/features/bridge-ibc/hooks/use-bridge-amount.ts`
  - keep amount UI state here
  - return every prop needed by widget amount field
- `apps/extension/src/widgets/amount-field.tsx`
  - presentational only
- `apps/extension/src/widgets/recipient-field.tsx`
  - widget clone of send-v2 field when reused by bridge-v2
- `apps/extension/src/widgets/contact-picker-sheet.tsx`
  - widget clone of send-v2 contact sheet when reused by bridge-v2

# Pitfalls

- Do not leave bridge-v2 using ad-hoc local state if a dedicated hook exists.
- Do not keep behavior logic inside cloned widget field components.
- Do not enable amount typing before source chain selection.
- Do not claim submit behavior exists if only button visuals were cloned.
- Do not patch the wrong file (`send-ibc.tsx`) when user explicitly asked for `pages/bridge-v2/index.tsx`.

# Verification

- For extension-only UI changes, verify with:
  - `yarn workspace @keplr-wallet/extension build:noop`
- If build passes, report exact file paths changed and whether button is visual-only or actually wired.

# References

- `references/bridge-v2-notes.md` — bridge-v2-specific notes: widget paths, gating rules, and drift to avoid.
