# Milestone Setup Guide

## Current Milestones

### Active Releases

#### 4.2.0 - Stabilization Release
- **Due Date:** December 15, 2025 (Monday)
- **Description:**
  ```
  Focus: Stability improvements based on 4.1.0 feedback

  Key themes:
  - Bug fixes from 4.1.0 adoption
  - Performance improvements
  - Documentation updates

  See CHANGELOG.md for detailed scope.
  ```

#### 4.3.0 - Connector Upgrade
- **Due Date:** January 13, 2026 (Monday)
- **Description:**
  ```
  Focus: Connector upgrade and enhancement evaluation

  Key themes:
  - Upgrade snowflake-connector-python to 4.0+
  - Evaluate pending enhancement requests
  - Performance testing with new connector

  Breaking changes: None planned
  ```

#### 4.4.0 - Performance & Features
- **Due Date:** February 15, 2026 (Sunday - close to mid-month)
- **Description:**
  ```
  Focus: Performance improvements and feature enhancements

  Key themes:
  - Script loading optimizations
  - New configuration options
  - User experience improvements

  Breaking changes: None planned
  ```

#### 4.5.0 - Pre-5.0 Foundation
- **Due Date:** March 15, 2026 (Sunday - close to mid-month)
- **Description:**
  ```
  Focus: Foundation for 5.0.0

  Key themes:
  - Hook system research (pre/post deployment)
  - API improvements (backwards compatible)
  - Deprecation warnings for 5.0 changes

  Breaking changes: None planned
  ```

#### 5.0.0 - Major Release
- **Due Date:** June 1, 2026 (Monday)
- **Description:**
  ```
  Focus: Major architectural improvements

  Key themes:
  - Hook system implementation
  - Configuration file format improvements
  - Python 3.10+ minimum (drop 3.8, 3.9)
  - CLI command restructuring

  ⚠️ Breaking changes: Yes (see migration guide)
  ```

### Long-term Planning

#### Future / Backlog
- **Due Date:** None (rolling)
- **Description:**
  ```
  Ideas and requests not yet assigned to a release.

  Use this milestone for:
  - Good ideas that need more research
  - Features that don't fit current roadmap
  - Community requests under consideration
  ```

---

## Creating Milestones via GitHub CLI

### Quick Setup

```bash
# Set repository context
cd /path/to/schemachange

# Note: Use GitHub API since gh milestone command may not be available
# Create 4.2.0 (if not exists)
gh api repos/Snowflake-Labs/schemachange/milestones \
  -f title="4.2.0" \
  -f due_on="2025-12-15T08:00:00Z" \
  -f description="Stabilization release based on 4.1.0 feedback. Focus: bug fixes, performance, documentation."

# Create 4.3.0
gh api repos/Snowflake-Labs/schemachange/milestones \
  -f title="4.3.0" \
  -f due_on="2026-01-13T08:00:00Z" \
  -f description="Connector upgrade and enhancement evaluation. Focus: snowflake-connector-python 4.0+, enhancement requests, performance testing."

# Create 4.4.0
gh api repos/Snowflake-Labs/schemachange/milestones \
  -f title="4.4.0" \
  -f due_on="2026-02-15T08:00:00Z" \
  -f description="Performance and feature enhancements. Focus: optimize script loading, new configuration options, UX improvements."

# Create 4.5.0
gh api repos/Snowflake-Labs/schemachange/milestones \
  -f title="4.5.0" \
  -f due_on="2026-03-15T08:00:00Z" \
  -f description="Pre-5.0 foundation. Focus: hook system research, API improvements, deprecation warnings for 5.0 changes."

# Create 5.0.0
gh api repos/Snowflake-Labs/schemachange/milestones \
  -f title="5.0.0" \
  -f due_on="2026-06-01T08:00:00Z" \
  -f description="Major release with breaking changes. Focus: hook system, configuration improvements, Python 3.10+, CLI restructuring."

# Create Future/Backlog
gh milestone create "Future" \
  --description "Ideas and requests not yet assigned to a release. Use for community requests under consideration."
```

### Verify Milestones

```bash
# List all milestones
gh milestone list

# View milestone details
gh milestone view "4.2.0"
```

---

## Assigning Issues to Milestones

### Via GitHub CLI

```bash
# Assign single issue
gh issue edit 309 --milestone "4.2.0"

# Assign multiple issues (bash loop)
for issue in 309 310 311; do
  gh issue edit $issue --milestone "4.2.0"
done

# Assign all issues with a label to milestone
gh issue list --label "target: 4.2.0" --limit 100 --json number --jq '.[].number' | \
  xargs -I {} gh issue edit {} --milestone "4.2.0"
```

### Via GitHub Web UI

1. Go to issue page
2. Right sidebar → "Milestone"
3. Select from dropdown
4. Auto-saves

### Bulk Assignment

1. Go to **Issues** tab
2. Select multiple issues (checkboxes)
3. Click "Milestone" dropdown at top
4. Choose milestone
5. All selected issues updated

---

## Milestone Workflow

### Weekly Review (5 minutes)

```bash
# View current milestone progress
gh milestone view "4.2.0"

# List open issues in milestone
gh issue list --milestone "4.2.0" --state open

# List PRs in milestone
gh pr list --milestone "4.2.0"
```

### Monthly Planning (15 minutes)

```bash
# Review next milestone
gh milestone view "4.3.0"

# Move issues if needed
gh issue edit 123 --milestone "4.3.0"  # Move from 4.2.0 to 4.3.0

# Unassign issues that won't make it
gh issue edit 456 --milestone "Future"
```

### Release Day

```bash
# Check milestone completion
gh milestone view "4.2.0"

# Close milestone (via web UI after release)
# Or leave open if tracking post-release bugs
```

---

## Milestone + Label Strategy

### Recommended Workflow

Use **both** milestones and labels for maximum flexibility:

| Purpose | Tool | Example |
|---------|------|---------|
| Release tracking | Milestone | `4.2.0` |
| Target intent | Label | `target: 4.2.0` |
| Priority | Label | `priority: high` |
| Type | Label | `enhancement` |
| Status | Label | `status: in-progress` |

### Why Both?

- **Milestone = commitment**: "This will be in 4.2.0"
- **Label = intention**: "We want this in 4.2.0, but might slip"

### Workflow Example

```bash
# New feature request comes in
# Step 1: Add labels for triage
gh issue edit 123 --add-label "enhancement,target: 4.3.0,priority: medium"

# Step 2: After discussion, commit to milestone
gh issue edit 123 --milestone "4.3.0"

# Step 3: Mark in progress
gh issue edit 123 --add-label "status: in-progress"

# Step 4: If slips, update both
gh issue edit 123 --milestone "4.4.0"
gh issue edit 123 --remove-label "target: 4.3.0" --add-label "target: 4.4.0"
```

---

## Viewing & Filtering

### GitHub Web UI

**View by Milestone:**
- Issues tab → Filter: `is:open milestone:4.2.0`
- Issues tab → Filter: `is:closed milestone:4.2.0` (completed work)

**View by Label:**
- Issues tab → Click any label (e.g., `target: 4.2.0`)
- Combine: `is:open label:"target: 4.2.0" label:"priority: high"`

**Saved Searches (Bookmark These):**
```
# Critical items
is:open label:"priority: critical"

# Current release (4.2.0)
is:open milestone:4.2.0 sort:updated-desc

# Community PRs
is:open is:pr label:"community-contribution"

# Needs triage
is:open label:"status: needs-triage"

# Blocked items
is:open label:"status: blocked"
```

### GitHub CLI

```bash
# All issues in milestone
gh issue list --milestone "4.2.0"

# High priority in milestone
gh issue list --milestone "4.2.0" --label "priority: high"

# Community contributions
gh pr list --label "community-contribution"

# Export to CSV for analysis
gh issue list --milestone "4.2.0" --json number,title,labels,assignees --jq '.[] | [.number, .title, (.labels | map(.name) | join(",")), (.assignees | map(.login) | join(","))] | @csv'
```

---

## Alternative: Pinned Issues as "Project Board"

Create a pinned issue as your roadmap dashboard:

### Example: Roadmap Issue

Create issue titled: **"📍 Roadmap: Path to 5.0.0"**

Content:
```markdown
## 🗺️ schemachange Roadmap

Last updated: 2024-11-15

### 🚀 Current Release: 4.2.0 (Dec 16, 2024)

**Progress:** [View milestone](https://github.com/Snowflake-Labs/schemachange/milestone/1)

**Key items:**
- [ ] #309 - Fix logging issue
- [ ] #310 - Performance improvement
- [x] #311 - Documentation update

### ⏭️ Next: 4.3.0 (Jan 13, 2025)

**Focus:** Enhanced logging

[View milestone](https://github.com/Snowflake-Labs/schemachange/milestone/2)

### Future Releases

- **4.4.0** (Feb 10): Performance & Scalability
- **4.5.0** (Mar 10): Pre-5.0 Features
- **5.0.0** (Apr 14): Major Release

[View all milestones](https://github.com/Snowflake-Labs/schemachange/milestones)
```

**Pin this issue:**
1. Create issue
2. Right sidebar → "Pin issue"
3. Appears at top of Issues tab for everyone

**Update monthly** - takes 2 minutes

---

## Tips & Tricks

### Tip 1: Milestone Templates

Save descriptions in a file for consistency:

```bash
# Create template file
cat > docs/maintainers/MILESTONE_TEMPLATES.md << 'EOF'
# Copy-paste these when creating milestones

## Minor Release (4.x.0)
Focus: [One sentence theme]

Key themes:
- Theme 1
- Theme 2
- Theme 3

Breaking changes: None planned

## Major Release (5.0.0)
Focus: [Major theme]

Key themes:
- Major feature 1
- Major feature 2
- Major improvement 3

⚠️ Breaking changes: Yes (see migration guide)
EOF
```

### Tip 2: Bulk Operations

```bash
# Move all "target: 4.2.0" issues to milestone
gh issue list --label "target: 4.2.0" --limit 100 --json number --jq '.[].number' | \
  while read issue; do
    echo "Assigning #$issue to milestone 4.2.0"
    gh issue edit $issue --milestone "4.2.0"
  done
```

### Tip 3: Release Automation

When you create a release tag, reference the milestone:

```bash
# Tag release
git tag -a v4.2.0 -m "Release 4.2.0 - See milestone for details"

# In release notes, link milestone
gh release create v4.2.0 --notes "
## What's Changed

See full details in [Milestone 4.2.0](https://github.com/Snowflake-Labs/schemachange/milestone/1?closed=1)

## Install

\`\`\`bash
pip install schemachange==4.2.0
\`\`\`
"
```

### Tip 4: Milestone Dashboard Script

Create a quick status script:

```bash
#!/bin/bash
# docs/maintainers/scripts/milestone-status.sh

echo "📊 Milestone Status Report"
echo "=========================="
echo ""

for milestone in "4.2.0" "4.3.0" "4.4.0"; do
  echo "## $milestone"
  gh milestone view "$milestone" 2>/dev/null || echo "Not found"
  echo ""
done
```

---

## Summary: Your Workflow Without Projects

| Task | Tool | Time |
|------|------|------|
| **Plan releases** | Create milestones | 10 min/release |
| **Triage issues** | Add labels | 30 sec/issue |
| **Assign to release** | Set milestone | 10 sec/issue |
| **Track progress** | View milestone | 2 min/week |
| **Communicate** | Pinned issue or Discussion | 5 min/month |
| **Release** | Close milestone, create tag | 5 min/release |

**Total maintenance:** ~30 minutes/month ✅

---

## Next Steps

1. Create milestones (see commands above)
2. Assign existing issues to milestones
3. Create pinned roadmap issue (optional)
4. Bookmark milestone URLs
5. Set monthly calendar reminder: "Review milestones"

This gives you 90% of what Projects provides, with zero permission hassles! 🚀
