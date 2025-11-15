# 🗺️ schemachange Roadmap

**Last updated:** November 2025

This is a living roadmap showing planned releases and priorities. Dates and scope may change based on community feedback.

---

## 📅 Upcoming Releases (Mid-Month Mondays)

### 🚀 4.2.0 (December 15, 2025) - Stability & UX
**Status:** Ready for release

**What's included:**
- ✅ YAML validation improvements (#352)
- ✅ Dry-run bug fix (#356, fixes #326)
- ✅ Enhanced documentation and migration guide
- ✅ Authentication examples (JWT, OAuth, PAT, SSO)

[View 4.2.0 Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/X)

---

### 🔄 4.3.0 (January 13, 2026) - Connector Upgrade
**Status:** Planning

**What's planned:**
- Snowflake Connector Python 4.0.0 upgrade (#363)
- Community PR evaluation and inclusion
- Documentation enhancements

**Help wanted:**
- Testing connector upgrade compatibility
- Community PR reviews

[View 4.3.0 Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/X)

---

### 🌟 4.4.0 (February 16, 2026) - Community Enhancements
**Status:** Open for proposals

**What's planned:**
- Community-contributed features
- Configuration improvements
- Best practices documentation

**Propose features:** [Start a Discussion →](https://github.com/Snowflake-Labs/schemachange/discussions/categories/ideas)

---

### 🛠️ 4.5.0 (March 16, 2026) - Pre-5.0 Stabilization
**Status:** Planning

**What's planned:**
- Final features before 5.0.0 breaking changes
- Enhanced deprecation warnings for 5.0.0
- Migration guide preparation

---

### 💥 5.0.0 (April 13, 2026) - Breaking Changes
**Status:** Scoped

**What's included:**
- Remove deprecations from 4.1.0 release
- Clean API surface
- NO new features (stability focus)

**Breaking changes:**
- Deprecated CLI arguments removed
- Deprecated environment variables removed
- Old parameter names removed

**Migration guide:** Will be available in 4.5.0 release

---

## 🎯 How Releases Work

- **Cadence:** Mid-month Mondays, ~4 weeks apart
- **Scope:** Small, incremental improvements
- **Testing:** Comprehensive CI/CD before each release
- **Breaking changes:** Only in major versions (5.0, 6.0, etc.)

---

## 🗳️ How to Influence the Roadmap

### 1. Vote on existing issues
Use 👍 reactions on issues you care about. We track this!

### 2. Propose new features
[Start a Discussion in Ideas →](https://github.com/Snowflake-Labs/schemachange/discussions/categories/ideas)

Discuss first, then create an issue if there's support.

### 3. Contribute!
We prioritize features that come with:
- Pull requests with tests
- Clear documentation
- Maintainable code

See [Contributing Guide](../CONTRIBUTING.md)

### 4. Report bugs
[Create a bug report →](https://github.com/Snowflake-Labs/schemachange/issues/new/choose)

Critical bugs get fast-tracked!

---

## 📊 Prioritization Criteria

We prioritize based on:
1. **Impact:** How many users does this help?
2. **Contribution:** Is there a PR ready?
3. **Maintenance:** Can we maintain it long-term?
4. **Alignment:** Does it fit schemachange's purpose?

---

## 🔮 Beyond 5.0.0 (Future Considerations)

These are being discussed but not yet scheduled:
- Multithreaded execution (#347)
- Change history table improvements (#348)
- Enhanced Jinja capabilities
- Additional authentication methods

---

## 📈 View the Full Project Board

See all issues and PRs organized by release:
[schemachange Roadmap Project →](https://github.com/orgs/Snowflake-Labs/projects/X)

---

**Questions?** Ask in [General Discussions](https://github.com/Snowflake-Labs/schemachange/discussions/categories/general)

**Want to contribute?** See our [Contributing Guide](../CONTRIBUTING.md)
