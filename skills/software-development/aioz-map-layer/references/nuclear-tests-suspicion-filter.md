# Nuclear tests suspicion filter — reference

Session takeaway for `nuclear_tests` map-layer filter.

## Generated evidence checked

- `src/__generated__/api/types.gen.ts` exposes `GetNuclearTestData['query'].suspicion_level` as `string`
- `src/__generated__/api/zod.gen.ts` exposes `zGetNuclearTestQuery.shape.suspicion_level` as `z.string().optional()`
- Generated files did **not** provide a real enum/union to import

## User/domain correction

Do not assume values from DTO comment examples alone.

For current product/domain usage, narrowed filter values are:
- `None`
- `High`

These values came from user correction plus existing repo display logic (`TestSitesList` already treats `high` as the special case and everything else as non-high).

## Implementation rule

When generated API only says `string`:
1. Check generated comments for hints
2. Check current repo usage for real observed values
3. Prefer user/domain correction over speculative extra values
4. Keep narrowed values local to the filter implementation unless backend later publishes a real enum

## Follow-up trigger

If backend/OpenAPI upgrades `suspicion_level` to a real enum, replace local literal options with generated enum/union-derived values and remove this narrowing note.
