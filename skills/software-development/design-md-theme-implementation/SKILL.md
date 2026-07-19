---
name: design-md-theme-implementation
description: Implement or restyle an app UI to match an existing DESIGN.md spec, then verify rendered output against the spec.
---

# Design MD Theme Implementation

Use this when user asks to make app, page, or theme match an existing `DESIGN.md` in repo.

## Why this skill exists

Conversation lesson: freeform landing-page design drifted away from repo design spec. Correct approach was to treat `DESIGN.md` as source of truth for visual system, then map tokens into app globals, typography, component styling, and page composition before claiming done.

## Checklist

1. Find `DESIGN.md` first.
2. Read repo-local instruction files near app (`AGENTS.md`, `CLAUDE.md`) before editing.
3. Identify real app entry path before writing. For Next.js, verify exact `app/page.tsx`, `app/layout.tsx`, `app/globals.css` path actually served.
4. Extract from `DESIGN.md`:
   - color system
   - typography pairings
   - radii / shape language
   - spacing / layout model
   - elevation rules
   - component rules for buttons, cards, inputs, chips
5. Apply spec in layers:
   - `layout.tsx`: load exact fonts from spec
   - `globals.css`: map design tokens into theme variables
   - page/components: rewrite surfaces, copy hierarchy, spacing, and CTA styling to match component guidance
6. Verify with real build and render, not code inspection only.

## Implementation pattern

### 1) Treat DESIGN.md as visual source of truth
Do not improvise palette, shadows, radii, or CTA style if spec already defines them. If current page is light and spec is dark, convert whole theme, not isolated components.

### 2) Start with global tokens
For Tailwind / shadcn / Next.js stacks, update global CSS vars first. Usually:
- `app/globals.css`
- theme vars for background / foreground / card / primary / secondary / border / ring
- font vars for body + heading

This prevents one-off inline color drift.

### 3) Load spec fonts in layout
For Next.js app router:
- put exact font pair from spec in `app/layout.tsx`
- expose body and heading font vars
- wire `html` / `body` classes so headings and body text naturally inherit correct family

### 4) Restyle page by spec sections
Map prose from DESIGN.md into code:
- **Brand & Style / Overview** → overall mood, density, whitespace
- **Colors** → background layers, text contrast, accent restraint
- **Typography** → serif vs sans roles, uppercase labels, tracking
- **Layout & Spacing** → max widths, grid, vertical gaps
- **Elevation & Depth** → blur, transparency, tonal layers vs drop shadows
- **Shapes** → radius discipline; avoid random soft pills if spec wants precision
- **Components** → CTA outlines, card treatment, badge styling

### 5) Verify served path before debugging styling
If render does not match edited file:
- confirm on-disk file path actually used by app
- search for duplicate nested app roots before assuming cache problem
- check served HTML for content markers from edited file

### 6) Verify with production render
For Next.js, production server is often cleanest truth source:
- build app
- kill stale listeners on chosen port
- start clean prod server
- probe returned HTML for expected content markers
- inspect browser render or screenshot for visual alignment

## Common pitfalls

- Writing to wrong nested path (`web/web/app/page.tsx` vs `web/app/page.tsx`). Verify exact app root before large edits.
- Matching headline copy but not theme system. Spec compliance means colors, typography, spacing, depth, and components all align.
- Leaving default shadcn / starter theme vars in globals while only patching page classes.
- Using raw Tailwind palette colors (`bg-zinc-*`, `text-red-*`, etc.) for product-theme work when design-system tokens or theme helpers already exist. For restyles tied to repo design system, prefer semantic tokens (`bg-background`, `text-foreground`, `border-border`, etc.) or repo theme helpers over palette classes.
- Using heavy drop shadows when spec calls for glass / blur / tonal layering.
- Keeping oversized rounded pills when spec asks for sharper editorial precision.
- For narrow styling requests on an existing control, trace the exact rendered component and its callsite state before editing shared variants. Do not assume the target is the primary CTA; verify whether the user means a nested swap/toggle control, then wire visuals to the real `disabled` prop instead of only changing colors.
- Trusting dev server with stale processes when production build gives cleaner answer.

## Verification standard

Do not say "matches DESIGN.md" until all are checked:
- build succeeds
- live HTML contains expected new page markers
- visual check confirms major spec traits (background, type, accents, surfaces, radii)
- note any remaining mismatches explicitly

## Good output summary

Report:
- files changed
- exact spec traits applied
- build/render verification result
- remaining visual mismatches if partial
