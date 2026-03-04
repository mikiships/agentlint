# All-Day Build Contract: agentlint GitHub Action + v0.2.0

Status: In Progress
Date: 2026-03-04
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a GitHub Action that runs agentlint on PR diffs, and add JSON + markdown output formats for CI integration. This mirrors the agentmd action pattern: composite action + reusable workflow + PR comment support.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. **Do NOT run any git commands.** No `git add`, `git commit`, `git push`, `git status`. The orchestrator handles all git operations. If you feel the urge to commit, write to progress-log.md instead.
8. If stuck on same issue for 3 attempts, stop and write a blocker report to progress-log.md.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. JSON Output Format (core + CLI)

Add `--format json` to the CLI that outputs structured JSON for CI consumption.

Required files:
- `src/agentlint/report.py` (extend with JSON serialization)
- `src/agentlint/cli.py` (add --format flag: text|json|markdown)

- [ ] JSON output includes: findings list (severity, check name, file, line, message), summary (total, by-severity counts), metadata (version, timestamp)
- [ ] Schema matches: `{"version": "1.0.0", "metadata": {...}, "summary": {...}, "findings": [...]}`
- [ ] `--format json` flag on CLI
- [ ] Tests for JSON output structure and content

### D2. Markdown Output Format

Add `--format markdown` for PR comment rendering.

Required files:
- `src/agentlint/formatters.py` (new module)
- `src/agentlint/cli.py` (extend --format)

- [ ] Markdown output with header, summary table (check | severity | count), findings list grouped by file
- [ ] Collapsible `<details>` blocks for file-level findings
- [ ] Footer with agentlint link
- [ ] `--format markdown` flag on CLI
- [ ] Tests for markdown output structure

### D3. GitHub Action (composite)

Create a composite GitHub Action at `action.yml` in the repo root.

Required files:
- `action.yml` (composite action)
- `.github/workflows/agentlint-ci.yml` (reusable workflow example)

- [ ] Action inputs: `fail-on-error` (bool, default true), `fail-on-warning` (bool, default false), `format` (text|json|markdown, default text), `comment` (bool, default true), `python-version` (default "3.12")
- [ ] Action installs from PyPI (`pip install ai-agentlint`)
- [ ] Runs `agentlint` on the PR diff (gets diff from `git diff origin/main...HEAD`)
- [ ] Outputs: `exit-code`, `report` (the formatted output)
- [ ] PR comment via peter-evans/create-or-update-comment when `comment: true`
- [ ] Reusable workflow example that calls the action on `pull_request`
- [ ] YAML files validated with Python yaml.safe_load

### D4. Integration Tests

- [ ] CLI integration test: run agentlint on a sample diff, verify JSON output schema
- [ ] CLI integration test: run agentlint on a sample diff, verify markdown output structure
- [ ] CLI integration test: verify exit codes (0 for clean, 1 for findings with errors)
- [ ] Edge case: empty diff produces clean output in all formats

### D5. Docs + Packaging (v0.2.0)

- [ ] Update README.md: document --format flag, GitHub Action usage with copy-paste workflow YAML
- [ ] Add or update CHANGELOG.md with v0.2.0 notes
- [ ] Bump version to 0.2.0 in pyproject.toml and src/agentlint/__init__.py
- [ ] Full test suite passes (target: 130+ tests, baseline 105)

## 4. Test Requirements

- [ ] Unit tests for JSON format output
- [ ] Unit tests for markdown format output
- [ ] Integration tests for CLI with all format flags
- [ ] Edge cases: no findings, all severities, multiple files
- [ ] All 105 existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (new requirements discovered) -> STOP, report what's new
- All tests passing but deliverables remain -> continue to next deliverable
