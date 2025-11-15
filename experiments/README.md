# Experiments Folder

**Purpose:** Maintainer workspace for planning, experiments, and temporary documentation.

**Status:** This folder is tracked, but its **contents are not** (except this README).

---

## What This Folder Is For

This is a **scratchpad for maintainers** to:
- Plan releases (roadmaps, assessments, strategies)
- Draft documentation before finalizing
- Create test scripts and experiments
- Store temporary analysis and notes
- Work on ideas without committing them

**Think of it as:** Your personal workspace that's available to all maintainers but not cluttering version control.

---

## What's Typically Here

When maintainers are working, you might find:
- **Point-in-time documentation** (e.g., `SETUP_COMPLETE.md`, `QUICK_START.md`)
  - Captures "what we did" at a specific moment
  - Useful for reference but becomes stale
  - Better here than in `docs/` where it duplicates git/issue history
- **Release planning** documents (e.g., `4.3.0_RELEASE_PLAN.md`)
- **Assessment documents** (e.g., `PR_REVIEW_*.md`)
- **Test scripts** (e.g., `test.sh`, `triage-issues.sh`)
- **Draft documentation** before finalizing
- **Analysis and investigations**

**Most files are NOT tracked in git** - they're personal/temporary work products.

---

## How It Works

```gitignore
# In .gitignore:
experiments/*           # Ignore all contents
!experiments/README.md  # Except this README
```

**Result:**
- ✅ Folder exists in repository (maintainers know about it)
- ✅ This README is tracked (explains purpose)
- ❌ Your work files are NOT tracked (keep it clean)

---

## Guidelines

### ✅ DO Use This Folder For:
- **Point-in-time documentation** - "what we did" summaries
- **Release planning** and assessments
- **Draft documentation** (before moving to `docs/`)
- **Test scripts** with hardcoded values (e.g., specific issue numbers)
- **Personal notes** and analysis
- **Temporary work** products

### ❌ DON'T Put Here:
- **Timeless guidance** (→ use `docs/maintainers/` instead)
- **Reusable scripts** without hardcoded values (→ use `docs/maintainers/scripts/`)
- **Templates** that maintainers need (→ use `docs/maintainers/`)
- **Public documentation** (→ use root or `docs/`)

---

## When to Move Files Out

**If your work becomes permanent, move it:**

| File Type | Move To | Example |
|-----------|---------|---------|
| Maintainer guide | `docs/maintainers/` | Setup guides, architecture docs |
| User documentation | Root (`/`) | README, TROUBLESHOOTING, SECURITY |
| Contributor guide | `.github/` | CONTRIBUTING, templates |
| Workflow/script | Appropriate folder | CI/CD scripts, test helpers |
| Reference only | Keep here | Old planning docs, assessments |

---

## Example Workflow

```bash
# 1. Create release plan (draft)
echo "# 4.3.0 Release Plan" > experiments/4.3.0_PLAN.md
# Edit and iterate...

# 2. When finalized, decide:
# - Keep as reference? → Leave in experiments/ (not tracked)
# - Share with team? → Move to docs/maintainers/
# - Make public? → Move to appropriate location and commit

# 3. Clean up old experiments periodically
cd experiments/
rm old_plan.md  # Not tracked, so just delete
```

---

## Why This Pattern?

### Benefits:
1. **Workspace exists** - All maintainers know where to put temporary work
2. **No clutter** - Personal work doesn't show up in `git status`
3. **Flexible** - Delete old files without affecting git history
4. **Visible** - README explains the folder to new maintainers
5. **Professional** - Repository stays clean for OSS community

### Alternative (What We Don't Do):
- Track everything → Git history filled with temporary docs
- No experiments/ folder → Each maintainer creates their own, inconsistent
- Fully ignore folder → Maintainers don't know it exists

---

## For New Maintainers

**This folder is your workspace!** Use it freely:
- Create planning docs
- Draft ideas
- Experiment with scripts
- Take notes

**Don't worry about committing** - it's not tracked. When something becomes permanent, move it to the appropriate location in the repo.

---

## Current Maintainer Notes

> Add any project-specific notes here for your team...

**Example:** "When planning releases, use the format `X.Y.Z_RELEASE_PLAN.md` for consistency."

---

**Questions?** This folder is for you - use it however helps your workflow!
