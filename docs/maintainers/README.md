# Maintainer Documentation

**Audience:** Repository maintainers and collaborators

This folder contains guides for maintaining the schemachange repository with minimal time investment (~1 hour/month).

---

## 📚 Documentation Index

### Essential Reading

1. **[REPOSITORY_ECOSYSTEM.md](REPOSITORY_ECOSYSTEM.md)** - START HERE
   - Complete overview of how everything works together
   - Automation workflows explained
   - Weekly maintenance workflow (15 min)
   - What's implemented vs. what's optional
   - File organization and purpose

### Setup Guides (One-Time)

2. **[PROJECT_SETUP.md](PROJECT_SETUP.md)** - 15 minutes
   - Set up GitHub Projects for auto-updating roadmap
   - Create views and automation
   - Zero-maintenance visualization

3. **[DISCUSSION_CATEGORIES.md](DISCUSSION_CATEGORIES.md)** - 30 minutes
   - Enable and configure GitHub Discussions
   - Set up categories (Q&A, Ideas, General, etc.)
   - Create pinned welcome posts

4. **[DISCUSSION_TEMPLATES/](DISCUSSION_TEMPLATES/)** - Reference
   - Templates to copy when creating pinned discussions
   - `00_welcome.md` - Welcome post
   - `01_roadmap.md` - Roadmap post (update links to your project)

---

## 🎯 Quick Start for New Maintainers

### Week 1: Familiarize
1. Read [REPOSITORY_ECOSYSTEM.md](REPOSITORY_ECOSYSTEM.md) (15 min)
2. Review workflows in `.github/workflows/` (10 min)
3. Check label structure: `gh label list` (5 min)

### Week 2: Optional Setup
1. Set up GitHub Projects (optional but nice): [PROJECT_SETUP.md](PROJECT_SETUP.md) (15 min)
2. Enable Discussions (optional but reduces issue noise): [DISCUSSION_CATEGORIES.md](DISCUSSION_CATEGORIES.md) (30 min)

### Ongoing: Weekly Maintenance
**Total time: 15 minutes/week = 1 hour/month**

```bash
# Monday morning routine (15 min)

# 1. Check critical items (2 min)
gh issue list --label "priority: critical"

# 2. Check PRs ready for review (5 min)
gh pr list --label "status: needs-review"

# 3. Review and merge (8 min)
gh pr review <number> --approve --body "LGTM! Thanks!"
gh pr merge <number> --squash --delete-branch
```

**That's it!** Automation handles the rest.

---

## 🤖 What's Automated

You don't need to do these manually:

✅ **Labeling**
- New issues get `status: needs-triage`
- Community PRs get `community-contribution`
- PRs labeled by files changed (`documentation`, `dependencies`)

✅ **Status Updates**
- When author responds → Remove `awaiting-response`, add `needs-review`
- When PR merged → Auto-close related issues

✅ **Cleanup**
- Stale bot closes abandoned items (60+ days awaiting author response)
- Only items with `status: awaiting-response` can go stale
- Items waiting on maintainers are protected

✅ **Communication**
- Community contributors get welcome message with instructions
- Response time expectations set automatically

✅ **Testing**
- CI runs on all PRs (pytest, ruff)
- Tests must pass before merge

---

## 📋 Decision Framework

When triaging issues/PRs, use this framework:

### Is it critical?
```
Security issue? Data loss? Production blocker?
→ Add: priority: critical, respond within 1-2 weeks
```

### Is it a bug?
```
Confirmed bug?
→ Add: bug, priority: [high|medium|low], target: [next release]
```

### Is it a feature request?
```
Aligns with roadmap? Has community support?
→ Add: enhancement, priority: medium, target: [future release]

Breaking change?
→ Add: breaking-change, target: 5.0.0 (or next major)

Not aligned with project goals?
→ Close with explanation
```

### Is it a question?
```
Could be answered in Discussions?
→ Close, point to Discussions Q&A

Needs clarification?
→ Add: status: awaiting-response, comment asking for details
```

### Is it a PR?
```
Community PR?
→ Already auto-labeled, just review

Needs changes?
→ Add: status: awaiting-response, request changes

Ready to merge?
→ Approve and merge, automation handles rest
```

---

## 🏷️ Label Quick Reference

### Most Common Labels for Triaging

```bash
# Priority (you decide)
priority: critical    # Security, data loss, blocker
priority: high        # Important for next release
priority: medium      # Nice to have
priority: low         # Future consideration

# Target (roadmap planning)
target: 4.2.0        # Current release
target: 4.3.0        # Next release
target: future       # Someday

# Status (track progress)
status: needs-review       # Waiting for maintainer
status: awaiting-response  # Waiting for author
status: in-progress        # Being worked on
status: blocked            # Blocked by external dependency
```

See [REPOSITORY_ECOSYSTEM.md](REPOSITORY_ECOSYSTEM.md) for full label system.

---

## 🚀 Release Process

### When Ready to Release

```bash
# 1. Merge RC branch to main
git checkout main
git merge --no-ff rc4.2.0
git push origin main

# 2. Create and push tag
git tag -a v4.2.0 -m "Release 4.2.0"
git push origin v4.2.0

# 3. Create GitHub Release (via UI or CLI)
gh release create v4.2.0 --title "Release 4.2.0" --notes-from-tag

# Automation handles:
# - Building package
# - Publishing to PyPI
# - Extracting changelog
# - Updating release notes
```

See release roadmap in `experiments/` (not tracked, for your planning).

---

## 📊 Success Metrics

Track these monthly:

- **Response time:** <2 days for triage ✅
- **PR review time:** 2-4 weeks (realistic for 1hr/month) ✅
- **Open issues:** Keep <30 (stale bot helps) ✅
- **CI pass rate:** >95% ✅

---

## 🆘 Common Scenarios

### "I only have 1 hour this month"

Focus on:
1. Critical issues (5 min)
2. Community PRs ready to merge (30 min)
3. Quick triage of new issues (10 min)
4. Let automation handle the rest (15 min buffer)

### "Someone needs CI to run on their PR"

```bash
gh pr edit <number> --add-label "ci-run-tests"
```

The workflow trigger will run CI on that PR.

### "I need to defer work from 4.2.0 to 4.3.0"

```bash
gh issue edit <number> --remove-label "target: 4.2.0" --add-label "target: 4.3.0"
```

If using GitHub Projects, it will auto-update.

### "Issue is stale but should stay open"

```bash
# Remove awaiting-response label so stale bot ignores it
gh issue edit <number> --remove-label "status: awaiting-response"

# Or add exempt label
gh issue edit <number> --add-label "priority: critical"
```

### "I want to see the big picture"

If you set up GitHub Projects:
- View: "Roadmap" - See all releases at a glance
- View: "Current Release" - See progress on current work

If not using Projects:
```bash
gh issue list --milestone "4.2.0"
gh pr list --label "target: 4.2.0"
```

---

## 📖 Additional Resources

- [Main README](../../README.md) - User documentation
- [Contributing Guide](../../.github/CONTRIBUTING.md) - Contributor documentation
- [Workflows](../../.github/workflows/) - Automation configuration
- [Experiments folder](../../experiments/) - Maintainer workspace (folder tracked, contents not tracked)

---

## 💡 Philosophy

> **"Automate everything. Focus on high-value work. Set realistic expectations."**

This repository is designed to be maintainable with minimal time investment. The automation handles routine tasks, documentation helps the community help itself, and clear communication prevents constant "when will you review my PR?" messages.

**Remember:** You're volunteers maintaining an OSS project. It's okay to:
- Take 2-4 weeks to review PRs
- Defer features to future releases
- Close issues that don't align with the project
- Ask contributors to improve their PRs

The ecosystem supports your time constraints, not works against them.

---

**Questions?** Update this documentation! It's for maintainers, by maintainers.
