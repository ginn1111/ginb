---
name: ui-v2-component-integration
title: UI-v2 Component Integration
description: Integrate reusable ui-v2 components (TokenPickerSheet, NetworkPickerSheet, AmountField, TokenField, NetworkField, LabeledPickerTrigger) into pages outside the send flow — bridge, swap, stake, etc.
triggers:
  - Need token/network selection on a non-send page
  - Replacing inline BottomSheet + SearchToken with TokenPickerSheet / NetworkPickerSheet
  - Adding network picker sheet driven by a token selection
  - Adding address/contact picker (ContactPickerSheet) for recipient field
  - Adding recipient selection (RecipientInput + RecipientModal) for IBC transfers
  - Adding memo input below recipient on bridge-v2 / non-send pages
  - Conditionally showing recipient field based on destination network type (bridge vs non-bridge)
  - Reusing sendConfigs.memoConfig for memo state instead of local React state
  - Wiring LabeledPickerTrigger with icon and value for token/network/address display
  - Adding bridge (EVML) destination network picker (BridgeNetworkPickerSheet)
  - Handling disabled state or zero-balance filtering in picker sheets
  - Fixing stale pending state in picker sheets when current prop changes externally
  - Integrating ui-v2 send components into any page
  - Formatting token amounts from CoinPretty (ViewToken.token) for display
  - Summing token balances across chains with correct minimal-denom conversion
  - Using useIBCBridgeTokens (instead of useSendTokenData) for bridge-v2 page
---

# UI-v2 Component Integration

When a page outside the send flow (bridge, swap, etc.) needs token or network selection, reuse the send-v2 components directly instead of building inline modals.

## Key imports

```tsx
// Sheet pickers
import { TokenPickerSheet } from "@/components/ui-v2/send/token-picker-sheet";
import { NetworkPickerSheet } from "@/components/ui-v2/send/network-picker-sheet";

// Display components
import { TokenIcon } from "@/components/ui-v2/send/token-icon";
import { LabeledPickerTrigger } from "@/features/bridge-ibc/ui/labeled-picker-trigger";

// Data + helpers
import { useSendTokenData } from "@/hooks/send-v2/use-send-token-data";
import type { SendTokenGroup } from "@/hooks/send-v2/use-send-token-data";
import type { ViewToken } from "@/pages/main";

// Standalone helper imports
import {
  getViewTokenChainId,
  getViewTokenChainName,
  getViewTokenChainImageUrl,
} from "@/hooks/send-v2/use-send-token-data";

// Bridge page alternative: useIBCBridgeTokens instead of useSendTokenData
// Use when the page is bridge-v2 (supports both IBC and EVM Bridge transfer types)
import {
  BridgeOrIBCTransferType,
  TokenSummary,
  useIBCBridgeTokens,
} from "@/features/bridge-ibc/hooks/use-ibc-bridge-tokens";
import { BridgeNetworkPickerSheet } from "@/features/bridge-ibc/ui/bridge-network-picker-sheet";
import { getBridgeNetworkConfig } from "@/constants/bridge-networks";
import { useAiozBridge } from "@/hooks";
```

## TokenPickerSheet

**Props**: `open`, `tokenList: SendTokenGroup[]`, `current: SendTokenGroup | null`, `onConfirm: (token: SendTokenGroup) => void`, `onClose`

```tsx
const { tokenList } = useSendTokenData();
const [selectedTokenData, setSelectedTokenData] =
  useState<SendTokenGroup | null>(null);

<TokenPickerSheet
  open={modals.token}
  tokenList={tokenList}
  current={selectedTokenData}
  onConfirm={(token) => {
    setSelectedTokenData(token);
    // Auto-default first network
    const firstVariant = token.variants[0];
    if (firstVariant) {
      setFromNetworkData(firstVariant);
      form.setValue("fromNetwork", firstVariant.chainInfo.chainId);
    }
    setModals((prev) => ({ ...prev, token: false }));
  }}
  onClose={() => setModals((prev) => ({ ...prev, token: false }))}
/>
```

## NetworkPickerSheet (unified, shared)

Single component at `@/widgets/network-picker-sheet/network-picker-sheet.tsx`, re-exported from both `@/components/ui-v2/send/network-picker-sheet` and `@/components/ui-v2/bridge/network-picker-sheet`. Both send and bridge pages import the same widget.

**Props**: `open`, `current: Partial&lt;ViewToken&gt; | null`, `networks: Partial&lt;ViewToken&gt;[]`, `onConfirm: (network: Partial&lt;ViewToken&gt;) => void`, `onClose`, `showBalance?: boolean`

### No `tokenSymbol` prop

`tokenSymbol` is derived internally via `useMemo` from `current?.token ?? networks[0]?.token`, creating `new CoinPretty(token.currency, new Dec(0)).hideAmount(true).hideIBCMetadata(true).toString()`. All callers removed the prop.

### Balance via `formatBalance` helper

Pure function in `@/features/bridge-ibc/lib/utils.ts` — takes `CoinPretty` directly (not `Partial&lt;ViewToken&gt;`) + optional `chainId` for ERC20/BEP20 distinction. Widget calls it per row:

```tsx
const bal = showBalance && viewToken.token
  ? formatBalance(viewToken.token, viewToken.chainInfo?.chainId)
  : "";
```

See `references/network-picker-balance-formats.md` for the helper implementation details and token type classification (native, ibc/, cw20, erc20, bep20).

```tsx
const { getNetworksForToken } = useSendTokenData();
const [fromNetworkData, setFromNetworkData] = useState<ViewToken | null>(null);

<NetworkPickerSheet
  open={modals.fromNetwork}
  tokenSymbol={selectedToken}
  current={fromNetworkData}
  networks={
    selectedTokenData
      ? getNetworksForToken(selectedTokenData)
      : []
  }
  onConfirm={(network) => {
    setFromNetworkData(network);
    form.setValue("fromNetwork", getViewTokenChainId(network));
    setModals((prev) => ({ ...prev, fromNetwork: false }));
  }}
  onClose={() => setModals((prev) => ({ ...prev, fromNetwork: false }))}
/>
```

## LabeledPickerTrigger as trigger

Use `LabeledPickerTrigger` with `icon` and `value` for both token and network fields.

**Token trigger** (use `TokenIcon`):

```tsx
<LabeledPickerTrigger
  label="Token"
  placeholder="Choose your token"
  value={selectedTokenData?.symbol ?? ""}
  onClick={() => openModal("token")}
  icon={
    selectedTokenData ? (
      <TokenIcon
        symbol={selectedTokenData.symbol}
        size={40}
        imageUrl={selectedTokenData.imageUrl}
      />
    ) : undefined
  }
/>
```

**Network trigger** (inline image circle):

```tsx
<LabeledPickerTrigger
  label="From"
  placeholder={selectedTokenData ? "Select network" : "Select token first"}
  value={fromNetworkName}
  onClick={() => openModal("fromNetwork")}
  disabled={!selectedTokenData}
  icon={
    fromNetworkData ? (
      <View
        width={40} height={40} borderRadius={20}
        flexShrink={0} overflow="hidden"
        backgroundColor="rgba(255,255,255,0.05)"
        alignItems="center" justifyContent="center"
        borderWidth={1} borderColor="rgba(255,255,255,0.10)"
      >
        {fromNetworkImageUrl ? (
          <img src={fromNetworkImageUrl} alt={fromNetworkName}
               width={40} height={40} style={{ display: "block" }} />
        ) : (
          <View width={10} height={10} borderRadius={5}
                backgroundColor="rgba(255,255,255,0.20)" />
        )}
      </View>
    ) : undefined
  }
/>
```

## State management pattern

Keep **two independent states** for the selection flow:

| State | Type | Description |
|-------|------|-------------|
| `selectedTokenData` | `SendTokenGroup \| null` | Grouped token (symbol + balance + variants) |
| `fromNetworkData` | `ViewToken \| null` | Specific network variant for selected token |

Connection: token confirm auto-sets `fromNetworkData` to its first variant. Network confirm just updates `fromNetworkData`.

## AmountField integration

For quick mock wiring, this works:

```tsx
<Controller
  name="amount"
  render={({ field }) => (
    <AmountField
      amount={String(field.value ?? "")}
      onAmountChange={field.onChange}
      onMax={() => undefined}
      tokenSymbol={selectedTokenData?.symbol ?? ""}
      conversionLabel="≈ $0.00"
      isInsufficient={false}
      networkConfirmed={Boolean(selectedTokenData)}
    />
  )}
/>
```

For `bridge-v2`, prefer real hook wiring via `useBridgeAmount` once the page owns `BridgeV2FormValues`:

```tsx
const networkConfirmed = Boolean(selectedToken && selectedFromChainId);

const {
  amount,
  chainCurrency,
  conversionLabel,
  isInsufficient,
  handleAmountChange,
  handleMaxClick,
} = useBridgeAmount({
  form,
  fromNetworkToken: fromNetworkData?.token,
  networkConfirmed,
});

<Controller
  name="amount"
  render={() => (
    <AmountField
      amount={amount}
      onAmountChange={handleAmountChange}
      onMax={handleMaxClick}
      tokenSymbol={token?.symbol}
      chainCurrency={chainCurrency}
      conversionLabel={conversionLabel}
      isInsufficient={isInsufficient}
      networkConfirmed={networkConfirmed}
    />
  )}
/>
```

Important:
- `BridgeV2FormValues.amount` should be `string`, not `number`.
- `useForm` default for `amount` should be `""`, not `0`.
- Gate editing with `networkConfirmed = Boolean(selectedToken && selectedFromChainId)`, not token-only.

## useIBCBridgeTokens hook (bridge-v2 page)

For the `bridge-v2` page, use `useIBCBridgeTokens` instead of `useSendTokenData`. It returns tokens grouped by denomination with a `transferType` field distinguishing IBC vs EVM Bridge.

```tsx
import {
  BridgeOrIBCTransferType,
  TokenSummary,
  useIBCBridgeTokens,
} from "@/features/bridge-ibc/hooks/use-ibc-bridge-tokens";

const { bridgeIbcTokens, getNetworksForToken } = useIBCBridgeTokens();
```

`TokenSummary` extends `SendTokenGroup` adding `transferType: "bridge" | "ibc"`. Conditionally render different "To" fields based on type.

## BridgeNetworkPickerSheet (BRIDGE "To" field)

For EVM Bridge transfers, the "To" field is a network picker (not an address book). Use `BridgeNetworkPickerSheet` + `getAvailableToNetworks` from `useAiozBridge`.

```tsx
import { useAiozBridge } from "@/hooks";
import { BridgeNetworkPickerSheet } from "@/features/bridge-ibc/ui/bridge-network-picker-sheet";
import { getBridgeNetworkConfig } from "@/constants/bridge-networks";

const { getAvailableFromNetworks, getAvailableToNetworks } = useAiozBridge();
const [toNetworkData, setToNetworkData] = useState<string | null>(null);

// Separate modal key from IBC's ContactPickerSheet to avoid conflicts
const [modals, setModals] = useState({
  token: false,
  fromNetwork: false,
  toNetwork: false,
  toNetworkBridge: false,
});
```

Render the BRIDGE "To" field conditionally:

```tsx
{selectedTokenData?.transferType === BridgeOrIBCTransferType.BRIDGE && (
  <LabeledPickerTrigger
    label="To"
    placeholder={fromNetworkData ? "Select destination" : "Select network first"}
    uppercaseLabel
    value={toNetworkData
      ? getBridgeNetworkConfig(toNetworkData)?.displayName ?? toNetworkData
      : undefined}
    onClick={() => openModal("toNetworkBridge")}
    disabled={!fromNetworkData}
    icon={toNetworkData ? (
      <View width={40} height={40} borderRadius={20} flexShrink={0}
            overflow="hidden" backgroundColor="rgba(255,255,255,0.05)"
            alignItems="center" justifyContent="center"
            borderWidth={1} borderColor="rgba(255,255,255,0.10)">
        {(() => {
          const cfg = getBridgeNetworkConfig(toNetworkData);
          return cfg?.logoUrl ? (
            <img src={cfg.logoUrl} alt={cfg.displayName}
                 width={40} height={40} style={{ display: "block" }} />
          ) : (
            <View width={10} height={10} borderRadius={5}
                  backgroundColor="rgba(255,255,255,0.20)" />
          );
        })()}
      </View>
    ) : undefined}
  />
)}
```

Wire the picker sheet:

```tsx
<BridgeNetworkPickerSheet
  open={modals.toNetworkBridge}
  current={toNetworkData}
  networks={fromNetworkData
    ? getAvailableToNetworks(getViewTokenChainId(fromNetworkData)) ?? []
    : []}
  onConfirm={(networkId) => {
    setToNetworkData(networkId);
    form.setValue("toNetwork", networkId);
    setModals((prev) => ({ ...prev, toNetworkBridge: false }));
  }}
  onClose={() => setModals((prev) => ({ ...prev, toNetworkBridge: false }))}
/>
```

### BridgeNetworkPickerSheet props

| Prop | Type | Description |
|------|------|-------------|
| `open` | `boolean` | Sheet visibility |
| `current` | `string \| null` | Currently selected network ID (e.g. "ETH", "BSC") |
| `networks` | `string[]` | Available bridge network IDs (from `getAvailableToNetworks`) |
| `onConfirm` | `(networkId: string) => void` | Called when user selects a network |
| `onClose` | `() => void` | Called when sheet closes |

The component resolves display info (name, logo) internally via `getBridgeNetworkConfig`.

### IBC vs BRIDGE "To" — which components

| Transfer type | "To" component | Data source | Modal key |
|---|---|---|---|
| `IBC` | `ContactPickerSheet` | `useSendAddresses({ chainId, isIBCTransfer: true })` | `toNetwork` |
| `BRIDGE` | `BridgeNetworkPickerSheet` | `getAvailableToNetworks(fromChainId)` | `toNetworkBridge` |

Use separate modal keys (`toNetwork` vs `toNetworkBridge`) so both sheets coexist without race conditions.

## Memo field on bridge-v2 / non-send pages

When a non-send page already uses `useSendIbc` or another tx-config hook that exposes `sendConfigs.memoConfig`, reuse that config directly for memo UI. Do **not** add parallel local memo state.

### Preferred pattern

- add `memo` to page form values and default values so form shape stays aligned with the rest of the flow
- render memo with same visibility gate as recipient when the user explicitly wants matching behavior
- wire the input to `sendConfigs.memoConfig`, not `react-hook-form` field state, because tx config already owns validation + query-string restoration

```tsx
import { BridgeMemoField } from "@/components/ui-v2/send/bridge-memo-field";

const {
  sendConfigs,
  state: sendIbcState,
  actions: sendIbcActions,
} = useSendIbc(...);

{!isBridgeNetwork && selectedToChainId && (
  <RecipientField ... />
)}

{!isBridgeNetwork && selectedToChainId && (
  <BridgeMemoField memoConfig={sendConfigs.memoConfig} />
)}
```

### Why

`useSendIbc` already restores and validates memo through `sendConfigs.memoConfig` and `useTxConfigsQueryString`. Reusing that path avoids duplicated state and keeps memo behavior consistent with send flows.

## ContactPickerSheet (address / "To" field)

**Props**: `open`, `addresses: SendAddressItem[]`, `onSelect: (address: string) => void`, `onClose`

```tsx
import { ContactPickerSheet } from "@/components/ui-v2/send/contact-picker-sheet";
import { useSendAddresses } from "@/hooks/send-v2/use-send-addresses";

const [toAddress, setToAddress] = useState("");
const addresses = useSendAddresses({
  chainId: fromNetworkData ? getViewTokenChainId(fromNetworkData) : undefined,
  isIBCTransfer: true,
});

<LabeledPickerTrigger
  label="To"
  placeholder={fromNetworkData ? "Select recipient" : "Select network first"}
  value={toAddress}
  onClick={() => openModal("toNetwork")}
  disabled={!fromNetworkData}
/>

<ContactPickerSheet
  open={modals.toNetwork}
  addresses={addresses}
  onSelect={(address) => {
    setToAddress(address);
    form.setValue("toNetwork", address);
    setModals((prev) => ({ ...prev, toNetwork: false }));
  }}
  onClose={() => setModals((prev) => ({ ...prev, toNetwork: false }))}
/>
```

`useSendAddresses` needs a `chainId` (from the selected source network) and optionally `isIBCTransfer`. It merges saved addresses + other vault addresses, deduplicating by address string.

## Search inside shared picker sheets

When `bridge-v2` needs search in token/network sheets, **do not patch `pages/bridge-v2/index.tsx` first**. That page already consumes shared picker components:

- `@/components/ui-v2/bridge/token-picker-sheet`
- `@/features/bridge-ibc/ui/bridge-view-network-picker-sheet`
- `@/widgets/network-picker-sheet/network-picker-sheet`

So search belongs in the shared picker components. Page wiring usually stays unchanged.

### Implementation pattern

Reuse existing search UI + helper instead of ad-hoc filter code:

```tsx
import { performSearch } from "@/hooks/use-search";
import { Search, X } from "lucide-react";
import { Input, XStack, View } from "tamagui";
import { useMemo, useState } from "react";
```

Use the same inline search row pattern already present in `send/contact-picker-sheet.tsx`:

```tsx
const [query, setQuery] = useState("");

const filtered = useMemo(
  () => performSearch(items, query, fields),
  [items, query]
);
```

Token picker search fields:

- token `symbol`
- `variants[].chainInfo.chainName`
- `variants[].chainInfo.chainId`

Network picker search fields:

- `chainInfo.chainName`
- `chainInfo.chainId`

Recommended empty states:

- base list empty: `No tokens available` / `No networks available`
- search miss: `No tokens found` / `No networks found`

### Bridge-v2 consequence

Because `bridge-v2/index.tsx` already uses the shared bridge/send picker components, adding search at component level automatically enables it for:

- source token picker
- source network picker
- destination network picker

No extra prop plumbing needed unless the page wants custom placeholder text or custom search fields.

## Empty state handling

Both picker sheets handle empty arrays internally:

- **NetworkPickerSheet**: Renders "No networks available" centered text when `networks.length === 0`. No need to guard externally.
- **TokenPickerSheet**: Renders nothing special — empty list shows blank scroll area. Zero-balance tokens appear at `opacity: 0.4`, unclickable (see below).
- **ContactPickerSheet**: Has its own empty messages ("No saved addresses yet" / "No addresses found") based on whether the source address list was empty or just filtered to zero.

## Disabled zero-balance tokens in TokenPickerSheet

Tokens with `balance <= 0` are **shown but disabled** — they appear in the list at reduced opacity and cannot be selected:

```tsx
const isZeroBalance = token.balance <= 0;

<XStack
  opacity={isZeroBalance ? 0.4 : 1}
  cursor={isZeroBalance ? "default" : "pointer"}
  pressStyle={isZeroBalance ? {} : { backgroundColor: "rgba(255,255,255,0.04)" }}
  onPress={isZeroBalance ? undefined : () => handleSelect(token)}
>
```

Do NOT filter zero-balance tokens out before passing to `TokenPickerSheet` — the component handles visibility and disabled state itself.

## Code organization: extract pure functions from hooks

When a hook's `useMemo` grows beyond 20 lines (summing balances, formatting labels, filtering) the logic becomes hard to test and read. Extract **pure functions** outside the component — they're trivially testable without React and make the hook a thin wiring layer.

### Pattern from `useIBCBridgeTokens`

```ts
// ❌ Before: all logic inlined in useMemo
const ibcTokens = useMemo(() => {
  const zeroDec = new Dec(0);
  return Array.from(balancesGroupByToken.values())
    .map((tokens) => {
      const token = tokens[0].token;
      const totalDec = tokens.reduce(...);
      const totalCoinPretty = new CoinPretty(token.currency, totalDec);
      return { token, totalDec, totalLabel: totalCoinPretty.maxDecimals(6)... };
    })
    .filter((s) => s.totalDec.gt(zeroDec));
}, [balancesGroupByToken]);

// ✅ After: pure functions outside, hook is just wiring
function sumTokenBalances(tokens: ViewToken[]): Dec { ... }
function formatTokenLabel(dec: Dec, denom: string, maxDec = 6): string { ... }
function summarizeTokenGroup(tokens: ViewToken[]): TokenSummary { ... }
function summarizeNonEmptyTokenGroups(groups: Map<string, ViewToken[]>): TokenSummary[] { ... }

const ibcTokens = useMemo(
  () => summarizeNonEmptyTokenGroups(balancesGroupByToken),
  [balancesGroupByToken]
);
```

### Naming convention

| Function | Input → Output | When |
|---|---|---|
| `sum*` | Raw data → aggregate value | Combining multiple items |
| `format*` | Value → display string | Label construction |
| `summarize*` | Group → structured result | Wrapping data for UI |
| `filter*` | Array → filtered array | Selection logic |

### Benefits

- **Testable**: call the pure fn with mock data, assert on return value — no `renderHook`, no store mocking
- **Reusable**: `formatTokenLabel` can be used in hooks, components, and tests
- **Readable**: `summarizeNonEmptyTokenGroups` reads as a sentence, not a nested pipeline
- **Type-safe**: explicit interface for inputs/outputs surfaces mismatches at compile time

## RecipientInput + RecipientModal (address book for non-bridge networks)

When a page needs recipient selection (IBC transfers, non-bridge destinations), use `RecipientInput` for field UI and prefer a shared `ContactPickerSheet`-style picker for address-book selection. In `bridge-v2`, wire the picker from `@/widgets/contact-picker-sheet` instead of embedding `RecipientModal` inline.

```tsx
import { RecipientInput } from "@/components/send/recipient-input";
import { RecipientModal } from "@/components/send/recipient-modal";
import { BottomModal } from "@/components/bottom-modal";
import { useRecipientConfig } from "@keplr-wallet/hooks";
import { useStore } from "@/stores";
import { getNetworkIdFromChainId } from "@/constants/bridge-networks";
```

**Pattern**: Conditionally render the recipient field when the destination network is **not** a bridge network:

```tsx
const { chainStore } = useStore();

// Check if destination is a bridge network (AIOZ, ETH, BSC)
const isBridgeNetwork = (() => {
  if (!selectedToChainId) return false;
  const networkId = getNetworkIdFromChainId(selectedToChainId);
  return !!networkId;
})();

const recipientConfig = useRecipientConfig(
  chainStore,
  selectedToChainId || "",
  {
    allowHexAddressOnly: false,
    allowHexAddressToBech32Address: false,
  }
);

const [modals, setModals] = useState({
  token: false,
  fromNetwork: false,
  toNetwork: false,
  recipient: false,
});
```

**Render recipient field conditionally**:

```tsx
{!isBridgeNetwork && selectedToChainId && (
  <Controller
    name="recipient"
    render={() => (
      <RecipientInput
        recipientConfig={recipientConfig}
        onOpenAddressBook={() => openModal("recipient")}
        showAddressBookButton={true}
        chainId={selectedToChainId}
      />
    )}
  />
)}
```

**Preferred wiring in `bridge-v2`**:

```tsx
import { useSendAddresses } from "@/hooks/send-v2/use-send-addresses";
import { ContactPickerSheet } from "@/widgets/contact-picker-sheet";

const recipientAddresses = useSendAddresses({
  chainId: selectedToChainId || undefined,
  isIBCTransfer: true,
});

<ContactPickerSheet
  open={modals.recipient}
  addresses={recipientAddresses}
  onSelect={(address) => {
    recipientConfig.setValue(address);
    form.setValue("recipient", address);
    setModals((prev) => ({ ...prev, recipient: false }));
  }}
  onClose={() => setModals((prev) => ({ ...prev, recipient: false }))}
/>
```

Use `RecipientInput` for input field + open-address-book affordance, but use shared `ContactPickerSheet` for actual saved-address / my-accounts selection when page already follows ui-v2 sheet patterns. Keep `RecipientModal` as fallback only when you need its manual-entry tabs inside modal.

## Pitfalls
- When extracting a UI control from one flow into `widgets/` and reusing it in another page, move only presentation into widget first. Keep state/behavior in existing page or feature hooks.
- If target page already has a domain hook exposing `sendConfigs`, actions, and validation state, reuse that hook for widget wiring. Do **not** pull in parallel send-model setup hooks (`useGasSimulatorSetup`, `useFeeSetup`, `useBalanceSetup`, extra send effects) from a different flow unless the target truly lacks that state. This avoids duplicate fee/gas plumbing and type drift.
- For fee pickers specifically: compute display data from existing `sendConfigs.feeConfig`, persist tier changes through existing UI config store hooks, and place widget directly after amount field so source and target layouts stay aligned.


- **When the user says "in this file, not that file"**, stop immediately and work in the correct file. Do NOT continue work in the wrong file just because you've already started. Re-read the target file and implement there. This avoids wasted work and user frustration.
- When the user asks for a **narrow UI follow-up** like "add submit button from send-v2 into bridge-v2", scope tightly: port visual/layout/disabled-state pattern first, verify build, and do not invent a new submit flow or wire fake behavior unless the target action path is already present or explicitly requested.
- When the user says **"Verify"** after a UI-v2 integration change, treat that as verification-only mode: run the smallest relevant command-backed check, inspect diff if useful, and reply with terse evidence instead of more implementation chatter.
- When adding memo to a page already backed by `useSendIbc`, reuse `sendConfigs.memoConfig` and align visibility with the existing recipient gate unless the user explicitly asks for stricter recipient-value-based visibility.
- In `useSendIbc`-backed bridge/send flows, keep form state as source of truth and sync into `sendConfigs` with `useEffect` (`amount`, `recipient`, `memo`). If an event handler updates form-owned fields, set both immediately in the handler for responsive UI, then let the effect preserve one-way form -> `sendConfigs` sync for restore/programmatic updates. Avoid split ownership where some fields live only in `sendConfigs` and others only in form state.
- For `bridge-v2` recipient picking, prefer shared sheet clone under `src/widgets/contact-picker-sheet.tsx` over inline `BottomModal` + `RecipientModal` once the shared sheet exists. Use shared ui-v2 sheet patterns instead of bespoke modal content.
- `TokenPickerSheet` expects `SendTokenGroup[]` from `useSendTokenData()`, not raw `ViewToken[]` or flat arrays.
- `TokenPickerSheet` shows zero-balance tokens at `opacity: 0.4` with no `onPress` — they are visible but unselectable. Do NOT pre-filter.
- `NetworkPickerSheet` expects `ViewToken[]` derived via `getNetworksForToken(token)`.
- If a page has a "swap networks" / reverse-direction button, disable it unless the current destination chain exists in the source-side token variants **and** that destination variant has `token.toDec().gt(new Dec(0))`. In bridge-v2, source-side variants come from `availableNetworks`; check the selected `to` chain against that array, not just `from !== to`.
- `NetworkPickerSheet` renders "No networks available" centered text when `networks` is empty — let the component handle empty state.
- `ContactPickerSheet` expects `SendAddressItem[]` from `useSendAddresses()` hook, needs `chainId` to resolve addresses.
- Auto-default the network after token selection so the from field is never empty when a token is chosen.
- Use `disabled` on the From trigger when no token is selected to avoid opening an empty sheet.
- Use `disabled` on the To trigger when no network is selected — address book is meaningless without a source chain.
- Use `getViewTokenChainId` (not bare `chainId` access) — it handles chain info type variance.
- If `LabeledPickerTrigger` lacks a `disabled` prop, add it: cursor becomes `default`, onClick drops.
- **Stale pending state in picker sheets**: Both `TokenPickerSheet` and `NetworkPickerSheet` use `useState` initialized from the `current` prop. If the parent re-renders with a new `current` value (e.g., user switches to a different token via another route), the `pending` state is stale because `useState` only reads the initial value. Fix: add a `useRef` tracker + render-time sync:

  ```tsx
  import { useRef, useState } from "react";

  const [pending, setPending] = useState<ViewToken | null>(current);

  const pendingCurrent = useRef(current);

  if (pendingCurrent.current !== current) {
    pendingCurrent.current = pending;

    setPending(current);
  }
  ```

  This forces `pending` to align with the latest `current` prop on the next render after the prop changes, while still allowing local selection changes within the sheet. Apply this to every picker sheet component that tracks a `pending` selection state.

## Token amount formatting

See `references/coin-pretty-token-formatting.md` for how `CoinPretty` works internally, the correct formatting chain (`maxDecimals` / `trim` / `shrink`), and the common `coinDecimals` vs `10^coinDecimals` multiplier pitfall when summing balances across chains.
