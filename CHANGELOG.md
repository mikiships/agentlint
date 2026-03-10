# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-03-10

### Added
- New `check-context` command: validates AGENTS.md, CLAUDE.md, GEMINI.md, and similar context files for staleness, bloat, and conflicts — no git diff required.
- Six new context checks:
  - `CTX001 path-rot` — detects referenced file/directory paths that no longer exist.
  - `CTX002 script-rot` — detects `npm run <script>` references missing from `package.json`.
  - `CTX003 bloat` — flags context files >8k chars (warning) or >15k chars (error) with ETH Zurich ICSE 2026 stat.
  - `CTX004 stale-todos` — flags TODO/FIXME/HACK/XXX markers as agent-confusing noise.
  - `CTX005 year-rot` — flags references to years 2023 and earlier as potentially stale guidance.
  - `CTX006 multi-file-conflict` — detects conflicting test/build commands across multiple context files.
- Freshness score (0–100): computed from findings (error −15, warning −5, info −2).
- `--format text|json|markdown` for `check-context` output.
- `--repo-root` option to control path resolution in `check-context`.
- `action.yml` updated: new `mode: context-check` input, `context-file` input, `freshness-score` and `context-findings` outputs.
- `scripts/ci-context-check.sh`: CI helper that runs context check and emits GitHub Action step outputs.
- Example workflow at `.github/workflows/examples/agentlint-context-check.yml` (weekly schedule + on push to context files).
- 57 new tests covering all 6 checks, CLI integration, and all 3 formatters.

## [0.3.0] - 2026-03-08

### Added
- New `mcp_permissions` check: flags dangerous MCP (Model Context Protocol) configuration patterns in diffs.
  - Detects `autoApprove: true` (boolean) — bypasses all per-tool approval prompts.
  - Detects `autoApprove: ["*"]` — wildcard grants unrestricted auto-approval.
  - Detects `trustLevel: "all"` — grants unrestricted trust to an MCP server.
  - Detects filesystem root access (`roots: ["/"]`) — overly broad path permissions.
  - Works via line-pattern matching (any file) and structural JSON parsing (`.mcp.json` / `claude_config.json`).
  - 23 new tests covering file-path detection, false positives, edge cases, and clean configs.
- Version bumped to `0.3.0`.

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
