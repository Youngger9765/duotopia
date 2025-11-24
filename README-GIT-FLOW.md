# Git Issue PR Flow 自動化指南

本專案使用自動化 Git Issue PR Flow 工具簡化開發流程。

## 🎯 工作流程概覽

```
Issue → Feature Branch → Staging (auto-deploy) → Main (Release PR)
```

## 📦 快速開始

### 1. 安裝 Git Issue PR Flow Agent

```bash
# 在終端機執行（只需執行一次）
echo 'source ~/project/duotopia/.claude/agents/git-issue-pr-flow.sh' >> ~/.zshrc
source ~/.zshrc

# 驗證安裝
git-flow-help
```

### 2. 查看當前狀態

```bash
git-flow-status
```

輸出範例：
```
📊 Git Flow Status

Current branch: staging
Status: On staging branch
Next: Run create-release-pr to prepare release

⏳ 2 commit(s) in staging not yet in main

📋 Draft PR #10: 🚀 Release: Staging → Main

🌐 Staging URLs:
  Frontend: https://duotopia-staging-frontend-316409492201.asia-east1.run.app
  Backend:  https://duotopia-staging-backend-316409492201.asia-east1.run.app
```

## 🔧 常用工作流程

### Scenario 1: 修復一個 Issue

```bash
# 1. 創建 feature branch（從 staging 分支）
create-feature-fix 7 student-login-loading

# 2. 修改代碼並測試
npm run build
npm run typecheck
# ... 實際測試功能 ...

# 3. Commit 修改
git add .
git commit -m "fix: 修復學生登入 Step 1 的錯誤訊息閃現和 loading 狀態問題"

# 4. 部署到 staging（自動執行以下操作）
#    - Merge feature branch 到 staging
#    - Push 到 GitHub 觸發 CI/CD
#    - 在 Issue 中留言部署資訊
deploy-feature 7

# 5. 測試 staging 環境
open https://duotopia-staging-frontend-316409492201.asia-east1.run.app

# 6. 確認修復後，更新 Release PR
update-release-pr
```

### Scenario 2: 開發新功能（不關聯 Issue）

```bash
# 1. 創建 feature branch
create-feature audio-playback-refactor

# 2. 修改代碼並測試
# ... 開發 + 測試 ...

# 3. Commit 修改
git add .
git commit -m "feat: 重構錄音播放架構"

# 4. 部署到 staging
deploy-feature-no-issue

# 5. 更新 Release PR
update-release-pr
```

### Scenario 3: 累積多個修復後發布

```bash
# 假設已經部署了多個 fixes 到 staging
# Issue #7, #10, #12 都已修復並部署

# 1. 創建/更新 Release PR
update-release-pr
# 這會自動找出所有相關 issues 並加入 "Fixes #7, #10, #12"

# 2. 測試所有修復
# ... 在 staging 環境測試 ...

# 3. 確認無誤後，標記 PR 為 ready
gh pr list --base main --head staging  # 查看 PR 編號
gh pr ready 10

# 4. Merge PR 到 main（自動關閉所有 issues）
gh pr merge 10 --merge
```

## 📋 命令參考

| 命令 | 說明 | 範例 |
|------|------|------|
| `create-feature-fix <issue> <desc>` | 創建修復 issue 的 feature branch | `create-feature-fix 7 student-login-loading` |
| `create-feature <desc>` | 創建新功能的 feature branch | `create-feature audio-refactor` |
| `deploy-feature <issue>` | 部署到 staging 並更新 issue | `deploy-feature 7` |
| `deploy-feature-no-issue` | 部署到 staging（不關聯 issue）| `deploy-feature-no-issue` |
| `update-release-pr` | 創建/更新 staging → main 的 Release PR | `update-release-pr` |
| `git-flow-status` | 查看當前工作流程狀態 | `git-flow-status` |
| `git-flow-help` | 顯示所有可用命令 | `git-flow-help` |

## 🌐 環境 URLs

### Staging（測試環境）
- **Frontend**: https://duotopia-staging-frontend-316409492201.asia-east1.run.app
- **Backend**: https://duotopia-staging-backend-316409492201.asia-east1.run.app
- **API Docs**: https://duotopia-staging-backend-316409492201.asia-east1.run.app/docs

### Production（生產環境）
- 部署後由 Cloud Run 自動更新

## 🔍 Git Flow 規則

### ✅ 應該做的事

1. **Feature branch 直接 merge 到 staging** - 使用 `deploy-feature`
2. **Staging 自動觸發 CI/CD** - Push 後自動部署
3. **只為 staging → main 創建 PR** - 用於 Release tracking
4. **PR 使用 Draft 狀態** - 測試完成後再標記為 ready
5. **PR 包含所有相關 issues** - 使用 `Fixes #N` 語法

### ❌ 不應該做的事

1. **不要為 feature → staging 創建 PR** - 直接 merge
2. **不要手動 merge feature branch** - 使用 `deploy-feature`
3. **不要直接 push 到 main** - 必須透過 PR
4. **不要跳過 staging 測試** - 所有變更都要在 staging 測試

## 🐛 疑難排解

### Q: `deploy-feature` 失敗怎麼辦？

```bash
# 檢查是否在 feature branch
git branch --show-current

# 確保 staging 是最新的
git checkout staging
git pull origin staging

# 重新嘗試部署
git checkout fix/issue-7-student-login-loading
deploy-feature 7
```

### Q: 如何修改已經部署的 commit？

```bash
# 在 feature branch 上修改
git add .
git commit --amend

# 重新部署
deploy-feature 7
```

### Q: 如何取消某個 feature 的部署？

```bash
# Revert staging 到指定 commit
git checkout staging
git log  # 找到要回到的 commit
git reset --hard <commit_hash>
git push origin staging --force-with-lease

# ⚠️ 注意：這會影響其他已部署的 features
```

### Q: Release PR 需要修改內容怎麼辦？

```bash
# 直接在 staging 修改後再次執行
update-release-pr

# PR 會自動更新內容
```

## 📚 進階用法

### 自訂 Release PR 內容

```bash
# 手動編輯 PR
gh pr list --base main --head staging  # 找到 PR 編號
gh pr edit 10

# 或是使用 Web UI
gh pr view 10 --web
```

### 批次更新多個 Issues

```bash
# 在 Release PR body 中加入
# Fixes #7, #10, #12, #15
# Merge PR 時會自動關閉這些 issues
```

### 檢視 CI/CD 部署狀態

```bash
# 查看最新的 GitHub Actions 執行
gh run list --branch staging --limit 5

# 查看特定 run 的詳細資訊
gh run view <run_id>
```

## 🎓 最佳實踐

1. **每個 issue 一個 feature branch** - 保持變更範圍小
2. **經常部署到 staging** - 早發現問題早修復
3. **在 staging 充分測試** - 確保功能正常後再 release
4. **使用有意義的 branch 名稱** - 方便追蹤和管理
5. **Commit message 遵循規範** - `fix:`, `feat:`, `refactor:` 等
6. **Release PR 累積適量變更** - 不要太多也不要太少（建議 3-5 個 issues）

## 🔗 相關文件

- [CLAUDE.md](./CLAUDE.md) - 完整的開發指南
- [.claude/agents/git-issue-pr-flow-agent.md](./.claude/agents/git-issue-pr-flow-agent.md) - Agent 詳細文件
- [.claude/agents/git-issue-pr-flow.sh](./.claude/agents/git-issue-pr-flow.sh) - Agent 腳本原始碼
- [CICD.md](./CICD.md) - CI/CD 部署文件

---

**有問題？** 執行 `git-flow-help` 或查看 [.claude/agents/git-issue-pr-flow-agent.md](./.claude/agents/git-issue-pr-flow-agent.md)
