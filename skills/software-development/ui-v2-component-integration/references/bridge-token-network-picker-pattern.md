# Bridge page: Token + Network picker integration

Consolidated pattern from three sessions (2026-06-24 – 2026-06-25) replacing `BottomSheet` + `SearchToken` with `TokenPickerSheet`, `NetworkPickerSheet`, `ContactPickerSheet`, and `BridgeNetworkPickerSheet` in `apps/extension/src/pages/bridge-v2/index.tsx`.

## Session 1: Token + Network picker

1. **Imports**: Removed `BottomSheet` and `SearchToken`. Added `TokenPickerSheet`, `NetworkPickerSheet`, `TokenIcon`, `useSendTokenData`, `getViewTokenChainId/Name/ImageUrl`, `ViewToken`, `View` (tamagui).

2. **State**: Changed from `form.watch("token")` string to `selectedTokenData: SendTokenGroup | null` + `fromNetworkData: ViewToken | null`.

3. **TokenPickerSheet** replaces old `BottomSheet > Controller > SearchToken`. `onConfirm` receives `SendTokenGroup`, sets both states and defaults `fromNetworkData` from first variant.

4. **NetworkPickerSheet** wired with `getNetworksForToken(selectedTokenData)`.

5. **LabeledPickerTrigger** got a `disabled` prop — used for From field.

## Session 2: Contact picker + empty/disabled states

### ContactPickerSheet for "To" field

Added `ContactPickerSheet` as the "To" address picker. Pattern:

- Import `ContactPickerSheet` + `useSendAddresses` + `SendAddressItem` type
- Add `toAddress` string state
- Call `useSendAddresses({ chainId: …, isIBCTransfer: true })` — chainId from `fromNetworkData`
- Update "To" `LabeledPickerTrigger`: show `toAddress` as `value`, `disabled` until network is selected, conditional placeholder
- Wire `<ContactPickerSheet>` to `modals.toNetwork`, `onSelect` sets `toAddress` + `form.setValue("toNetwork", address)`

### Empty state: NetworkPickerSheet

When `networks` array is empty, the sheet previously rendered a blank scroll area. Added:

```tsx
{networks.length === 0 ? (
  <View paddingVertical="$8" alignItems="center">
    <Text variant="bodySm" color="$color8">No networks available</Text>
  </View>
) : (
  networks.map(...)
)}
```

### Disabled zero-balance tokens: TokenPickerSheet

Tokens with `balance <= 0` are now shown at `opacity: 0.4` and cannot be selected:

```tsx
const isZeroBalance = token.balance <= 0;
opacity={isZeroBalance ? 0.4 : 1}
cursor={isZeroBalance ? "default" : "pointer"}
pressStyle={isZeroBalance ? {} : { backgroundColor: "rgba(255,255,255,0.04)" }}
onPress={isZeroBalance ? undefined : () => handleSelect(token)}
```

### Pitfalls encountered

- **Prettier inline ternary rule**: Multi-line ternaries must be split across lines — single-line ternary inside JSX props triggers `prettier --check` failure. Always format as `prop={condition ? (truthy) : (falsy)}` if the expression spans multiple lines.
- **Indentation cascade**: Wrapping `networks.map(...)` in a ternary adds +2 indent for everything inside the arrow body. Each nesting level in JSX is 2 spaces. Failing to cascade leads to syntax errors when prettier re-indents.
- **Stale pending state fix**: Both `TokenPickerSheet` and `NetworkPickerSheet` had the "old state problem" — opening the sheet a second time with a different `current` prop showed the old selection because `useState(pending)` only reads the initial value once. Fix is the `useRef` + render-time sync pattern:

  ```tsx
  const pendingCurrent = useRef(current);

  if (pendingCurrent.current !== current) {
    pendingCurrent.current = pending;
    setPending(current);
  }
  ```

  Place this right after the `useState` declarations. Applies to any component with a `pending` state initialized from a changing `current` prop.
- **ContactPickerSheet's `onSelect`** returns only the address string, not the full `SendAddressItem` — store it directly.

## Session 3: BRIDGE type "To" network picker

The bridge-v2 page supports two transfer types via `useIBCBridgeTokens`:
- **IBC**: "To" field picks a recipient address (ContactPickerSheet)
- **BRIDGE**: "To" field picks a destination EVM network (new BridgeNetworkPickerSheet)

### Why BridgeNetworkPickerSheet is separate from NetworkPickerSheet

- `NetworkPickerSheet` (for IBC) consumes `ViewToken[]` — token balances per chain
- `BridgeNetworkPickerSheet` consumes `string[]` — bridge network IDs ("ETH", "BSC", "AIOZ")
- Bridge network display info (logo, name) is resolved via `getBridgeNetworkConfig(networkId)`
- Available destinations come from `getAvailableToNetworks(fromChainId)` (a `useAiozBridge` hook method)

### Modal key separation

Both "To" pickers share the same `LabeledPickerTrigger` UI but use **different modal keys** to avoid race conditions:

```tsx
const [modals, setModals] = useState({
  token: false,
  fromNetwork: false,
  toNetwork: false,      // IBC: ContactPickerSheet
  toNetworkBridge: false, // BRIDGE: BridgeNetworkPickerSheet
});
```

### Updated imports for bridge page

```tsx
import { TokenPickerSheet } from "@/components/ui-v2/send/token-picker-sheet";
import { NetworkPickerSheet } from "@/components/ui-v2/bridge/network-picker-sheet";
import { ContactPickerSheet } from "@/components/ui-v2/send/contact-picker-sheet";
import { TokenIcon } from "@/components/ui-v2/send/token-icon";
import { LabeledPickerTrigger } from "@/features/bridge-ibc/ui/labeled-picker-trigger";
import { BridgeNetworkPickerSheet } from "@/features/bridge-ibc/ui/bridge-network-picker-sheet";
import { getBridgeNetworkConfig } from "@/constants/bridge-networks";
import {
  BridgeOrIBCTransferType,
  TokenSummary,
  useIBCBridgeTokens,
} from "@/features/bridge-ibc/hooks/use-ibc-bridge-tokens";
import { useAiozBridge } from "@/hooks";
import { useSendAddresses } from "@/hooks/send-v2/use-send-addresses";
import type { SendTokenGroup } from "@/hooks/send-v2/use-send-token-data";
import {
  useSendTokenData,
  getViewTokenChainId,
  getViewTokenChainName,
  getViewTokenChainImageUrl,
} from "@/hooks/send-v2/use-send-token-data";
import type { ViewToken } from "@/pages/main";
```

### Key module graph (v2)

```
useIBCBridgeTokens()
  ├── bridgeIbcTokens: TokenSummary[]              → TokenPickerSheet
  │     where TokenSummary extends SendTokenGroup
  │       with transferType: "bridge" | "ibc"
  ├── getNetworksForToken(token) → ViewToken[]     → NetworkPickerSheet
  └── ibcTokens, brideTokens (separate arrays)

useAiozBridge()
  ├── getAvailableFromNetworks() → string[]        (source chains)
  ├── getAvailableToNetworks(fromChainId) → string[] → BridgeNetworkPickerSheet
  ├── getDirection(fromNetwork, toNetwork, asset)
  ├── getEstimateFee(swapType)
  └── getResult(txHash)

getBridgeNetworkConfig(networkId) → { displayName, logoUrl, shortName, chainInfo }
  Used by BridgeNetworkPickerSheet to render network rows

useSendAddresses({ chainId, isIBCTransfer })
  └── addresses: SendAddressItem[]                 → ContactPickerSheet
```
