# All-Day Build Contract: agentlint v0.1.0

Status: In Progress
Date: 2026-03-03
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentlint`, a Python CLI that lints AI coding agent output (git diffs) for common problems. The key differentiator: **no LLM required** for core checks. Static analysis that's fast, free, and deterministic. It audits what an agent changed and flags scope drift, secret leaks, config vandalism, placeholder bombs, and more.

Target audience: developers using Claude Code, Codex, Cursor, Aider, Gemini CLI, or any coding agent.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Project Setup

Python package with:
- `pyproject.toml` (use hatchling or setuptools, NOT poetry)
- `src/agentlint/` package layout
- Entry point: `agentlint` CLI command
- Dependencies: `click` (CLI), `rich` (terminal output). No other runtime deps.
- Dev dependencies: `pytest`, `pytest-cov`, `ruff`
- Python 3.10+ required
- MIT license

## 4. Feature Deliverables

### D1. Core Diff Parser + Check Engine

Build the foundation: parse unified diffs (from `git diff` or piped input) and run checks against them.

Required files:
- `src/agentlint/cli.py` — Click CLI entry point
- `src/agentlint/parser.py` — Unified diff parser (parse hunks, files, additions, deletions)
- `src/agentlint/engine.py` — Check runner (discovers and runs all checks, collects results)
- `src/agentlint/models.py` — Data models (CheckResult, Severity enum, DiffFile, etc.)

CLI interface:
```
# Lint the last commit
agentlint check

# Lint staged changes
agentlint check --staged

# Lint a specific commit range
agentlint check HEAD~3..HEAD

# Lint piped diff
git diff | agentlint check --stdin

# With task description for scope checks
agentlint check --task "Add user authentication to the API"

# Output formats
agentlint check --format json
agentlint check --format table  # default, rich terminal
```

- [ ] Diff parser handles unified diff format (git diff output)
- [ ] Parser extracts: file paths, hunks, added/removed lines, binary files
- [ ] Engine discovers and runs checks, collects results with severity levels
- [ ] Severity levels: error, warning, info
- [ ] CLI with `check` command, all flags above working
- [ ] JSON output format (structured, machine-readable)
- [ ] Rich table output format (default, human-readable)
- [ ] Exit code: 0 = clean, 1 = warnings only, 2 = errors found
- [ ] Tests for D1 (parser, engine, CLI)

### D2. Core Checks (Static, No LLM)

Implement the 8 core lint checks. Each check is a separate module in `src/agentlint/checks/`.

Required files:
- `src/agentlint/checks/__init__.py`
- `src/agentlint/checks/scope_drift.py`
- `src/agentlint/checks/secret_leak.py`
- `src/agentlint/checks/test_regression.py`
- `src/agentlint/checks/config_vandalism.py`
- `src/agentlint/checks/dependency_injection.py`
- `src/agentlint/checks/todo_bombs.py`
- `src/agentlint/checks/permission_escalation.py`
- `src/agentlint/checks/dead_code.py`

**Check specifications:**

1. **scope_drift** — When `--task` is provided, extract file paths and keywords from the task description. Flag files modified that don't appear related to the task. Uses simple keyword matching + file path heuristics (not LLM).

2. **secret_leak** — Scan added lines for patterns matching API keys, tokens, passwords, AWS credentials, private keys, connection strings. Use regex patterns (similar to trufflehog's pattern set but simpler). Flag with ERROR severity.

3. **test_regression** — Flag test files that had lines deleted but no lines added (tests removed without replacement). Flag test files modified when tests weren't in the task scope. WARNING severity.

4. **config_vandalism** — Flag changes to CI configs (.github/workflows/*, .gitlab-ci.yml), lock files (package-lock.json, poetry.lock, Cargo.lock, uv.lock), and other infrastructure files when they weren't part of the task. WARNING severity.

5. **dependency_injection** — Detect new dependencies added (parse requirements.txt additions, pyproject.toml dependency additions, package.json additions, Cargo.toml additions). Flag if not mentioned in task. WARNING severity.

6. **todo_bombs** — Detect TODO, FIXME, HACK, XXX, PLACEHOLDER comments added in the diff. More than 3 = ERROR (agent left unfinished work). 1-3 = WARNING.

7. **permission_escalation** — Detect chmod, sudo, eval(), exec(), subprocess with shell=True, os.system() calls added in the diff. ERROR severity.

8. **dead_code** — Detect large blocks (5+ lines) of commented-out code added to the diff. WARNING severity.

- [ ] All 8 checks implemented as separate modules
- [ ] Each check has a `run(diff, task_description=None) -> list[CheckResult]` interface
- [ ] Each check has comprehensive regex patterns
- [ ] secret_leak covers: AWS keys, GitHub tokens, generic API keys, passwords in config, private key blocks
- [ ] scope_drift works without --task (skip check) and with --task (run check)
- [ ] All checks handle edge cases (empty diffs, binary files, renames)
- [ ] Tests for each individual check (at least 5 test cases per check)

### D3. Configuration + Ignore Rules

Allow users to customize which checks run and suppress false positives.

Required files:
- `src/agentlint/config.py`

Config via `.agentlint.toml` in project root:
```toml
[agentlint]
# Disable specific checks
disabled_checks = ["dead_code"]

# Severity overrides
[agentlint.severity]
todo_bombs = "info"  # downgrade from warning

# Ignore patterns (glob)
[agentlint.ignore]
scope_drift = ["*.md", "docs/*"]
config_vandalism = ["package-lock.json"]

# Secret patterns to ignore (for false positives)
[agentlint.secrets]
allowed_patterns = ["EXAMPLE_KEY_*", "test_token_*"]
```

- [ ] TOML config file discovery (walk up from cwd to find .agentlint.toml)
- [ ] Check disabling
- [ ] Severity overrides
- [ ] Per-check ignore patterns (glob matching on file paths)
- [ ] Secret allowlist patterns
- [ ] CLI flag `--no-config` to ignore config file
- [ ] CLI flag `--config PATH` to use specific config
- [ ] Tests for D3

### D4. Summary Report + CI Integration

Rich summary output and CI-friendly features.

Required files:
- `src/agentlint/report.py`

Features:
- Summary statistics at the end (X errors, Y warnings, Z info)
- Per-file breakdown in table format
- `--fail-on warning` or `--fail-on error` flag to control exit code threshold
- `--quiet` flag for CI (only output errors/warnings, no decoration)
- GitHub Actions output format (`::error file=...::message`)
- Example GitHub Actions workflow in README

- [ ] Summary report with statistics
- [ ] Per-file breakdown
- [ ] --fail-on flag
- [ ] --quiet flag
- [ ] GitHub Actions output format (--format github)
- [ ] Tests for D4

### D5. README + Packaging

Required files:
- `README.md`
- `CHANGELOG.md`

README must include:
- One-line description + badges (PyPI, Python version, license)
- Installation (`pip install agentlint`)
- Quick start (3 examples: basic, with task, CI)
- All checks listed with descriptions and examples
- Configuration section
- GitHub Actions integration example
- "Why agentlint?" section (static analysis, no LLM, fast, free, deterministic)
- Cross-links to coderace and agentmd ("The Agent Toolkit trilogy")
- Contributing section

- [ ] README with all sections above
- [ ] CHANGELOG.md
- [ ] pyproject.toml with all metadata (description, URLs, classifiers, keywords)
- [ ] `py.typed` marker file
- [ ] Package builds cleanly with `python -m build` or `uv build`

## 5. Test Requirements

- [ ] Unit tests for diff parser (various diff formats, edge cases)
- [ ] Unit tests for each of the 8 checks (at least 5 cases each = 40+ check tests)
- [ ] Unit tests for config loading
- [ ] Integration test: full CLI run on a sample diff with multiple issues
- [ ] Integration test: JSON output validation against schema
- [ ] Integration test: piped input mode
- [ ] Edge cases: empty diff, binary-only diff, rename-only diff, mega-diff (1000+ files)
- [ ] All tests pass with `pytest -v`
- [ ] Test coverage >80%
- [ ] Total test count target: 100+

## 6. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 7. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (new requirements discovered) -> STOP, report what's new
- All tests passing but deliverables remain -> continue to next deliverable
