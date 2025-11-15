# Quick Start: Complete Repository Setup

**Current status:** November 15, 2025

You're almost there! Here's what's done and what remains.

---

## ✅ Already Complete

### Milestones Created
- 4.2.0 (Dec 15, 2025) - 0 issues assigned
- 4.3.0 (Jan 13, 2026) - 0 issues assigned
- 4.4.0 (Feb 15, 2026) - 0 issues assigned
- 4.5.0 (Mar 15, 2026) - 0 issues assigned
- 5.0.0 (Jun 1, 2026) - 0 issues assigned

### Automation
- Auto-label new issues
- Auto-label PRs by files changed
- Welcome community contributors
- Remove "awaiting-response" when author responds
- Close stale items (60+ days)

### Documentation
- Contributing guide
- Issue templates
- PR template
- Maintainer guides (comprehensive!)

---

## 📋 Remaining Tasks (30 minutes)

### 1. Assign Issues to Milestones (15 min)

You have **63 open issues** with no milestones. Here's a quick approach:

```bash
# View all issues
gh issue list --limit 100 --json number,title,labels

# Quick assignment strategy:
# - Bugs → 4.2.0 (stabilization)
# - Connector upgrade → 4.3.0
# - Enhancements → 4.4.0 or Future
# - Questions → Close, point to Discussions
```

**Example assignments:**
```bash
# Bug fixes for 4.2.0
gh issue edit 326 --milestone "4.2.0"

# Connector upgrade for 4.3.0
gh issue edit 363 --milestone "4.3.0"

# Enhancement requests for future
gh issue edit 347 --milestone "Future"
gh issue edit 349 --milestone "Future"

# Questions - close and redirect
gh issue close 348 --reason "answered" --comment "Thanks! For questions like this, please use GitHub Discussions Q&A: https://github.com/Snowflake-Labs/schemachange/discussions/categories/q-a"
```

**Bulk approach:**
```bash
# List all bugs
gh issue list --label "bug" --json number,title

# Assign all bugs to 4.2.0
gh issue list --label "bug" --json number --jq '.[].number' | \
  while read issue; do
    echo "Assigning #$issue to 4.2.0"
    gh issue edit $issue --milestone "4.2.0"
  done
```

---

### 2. Create Public Roadmap (10 min)

**Option A: Pinned Issue** (Recommended)

1. Go to: https://github.com/Snowflake-Labs/schemachange/issues/new
2. Title: `📍 Roadmap: Path to 5.0.0`
3. Copy template from: `docs/maintainers/ROADMAP_ISSUE_TEMPLATE.md`
4. Paste, customize if needed
5. Create issue
6. Pin it: Right sidebar → "Pin issue"

**Option B: Pinned Discussion**

1. Go to: https://github.com/Snowflake-Labs/schemachange/discussions/new?category=announcements
2. Title: `🗺️ Development Roadmap`
3. Use same template
4. Create and pin

---

### 3. Configure Discussions (5 min)

Check if categories are set up:
https://github.com/Snowflake-Labs/schemachange/discussions

**Recommended categories:**
- 📢 Announcements (maintainers only)
- 💡 Ideas (feature requests)
- 🙏 Q&A (questions)
- 💬 General (community chat)

If not set up, see: `docs/maintainers/DISCUSSION_CATEGORIES.md`

---

## 🎯 After Setup (Ongoing)

### Weekly Routine (15 min)

```bash
# Monday mornings

# 1. Check current release (2 min)
gh api repos/Snowflake-Labs/schemachange/milestones/1 | \
  jq '{title, due_on, open_issues, closed_issues}'

# 2. Triage new issues (5 min)
gh issue list --label "status: needs-triage" --limit 10
# Add milestone + priority to each

# 3. Review community PRs (5 min)
gh pr list --label "community-contribution"

# 4. Check critical items (3 min)
gh issue list --label "priority: critical"
```

### Monthly Routine (10 min)

```bash
# First Monday of month

# 1. Review all milestones (5 min)
gh api repos/Snowflake-Labs/schemachange/milestones | \
  jq -r '.[] | "\(.title): \(.open_issues) open, due \(.due_on)"'

# 2. Update roadmap issue (5 min)
# - Update progress
# - Move completed items to ✅
# - Adjust dates if needed
```

---

## 📖 Key Documents

**Read these in order:**

1. **[REPOSITORY_ECOSYSTEM.md](REPOSITORY_ECOSYSTEM.md)** - How everything works
2. **[GITHUB_MANAGEMENT_WITHOUT_PROJECTS.md](GITHUB_MANAGEMENT_WITHOUT_PROJECTS.md)** - Complete guide
3. **[MILESTONE_SETUP.md](MILESTONE_SETUP.md)** - Milestone details
4. **[ROADMAP_ISSUE_TEMPLATE.md](ROADMAP_ISSUE_TEMPLATE.md)** - Public communication

---

## 🔗 Bookmarks

Save these:

```
Milestones:
https://github.com/Snowflake-Labs/schemachange/milestones

Current Release (4.2.0):
https://github.com/Snowflake-Labs/schemachange/milestone/1

All Issues:
https://github.com/Snowflake-Labs/schemachange/issues

Critical Issues:
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22priority%3A+critical%22

Community PRs:
https://github.com/Snowflake-Labs/schemachange/pulls?q=is%3Aopen+label%3Acommunity-contribution

Needs Triage:
https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22status%3A+needs-triage%22

Discussions:
https://github.com/Snowflake-Labs/schemachange/discussions
```

---

## ✅ Success Criteria

After completing the 3 remaining tasks, you'll have:

- ✅ All issues assigned to milestones
- ✅ Public roadmap visible to community
- ✅ Discussions configured for questions
- ✅ Clear progress tracking
- ✅ ~30 min/month maintenance

---

## 💡 Tips

**Keep it simple:**
- Don't over-triage. "Future" milestone is fine for most things.
- Focus on 4.2.0 (current release) first.
- Let automation handle routine tasks.

**Stay human:**
- Brief, direct comments on issues
- Set realistic expectations (2-4 weeks for PR reviews)
- It's okay to say "not planned" and close things

**Avoid bloat:**
- Don't create extra documents
- Use issue/PR comments for decisions
- Keep docs updated, not duplicated

---

## 🚀 Ready?

Pick a task:
1. **Assign issues** (most important)
2. **Create roadmap** (most visible)
3. **Set up discussions** (reduces noise)

Or just do them in order - takes 30 minutes total!
