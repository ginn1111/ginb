# Cross-Package React Ref Type Mismatch

## Symptom

TS2322 in webpack build:

```
Type '{ ref?: Ref<HTMLDivElement> | undefined; ... }' is not assignable to type 'DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>'.
  Types of property 'ref' are incompatible.
    Type 'React.Ref<HTMLDivElement> | undefined' is not assignable to type 'import("/path/to/node_modules/.../@types/react/index").Ref<HTMLDivElement> | undefined'.
```

Includes recursive `Type 'VoidOrUndefinedOnly' is not assignable to type 'VoidOrUndefinedOnly'` chain.

## Root Cause

Two copies of `@types/react` exist at different pnpm/node_modules paths. TypeScript treats them as unrelated types even though structurally identical. When a component accepts `ref` via `React.ComponentProps` or `forwardRef`, the caller's `React.Ref` and the callee's `React.Ref` come from different `@types/react` installs.

## Common Trigger

A UI package (`packages/aioz-ui`) pulls `@types/react@19.x` via its own dep, while the consuming app pulls a different copy. When a UI component declares props as `React.ComponentProps<'div'>` (which includes `ref`) or uses `forwardRef`, TypeScript can fail at the app build step even though the UI package builds cleanly in isolation.

## Quick Fix

Narrow props types that don't need `ref`:

```tsx
// Before — includes ref, triggers cross-package mismatch
function AvatarGroup({ className, ...props }: React.ComponentProps<'div'>) {

// After — excludes ref, no mismatch
function AvatarGroup({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
```

Same pattern for `React.ComponentProps<'span'>` → `React.HTMLAttributes<HTMLSpanElement>`.

## When to Use

When:
- UI component in a shared `core-v3`/`shadcn` package that doesn't need `ref`
- Only a subset of components in the file trigger the error (not every `div`)
- The file has other components already using `React.HTMLAttributes` that pass clean

When NOT to use:
- Component genuinely needs `ref` for focus management, measurement, or imperatively controlling a third-party library
- Component is `forwardRef`-wrapped — the mismatch is harder to fix (needs de-duping `@types/react` at pnpm level)

## Alternative Fixes

If narrowing props won't work:

1. Deduplicate `@types/react` with pnpm overrides in root `package.json`:
```json
"pnpm": {
  "overrides": {
    "@types/react": "19.2.13"
  }
}
```

2. Hoist the shared copy via pnpm config.

3. Use `skipLibCheck: true` in `tsconfig.json` — masks the problem but hides future real type errors too.

## Real Case

`/packages/aioz-ui/packages/core-v3/src/components/ui/avatar.tsx` — `AvatarGroupCount` and `AvatarGroup` at lines 381/394. Both were `React.ComponentProps<'div'>`. Neither uses `ref`. Narrowed to `React.HTMLAttributes<HTMLDivElement>`. Build went green immediately.