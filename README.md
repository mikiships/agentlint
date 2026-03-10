# agentlint

[![CI](https://img.shields.io/badge/ci-ready-brightgreen)](#github-actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#install)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#license)

`agentlint` is a Python CLI that lints AI coding-agent git diffs for common risky patterns using static analysis only (no LLM calls).

## Install

```bash
pip install ai-agentlint
```

For local development:

```bash
pip install -e ".[dev]"
```

## Quick Start

Basic check against last commit:

```bash
agentlint check
```

Check staged changes:

```bash
agentlint check --staged
```

Check a commit range:

```bash
agentlint check HEAD~3..HEAD
```

Pipe a diff through stdin:

```bash
git diff | agentlint check --stdin
```

Provide task context for scope-aware checks:

```bash
agentlint check --task "only update parser error handling"
```

JSON output for automation:

```bash
agentlint check --format json
```

Markdown output for PR comments:

```bash
agentlint check --format markdown
```

Available report formats: `text` (default), `json`, and `markdown`.

## Checks

- `scope_drift`: Warns when changed files appear unrelated to `--task`.
  Example: task is "parser bugfix" but diff edits `infra/main.tf`.
- `secret_leak`: Errors on likely credential leaks (AWS/GitHub tokens, passwords, private keys, DB URLs).
  Example: added line `password = "supersecret123"`.
- `test_regression`: Warns when test lines are deleted without replacement or tests are changed off-task.
  Example: delete `tests/test_api.py` assertions and add no test updates.
- `config_vandalism`: Warns for CI/infra/lock-file edits outside scope.
  Example: modify `.github/workflows/ci.yml` in a docs-only task.
- `dependency_injection`: Warns when new dependencies are introduced unexpectedly.
  Example: add `flask==3.0.0` to `requirements.txt` without dependency-related task text.
- `todo_bombs`: Warns/errors on TODO/FIXME/HACK spikes.
  Example: adding 4 TODO markers raises an error.
- `mcp_permissions`: Errors on dangerous MCP server configuration patterns.
  Example: `.mcp.json` with `"autoApprove": true` or `"autoApprove": ["*"]` (related to CVE-2026-21852 auto-approve bypass).
- `permission_escalation`: Errors on risky patterns (`sudo`, permissive `chmod`, `eval`, `exec`, `shell=True`, `os.system`).
  Example: `subprocess.run(cmd, shell=True)`.
- `dead_code`: Warns on added commented-out code blocks (5+ lines).
  Example: pasting a large block of `# old implementation` lines.

## Configuration

`agentlint` discovers `.agentlint.toml` by walking up from the current directory.

```toml
disabled_checks = ["scope_drift"]

[severity]
todo_bombs = "error"
config_vandalism = "info"

[ignore]
secret_leak = ["tests/fixtures/*"]
scope_drift = ["docs/*"]

[secrets]
allowed_patterns = ["^dummy_token_for_tests$"]
```

CLI config controls:

- `--config PATH`: Load config from explicit file.
- `--no-config`: Ignore discovered config files.

## GitHub Actions

Use the bundled composite action in this repository to lint PR diffs and post markdown results as a pull request comment.

```yaml
name: agentlint
on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  lint-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: git fetch origin main --depth=1
      - uses: ./
        id: agentlint
        with:
          fail-on-error: true
          fail-on-warning: false
          format: markdown
          comment: true
          python-version: "3.12"
      - if: always()
        run: |
          echo "exit-code=${{ steps.agentlint.outputs.exit-code }}"
          printf '%s\n' "${{ steps.agentlint.outputs.report }}"
```

## Context File Validation

Beyond linting git diffs, `agentlint` can validate your context files (AGENTS.md, CLAUDE.md, GEMINI.md) directly for staleness, bloat, and internal conflicts.

```bash
agentlint check-context
```

Or target a specific file:

```bash
agentlint check-context CLAUDE.md --format json
```

### Context checks

| ID | Severity | What it catches |
| --- | --- | --- |
| `CTX001` | warning | **path-rot** — file/dir paths mentioned in the context file that no longer exist |
| `CTX002` | warning | **script-rot** — `npm run <script>` references missing from `package.json` |
| `CTX003` | warning/error | **bloat** — context files >8k chars (warning) or >15k chars (error); per ETH Zurich ICSE 2026, stale context adds ~20% token overhead |
| `CTX004` | info | **stale-todos** — TODO/FIXME/HACK/XXX markers that may confuse agents |
| `CTX005` | warning | **year-rot** — references to 2023 or earlier may be outdated guidance |
| `CTX006` | warning | **multi-file-conflict** — conflicting test/build commands across multiple context files |

### Freshness score

Every run produces a **freshness score** (0–100). Each finding deducts points:
- error: −15
- warning: −5
- info: −2

A score below 70 suggests the context file needs a cleanup pass.

### Works alongside `agentlint check`

`agentlint check` lints what agents *write* (git diffs). `agentlint check-context` lints what agents *read* (context files). Together they cover the full agent quality surface.

### CI integration

Add a weekly context health check with the bundled GitHub Action:

```yaml
- uses: mikiships/agentlint@main
  with:
    mode: context-check
    # context-file: AGENTS.md  # optional, auto-detected otherwise
```

See [`.github/workflows/examples/agentlint-context-check.yml`](.github/workflows/examples/agentlint-context-check.yml) for a full example.

## Why agentlint?

- Enforces deterministic, static checks suitable for CI gates.
- Focuses on agent-specific failure patterns in patch output.
- Fast enough to run on every PR and staged commit.

## Part of the Agent Toolkit

agentlint is one of three tools for AI coding agent quality:

- **[coderace](https://github.com/mikiships/coderace)** — Race coding agents against each other on real tasks. Automated, reproducible, scored comparisons.
- **[agentmd](https://github.com/mikiships/agentmd)** — Generate and score context files (CLAUDE.md, AGENTS.md, .cursorrules) for AI coding agents.
- **[agentlint](https://github.com/mikiships/agentlint)** — Lint AI agent git diffs for risky patterns. Static analysis, no LLM required.

Measure (coderace) → Optimize (agentmd) → Guard (agentlint).

## Contributing

1. Create a branch.
2. Add or update checks/tests/docs together.
3. Run `pytest -v --cov=agentlint --cov-report=term-missing`.
4. Open a PR with a short rationale and sample diff cases.

## License

MIT. See `LICENSE`.
