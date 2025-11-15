# schemachange Documentation

This folder contains documentation for different audiences.

## For Users

User-facing documentation is in the repository root:

- [README.md](../README.md) - Getting started guide
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Common issues and solutions
- [SECURITY.md](../SECURITY.md) - Authentication methods and security best practices
- [CHANGELOG.md](../CHANGELOG.md) - Version history and release notes

## For Contributors

Contributor documentation:

- [CONTRIBUTING.md](../.github/CONTRIBUTING.md) - How to contribute code
- [Issue Templates](../.github/ISSUE_TEMPLATE/) - Report bugs or request features
- [PR Template](../.github/PULL_REQUEST_TEMPLATE.md) - Submit pull requests

## For Maintainers

Internal maintainer documentation in [`maintainers/`](maintainers/):

- [REPOSITORY_ECOSYSTEM.md](maintainers/REPOSITORY_ECOSYSTEM.md) - How everything works together
- [PROJECT_SETUP.md](maintainers/PROJECT_SETUP.md) - Setting up GitHub Projects
- [DISCUSSION_CATEGORIES.md](maintainers/DISCUSSION_CATEGORIES.md) - Setting up Discussions
- [DISCUSSION_TEMPLATES/](maintainers/DISCUSSION_TEMPLATES/) - Templates for pinned discussions

---

**Note:** This folder structure separates concerns:
- `/` (root) - User documentation
- `/.github/` - GitHub-required files (workflows, templates)
- `/docs/` - Organized documentation by audience
- `/experiments/` - Temporary/untracked work products (in .gitignore)
