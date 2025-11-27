# GitHub Project Setup Guide

This guide shows how to set up a GitHub Project that auto-updates from your workflow automation.

## Quick Setup (15 minutes)

### 1. Create Project (2 min)

1. Go to your repo: https://github.com/Snowflake-Labs/schemachange
2. Click **Projects** tab
3. Click **New Project**
4. Choose **Table** template (not Board - easier for low maintenance)
5. Name it: `schemachange Roadmap`
6. Click **Create**

### 2. Configure Fields (3 min)

GitHub Projects comes with default fields. Keep these:
- **Title** (from issue/PR title)
- **Assignees** (from issue/PR)
- **Status** (from issue state: Open, Closed)
- **Labels** (from issue/PR labels)

Add these custom fields:

#### Field 1: Release Target
- Click **+** next to fields
- Field name: `Release Target`
- Field type: `Single select`
- Options (add these):
  - `4.2.0`
  - `4.3.0`
  - `4.4.0`
  - `4.5.0`
  - `5.0.0`
  - `Future`
  - `Next` (for items not yet assigned)

#### Field 2: Priority
- Field name: `Priority`
- Field type: `Single select`
- Options:
  - `Critical` (color: red)
  - `High` (color: orange)
  - `Medium` (color: yellow)
  - `Low` (color: green)
  - `None` (color: gray)

#### Field 3: Type
- Field name: `Type`
- Field type: `Single select`
- Options:
  - `Bug`
  - `Enhancement`
  - `Documentation`
  - `Breaking Change`
  - `Question`
  - `Dependencies`

### 3. Set Up Automation (5 min)

Click **⚙️ Settings** (top right) → **Workflows**

#### Workflow 1: Auto-add Items

Click **+ New workflow** → Choose **Item added to project**

Configure:
- **When**: Item is added
- **Then**: Do nothing (just auto-add)

Now configure the trigger:
- Click **Edit** on the trigger
- Change from "manually" to **Auto-add to project**
- Filter: Issues and pull requests with label matching `target:*` OR `priority: critical`

This means: Any issue/PR with a `target: X.X.X` label or `priority: critical` automatically gets added!

#### Workflow 2: Set Release Target from Label

Click **+ New workflow** → Choose **Item added to project**

Configure:
- **When**: Item is added to project
- **Then**: Set field `Release Target`
- **To**: Extract from label `target:` prefix

Example: If issue has label `target: 4.3.0`, set field to `4.3.0`

#### Workflow 3: Set Priority from Label

Click **+ New workflow** → Choose **Item added to project**

Configure:
- **When**: Item is added to project
- **Then**: Set field `Priority`
- **To**: Extract from label `priority:` prefix

Example: If issue has label `priority: high`, set field to `High`

#### Workflow 4: Set Type from Label

Click **+ New workflow** → Choose **Item added to project**

Configure:
- **When**: Item is added to project
- **Then**: Set field `Type`
- **To**: Map from labels:
  - `bug` → `Bug`
  - `enhancement` → `Enhancement`
  - `documentation` → `Documentation`
  - `breaking-change` → `Breaking Change`
  - `question` → `Question`
  - `dependencies` → `Dependencies`

### 4. Create Saved Views (5 min)

Views are filtered/sorted versions of your project. Create these:

#### View 1: Current Release (4.2.0)

1. Click **New view** → **Table**
2. Name: `📍 Current Release (4.2.0)`
3. Filter: `Release Target is 4.2.0`
4. Sort by: `Priority` (Critical first)
5. Group by: `Type`
6. Save view

#### View 2: Next Release (4.3.0)

1. New view → Table
2. Name: `🔜 Next Release (4.3.0)`
3. Filter: `Release Target is 4.3.0`
4. Sort by: `Priority`
5. Group by: `Type`
6. Save view

#### View 3: Roadmap (All Releases)

1. New view → **Board**
2. Name: `🗺️ Roadmap`
3. No filter (show all)
4. Group by: `Release Target`
5. Sort within groups: `Priority`
6. Save view

This creates columns: 4.2.0 | 4.3.0 | 4.4.0 | 4.5.0 | 5.0.0 | Future

#### View 4: Community Contributions

1. New view → Table
2. Name: `🤝 Community PRs`
3. Filter: Has label `community-contribution`
4. Sort by: `Updated` (newest first)
5. Save view

#### View 5: Critical & Blocked

1. New view → Table
2. Name: `🚨 Needs Attention`
3. Filter: `Priority is Critical` OR `Status contains blocked`
4. Sort by: `Updated` (newest first)
5. Save view

#### View 6: Active Work

1. New view → Table
2. Name: `⚡ In Progress`
3. Filter: `Status contains in-progress` OR `Status contains Development`
4. Sort by: `Updated`
5. Save view

### 5. Make Project Public

1. Click **⚙️ Settings**
2. Under **Visibility**, choose **Public**
3. Save

Now anyone can view your roadmap!

## How It Works in Practice

### Scenario 1: New Issue Created

1. User creates issue #123: "Add OAuth support"
2. **Auto-label-issues.yml** adds `status: needs-triage`
3. You triage and add labels:
   ```bash
   gh issue edit 123 --add-label "enhancement,target: 4.3.0,priority: high"
   ```
4. **Project automation detects** `target: 4.3.0` label
5. **Issue #123 automatically added** to project
6. **Fields auto-set**: Release Target = 4.3.0, Priority = High, Type = Enhancement
7. **Visible in views**: "Next Release (4.3.0)" and "Roadmap"

**Your effort:** 1 command to add labels
**Project updates:** Automatic

### Scenario 2: Community PR Submitted

1. Community member opens PR #125: "Fix bug in dry-run"
2. **auto-label-prs.yml** adds `community-contribution, status: needs-review`
3. You add more labels:
   ```bash
   gh pr edit 125 --add-label "bug,target: 4.2.0,priority: high"
   ```
4. **PR #125 auto-added** to project
5. **Fields auto-set** from labels
6. **Visible in**: "Current Release (4.2.0)" and "Community PRs" views

### Scenario 3: Release Complete

1. You merge rc4.2.0 branch to main
2. GitHub automatically closes all issues in 4.2.0 milestone
3. **Project automatically updates** Status to "Done"
4. **"Current Release" view** now shows all items as complete
5. You update the view to 4.3.0:
   - Edit view filter: `Release Target is 4.3.0`
   - Rename view: `📍 Current Release (4.3.0)`

**Your effort:** Update one filter, rename one view (2 minutes)
**All items:** Already there from automation

## Weekly Workflow with Project

Your weekly 15-minute workflow now has visual support:

```bash
# Open Project in browser
# View: "Needs Attention" (critical & blocked items)
# → Review critical issues first

# View: "Community PRs"
# → See all community contributions
gh pr list --label "status: needs-review"
gh pr review <number> --approve

# View: "Current Release"
# → See progress toward 4.2.0
# → Already filtered and sorted!

# View: "Roadmap"
# → See big picture across all releases
```

The project **visualizes** what you already track with labels. Zero extra maintenance!

## Embedding Project in Discussions

Once your project is public, add it to your Roadmap discussion:

```markdown
## 📊 Visual Roadmap

See all planned work organized by release:

https://github.com/orgs/Snowflake-Labs/projects/X

### Quick Links to Views:
- [📍 Current Release](link) - What's in progress now
- [🔜 Next Release](link) - What's coming next
- [🗺️ Roadmap Board](link) - All releases at a glance
- [🤝 Community PRs](link) - Community contributions
```

## Tips for Success

### ✅ Do:
- **Use labels religiously** - They drive everything
- **Let automation handle it** - Don't manually drag cards
- **Check "Needs Attention" view** weekly - Catch blocked/critical items
- **Use Roadmap view** for planning discussions
- **Share project link** with stakeholders

### ❌ Don't:
- Manually move cards between columns (use labels instead)
- Create custom statuses (use GitHub's default + labels)
- Add items manually (let automation do it via labels)
- Over-customize (keep it simple)

## Maintenance: Almost Zero

**One-time (15 min):**
- Initial setup (done with this guide)

**Per release (~5 min):**
- Update "Current Release" view filter to next version
- Rename view

**Daily/Weekly:**
- **Nothing!** Automation handles everything

**Monthly (~2 min):**
- Scan Roadmap view for big picture
- Check if any items need re-prioritization

## Troubleshooting

**Issue not showing in project?**
- Check if it has a `target: X.X.X` label
- If not, add one: `gh issue edit <number> --add-label "target: 4.3.0"`
- It will auto-appear in project

**Fields not auto-populating?**
- Verify workflows are enabled (Settings → Workflows)
- Re-label the item to trigger automation

**Too many items in project?**
- Use views to filter (that's what they're for!)
- Archive completed releases: Settings → Archive items where `Release Target is 4.0.0`

## Advanced: GitHub CLI Integration

Check project status from command line:

```bash
# Install GitHub CLI if not already
brew install gh

# List items in project
gh project item-list <project-number> --owner Snowflake-Labs

# Add item to project
gh project item-add <project-number> --owner Snowflake-Labs --url <issue-url>
```

But with automation, you rarely need these commands!

## Summary

**Before Projects:**
- Labels track everything ✓
- Milestones group by release ✓
- Hard to visualize big picture ✗

**With Projects (auto-updating):**
- Labels drive everything ✓
- Milestones still work ✓
- Beautiful visual roadmap ✓
- Stakeholder-friendly views ✓
- Zero maintenance ✓

**The Magic:** Projects is just a **view layer** on top of your existing workflow. You keep using labels and milestones like before, but now you get automatic visualization!
