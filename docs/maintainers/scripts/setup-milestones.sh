#!/bin/bash
# Setup milestones for schemachange releases
# Usage: ./setup-milestones.sh
# Note: Milestones already exist - this script is for reference

set -e

echo "🎯 Schemachange Milestones Status"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Install it: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI ready"
echo ""

# List existing milestones
echo "📊 Current Milestones:"
echo ""

gh api repos/Snowflake-Labs/schemachange/milestones | \
  jq -r '.[] | "  \(.number). \(.title) - Due: \(.due_on // "No date") (\(.open_issues) open)"'

echo ""
echo "💡 Milestones already created! To update them:"
echo "   - Go to: https://github.com/Snowflake-Labs/schemachange/milestones"
echo "   - Click milestone → Edit"
echo ""
echo "📝 To assign issues to milestones:"
echo "   gh issue edit <number> --milestone '4.2.0'"
echo ""

echo ""
echo "🎉 Milestone setup complete!"
echo ""
echo "📋 View all milestones:"
echo "   https://github.com/Snowflake-Labs/schemachange/milestones"
echo ""
echo "💡 Next steps:"
echo "   1. Assign existing issues to milestones"
echo "   2. Update pinned roadmap issue (if you have one)"
echo "   3. Bookmark milestone URLs for quick access"
echo ""
