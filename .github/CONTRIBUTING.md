# Contributing to schemachange

Thank you for your interest in contributing! This guide will get you started quickly.

## Quick Start

```bash
# 1. Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/schemachange.git
cd schemachange

# 2. Install dependencies
pip install -e .[dev]

# 3. Make your changes and run tests
pytest
ruff check .
```

That's it! Open a PR when ready.

## Finding Something to Work On

- **New to the project?** Look for [`good-first-issue`](https://github.com/Snowflake-Labs/schemachange/labels/good-first-issue)
- **Need help?** Ask in [Discussions](https://github.com/Snowflake-Labs/schemachange/discussions)
- **Have an idea?** Discuss it in [Ideas](https://github.com/Snowflake-Labs/schemachange/discussions/categories/ideas) first

## Submitting Changes

1. **Create a branch** from main: `git checkout -b fix-issue-123`
2. **Make your changes**
3. **Run tests**: `pytest && ruff check .`
4. **Commit**: Use clear commit messages
5. **Push** and create a Pull Request

### PR Guidelines

**Required:**
- Tests pass (`pytest`)
- Code is formatted (`ruff format .`)

**Helpful (but optional):**
- Add tests if you're adding functionality
- Update docs if you're changing behavior
- Update CHANGELOG.md (or we can do it)

**We'll help you with:**
- Code review feedback
- Test suggestions
- Documentation improvements

## What to Expect

- **Triage**: Within 2 business days
- **Review**: Within 2-4 weeks
- **Questions?** Just ask in the PR comments

We're a small team (~1 hour/month maintenance), so we appreciate your patience!

## Code Standards

We use `ruff` for linting and formatting. Install pre-commit hooks for automatic formatting:

```bash
pre-commit install
```

Now your code will be automatically formatted on commit!

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_cli_misc.py

# Run with coverage
pytest --cov=schemachange
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
