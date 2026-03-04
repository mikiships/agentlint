# Progress Log

## D1 - Core Diff Parser + Check Engine
- Built package scaffold and CLI entry point (`agentlint check`) with diff input modes: last commit, `--staged`, explicit commit range, and `--stdin`.
- Implemented unified diff parser for files/hunks/additions/deletions, plus rename/new/deleted/binary markers.
- Implemented check engine discovery/execution pipeline, severity sorting, deterministic output payloads, and exit code policy (`0` clean, `1` warnings-only, `2` errors).
- Added D1 tests for parser, engine, and CLI behavior.
- Tests passed: `pytest -q` (30 tests).
- Next: implement D2 core static checks and check-specific tests.
- Blockers: none.

## D2 - Core Checks (Static, No LLM)
- Implemented eight built-in checks in `src/agentlint/checks/`: `scope_drift`, `secret_leak`, `test_regression`, `config_vandalism`, `dependency_injection`, `todo_bombs`, `permission_escalation`, `dead_code`.
- Added shared check utilities for keyword extraction, test-path detection, and diff iteration across added/deleted lines.
- Wired engine compatibility for check signatures that optionally consume config context while preserving `run(diff, task_description=None)` behavior.
- Added per-check tests (>=5 each) including empty/binary handling and task-aware behavior.
- Tests passed: `pytest -q`.
- Next: implement D3 config discovery/overrides/ignore rules and CLI flags.
- Blockers: git commit is blocked by sandbox write restrictions on `.git` (cannot create `index.lock`).

## D3 - Configuration + Ignore Rules
- Added `src/agentlint/config.py` with upward `.agentlint.toml` discovery, runtime config model, validation, and loading (including a stdlib-only fallback parser for constrained TOML shape).
- Implemented config controls: `disabled_checks`, severity overrides, per-check ignore glob lists, and `secrets.allowed_patterns` allowlist support.
- Wired CLI flags `--no-config` and `--config PATH` and passed runtime config into engine/check execution.
- Added config-focused tests and CLI config integration tests.
- Tests passed: `pytest -q`.
- Next: implement D4 reporting summary, CI output format, fail thresholds, and quiet mode.
- Blockers: git commit remains blocked by sandbox restrictions on `.git` writes.

## D4 - Summary Report + CI Integration
- Added `src/agentlint/report.py` with deterministic summary metrics, per-file breakdown aggregation, and output renderers for `table`, `json`, and GitHub Actions annotation format.
- Updated CLI with `--format github`, `--fail-on warning|error`, and `--quiet`, and wired reporting through the new module.
- Added/expanded tests for report formatting, GitHub annotation lines, quiet output, and fail-threshold behavior.
- Added a GitHub Actions usage snippet to `README.md`.
- Tests passed: `pytest -q`.
- Next: complete D5 docs + packaging assets, run build, run full coverage checks, and finish final summary.
- Blockers: git commit remains blocked by sandbox restrictions on `.git` writes.

## D5 - README + Packaging
- Replaced README with full project documentation: badges, install flow, quick start examples (basic/task/stdin/JSON/CI), full check catalog with examples, configuration docs, GitHub Actions workflow, rationale, related links (`coderace`, `agentmd`), contribution guidance, and license note.
- Added `CHANGELOG.md` (v0.1.0), `LICENSE` (MIT), `src/agentlint/py.typed`, and `.gitignore` for local artifacts.
- Finalized package metadata in `pyproject.toml` (classifiers, keywords, URLs, scripts, dev deps, build settings).
- Added integration tests for empty/binary/rename/JSON-shape/threshold/mega-diff flows.
- Validation complete:
  - `pytest -q` passes.
  - `.venv/bin/pytest -v --cov=agentlint --cov-report=term-missing` passes.
  - Coverage: `94%` total.
  - Test count: `105` tests.
- Packaging verification:
  - Attempted `python -m build` (blocked: `build` module unavailable in sandboxed env).
  - Attempted `uv build` with local cache override (blocked: uv runtime panic in this sandbox).
  - Editable install build path succeeded earlier via `.venv/bin/pip install -e ".[dev]"`.
- Blockers: git commit remains blocked by sandbox restrictions on `.git` writes (`index.lock` cannot be created).

## Final Summary
- Deliverables D1 through D5 are fully implemented in the working tree.
- All tests pass with >80% coverage and >100 test cases.
- Remaining environment blockers are external to code changes: git write restrictions and build-tool execution constraints in this sandbox.

## 2026-03-04 Build Contract (GitHub Action + v0.2.0) - D1
- Built JSON reporting schema in `src/agentlint/report.py` with top-level keys `version`, `metadata`, `summary`, and `findings`.
- Added JSON fields required for CI: finding entries (`severity`, `check`, `file`, `line`, `message`), summary totals/by-severity, and metadata (`version`, `timestamp`).
- Updated CLI format choices in `src/agentlint/cli.py` to `text|json|markdown` (default `text`) per contract.
- Updated unit/CLI/integration tests to assert the new JSON schema and content expectations.
- Tests passed: `pytest -q tests/test_report.py tests/test_cli.py tests/test_integration.py`.
- Next: implement D2 markdown formatter module and markdown-specific tests.
- Blockers: none.

## 2026-03-04 Build Contract (GitHub Action + v0.2.0) - D2
- Added `src/agentlint/formatters.py` with markdown rendering for PR comments.
- Implemented required markdown structure: report header, summary table (`check | severity | count`), file-grouped findings under collapsible `<details>` blocks, and a footer linking to the project.
- Wired markdown output in `src/agentlint/report.py` so CLI `--format markdown` now renders structured markdown content.
- Added markdown-focused unit tests in `tests/test_formatters.py` and extended report/CLI tests for markdown dispatch and output shape.
- Tests passed: `pytest -q tests/test_formatters.py tests/test_report.py tests/test_cli.py`.
- Next: implement D3 composite GitHub Action + reusable workflow and YAML validation tests.
- Blockers: none.

## 2026-03-04 Build Contract (GitHub Action + v0.2.0) - D3
- Created root `action.yml` composite action with required inputs: `fail-on-error`, `fail-on-warning`, `format`, `comment`, and `python-version` (with contract defaults).
- Implemented action runtime steps to install from PyPI (`pip install ai-agentlint`), run `agentlint` against `git diff origin/main...HEAD`, and expose outputs `exit-code` and `report`.
- Added optional PR commenting via `peter-evans/create-or-update-comment@v4` gated by `comment: true` and pull request event context.
- Added `.github/workflows/agentlint-ci.yml` reusable workflow example triggered on `pull_request`/`workflow_call` that invokes the composite action.
- Added YAML validation tests (`tests/test_github_action_yaml.py`) that parse both YAML files with `yaml.safe_load` and assert required structure.
- Updated dev dependencies in `pyproject.toml` to include `PyYAML` for YAML validation tests.
- Tests passed: `pytest -q tests/test_github_action_yaml.py`.
- Next: implement D4 integration test updates for JSON/markdown schema checks, exit-code behavior, and empty-diff coverage across all formats.
- Blockers: none.

## 2026-03-04 Build Contract (GitHub Action + v0.2.0) - D4
- Updated CLI failure semantics to contract-aligned binary exit codes: `0` for clean and `1` for failing findings.
- Added/updated integration coverage in `tests/test_integration.py` for:
  - JSON schema validation on sample diff output.
  - Markdown structure validation on sample diff output.
  - Exit-code behavior (`0` clean, `1` for error findings).
  - Empty-diff clean output across `text`, `json`, and `markdown` formats.
- Updated affected unit/CLI tests for the new exit-code contract.
- Tests passed: `pytest -q tests/test_engine.py tests/test_cli.py tests/test_report.py tests/test_formatters.py tests/test_integration.py`.
- Next: complete D5 docs/version/changelog updates and run full test suite.
- Blockers: none.

## 2026-03-04 Build Contract (GitHub Action + v0.2.0) - D5
- Updated docs for v0.2.0:
  - `README.md` now documents `--format` options (`text|json|markdown`) and includes a copy-paste GitHub workflow snippet that uses the composite action and prints outputs.
  - `CHANGELOG.md` now includes a `0.2.0` release section covering JSON/markdown output, action/workflow support, and exit-code behavior.
- Bumped version to `0.2.0` in `pyproject.toml` and `src/agentlint/__init__.py`.
- Added expanded output-contract coverage in `tests/test_output_contracts.py` to validate JSON/markdown schema behavior across many data combinations.
- Validation complete:
  - `pytest --collect-only` reports `134 tests collected`.
  - `pytest -q` passes for the full suite.
- Next: none (all deliverables D1-D5 complete).
- Blockers: none.

## Final Summary (2026-03-04 Build Contract: GitHub Action + v0.2.0)
- Completed D1 through D5 in order.
- Added JSON output contract (`version`/`metadata`/`summary`/`findings`), markdown formatter with collapsible file groups, composite GitHub Action, reusable workflow example, YAML validation tests, documentation updates, and version bump to `0.2.0`.
- Full suite passes with `134` collected tests (above the 130+ target).
- No blockers remain.
