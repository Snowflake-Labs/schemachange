# Roadmap Issue Template

Use this template to create a pinned issue that serves as your public roadmap.

---

## How to Create

1. Go to: https://github.com/Snowflake-Labs/schemachange/issues/new
2. Title: `📍 Roadmap: Path to 5.0.0`
3. Copy content below
4. After creating, pin it: Right sidebar → "Pin issue"
5. Update monthly (takes 5 minutes)

---

## Template Content

```markdown
# 🗺️ schemachange Roadmap

> **Last updated:** [DATE]
>
> This is our development roadmap through 5.0.0. Dates are tentative and may shift based on community feedback and maintainer availability.

## 📊 How We Plan

We use **[Milestones](https://github.com/Snowflake-Labs/schemachange/milestones)** to track releases and **[Labels](https://github.com/Snowflake-Labs/schemachange/labels)** to categorize issues.

- **Milestones** show our release schedule and what's committed
- **Labels** like `target: 4.x.0`, `priority: high`, `enhancement` help with planning
- **This issue** provides a human-readable summary

---

## 🚀 Current Release: 4.2.0

**Target Date:** December 15, 2025 (Monday)

**Focus:** Stabilization based on 4.1.0 feedback

**Status:** [View Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/1)

### Key Themes
- Bug fixes from 4.1.0 adoption
- Performance improvements
- Documentation updates
- No breaking changes

### Notable Items
- [ ] #326 - Error during initial deploy with dry-run
- [ ] [Add your issues here]

---

## ⏭️ Next: 4.3.0 - Connector Upgrade

**Target Date:** January 13, 2026 (Monday)

**Focus:** Connector upgrade and enhancement evaluation

**Status:** [View Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/2)

### Key Themes
- Upgrade snowflake-connector-python to 4.0+
- Evaluate pending enhancement requests
- Performance testing with new connector
- No breaking changes

### Looking for Contributors
- [ ] #363 - Help test connector 4.0 upgrade
- [ ] Research: Impact on existing deployments

---

## 🔮 Future Releases

### 4.4.0 - Performance & Features
**Target:** February 15, 2026

Focus on performance and feature enhancements.

- Script loading optimizations
- New configuration options
- User experience improvements

[View Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/3)

---

### 4.5.0 - Pre-5.0 Foundation
**Target:** March 15, 2026

Foundation work for 5.0, fully backwards compatible.

- Hook system research (pre/post deployment scripts)
- API improvements (non-breaking)
- Deprecation warnings for 5.0 changes

[View Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/4)

---

### 5.0.0 - Major Release ⚠️
**Target:** June 1, 2026

Our next major release with breaking changes.

**Breaking Changes:**
- Python 3.10+ minimum (dropping 3.8, 3.9 support)
- Hook system implementation
- Configuration file format improvements
- CLI command restructuring

**New Features:**
- Pre/post deployment hooks
- Improved dry-run output
- Better transaction handling

[View Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/5)

📖 Migration guide will be published 4 weeks before release.

---

## 💡 Backlog & Future Ideas

Items not yet assigned to a release: [View "Future" Milestone →](https://github.com/Snowflake-Labs/schemachange/milestone/6)

Some ideas we're considering:
- Integration with dbt
- Support for Snowflake Git integration
- Rollback/revert capabilities
- Multi-database deployments

Have an idea? [Open a feature request](https://github.com/Snowflake-Labs/schemachange/issues/new?labels=enhancement&template=feature_request.md)!

---

## 🎯 Release Cadence

- **Minor releases (4.x.0):** ~4 weeks apart, mid-month on Mondays
- **Patch releases (4.x.Y):** As needed for critical bugs
- **Major releases (X.0.0):** Once per year

All dates are tentative and may shift based on:
- Community feedback and bug reports
- Maintainer availability (~1 hour/month)
- Complexity of planned features

---

## 📈 How to Track Progress

### For Users
- ⭐ **Star this issue** to get notifications on updates
- 📊 **Check [Milestones](https://github.com/Snowflake-Labs/schemachange/milestones)** for live progress
- 💬 **Join [Discussions](https://github.com/Snowflake-Labs/schemachange/discussions)** to share feedback

### For Contributors
- 🏷️ Look for issues tagged [`good first issue`](https://github.com/Snowflake-Labs/schemachange/labels/good%20first%20issue)
- 🤝 See our [Contributing Guide](.github/CONTRIBUTING.md)
- 💡 Comment on issues to express interest or ask questions

---

## ℹ️ About This Roadmap

**Maintainer time:** We're a small team with ~1 hour/month. Dates may shift.

**Community input:** We prioritize based on:
- Issue upvotes (👍 reactions)
- Real-world impact
- Alignment with project vision
- Maintainability

**Transparency:** This roadmap is updated monthly. If we need to adjust dates or scope, we'll communicate here and in the milestone pages.

---

## 🙋 Questions?

- **General questions:** [GitHub Discussions](https://github.com/Snowflake-Labs/schemachange/discussions)
- **Specific features:** Comment on the relevant issue
- **This roadmap:** Comment below!

---

_Last updated by @[MAINTAINER] on [DATE]_
```

---

## Maintenance Schedule

**Monthly update (5 minutes):**
1. Update "Last updated" date at top
2. Move completed items to checkmark (✅)
3. Update progress percentages from milestones
4. Add any new notable items
5. Adjust dates if needed (be transparent)

**After each release:**
1. Move "Next" to "Current"
2. Promote next release
3. Update milestone links
4. Add release notes link

---

## Pro Tips

### Tip 1: Use GitHub's Auto-Update
Enable "Subscribe" on this issue to get notified of all comments.

### Tip 2: Link from README
Add this to your main README.md:
```markdown
📍 **Roadmap:** See our [development roadmap](https://github.com/Snowflake-Labs/schemachange/issues/XXX) for planned releases.
```

### Tip 3: Reference in PRs
When merging PRs, reference the roadmap:
```markdown
Closes #123

Part of 4.3.0 roadmap: See #XXX (roadmap issue)
```

### Tip 4: Community Engagement
Ask for input in the roadmap issue:
```markdown
## 🗳️ What should we prioritize?

React with 👍 to the features you want most:
- 👍 Hook system
- 👍 dbt integration
- 👍 Rollback capabilities

Comment with your use case!
```

---

## Alternative: GitHub Discussion

Instead of an issue, you can create a **pinned Discussion** in the "Announcements" category:

**Pros:**
- Better for ongoing conversation
- Can mark best answers
- Cleaner for long-term tracking

**Cons:**
- Can't assign to milestones
- Slightly less discoverable

**Create at:** https://github.com/Snowflake-Labs/schemachange/discussions/new?category=announcements

Use the same template above!
