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

## Why agentlint?

- Enforces deterministic, static checks suitable for CI gates.
- Focuses on agent-specific failure patterns in patch output.
- Fast enough to run on every PR and staged commit.

## Related Projects

- [coderace](https://github.com/openai/coderace)
- [agentmd](https://github.com/agentmd/agentmd)

## Contributing

1. Create a branch.
2. Add or update checks/tests/docs together.
3. Run `pytest -v --cov=agentlint --cov-report=term-missing`.
4. Open a PR with a short rationale and sample diff cases.

## License

MIT. See `LICENSE`.
