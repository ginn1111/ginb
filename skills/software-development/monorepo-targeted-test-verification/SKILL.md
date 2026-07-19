---
name: monorepo-targeted-test-verification
description: Run focused tests in monorepos without bypassing package-local Jest/ts-jest/Babel config.
---

# Monorepo targeted test verification

Use when verifying one file or small test subset inside monorepo packages that may carry local Jest, ts-jest, Babel, or TypeScript config.

## Trigger signals

- Root-level `jest path/to/file` throws parser errors on valid TypeScript
- Error says `Cannot use import statement outside a module`
- Error says unexpected token on TS syntax like parameter annotations
- Package has its own `jest.config.js`, `.babelrc`, or package-local `test` script

## Steps

1. Find package owning changed test file.
2. Run targeted test from package directory, not repo root.
3. Prefer package script first, for example:
   - `yarn test src/path/to/file.test.ts --runInBand`
   - or package-specific variant that preserves local config
4. If parser/module error appears from root-run Jest, treat it as possible config-path issue before changing test code.
5. Only patch test file after package-local run proves real TypeScript or assertion failure.

## Pitfalls

- Root-level Jest invocation can miss package-local `ts-jest` or Babel setup and create false syntax/module failures.
- Do not strip TypeScript syntax from tests only to satisfy wrong runner path.
- When moving from root command to package-local command, re-check failing assertions separately from runner/config issues.

## Verification

- Confirm targeted test passes from owning package directory.
- Record exact passing command in handoff.

## References

- `references/root-vs-package-jest.md` — short note on false parser failures from root-level Jest in package-owned tests.
