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
