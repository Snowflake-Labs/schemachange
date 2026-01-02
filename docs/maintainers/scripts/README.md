# Maintainer Scripts

Helper scripts for common maintenance tasks.

## Available Scripts

### `setup-milestones.sh`

**Purpose:** One-time setup of release milestones

**Usage:**
```bash
cd /path/to/schemachange
./docs/maintainers/scripts/setup-milestones.sh
```

**What it does:**
- Creates milestones for: 4.2.0, 4.3.0, 4.4.0, 4.5.0, 5.0.0, Future
- Sets due dates
- Adds descriptions
- Skips if milestone already exists

**Requirements:**
- GitHub CLI (`gh`) installed
- Authenticated: `gh auth status`
- Write access to repository

**Time:** 2 minutes

---

## Creating Your Own Scripts

Add scripts here for tasks you do frequently:

```bash
# Example: milestone-status.sh
#!/bin/bash
echo "📊 Current Release Status"
gh milestone view "4.2.0"
```

Make them executable:
```bash
chmod +x docs/maintainers/scripts/milestone-status.sh
```

---

## Tips

### Bookmark Common Commands

Instead of scripts, you can also:

1. **Create shell aliases:**
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   alias sc-status='cd /path/to/schemachange && gh milestone view "4.2.0"'
   alias sc-prs='cd /path/to/schemachange && gh pr list --label "community-contribution"'
   ```

2. **Use GitHub CLI aliases:**
   ```bash
   gh alias set critical 'issue list --label "priority: critical"'
   gh alias set current 'milestone view "4.2.0"'

   # Then use:
   gh critical
   gh current
   ```

3. **Bookmark GitHub URLs:**
   - Current milestone: https://github.com/Snowflake-Labs/schemachange/milestone/1
   - Critical issues: https://github.com/Snowflake-Labs/schemachange/issues?q=is%3Aopen+label%3A%22priority%3A+critical%22
   - Community PRs: https://github.com/Snowflake-Labs/schemachange/pulls?q=is%3Aopen+label%3Acommunity-contribution

Choose what works best for your workflow!
