# Bridge-v2 notes

Session-derived notes for `apps/extension/src/pages/bridge-v2/index.tsx`.

## Patterns used

- Recipient UI came from send-v2 pattern.
- Amount field cloned into `apps/extension/src/widgets/amount-field.tsx`.
- Amount widget stripped of local state after user correction; hook owns all state.
- Submit button cloned from `apps/extension/src/components/ui-v2/send/send-v2-form.tsx` visual block only.

## Useful gates

- `networkConfirmed = Boolean(selectedToken && selectedFromChainId)`
- recipient shown only when destination network is not bridge network
- submit button visual disabled when token/from/to missing or amount invalid/insufficient

## Verification command

- `yarn workspace @keplr-wallet/extension build:noop`

## Common drift to avoid

- local UI state creeping back into widget clones
- importing cloned UI from original `components/ui-v2/send/*` path instead of `widgets/*`
- wiring a fake submit handler before real bridge submission flow exists
