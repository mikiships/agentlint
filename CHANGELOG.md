# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-03-04

### Added
- Contract JSON report schema for CI integrations with top-level `version`, `metadata`, `summary`, and `findings`.
- Markdown formatter (`--format markdown`) with grouped file findings in collapsible `<details>` blocks for PR comments.
- Composite GitHub Action (`action.yml`) with inputs for failure thresholds, output format, optional PR commenting, and Python version selection.
- Reusable workflow example at `.github/workflows/agentlint-ci.yml` for `pull_request` and `workflow_call`.
- YAML validation tests using `yaml.safe_load` for action and workflow files.

### Changed
- CLI format choices now use `text|json|markdown` (default `text`).
- Exit code behavior is now binary (`0` clean, `1` failing findings).
- Project version bumped to `0.2.0`.

## [0.1.0] - 2026-03-03

### Added
- Core CLI command `agentlint check` with support for staged diffs, commit ranges, and stdin.
- Unified diff parser with file/hunk/line modeling and binary/rename/new/delete handling.
- Static check engine with deterministic severity ordering and stable JSON/table outputs.
- Eight built-in checks:
  - `scope_drift`
  - `secret_leak`
  - `test_regression`
  - `config_vandalism`
  - `dependency_injection`
  - `todo_bombs`
  - `permission_escalation`
  - `dead_code`
- Config support via `.agentlint.toml` discovery and explicit/disabled loading options.
- Reporting module with summary counts, per-file rollups, and GitHub Actions annotation output.
- Packaging metadata and typed marker file (`py.typed`).
- Comprehensive test suite (100+ tests) with parser, checks, CLI, config, report, and integration coverage.
