# agentlint v0.4.0 Build Log

## Final Summary — 2026-03-10

All 5 deliverables complete. All tests passing. PyPI published.

### What was built

**D1 — Core engine** (`src/agentlint/context_checker.py`, `src/agentlint/context_models.py`)
- `ContextChecker` class with `run()` returning `ContextReport`
- `ContextFinding` and `ContextReport` dataclasses
- All 6 checks implemented: CTX001 path-rot, CTX002 script-rot, CTX003 bloat, CTX004 stale-todos, CTX005 year-rot, CTX006 multi-file-conflict
- Freshness score computed (0–100), error −15, warning −5, info −2

**D2 — CLI** (`src/agentlint/cli.py`)
- `agentlint check-context [FILE] --format text|json|markdown --repo-root PATH --no-config`
- Auto-detects AGENTS.md > CLAUDE.md > GEMINI.md > .cursorrules
- Exit 1 on error findings, exit 0 otherwise

**D3 — Formatters** (`src/agentlint/context_formatters.py`)
- Text formatter with severity icons and aligned columns
- JSON formatter (valid JSON, snake_case keys)
- Markdown formatter (GFM table + bold freshness score)

**D4 — GitHub Action** (`action.yml`, `scripts/ci-context-check.sh`, `.github/workflows/examples/agentlint-context-check.yml`)
- `mode: context-check` input, `context-file` input
- `freshness-score` and `context-findings` outputs
- CI script exits non-zero on ERROR findings; graceful skip if file missing
- Example workflow: weekly schedule + on push to context files

**D5 — Docs + publish**
- README: "Context File Validation" section with check table, freshness score explanation, CI usage
- CHANGELOG: full v0.4.0 entry
- pyproject.toml: version bumped to 0.4.0
- All commits pushed to GitHub

### Test count

**214 total tests** (157 pre-existing + 57 new)

New test breakdown:
- `tests/test_context_checker.py`: 33 tests (CTX001–CTX006 × 3–5 cases each + auto-detect + freshness score)
- `tests/test_cli_check_context.py`: 9 tests (basic, auto-detect, no-file error, file-not-found, JSON, markdown, exit codes)
- `tests/test_context_formatters.py`: 15 tests (text × 6, JSON × 4, markdown × 5)

### PyPI

https://pypi.org/project/ai-agentlint/0.4.0/

### Blockers

None. All deliverables completed in single pass.
