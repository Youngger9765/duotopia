#!/bin/bash

# Git Issue PR Flow Agent - Duotopia Project
# Automates the standardized Git Issue PR Flow workflow

# Configuration
STAGING_FRONTEND_URL="https://duotopia-staging-frontend-316409492201.asia-east1.run.app"
STAGING_BACKEND_URL="https://duotopia-staging-backend-316409492201.asia-east1.run.app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create feature branch for bug fix
create-feature-fix() {
  local issue_num=$1
  local description=$2

  if [ -z "$issue_num" ] || [ -z "$description" ]; then
    echo -e "${RED}❌ Usage: create-feature-fix <issue_number> <description>${NC}"
    echo "   Example: create-feature-fix 7 student-login-loading"
    return 1
  fi

  git checkout staging
  git pull origin staging
  git checkout -b "fix/issue-${issue_num}-${description}"

  echo -e "${GREEN}✅ Created branch: fix/issue-${issue_num}-${description}${NC}"
  echo -e "${BLUE}📝 Make your changes and commit${NC}"
  echo -e "${BLUE}🚀 Then run: deploy-feature ${issue_num}${NC}"
}

# Create feature branch for new feature
create-feature() {
  local description=$1

  if [ -z "$description" ]; then
    echo -e "${RED}❌ Usage: create-feature <description>${NC}"
    echo "   Example: create-feature audio-playback-refactor"
    return 1
  fi

  git checkout staging
  git pull origin staging
  git checkout -b "feat/${description}"

  echo -e "${GREEN}✅ Created branch: feat/${description}${NC}"
  echo -e "${BLUE}📝 Make your changes and commit${NC}"
  echo -e "${BLUE}🚀 Then run: deploy-feature-no-issue${NC}"
}

# Deploy feature branch to staging (with issue tracking)
deploy-feature() {
  local issue_num=$1
  local branch=$(git branch --show-current)

  if [ -z "$issue_num" ]; then
    echo -e "${RED}❌ Usage: deploy-feature <issue_number>${NC}"
    return 1
  fi

  # Ensure on feature branch
  if [[ ! $branch =~ ^(fix|feat)/ ]]; then
    echo -e "${RED}❌ Must be on a feature branch (fix/* or feat/*)${NC}"
    return 1
  fi

  # Check if last commit contains issue number
  local last_commit=$(git log -1 --pretty=%B)
  if ! echo "$last_commit" | grep -qE "#$issue_num|Fixes #$issue_num"; then
    echo -e "${YELLOW}⚠️  Warning: Last commit message doesn't contain #${issue_num}${NC}"
    echo -e "${YELLOW}   This issue won't be automatically tracked in Release PR${NC}"
    echo -e "${YELLOW}   Last commit: $(git log -1 --oneline)${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}❌ Deployment cancelled${NC}"
      echo -e "${BLUE}💡 Amend your commit to include 'Fixes #${issue_num}':${NC}"
      echo -e "   git commit --amend"
      return 1
    fi
  fi

  echo -e "${YELLOW}🔄 Deploying $branch to staging...${NC}"

  # Merge to staging
  git checkout staging
  git pull origin staging
  git merge --no-ff "$branch" -m "Merge $branch into staging"

  # Push to trigger CI/CD
  if git push origin staging; then
    echo -e "${GREEN}✅ Deployed to staging${NC}"
    echo -e "${BLUE}🌐 Frontend: $STAGING_FRONTEND_URL${NC}"
    echo -e "${BLUE}🌐 Backend: $STAGING_BACKEND_URL${NC}"

    local commit_hash=$(git rev-parse HEAD)

    # Update issue with deployment info
    echo -e "${YELLOW}📝 Updating issue #${issue_num}...${NC}"
    gh issue comment "$issue_num" --body "## 🚀 已部署到 Staging

**前端**: $STAGING_FRONTEND_URL
**後端**: $STAGING_BACKEND_URL

**Branch**: \`$branch\`
**Commit**: \`$commit_hash\`

請協助測試，確認修復是否正常運作。"

    echo -e "${GREEN}✅ Updated issue #${issue_num}${NC}"
    echo -e "${BLUE}📋 Run 'update-release-pr' to add this issue to release PR${NC}"
  else
    echo -e "${RED}❌ Failed to push to staging${NC}"
    return 1
  fi
}

# Deploy feature branch to staging (without issue tracking)
deploy-feature-no-issue() {
  local branch=$(git branch --show-current)

  # Ensure on feature branch
  if [[ ! $branch =~ ^(fix|feat)/ ]]; then
    echo -e "${RED}❌ Must be on a feature branch (fix/* or feat/*)${NC}"
    return 1
  fi

  echo -e "${YELLOW}🔄 Deploying $branch to staging...${NC}"

  # Merge to staging
  git checkout staging
  git pull origin staging
  git merge --no-ff "$branch" -m "Merge $branch into staging"

  # Push to trigger CI/CD
  if git push origin staging; then
    echo -e "${GREEN}✅ Deployed to staging${NC}"
    echo -e "${BLUE}🌐 Frontend: $STAGING_FRONTEND_URL${NC}"
    echo -e "${BLUE}🌐 Backend: $STAGING_BACKEND_URL${NC}"
    echo -e "${BLUE}📋 Run 'update-release-pr' to create/update release PR${NC}"
  else
    echo -e "${RED}❌ Failed to push to staging${NC}"
    return 1
  fi
}

# Create or update release PR (staging → main)
create-release-pr() {
  echo -e "${YELLOW}📝 Creating/updating release PR...${NC}"

  # Get list of commits between staging and main (full message, not just oneline)
  local commits=$(git log main..staging --format='%B')
  local issue_pattern='#[0-9]+'
  local issues=$(echo "$commits" | grep -oE "$issue_pattern" | sort -u | tr '\n' ' ')

  # Build PR body
  local pr_body="## 📦 Release Notes

This PR includes the following fixes and features:

"

  if [ -n "$issues" ]; then
    for issue in $issues; do
      pr_body+="- Fixes $issue
"
    done
  else
    pr_body+="- General improvements and bug fixes
"
  fi

  pr_body+="
## 🧪 Testing
All changes have been tested in staging environment:
- **Frontend**: $STAGING_FRONTEND_URL
- **Backend**: $STAGING_BACKEND_URL

## ✅ Checklist
- [ ] All issues tested and verified
- [ ] No console errors
- [ ] All tests passing
- [ ] Ready for production deployment

---
Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"

  # Check if PR exists
  local existing_pr=$(gh pr list --base main --head staging --json number --jq '.[0].number' 2>/dev/null)

  if [ -n "$existing_pr" ]; then
    echo -e "${YELLOW}📝 Updating existing PR #${existing_pr}...${NC}"
    gh pr edit "$existing_pr" --body "$pr_body"
    echo -e "${GREEN}✅ Updated PR #${existing_pr}${NC}"
    gh pr view "$existing_pr" --web
  else
    echo -e "${YELLOW}📝 Creating new release PR...${NC}"
    local pr_url=$(gh pr create \
      --base main \
      --head staging \
      --title "🚀 Release: Staging → Main" \
      --body "$pr_body" \
      --draft 2>&1)

    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Created draft PR${NC}"
      echo "$pr_url"
    else
      echo -e "${RED}❌ Failed to create PR: $pr_url${NC}"
      return 1
    fi
  fi

  echo ""
  echo -e "${BLUE}🎯 Next Steps:${NC}"
  echo -e "  1. Test all changes in staging"
  echo -e "  2. Mark PR as ready for review: ${YELLOW}gh pr ready <PR_NUMBER>${NC}"
  echo -e "  3. Merge PR to deploy to production and auto-close issues"
}

# Alias for convenience
update-release-pr() {
  create-release-pr
}

# Show current workflow status
git-flow-status() {
  echo -e "${BLUE}📊 Git Flow Status${NC}"
  echo ""

  # Current branch
  local current_branch=$(git branch --show-current)
  echo -e "Current branch: ${YELLOW}$current_branch${NC}"

  # Check if on feature branch
  if [[ $current_branch =~ ^(fix|feat)/ ]]; then
    echo -e "Status: ${GREEN}On feature branch${NC}"
    echo -e "Next: Commit changes, then run ${YELLOW}deploy-feature <issue_number>${NC}"
  elif [[ $current_branch == "staging" ]]; then
    echo -e "Status: ${GREEN}On staging branch${NC}"
    echo -e "Next: Run ${YELLOW}create-release-pr${NC} to prepare release"
  elif [[ $current_branch == "main" ]]; then
    echo -e "Status: ${GREEN}On main branch${NC}"
    echo -e "Next: Create feature branch with ${YELLOW}create-feature-fix <issue> <desc>${NC}"
  else
    echo -e "Status: ${YELLOW}Unknown branch${NC}"
  fi

  echo ""

  # Pending commits to staging
  local pending_staging=$(git log main..staging --oneline 2>/dev/null | wc -l | tr -d ' ')
  if [ "$pending_staging" -gt 0 ]; then
    echo -e "${YELLOW}⏳ $pending_staging commit(s) in staging not yet in main${NC}"
  else
    echo -e "${GREEN}✅ Staging and main are in sync${NC}"
  fi

  echo ""

  # Check for existing release PR
  local existing_pr=$(gh pr list --base main --head staging --json number,title,isDraft --jq '.[0]' 2>/dev/null)
  if [ -n "$existing_pr" ]; then
    local pr_number=$(echo "$existing_pr" | jq -r '.number')
    local pr_title=$(echo "$existing_pr" | jq -r '.title')
    local is_draft=$(echo "$existing_pr" | jq -r '.isDraft')

    if [ "$is_draft" = "true" ]; then
      echo -e "${YELLOW}📋 Draft PR #$pr_number: $pr_title${NC}"
    else
      echo -e "${GREEN}📋 PR #$pr_number: $pr_title${NC}"
    fi
  else
    echo -e "${BLUE}📋 No release PR found${NC}"
  fi

  echo ""
  echo -e "${BLUE}🌐 Staging URLs:${NC}"
  echo -e "  Frontend: $STAGING_FRONTEND_URL"
  echo -e "  Backend:  $STAGING_BACKEND_URL"
}

# Patrol open issues
patrol-issues() {
  echo -e "${BLUE}🔍 Patrolling GitHub Issues...${NC}"
  echo ""

  # Get open issues
  local issues=$(gh issue list --json number,title,labels,createdAt,updatedAt,assignees --limit 20)

  if [ "$issues" = "[]" ]; then
    echo -e "${GREEN}✅ No open issues found!${NC}"
    return 0
  fi

  # Summary stats
  local total=$(echo "$issues" | jq '. | length')
  local bugs=$(echo "$issues" | jq '[.[] | select(.labels[]? | .name == "bug")] | length')
  local enhancements=$(echo "$issues" | jq '[.[] | select(.labels[]? | .name == "enhancement")] | length')
  local unassigned=$(echo "$issues" | jq '[.[] | select(.assignees | length == 0)] | length')
  local approved=$(echo "$issues" | jq '[.[] | select(.labels[]? | .name == "✅ tested-in-staging")] | length')

  echo -e "${YELLOW}📊 Issue Summary:${NC}"
  echo -e "  Total open: ${YELLOW}$total${NC}"
  echo -e "  🐛 Bugs: ${RED}$bugs${NC}"
  echo -e "  ✨ Enhancements: ${GREEN}$enhancements${NC}"
  echo -e "  ✅ Tested in staging: ${GREEN}$approved${NC}"
  echo -e "  👤 Unassigned: ${YELLOW}$unassigned${NC}"
  echo ""

  # List issues by priority
  echo -e "${BLUE}📋 Open Issues:${NC}"
  echo ""

  echo "$issues" | jq -r '.[] |
    "  #\(.number) - \(.title)\n" +
    "    Labels: \(if .labels | length > 0 then [.labels[].name] | join(", ") else "none" end)\n" +
    "    Created: \(.createdAt | split("T")[0])\n" +
    "    Updated: \(.updatedAt | split("T")[0])\n"'

  echo ""
  echo -e "${BLUE}💡 Quick Actions:${NC}"
  echo -e "  ${YELLOW}create-feature-fix <issue_number> <description>${NC} - Start working on an issue"
  echo -e "  ${YELLOW}check-approvals${NC}                                 - Check approval status for release"
  echo -e "  ${YELLOW}gh issue view <issue_number>${NC}                    - View issue details"
  echo -e "  ${YELLOW}gh issue view <issue_number> --web${NC}              - Open in browser"
}

# Check if all issues in Release PR are approved
check-approvals() {
  echo -e "${BLUE}🔍 Checking approval status...${NC}"
  echo ""

  # Find Release PR
  local pr_info=$(gh pr list --state open --base main --head staging --json number,title,isDraft,body --limit 1)

  if [ "$pr_info" = "[]" ]; then
    echo -e "${YELLOW}⚠️  No Release PR found${NC}"
    echo -e "${BLUE}💡 Run ${YELLOW}update-release-pr${BLUE} to create one${NC}"
    return 0
  fi

  local pr_number=$(echo "$pr_info" | jq -r '.[0].number')
  local pr_title=$(echo "$pr_info" | jq -r '.[0].title')
  local is_draft=$(echo "$pr_info" | jq -r '.[0].isDraft')
  local pr_body=$(echo "$pr_info" | jq -r '.[0].body')

  echo -e "${BLUE}📋 Release PR #${pr_number}:${NC} $pr_title"
  if [ "$is_draft" = "true" ]; then
    echo -e "  Status: ${YELLOW}Draft${NC}"
  else
    echo -e "  Status: ${GREEN}Ready for review${NC}"
  fi
  echo ""

  # Extract issue numbers from PR body
  local issues=$(echo "$pr_body" | grep -oE '#[0-9]+' | sed 's/#//' | sort -u)

  if [ -z "$issues" ]; then
    echo -e "${YELLOW}⚠️  No issues found in PR body${NC}"
    return 0
  fi

  echo -e "${BLUE}📊 Checking approval status for each issue:${NC}"
  echo ""

  local all_approved=true
  local approved_count=0
  local total_count=0

  for issue in $issues; do
    total_count=$((total_count + 1))

    # Get issue labels
    local labels=$(gh issue view "$issue" --json labels --jq '.labels[].name' | tr '\n' ',' | sed 's/,$//')

    if echo "$labels" | grep -q "✅ tested-in-staging"; then
      echo -e "  ✅ Issue #${issue} - ${GREEN}Approved${NC}"
      approved_count=$((approved_count + 1))
    else
      echo -e "  ⏳ Issue #${issue} - ${YELLOW}Waiting for approval${NC}"
      all_approved=false
    fi
  done

  echo ""
  echo -e "${YELLOW}📈 Progress: ${approved_count}/${total_count} issues approved${NC}"
  echo ""

  if [ "$all_approved" = true ]; then
    echo -e "${GREEN}🎉 All issues approved! Ready to deploy to production.${NC}"
    echo ""
    echo -e "${BLUE}💡 Next steps:${NC}"
    if [ "$is_draft" = "true" ]; then
      echo -e "  1. ${YELLOW}gh pr ready $pr_number${NC} - Mark PR as ready for review"
    fi
    echo -e "  2. ${YELLOW}gh pr merge $pr_number --merge${NC} - Merge to main and deploy"
  else
    echo -e "${YELLOW}⏳ Waiting for all issues to be tested and approved in staging.${NC}"
    echo ""
    echo -e "${BLUE}💡 Approval process:${NC}"
    echo -e "  1. Test each issue in staging environment"
    echo -e "  2. Case owner comments \"測試通過\" or \"approved\" on issue"
    echo -e "  3. GitHub Actions auto-adds \"✅ tested-in-staging\" label"
    echo -e "  4. When all approved, PR auto-marks as ready for review"
  fi

  echo ""
  echo -e "${BLUE}🌐 Staging URLs:${NC}"
  echo -e "  Frontend: $STAGING_FRONTEND_URL"
  echo -e "  Backend:  $STAGING_BACKEND_URL"
}

# Show help
git-flow-help() {
  echo -e "${BLUE}🤖 Git Issue PR Flow Agent - Available Commands${NC}"
  echo ""
  echo -e "${GREEN}Feature Development:${NC}"
  echo -e "  ${YELLOW}create-feature-fix <issue> <desc>${NC}  - Create fix branch for issue"
  echo -e "  ${YELLOW}create-feature <desc>${NC}              - Create feature branch"
  echo -e "  ${YELLOW}deploy-feature <issue>${NC}             - Deploy to staging (with issue)"
  echo -e "  ${YELLOW}deploy-feature-no-issue${NC}            - Deploy to staging (no issue)"
  echo ""
  echo -e "${GREEN}Release Management:${NC}"
  echo -e "  ${YELLOW}create-release-pr${NC}                  - Create/update release PR"
  echo -e "  ${YELLOW}update-release-pr${NC}                  - Alias for create-release-pr"
  echo -e "  ${YELLOW}check-approvals${NC}                    - Check approval status for release"
  echo ""
  echo -e "${GREEN}Status & Info:${NC}"
  echo -e "  ${YELLOW}git-flow-status${NC}                    - Show current workflow status"
  echo -e "  ${YELLOW}patrol-issues${NC}                      - List and analyze open GitHub issues"
  echo -e "  ${YELLOW}git-flow-help${NC}                      - Show this help message"
  echo ""
  echo -e "${BLUE}📚 Example Workflow:${NC}"
  echo -e "  1. ${YELLOW}create-feature-fix 7 student-login-loading${NC}"
  echo -e "  2. Make changes and commit"
  echo -e "  3. ${YELLOW}deploy-feature 7${NC}"
  echo -e "  4. Test in staging"
  echo -e "  5. ${YELLOW}update-release-pr${NC}"
  echo -e "  6. Case owner tests and comments \"測試通過\" (auto-adds label)"
  echo -e "  7. ${YELLOW}check-approvals${NC} (verify all issues approved)"
  echo -e "  8. ${YELLOW}gh pr merge <PR_NUMBER>${NC} (auto-ready when all approved)"
}

# Export functions for use in shell
export -f create-feature-fix
export -f create-feature
export -f deploy-feature
export -f deploy-feature-no-issue
export -f create-release-pr
export -f update-release-pr
export -f git-flow-status
export -f patrol-issues
export -f check-approvals
export -f git-flow-help

echo -e "${GREEN}✅ Git Issue PR Flow Agent loaded${NC}"
echo -e "${BLUE}Run ${YELLOW}git-flow-help${NC}${BLUE} to see available commands${NC}"
