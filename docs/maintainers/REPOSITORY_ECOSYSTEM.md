# schemachange Repository Ecosystem

**Complete guide to how everything works together**

Last updated: November 2025

---

## 🎯 Overview

This document explains how all the pieces of the schemachange repository work together to create a low-maintenance, contributor-friendly ecosystem.

**Maintenance Budget:** ~1 hour/month
**Contributors:** Welcomed and supported through automation

---

## 🏗️ Architecture

```
Repository Ecosystem
├── Automation (GitHub Actions)
│   ├── Auto-labeling (issues, PRs)
│   ├── Stale bot (cleanup)
│   ├── Community helpers (welcome, guidance)
│   └── CI/CD (tests, linting, publishing)
│
├── Organization (GitHub Features)
│   ├── Labels (36 labels for categorization)
│   ├── Milestones (per-release planning)
│   ├── Projects (roadmap visualization)
│   └── Discussions (community engagement)
│
├── Documentation (Contributor Support)
│   ├── README.md (getting started)
│   ├── CONTRIBUTING.md (detailed guide)
│   ├── CONTRIBUTING_QUICKSTART.md (5-min start)
│   ├── TROUBLESHOOTING.md (common issues)
│   ├── SECURITY.md (authentication)
│   └── CHANGELOG.md (release notes)
│
└── Workflows (Automated Processes)
    ├── Issue → Triage → Review → Close
    ├── PR → Label → Test → Review → Merge
    ├── Stale → Warn → Close
    └── Release → Build → Publish → Announce
```

---

## 🤖 Automated Workflows

### What Runs Automatically

| Workflow | Trigger | What It Does | Maintenance Saved |
|----------|---------|--------------|-------------------|
| **auto-label-issues.yml** | Issue opened | Adds `status: needs-triage` | 2 min/issue |
| **auto-label-prs.yml** | PR opened | Adds `community-contribution` + file-based labels | 3 min/PR |
| **remove-awaiting-response.yml** | Author comments/commits | Moves to `status: needs-review` | 1 min/response |
| **community-pr-helper.yml** | Community PR opened | Posts welcome message with instructions | 5 min/PR |
| **stale.yml** | Weekly (Sunday) | Closes items awaiting author response 60+ days | 15 min/week |
| **master-pytest.yml** | PR to main | Runs full test suite (pytest, ruff) | N/A |
| **dev-pytest.yml** | PR to dev/rc | Runs tests on development branches | N/A |
| **python-publish.yml** | Release published | Builds and publishes to PyPI | 10 min/release |

**Total time saved:** ~20-30 min/week = **80-120 min/month**

---

## 🏷️ Label System (36 Labels)

### Type Labels (Auto-applied)
- `bug`, `enhancement`, `question`, `documentation`, `dependencies`

### Status Labels (Track progress)
- `status: needs-triage` → `status: needs-review` → `status: in-progress` → Closed
- `status: awaiting-response` → (author responds) → `status: needs-review`
- `status: blocked`, `status: needs-tests`

### Priority Labels (Maintainer applied)
- `priority: critical`, `priority: high`, `priority: medium`, `priority: low`

### Target Labels (Roadmap planning)
- `target: 4.2.0`, `target: 4.3.0`, `target: 4.4.0`, `target: 4.5.0`, `target: 5.0.0`, `target: future`

### Special Labels
- `good-first-issue`, `help-wanted`, `community-contribution`, `security`, `breaking-change`, `stale`

### Workflow Labels
- `ci-run-tests`, `Development in Progress`, `Under Review`, `Workaround`

---

## 📊 GitHub Projects Setup

### Project: "schemachange Roadmap"

**Type:** Table view (easier than Board for low maintenance)

**Auto-populated from:**
- Issues/PRs with `target: *` labels
- Automatically syncs status, priority, type

**Saved Views:**
1. **Current Release** - `target: 4.2.0`, sorted by priority
2. **Next Release** - `target: 4.3.0`, sorted by priority
3. **All Active Work** - Open items not in `target: future`
4. **Community Contributions** - All `community-contribution` items
5. **Needs Attention** - `priority: critical` OR `status: blocked`

**Maintenance:** Zero - updates automatically from labels

---

## 💬 GitHub Discussions Structure

### Categories

**📢 Announcements** (Maintainers only)
- Release announcements
- Breaking change notices
- Roadmap updates

**💬 General**
- Best practices
- Workflows and setups
- General conversation

**💡 Ideas** (Feature proposals)
- Discuss before creating issues
- Validate community interest
- Template-guided

**🙏 Q&A** (Primary support channel)
- Questions about using schemachange
- Troubleshooting help
- Can mark answers
- Searchable by future users

**🏆 Show and Tell**
- Community showcases
- CI/CD pipelines
- Integration examples
- Monitoring setups

**🔧 Troubleshooting**
- Complex debugging
- Environment-specific issues

### Pinned Discussions (3)

1. **Welcome & Guidelines** - How to use Discussions effectively
2. **schemachange Roadmap** - Living roadmap with release dates
3. **Common Issues & Solutions** - Top 10 Q&As from TROUBLESHOOTING.md

---

## 📝 Documentation Strategy

### For Users (Getting Help)

```
User needs help
    ↓
[Try schemachange verify command]
    ↓
[Search Discussions Q&A]
    ↓
[Check TROUBLESHOOTING.md]
    ↓
[Ask in Q&A Discussion]
    ↓
[If bug: Create Issue]
```

### For Contributors (Getting Started)

```
Want to contribute
    ↓
[Read CONTRIBUTING_QUICKSTART.md] (5 min)
    ↓
[Find good-first-issue]
    ↓
[Comment to claim it]
    ↓
[Follow quickstart setup]
    ↓
[Submit PR]
    ↓
[Automation guides you]
```

---

## 🔄 Maintainer Workflow (1 hour/month)

### Weekly Check-in (15 min/week)

```bash
# 1. Check items ready for review (5 min)
gh pr list --label "status: needs-review"
gh issue list --label "status: needs-review"

# 2. Check critical items (2 min)
gh issue list --label "priority: critical"

# 3. Review and merge PRs (8 min)
gh pr review <number> --approve --body "LGTM! Thanks!"
gh pr merge <number> --squash --delete-branch
```

### Monthly Tasks (15 min)

- Check GitHub Project board progress
- Update pinned roadmap Discussion (if scope changed)
- Post monthly release announcement (if released)

**That's it!** Everything else is automated.

---

## 🎯 What Makes This Low-Maintenance

### 1. Automation Handles Routine Tasks
- Auto-labeling (no manual categorization)
- Auto-cleanup (stale bot)
- Auto-guidance (community helper bot)
- Auto-status updates (awaiting-response removal)

### 2. Self-Service Documentation
- Comprehensive guides reduce questions
- Discussions Q&A builds searchable knowledge base
- Troubleshooting guide covers common issues
- Templates guide contributors

### 3. Clear Expectations Set
- Response times published (2-4 weeks for PRs)
- Roadmap shows what's planned
- Labels show status transparently
- Project board shows progress

### 4. Community Empowerment
- Discussions let community help each other
- Good-first-issue labels attract new contributors
- Quickstart guide makes contributing easy
- Templates ensure quality submissions

---

## ✅ What's Implemented

### Automation ✅
- [x] Auto-label issues with `needs-triage`
- [x] Auto-label PRs with `community-contribution`
- [x] Auto-label PRs by files changed
- [x] Auto-remove `awaiting-response` when author responds
- [x] Welcome message for community PRs
- [x] Stale bot (only closes abandoned items)
- [x] CI/CD with ruff and pytest
- [x] Auto-publish to PyPI on release

### Organization ✅
- [x] 36 comprehensive labels
- [x] Milestones for releases 4.2.0-5.0.0
- [x] Issue templates (bug, feature, question)
- [x] Issue template config (directs to Discussions)
- [x] PR template with checklist

### Documentation ✅
- [x] README.md (comprehensive)
- [x] CONTRIBUTING.md (detailed guide)
- [x] CONTRIBUTING_QUICKSTART.md (5-min start)
- [x] TROUBLESHOOTING.md (common issues)
- [x] SECURITY.md (authentication guide)
- [x] CHANGELOG.md (maintained)

### Workflows ✅
- [x] CI/CD workflows (master-pytest, dev-pytest)
- [x] Auto-labeling workflows
- [x] Stale bot workflow
- [x] Community helper workflows
- [x] PyPI publishing workflow

---

## 🚧 What's Missing (Optional Enhancements)

### GitHub Projects (15 min setup)
- [ ] Create "schemachange Roadmap" Project
- [ ] Configure auto-add workflow (items with `target: *` labels)
- [ ] Create saved views (Current Release, Next Release, etc.)
- [ ] Make project public
- [ ] Link from Discussions roadmap

### GitHub Discussions (30 min setup)
- [ ] Enable Discussions in repo settings
- [ ] Create categories (Announcements, General, Ideas, Q&A, Show and Tell, Troubleshooting)
- [ ] Create and pin Welcome discussion (use template)
- [ ] Create and pin Roadmap discussion (use template)
- [ ] Create and pin Common Issues Q&A discussion (use template)
- [ ] Update links in templates (replace LINK_TO_* placeholders)

### Documentation Polish (30 min)
- [ ] Add Discussions badge to README
- [ ] Update CONTRIBUTING.md to mention CONTRIBUTING_QUICKSTART.md
- [ ] Consider moving some TROUBLESHOOTING.md content to Discussions Q&A
- [ ] Add "Help Wanted" section to README

### Community Engagement (Ongoing)
- [ ] Post announcement when Discussions goes live
- [ ] Encourage community to answer questions in Q&A
- [ ] Recognize top contributors in releases
- [ ] Consider "Contributor of the Month" in Announcements

---

## 📈 Success Metrics

### Automation Effectiveness
- **Issues triaged:** Auto-labeled within seconds (vs 2 days manual)
- **PRs categorized:** Auto-labeled within seconds (vs 3 min manual)
- **Stale items closed:** Weekly automatic (vs manual monthly cleanup)
- **Community PRs welcomed:** Instant helpful message (vs manual response)

### Community Engagement
- **Response times:** <2 days for triage (target met via automation)
- **PR review times:** 2-4 weeks (realistic for 1hr/month maintenance)
- **Discussion activity:** Track Q&A questions answered by community
- **Contributor growth:** Track `community-contribution` PRs merged

### Repository Health
- **Open issue count:** Maintain <30 (stale bot helps)
- **PR merge rate:** >80% of reviewed PRs merged
- **Test coverage:** Maintain >85%
- **CI pass rate:** >95%

---

## 🔮 Future Enhancements

### If Maintenance Budget Increases

**With 2 hours/month:**
- Monthly "State of schemachange" post in Discussions
- More proactive community engagement
- Video tutorials or demos

**With 4 hours/month:**
- Regular office hours in Discussions
- More detailed roadmap planning
- Contributor mentoring program

### Additional Automation Ideas

- **Welcome bot for first-time contributors** (beyond just PRs)
- **Auto-assign reviewers** based on code sections
- **Automatic changelog generation** from PR titles
- **Release notes automation** from milestone issues

---

## 📚 Key Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| README.md | Getting started, main documentation | All users |
| CONTRIBUTING.md | Detailed contribution guide | Contributors |
| CONTRIBUTING_QUICKSTART.md | 5-minute quick start | New contributors |
| TROUBLESHOOTING.md | Common problems and solutions | Users needing help |
| SECURITY.md | Authentication methods, best practices | Users setting up auth |
| CHANGELOG.md | Version history, breaking changes | All users |
| DISCUSSION_CATEGORIES.md | How Discussions are organized | Maintainers |
| REPOSITORY_ECOSYSTEM.md | How everything works together | Maintainers |

---

## 🎉 Summary

### What You Have Now

✅ **Automated** - 90% of routine tasks handled by bots
✅ **Organized** - Clear labels, milestones, and roadmap
✅ **Documented** - Comprehensive guides for users and contributors
✅ **Sustainable** - Designed for 1 hour/month maintenance
✅ **Contributor-friendly** - Clear path from idea to merged PR
✅ **Transparent** - Roadmap, status, and progress all visible

### To Complete the Ecosystem

1. **Enable GitHub Discussions** (5 min)
2. **Create 3 pinned discussions** (15 min)
3. **Set up GitHub Project** (15 min)
4. **Update placeholder links** (5 min)

**Total setup time remaining:** ~40 minutes

Then you're done! The ecosystem maintains itself with just 1 hour/month from you.

---

**Questions?** This file is for maintainers. Users should see README.md or ask in Discussions.
