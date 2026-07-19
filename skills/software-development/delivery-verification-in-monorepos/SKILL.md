---
name: delivery-verification-in-monorepos
description: Verify scoped code changes in large monorepos without losing signal to unrelated package failures.
---

# Delivery verification in monorepos

Use when:
- Change touches one package or one UI surface inside big monorepo.
- User asks for build/test proof.
- Repo-level `test`/`build` may include unrelated workspaces.

## Goals

- Prove changed area still compiles and tests.
- Separate change-caused failures from ambient monorepo failures.
- Leave concise evidence with exact commands and outcomes.

## Steps

1. **Run nearest scoped verification first**
   - Prefer package-local typecheck/build-noop/unit tests for touched package.
   - Use repo guidance from `AGENTS.md` before expensive root commands.
   - For UI/page-only changes, start with smallest command that exercises changed code path.

2. **Run root verification when explicitly required**
   - If user, system, or delivery brief asks for root `yarn run test` / `yarn run build`, run them after scoped checks.
   - Do not substitute narrower commands for explicit root verification request.

3. **Classify failures before changing code**
   - If scoped command fails in touched package, fix code.
   - If root command fails in unrelated workspace/package-manager boundary and scoped checks for changed package already pass, report failure as repo-level blocker, not regression from your diff.
   - Name failing workspace/task exactly.

4. **Report evidence in two layers**
   - Layer 1: changed-package verification with exact pass/fail result.
   - Layer 2: root verification result, including unrelated blockers if present.
   - Say plainly whether work is fully verified or only scoped-verified due external blocker.

## Pitfalls

- Do not claim "verified" from typecheck alone when system explicitly asked for root test/build.
- Do not chase unrelated monorepo failures unless they block proving changed package or user asks.
- Do not hide ambient failures; separate them from your diff.

## References

- `references/bridge-page-fee-subtraction.md` — concrete example: changed page passed scoped extension checks, root build passed, root test failed in unrelated workspace.
