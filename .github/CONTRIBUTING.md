# Contributing to schemachange

Thank you for your interest in contributing! This guide will get you started quickly.

## Quick Start

### 1. Install uv

schemachange uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it first:

- **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Any platform (via pip)**: `pip install uv`

### 2. Fork, clone, and set up

```bash
git clone https://github.com/YOUR_USERNAME/schemachange.git
cd schemachange

# Pin to Python 3.13 (required — uv defaults to the latest Python otherwise)
echo "3.13" > .python-version

# Install all dependencies (including dev) using the lockfile
uv sync --extra dev
```

### 3. Make your changes and run tests

```bash
uv run pytest
uv run ruff check .
```

That's it! Open a PR when ready.

## Finding Something to Work On

- **New to the project?** Look for [`good-first-issue`](https://github.com/Snowflake-Labs/schemachange/labels/good-first-issue)
- **Need help?** Ask in [Discussions](https://github.com/Snowflake-Labs/schemachange/discussions)
- **Have an idea?** Discuss it in [Ideas](https://github.com/Snowflake-Labs/schemachange/discussions/categories/ideas) first

## Submitting Changes

1. **Create a branch** from main: `git checkout -b fix-issue-123`
2. **Make your changes**
3. **Run tests**: `uv run pytest && uv run ruff check .`
4. **Commit**: Use clear commit messages
5. **Push** and create a Pull Request

### PR Guidelines

**Required:**
- Tests pass (`uv run pytest`)
- Code is formatted (`uv run ruff format .`)

**Helpful (but optional):**
- Add tests if you're adding functionality
- Update docs if you're changing behavior
- Update CHANGELOG.md (or we can do it)

**We'll help you with:**
- Code review feedback
- Test suggestions
- Documentation improvements

## What to Expect

- **Triage**: Within 1 week
- **Review**: Within 2-4 weeks
- **Questions?** Just ask in the PR comments

We're a small team (~1 hour/month maintenance), so we appreciate your patience!

## Code Standards

We use `ruff` for linting and formatting. Install pre-commit hooks to have these run automatically on every commit:

```bash
uv run pre-commit install
```

The hooks handle: trailing whitespace, YAML/TOML validation, merge conflict detection, Python syntax upgrades (`pyupgrade`), and `ruff` linting and formatting. You won't need to run `ruff` manually if pre-commit is installed.

> **Note:** This repository relies on [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning) to detect accidentally committed credentials. No local setup required — it runs automatically on every push.

## Testing

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_cli_misc.py

# Run with coverage
uv run pytest --cov=schemachange
```

## Need Help?

- **Questions?** [Ask in Discussions](https://github.com/Snowflake-Labs/schemachange/discussions/categories/q-a)
- **Found a bug?** [Open an issue](https://github.com/Snowflake-Labs/schemachange/issues/new/choose)
- **Confused?** Check the [README](../README.md) or [Troubleshooting Guide](../TROUBLESHOOTING.md)

## Community Guidelines

- Be respectful and constructive
- Focus PRs on one issue at a time
- Ask questions early if anything is unclear

That's all you need to know! Thanks for contributing to schemachange!

## Maintainer: Release Checklist

Before tagging a release from an `rc*` branch:

1. **Upgrade the lockfile** to pick up transitive dependency security fixes:
   ```bash
   uv lock --upgrade
   uv run pytest
   ```
   Commit the updated `uv.lock` if anything changed.

2. **Check Dependabot alerts** at `https://github.com/Snowflake-Labs/schemachange/security/dependabot` — confirm all high/critical open alerts are resolved in the new lockfile.

3. **Bump the version** in `pyproject.toml` and `setup.cfg`.

4. **Update `CHANGELOG.md`** with the release date and a summary of changes.

5. **Open a PR** from the `rc*` branch into `master`, merge, then tag the release.
