# Managing schemachange Without GitHub Projects

You don't need GitHub Projects! Here's your complete toolkit for low-maintenance repository management.

---

## 🎯 Your Stack

| Tool | Purpose | Maintenance | Power |
|------|---------|-------------|-------|
| **Milestones** | Release tracking | 5 min/month | ⭐⭐⭐⭐⭐ |
| **Labels** | Categorization | 30 sec/issue | ⭐⭐⭐⭐⭐ |
| **GitHub Actions** | Automation | One-time setup | ⭐⭐⭐⭐⭐ |
| **Issue Templates** | Quality control | Zero maintenance | ⭐⭐⭐⭐ |
| **Pinned Issues** | Communication | 5 min/month | ⭐⭐⭐⭐ |
| **GitHub CLI** | Bulk operations | As needed | ⭐⭐⭐⭐⭐ |

**Total maintenance:** ~30 minutes/month

---

## 🚀 Quick Start (30 minutes)

### Step 1: Verify Milestones (2 min)

Milestones are already created! Verify them:

```bash
cd /path/to/schemachange
./docs/maintainers/scripts/setup-milestones.sh
```

Your milestones:
- ✅ 4.2.0 (Dec 15, 2025) - Current release
- ✅ 4.3.0 (Jan 13, 2026) - Connector upgrade
- ✅ 4.4.0 (Feb 15, 2026) - Performance & features
- ✅ 4.5.0 (Mar 15, 2026) - Pre-5.0 foundation
- ✅ 5.0.0 (Jun 1, 2026) - Major release

**Verify:**
```bash
gh milestone list
```

---

### Step 2: Assign Existing Issues (10 min)

**Option A: Bulk assign by label**
```bash
# All "target: 4.2.0" issues → 4.2.0 milestone
gh issue list --label "target: 4.2.0" --limit 100 --json number --jq '.[].number' | \
  while read issue; do
    gh issue edit $issue --milestone "4.2.0"
  done
```

**Option B: Manual triage**
```bash
# List unlabeled issues
gh issue list --limit 20

# Assign one by one
gh issue edit 309 --milestone "4.2.0" --add-label "priority: high,enhancement"
gh issue edit 310 --milestone "4.3.0" --add-label "priority: medium,bug"
```

**Verify:**
```bash
gh milestone view "4.2.0"
```

---

### Step 3: Create Public Roadmap (10 min)

**Option A: Pinned Issue (Recommended)**

1. Create issue: https://github.com/Snowflake-Labs/schemachange/issues/new
2. Title: `📍 Roadmap: Path to 5.0.0`
3. Copy content from: `docs/maintainers/ROADMAP_ISSUE_TEMPLATE.md`
4. After creating: Right sidebar → "Pin issue"
5. Done!

**Option B: Pinned Discussion**

1. Create discussion: https://github.com/Snowflake-Labs/schemachange/discussions/new?category=announcements
2. Title: `🗺️ Development Roadmap: Path to 5.0.0`
3. Use same template
4. Pin it

---

## 📊 Daily/Weekly/Monthly Workflows

### Daily: Issue Triage (2 min)

New issue comes in → Your automation handles it:

```
✅ Auto-labeled: "status: needs-triage"
✅ Auto-added to discussion if it's a question
✅ Auto-labeled by file changes if it's a PR
```

**You just need to:**
```bash
# Review new issues
gh issue list --label "status: needs-triage" --limit 5

# Add milestone + priority
gh issue edit 123 --milestone "4.3.0" --add-label "priority: high"

# Or defer
gh issue edit 124 --milestone "Future" --add-label "priority: low"
```

**2 minutes, done!**

---

### Weekly: Progress Check (5 min)

```bash
# Current release progress
gh milestone view "4.2.0"

# What needs attention?
gh issue list --label "priority: critical"
gh issue list --label "status: blocked"

# Community PRs
gh pr list --label "community-contribution"
```

**Bookmark these URLs:**
```
Current milestone:
https://github.com/Snowflake-Labs/schemachange/milestone/1

Critical issues:
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22priority%3A+critical%22

Community PRs:
https://github.com/Snowflake-Labs/schemachange/pulls?q=is%3Aopen+label%3Acommunity-contribution
```

---

### Monthly: Roadmap Update (15 min)

```bash
# 1. Review all milestones (5 min)
for milestone in "4.2.0" "4.3.0" "4.4.0"; do
  echo "=== $milestone ==="
  gh milestone view "$milestone"
done

# 2. Adjust as needed (5 min)
# Move issues that won't make it
gh issue edit 125 --milestone "4.3.0"  # Slip from 4.2.0

# Add new issues to upcoming releases
gh issue edit 126 --milestone "4.3.0" --add-label "target: 4.3.0"

# 3. Update public roadmap (5 min)
# Edit your pinned issue with latest status
```

**Calendar reminder:** 1st Monday of each month

---

## 🔍 Powerful Queries (Bookmark These)

### View by Release

```bash
# Current release (4.2.0)
https://github.com/Snowflake-Labs/schemachange/milestone/1

# Or via CLI
gh issue list --milestone "4.2.0"
gh pr list --milestone "4.2.0"
```

### View by Priority

```bash
# Critical items
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22priority%3A+critical%22

# Or via CLI
gh issue list --label "priority: critical"
```

### View by Status

```bash
# Needs triage
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22status%3A+needs-triage%22

# Blocked
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22status%3A+blocked%22

# In progress
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22status%3A+in-progress%22
```

### Community Contributions

```bash
# All community PRs
https://github.com/Snowflake-Labs/schemachange/pulls?q=is%3Aopen+label%3Acommunity-contribution

# New contributors (first PR)
https://github.com/Snowflake-Labs/schemachange/pulls?q=is%3Aopen+label%3Afirst-time-contributor
```

### Complex Queries

```bash
# High priority bugs in current release
gh issue list --milestone "4.2.0" --label "bug,priority: high"

# Enhancement requests from community
gh issue list --label "enhancement,community-contribution" --state open

# Stale items awaiting response
gh issue list --label "status: awaiting-response"
```

---

## 🤖 What Your Automation Does

You already have these workflows set up (zero maintenance):

### Auto-Labeling
- ✅ New issues → `status: needs-triage`
- ✅ Community PRs → `community-contribution`
- ✅ PRs by file → `type: docs`, `area: cli`, etc.

### Auto-Responses
- ✅ Community PRs → Welcome message with checklist
- ✅ Author responds → Remove `status: awaiting-response`

### Stale Management
- ✅ No response in 14 days → Warn
- ✅ No response in 30 days → Close (politely)

### What You Don't Need to Do
- ❌ Manually label issues
- ❌ Manually welcome contributors
- ❌ Manually close stale issues
- ❌ Manually track PR status

**The bots handle it!**

---

## 🎨 Visual Roadmap (Without Projects)

### Option 1: Milestone Page
GitHub's milestone page is actually quite visual:

**Link:** https://github.com/Snowflake-Labs/schemachange/milestones

Shows:
- ✅ Progress bars (X% complete)
- ✅ Open/closed counts
- ✅ Due dates
- ✅ Sorting by due date

**Bookmark this!** It's your project board.

### Option 2: Pinned Roadmap Issue
Your pinned issue provides a narrative view:
- Current sprint
- Next up
- Future releases
- Backlog

**Link:** (After you create it) `https://github.com/Snowflake-Labs/schemachange/issues/XXX`

### Option 3: Labels Page
Filter by target:

**Link:** https://github.com/Snowflake-Labs/schemachange/labels

Click `target: 4.2.0` to see all issues for that release.

---

## 📦 Release Day Workflow

When it's time to release 4.2.0:

```bash
# 1. Verify milestone completion
gh milestone view "4.2.0"

# 2. Create release branch (if using branching strategy)
git checkout -b rc4.2.0

# 3. Tag release
git tag -a v4.2.0 -m "Release 4.2.0"
git push origin v4.2.0

# 4. Create GitHub release
gh release create v4.2.0 \
  --title "v4.2.0 - Stabilization Release" \
  --notes-file CHANGELOG.md \
  --latest

# 5. Close milestone
gh milestone close "4.2.0"

# 6. Update roadmap issue
# Edit pinned issue: Move 4.3.0 to "Current", update dates

# 7. Celebrate! 🎉
```

---

## 💡 Pro Tips

### Tip 1: Use Saved Searches
Create browser bookmarks with custom queries:

```
Critical & Blocked:
/issues?q=is%3Aopen+(label%3A%22priority%3A+critical%22+OR+label%3A%22status%3A+blocked%22)

This Week's Work:
/issues?q=is%3Aopen+milestone%3A4.2.0+sort%3Aupdated-desc

Community Needs Review:
/pulls?q=is%3Aopen+label%3Acommunity-contribution+review%3Arequired
```

### Tip 2: Milestone Dashboard Script
Create a quick status script:

```bash
#!/bin/bash
# ~/scripts/schemachange-status.sh

cd /path/to/schemachange

echo "📊 schemachange Status"
echo "===================="
gh milestone view "4.2.0"
echo ""
echo "🚨 Critical Issues:"
gh issue list --label "priority: critical" --limit 5
echo ""
echo "🤝 Community PRs:"
gh pr list --label "community-contribution" --limit 5
```

Run it: `~/scripts/schemachange-status.sh`

### Tip 3: Calendar Integration
Add milestones to your calendar:

```
Dec 15, 2025 - Release 4.2.0
Jan 13, 2026 - Release 4.3.0
Feb 15, 2026 - Release 4.4.0
Mar 15, 2026 - Release 4.5.0
Jun 1, 2026  - Release 5.0.0
```

Set reminders 1 week before.

### Tip 4: Bulk Operations
Need to update many issues? Use loops:

```bash
# Add label to all issues in milestone
gh issue list --milestone "4.3.0" --limit 100 --json number --jq '.[].number' | \
  xargs -I {} gh issue edit {} --add-label "target: 4.3.0"

# Close all issues with specific label
gh issue list --label "wontfix" --state open --json number --jq '.[].number' | \
  xargs -I {} gh issue close {} --reason "not planned"
```

### Tip 5: Export for Reporting
Need to report to stakeholders?

```bash
# Export current milestone to CSV
gh issue list --milestone "4.2.0" --limit 100 \
  --json number,title,labels,state,assignees \
  --jq '.[] | [.number, .title, .state, (.labels | map(.name) | join(";")), (.assignees | map(.login) | join(";"))] | @csv' \
  > 4.2.0-status.csv
```

Open in Excel/Sheets for pretty charts!

---

## 🆚 Projects vs Your Setup

| Feature | GitHub Projects | Your Setup | Winner |
|---------|----------------|------------|---------|
| Visual board | ✅ Yes | ✅ Milestones page | Tie |
| Auto-update | ✅ Yes | ✅ Via labels | Tie |
| Custom fields | ✅ Yes | ✅ Via labels | Tie |
| Permissions needed | ❌ Org admin | ✅ Repo write | **You!** |
| Learning curve | ⚠️ Medium | ✅ Low | **You!** |
| Maintenance | ⚠️ Medium | ✅ Low | **You!** |
| Mobile app | ✅ Yes | ✅ GitHub app | Tie |
| API access | ✅ Yes | ✅ Yes | Tie |
| Community visibility | ✅ Yes | ✅ Yes | Tie |

**Conclusion:** Your setup is simpler and just as powerful!

---

## 🎓 Learning Resources

### GitHub Milestones
- Docs: https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones
- CLI: `gh milestone --help`

### GitHub Labels
- Docs: https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels
- CLI: `gh label --help`

### GitHub CLI
- Docs: https://cli.github.com/manual/
- Cheatsheet: https://github.com/github/gh-cli/blob/trunk/docs/gh.md

### Advanced Queries
- Docs: https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests
- Examples: https://github.com/search/advanced

---

## 🚀 Summary: You Have Everything You Need!

✅ **Milestones** = Your project board
✅ **Labels** = Your custom fields
✅ **Automation** = Reduces manual work
✅ **CLI** = Power user tools
✅ **Pinned issue** = Public roadmap
✅ **GitHub search** = Flexible views

**No Projects needed!**

---

## 📞 Questions?

- See: `docs/maintainers/MILESTONE_SETUP.md` for detailed milestone guide
- See: `docs/maintainers/ROADMAP_ISSUE_TEMPLATE.md` for communication template
- Run: `docs/maintainers/scripts/setup-milestones.sh` to get started

**You're all set! 🎉**
