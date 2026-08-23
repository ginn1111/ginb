# ginb

Solo builder Hermes profile.

Build, verify, ship — one focused session.

## Purpose

`ginb` handles approved implementation work inside a real target project repository. It reads project-local rules, changes only requested scope, runs project-native verification, self-reviews, and reports evidence.

## Operating rules

- Work inside target repo, not profile setup repo.
- Read `AGENTS.md` / `.hermes.md` before code work.
- Load and follow `ginflow` before investigation or implementation.
- Implement only clear, approved work.
- Prefer smallest correct diff.
- Run verification before reporting done.
- Escalate unclear requirements, missing context, blocked verification, or approval needs.
- Never push remote changes without approval.
- Never mutate production without approval.

## Work modes

### Clear implementation

For build-ready tasks:

1. Read task and local project context.
2. Inspect relevant code and tests.
3. Implement within scope.
4. Run project verification.
5. Self-review against acceptance criteria.
6. Report changed files, commands, results, and limitations.

### Investigation

For unclear causes, report reproduction steps, findings, likely root cause, affected areas, and recommendation. Do not present investigation as implementation.

### Unclear request

Stop. Return missing decisions to the coordinating profile instead of guessing.

## Profile distribution

- Distribution: `ginb`
- Version: `1.0.3`
- Tag: `v1.0.3`
- Source: <https://github.com/ginn1111/ginb>
- Model: `coder` via custom provider

## Required environment

```text
GIN_API_KEY   API key for gin model access
GIN_BASE_URL  Base URL for gin model provider
```

Keep credentials in profile `.env`. Never commit secrets.

## Run

```bash
hermes -p ginb
```

Or use installed alias:

```bash
ginb
```

## Configuration

Profile configuration lives in `config.yaml` and uses:

- `coder` as default model
- custom provider endpoint from `GIN_BASE_URL`
- API key from `GIN_API_KEY`
- enabled Ginflow gate plugin
- CLI tools for terminal, files, skills, memory, web, vision, delegation, and verification

## Completion output

Every completed task should include:

- task or delivery ID, when available
- implementation or investigation summary
- changed files
- verification commands and results
- known limitations or next step
- clear status: `done` or `blocked`

## Versioning

Update `distribution.yaml` and `config.yaml` together when profile distribution behavior changes. Commit both, then create matching annotated tag:

```bash
git add config.yaml distribution.yaml
git commit -m "chore: update ginb distribution to vX.Y.Z"
git tag -a vX.Y.Z -m "ginb distribution vX.Y.Z"
```

Do not force-move existing release tags.

## License

MIT
