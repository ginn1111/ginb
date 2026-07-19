---
name: map-layer-migration
description: "Rename or add map layers in AIOZ World Deck. Ordered 16-step migration from store constants through doc updates."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Map Layer Migration — AIOZ World Deck

Rename or add a map layer across the full stack. Order matters — each step enables the next.

**Use when:** adding a new map layer or renaming an existing one (e.g. `emerg_squawks` → `military_tracker`).

---

## 16-Step Migration Order

```
Step   Layer                    What changes
─────────────────────────────────────────────────────
  1    Store constants          Add defaults/type list to `src/store/map-layer/constants.ts`
  2    Layer key config         Update `src/constants/mapLayers.ts` + `mapLayerConfig.ts`
  3    Store state              Update `map-layer/index.ts` (layerQuery) + `map/index.ts` (INTERACTIVE_LAYER_IDS)
  4    Icon                     Rename/add in `src/assets/icons/LayerIcons.ts`
  5    Sprite registration      Update `src/hooks/useMapImageLoader.ts` (import + LAYER_SPRITES entry)
  6    Hook (new)               Create geo JSON hook (e.g. `useMilitaryTrackerGeoJson.ts`)
  7    Component (new)          Create layer component (e.g. `MilitaryTrackerLayer.tsx`)
  8    Registry                 Update `src/store/map-layer-registry.ts` (import + LAYER_COMPONENT_MAP)
  9    Selectors                Update `src/store/map-layer/selector.ts` (activeLayers interactive IDs)
 10    Feature layouts          Update `src/features/layout-manager/model/defaultMapLayers.ts`
 11    Default state            Update `src/hooks/query/useMapLayers.ts`
 12    Layer counts             Update `src/hooks/query/useLayerCounts.ts`
 13    Builders                 Add/rename builder in `src/components/widget/MaplibreViewer/builders.ts`
 14    Hook keys                Clean up old entries from `src/hooks/hook-keys.ts`
 15    Type-check               `pnpm type-check` — verify no NEW errors (ignore pre-existing)
 16    Docs                     Update `docs/data/map-layers.md`, `DATA_LAYER_STYLE_GUIDE.md`, `README.md`
```

## Phase 2 — Cleanup (for renames only)

After the new layer is fully wired:

| Task | Action |
|---|---|
| Legacy-type old key | Add old key to `LEGACY_MAP_LAYERS` in `mapLayers.ts` so orphan references still compile |
| Delete dead files | Remove old hook, component, service, mock files |
| Remove registry entry | Remove old lazy import + LAYER_COMPONENT_MAP entry |
| Remove selectors | Remove old `activeLayers.old_key` entries |
| Remove layer counts | Remove old count entry + query call |
| Remove interactive IDs | Remove old sprite-layer and sprite-clusters from `store/map/index.ts` |
| Remove builders | Remove old builder function |
| Remove hook keys | Remove old `get<OldKey>` key |
| Remove mapLayerConfig | Remove old key from mapLayerConfig.ts |
| Remove default state | Remove old key from useMapLayers.ts |
| Remove old feature layout | Remove old key from defaultMapLayers.ts |
| Type-check | `pnpm type-check` — must be clean (only pre-existing unrelated errors) |
| Docs | Update table, policy list, sizing rows; add legacy comment so history is traceable |

## Verification

After every mutation step run:
```bash
pnpm type-check
```

Report success only when no new errors appear. Pre-existing errors in unrelated files (CloudflareRadar, BreakingNews, ElectionDashboard, SpaceIntelligence, etc.) are not your concern.

## Pitfalls

- **`\n` corruption in patch tool:** When using `patch` with multi-line strings, the tool can inject literal `\n` escape sequences instead of real newlines. Always verify patched files with `read_file` after the edit. If corrupted, overwrite the affected section with `write_file`.
- **Fuzzy matching dangers:** The patch tool's fuzzy matching can match adjacent lines that look similar to the old_string, deleting more than intended. After each patch on hook-keys and similar densely-packed files, verify with `git diff HEAD -- <file>` or `read_file`.
- **subagent-driven-development for large tasks:** For new component or hook files (tasks 6-7), delegate to a subagent with full context of the original file. The subagent has no conversation history — pass the original file content and the exact changes needed.
- **type-check noise:** Filter pre-existing errors by grep'ing for your changed files: `pnpm type-check 2>&1 | grep -E '<your-files>'`. The full error dump is overwhelming.
- **LEGACY_MAP_LAYERS is critical.** Without adding the old key here, the entire project gets TS errors because the `MapLayer` union type shrinks and `activeLayers` becomes too narrow for orphan references in the selector/registry. Add it before or simultaneously with removing references.
