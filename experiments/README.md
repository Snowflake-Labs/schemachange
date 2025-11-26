# experiments/ Folder

## Purpose

This folder is for **local development experiments and analysis** that should **NOT** be committed to the repository.

**What's tracked:** Only this README (provides guidelines for everyone)  
**What's not tracked:** Everything else you create here (your local workspace)

---

## What You'll Typically Create Here

As you work on the project, you might create:

- **Investigation notes** - `issue_388_analysis.md`, `bug_investigation.md`
- **Draft release notes** - `v4.2.0_draft.md`, `changelog_notes.md`
- **Test coverage analysis** - `test_decisions.md`, `regression_notes.md`
- **Experimental code** - `test_script.py`, `proof_of_concept.sql`
- **Configuration files** - Local test setups, temporary configs
- **Working notes** - Personal TODO lists, design sketches

**All of these stay local** - they're automatically ignored by git.

### Occasionally, Something Gets Committed

Very rarely, if you create something with **lasting value for all developers**, it might get committed:
- Consolidated release summaries
- Test coverage references (explaining what tests protect)
- Strategic decision documents (explaining "why" for the future)

But this is the exception, not the rule. **Default: everything stays local.**

---

## Guidelines

### ✅ DO Use This Folder For:
- **Local analysis documents** - Investigation notes, problem analysis
- **Experimental code** - Test scripts, proof-of-concepts
- **Temporary configurations** - Local test setups
- **Working notes** - Personal development documentation
- **Release preparation** - Draft release notes, change summaries

### ❌ DO NOT Commit:
- **Point-in-time updates** - Dated working notes
- **Multiple versions** - Iterative analysis files (consolidate before commit)
- **Personal experiments** - Keep in your local context
- **Temporary test files** - Unless they become permanent tests

---

## What Gets Committed (Rarely)

Only commit files from this folder if they provide **lasting value** to the project:

### Acceptable to Commit:
- ✅ **Consolidated release summaries** (e.g., `COMPREHENSIVE_4.2.0_RELEASE_NOTES.md`)
- ✅ **Test coverage references** (documenting regression protection)
- ✅ **Strategic decision documents** (explaining "why" for future developers)
- ✅ **Reusable test configurations** (if applicable to all developers)

### Do NOT Commit:
- ❌ Dated working notes (`ANALYSIS_2025-11-15.md`)
- ❌ Multiple versions of the same analysis
- ❌ Personal TODO lists
- ❌ Iterative problem-solving documents
- ❌ Temporary test scripts

---

## Best Practices

### Before Committing Anything:
1. **Consolidate** - Merge multiple analysis files into one comprehensive document
2. **Remove dates** - Make content timeless, not point-in-time
3. **Focus on "why"** - Document decisions and rationale, not just "what"
4. **Check relevance** - Will this help future developers?

### Example: Good vs Bad

**❌ Bad (Don't Commit):**
```
experiments/
├── issue_388_analysis_v1.md
├── issue_388_analysis_v2.md
├── issue_388_final.md
├── PASSPHRASE_FIX_2025-11-15.md
├── TODO_review.md
└── my_local_test.sh
```

**✅ Good (Can Commit):**
```
experiments/
├── COMPREHENSIVE_4.2.0_RELEASE_NOTES.md  # Consolidated, timeless
├── TEST_COVERAGE_REFERENCE.md            # Lasting value for regression protection
└── README.md                             # This guide
```

---

## Workflow

### During Development:
1. Create analysis files freely in `experiments/`
2. Iterate, revise, create multiple versions
3. Keep everything local

### Before Release:
1. Consolidate multiple files into comprehensive summaries
2. Remove dates and make content timeless
3. Focus on decisions, not just actions
4. Create reference documents for regression protection

### After Release:
1. Clean up local experiments folder
2. Archive or delete temporary analysis files
3. Keep only what has lasting value

---

## gitignore Configuration

The `.gitignore` is configured to:
- **Ignore** everything in experiments/ folder
- **Except** this README.md

```gitignore
# Experiments folder - track the folder but not its contents (maintainer workspace)
experiments/*
!experiments/README.md
```

This means:
- ✅ **Everything you create** in experiments/ stays local automatically
- ✅ **No accidental commits** - git will ignore your local files
- ✅ **Freedom to experiment** - create as many files as you want
- ✅ **Only README tracked** - provides guidelines for everyone

**In the rare case** something should be committed from experiments/, discuss with maintainers first and update .gitignore to allow that specific file.

---

## Why This Approach?

### Benefits:
- ✅ **Freedom to experiment** - Create as many working files as needed locally
- ✅ **Clean repository** - No point-in-time clutter in git history
- ✅ **Valuable documentation** - Only lasting-value content in repo
- ✅ **Local context** - Each developer can work their own way

### Anti-patterns to Avoid:
- ❌ Committing every analysis iteration
- ❌ Point-in-time notes in git history
- ❌ Multiple versions of the same document
- ❌ Working notes that become obsolete

---

## For Contributors

If you're contributing to schemachange:

1. **Use `experiments/` freely** for your local development
2. **Don't commit** your experiments unless they provide lasting value
3. **Consolidate** before considering any commit from this folder
4. **Ask yourself**: "Will this help someone 6 months from now?"

---

## For Maintainers

When you see PRs with `experiments/` content:

### Review Criteria:
- ✅ Is it consolidated (not multiple versions)?
- ✅ Is it timeless (not dated/point-in-time)?
- ✅ Does it document "why" (not just "what")?
- ✅ Will it help future developers?

### If No to Any:
- Request consolidation
- Request removal of dates
- Request focus on lasting value
- Or suggest keeping it local

---

## Example Use Cases

### Release Preparation (Good)
```
# During development (local only):
experiments/
├── issue_388_investigation.md
├── issue_388_v2.md
├── issue_388_final_fix.md
├── test_coverage_notes.md
└── my_analysis.md

# Before release (consolidate, then commit):
experiments/
└── COMPREHENSIVE_4.2.0_RELEASE_NOTES.md  ← Commit this
```

### Test Coverage Reference (Good)
```
# Document what tests protect (lasting value):
experiments/
└── TEST_COVERAGE_REFERENCE.md  ← Helps prevent regressions
```

### Strategic Decisions (Good)
```
# Document "why" for future:
experiments/
└── CONFIGURATION_STRATEGY.md  ← Explains why we do things this way
```

---

## Summary

### Simple Rules:

1. **This folder is your local scratch space** - experiment freely
2. **Everything you create stays local** (except this README)
3. **Git automatically ignores** your files here
4. **If something becomes valuable** for all developers - discuss with maintainers first

### Quick Start for New Contributors:

**Just cloned the repo?**
1. You'll only see this README
2. Create your own analysis files as needed
3. They'll automatically stay local (not in git)
4. Work freely without worrying about commits

**Working on a release?**
1. Create draft notes and analysis files here
2. Iterate as much as you want
3. Before release: if valuable, consolidate and discuss with maintainers
4. Most of your work will stay local - that's intentional

**Created something valuable?**
1. Consolidate multiple iterations into one document
2. Make it timeless (no dates, no point-in-time references)
3. Focus on "why" decisions were made
4. Discuss with maintainers before committing

---

## How Cursor AI Helps

The `.cursor/rules/06-experiments-folder.md` file enforces these guidelines:
- Prevents accidental point-in-time commits
- Reminds you to keep things local
- Guides you toward valuable documentation when appropriate

---

**Questions?** Discuss with maintainers before committing anything from `experiments/`.
