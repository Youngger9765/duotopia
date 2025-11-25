# 🚨 Issue 處理強制 Checklist

**⚠️ 每次處理 GitHub Issue 都必須完整執行這個 Checklist，一步都不能跳過！**

---

## 📋 Phase 1: 開始前檢查（0 commits）

### ✅ 1.1 確認 Issue 存在
```bash
gh issue view <ISSUE_NUMBER>
```
- [ ] Issue 已創建
- [ ] Issue 有清楚的問題描述
- [ ] 理解問題內容

### ✅ 1.2 檢查是否涉及 Schema 變更
```bash
# 檢查是否需要修改這些檔案
ls backend/alembic/versions/
ls backend/app/models/
```
- [ ] 如果涉及 DB schema 變更 → **停止自動處理，等待人工批准**
- [ ] 如果不涉及 → 繼續

### ✅ 1.3 確認當前 branch 是 staging
```bash
git checkout staging
git pull origin staging
git status  # 確保 clean
```
- [ ] 在 staging branch
- [ ] 已 pull 最新
- [ ] Working directory clean

---

## 📋 Phase 2: 創建 Feature Branch（0 commits）

### ✅ 2.1 創建 feature branch（使用 agent）
```bash
source /Users/young/project/duotopia/.claude/agents/git-issue-pr-flow.sh
create-feature-fix <ISSUE_NUMBER> <description>
```
- [ ] Branch 名稱格式正確：`fix/issue-<NUM>-<description>`
- [ ] 已切換到 feature branch
- [ ] Branch 從 staging 分出

### ⚠️ 2.2 **絕對不要在 staging 直接 commit**
```bash
# ❌ 錯誤示範
git checkout staging
git commit -m "fix something"  # 這是錯的！

# ✅ 正確做法
git checkout fix/issue-X-xxx   # 必須在 feature branch
git commit -m "fix something"
```
- [ ] 確認當前在 feature branch（不是 staging！）

---

## 📋 Phase 3: TDD 開發（開始 commit）

### ✅ 3.1 寫測試（Red Phase）
```bash
# 創建測試檔案
touch backend/tests/integration/api/test_issue_<NUM>.py
# 或 frontend/tests/e2e/test_issue_<NUM>.spec.ts
```
- [ ] 測試檔案已創建
- [ ] 測試現在應該 FAIL（確認問題存在）

### ✅ 3.2 修復問題（Green Phase）
```bash
# 修改程式碼
# ...
```
- [ ] 程式碼已修改
- [ ] 測試現在應該 PASS

### ✅ 3.3 Commit（使用正確的 commit message）
```bash
git add .
# ⚠️ 重要：使用 "Related to #N"，不要用 "Fixes #N"
git commit -m "fix: [描述] (Related to #<ISSUE_NUMBER>)"
```
- [ ] Commit message 包含 `Related to #<NUM>`
- [ ] **絕對不要用** `Fixes #<NUM>`（會提前關閉 issue）

### ✅ 3.4 本地測試
```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm run typecheck && npm run build
```
- [ ] 所有測試通過
- [ ] TypeScript 編譯通過
- [ ] 沒有 console.log 或 debug code

---

## 📋 Phase 4: Push & Per-Issue Test Environment（觸發 CI/CD）

### ✅ 4.1 Push feature branch
```bash
git push origin fix/issue-<NUM>-xxx
```
- [ ] Push 成功
- [ ] **確認 push 的是 feature branch，不是 staging！**

### ✅ 4.2 等待 Per-Issue Test Environment 部署
```bash
# 監控 GitHub Actions
gh run list --branch fix/issue-<NUM>-xxx --limit 5
```
- [ ] GitHub Actions 開始執行
- [ ] Per-Issue Test Environment 部署成功
- [ ] 在 Issue 中看到自動留言的測試 URLs

---

## 📋 Phase 5: 創建 PR（技術層）

### ✅ 5.1 **強制創建 PR** - 這是最重要的步驟！
```bash
gh pr create --base staging --head fix/issue-<NUM>-xxx \
  --title "Fix: [問題描述]" \
  --body "Related to #<ISSUE_NUMBER>

## 🎯 Purpose
[一句話描述]

## 🔍 Problem Analysis
[5 Why 根因分析]

## ✅ Solution
[技術方案]

## 🧪 Testing
[測試覆蓋]

（使用 .github/pull_request_template.md 填寫完整內容）"
```
- [ ] **PR 已創建**（這是強制步驟！）
- [ ] PR base 是 `staging`
- [ ] PR head 是 `fix/issue-<NUM>-xxx`
- [ ] PR description 包含完整工程報告
- [ ] PR description 使用 `Related to #<NUM>`

### ⚠️ 5.2 絕對不能跳過 PR
```
❌ 錯誤做法：
git checkout staging
git merge fix/issue-X-xxx  # 直接 merge，沒有 PR
git push origin staging

✅ 正確做法：
創建 PR → CI/CD 檢查 → Code Review → Merge PR
```
- [ ] 理解為什麼需要 PR（Code Review + CI/CD Gate）

---

## 📋 Phase 6: CI/CD 自動檢查（等待）

### ✅ 6.1 監控 PR 中的 CI/CD
```bash
gh pr checks <PR_NUMBER>
```
- [ ] GitHub Actions 在 PR 中執行
- [ ] 所有 tests 通過（pytest, npm test）
- [ ] TypeScript 編譯通過
- [ ] ESLint 檢查通過
- [ ] Build 成功

### ✅ 6.2 如果 CI/CD 失敗
```bash
# 修復問題
git add .
git commit -m "fix: [修復 CI/CD 問題]"
git push origin fix/issue-<NUM>-xxx
# → PR 會自動更新，CI/CD 重新執行
```
- [ ] 修復所有 CI/CD 錯誤
- [ ] PR 中所有檢查都是綠色 ✅

---

## 📋 Phase 7: 在 Issue 提供測試指引（業務層）

### ✅ 7.1 在 Issue 留言（給案主，用業務語言）
```bash
gh issue comment <ISSUE_NUMBER> --body "## 🧪 測試指引

### 測試環境
- **Per-Issue Test Environment**: https://duotopia-preview-issue-<NUM>-frontend.run.app
- **測試帳號**: [如果需要]

### 測試步驟
1. [步驟 1 - 用業務語言]
2. [步驟 2 - 用業務語言]
3. [步驟 3 - 用業務語言]

### 預期結果
- ✅ [應該看到什麼]
- ❌ [不應該看到什麼]

### 測試通過標準
如果以上都符合，請留言「測試通過」或「✅」

**技術細節請看 PR #<PR_NUM>**"
```
- [ ] Issue 留言已發送
- [ ] 使用業務語言（案主看得懂）
- [ ] 提供 Per-Issue Test Environment URL
- [ ] 提供清楚的測試步驟
- [ ] 連結到 PR（技術細節）

---

## 📋 Phase 8: 等待雙重批准

### ✅ 8.1 等待系統通過（CI/CD）
- [ ] PR 中所有 GitHub Actions 綠燈 ✅
- [ ] 所有自動化測試通過

### ✅ 8.2 等待業務通過（案主）
```bash
# 案主在 Issue 中留言「測試通過」或「✅」
```
- [ ] 案主在 Per-Issue Test Environment 測試
- [ ] 案主在 Issue 中留言批准

### ✅ 8.3 檢查批准狀態
```bash
check-approvals
```
- [ ] 執行 `check-approvals` 自動偵測
- [ ] Issue 有 `✅ tested-in-staging` label

---

## 📋 Phase 9: Merge PR to Staging

### ✅ 9.1 雙重批准確認
```
確認清單：
✅ 系統通過：PR 中 CI/CD 全部綠燈
✅ 業務通過：Issue 中案主批准
```
- [ ] 兩個批准都完成

### ✅ 9.2 Merge PR
```bash
gh pr merge <PR_NUMBER> --squash
```
- [ ] PR 已 merge 到 staging
- [ ] PR 狀態變成 MERGED
- [ ] Staging 包含修復

### ⚠️ 9.3 絕對不要手動 merge
```bash
# ❌ 錯誤做法
git checkout staging
git merge fix/issue-X-xxx
git push origin staging

# ✅ 正確做法
gh pr merge <PR_NUMBER> --squash
```
- [ ] 使用 `gh pr merge` 指令
- [ ] 不要手動 git merge

---

## 📋 Phase 10: 部署到 Staging 後通知

### ✅ 10.1 在 Issue 通知案主
```bash
gh issue comment <ISSUE_NUMBER> --body "✅ 已部署到 Staging

**測試 URL**:
- Frontend: https://duotopia-staging-frontend-...
- Backend: https://duotopia-staging-backend-...

請在 Staging 環境最終確認。"
```
- [ ] Issue 留言已發送
- [ ] 提供 Staging URLs

### ✅ 10.2 清理 Per-Issue Test Environment
```bash
# Per-Issue Test Environment 會在 Issue 關閉時自動清理
# 或手動清理：
gh workflow run cleanup-preview.yml -f issue_number=<NUM>
```
- [ ] 了解清理機制

---

## 📋 Phase 11: Production 發布（最後階段）

### ✅ 11.1 創建 Release PR
```bash
update-release-pr
```
- [ ] Release PR 已創建（staging → main）
- [ ] Release PR 包含 `Fixes #<NUM>`
- [ ] Release PR 列出所有要發布的 issues

### ✅ 11.2 Merge to Production
```bash
gh pr merge <RELEASE_PR_NUMBER> --merge
```
- [ ] Release PR merge 到 main
- [ ] Issue 自動關閉
- [ ] Production 部署完成

---

## 🔴 絕對禁止的操作

### ❌ 1. 直接在 staging commit
```bash
git checkout staging
git commit -m "fix"     # ❌ 絕對不行！
git push origin staging # ❌ 絕對不行！
```

### ❌ 2. 跳過 PR
```bash
git checkout staging
git merge fix/issue-X   # ❌ 沒有 PR = 違規
```

### ❌ 3. 使用 Fixes 關鍵字在 feature branch
```bash
git commit -m "Fixes #18"  # ❌ 會提前關閉 issue
```

### ❌ 4. 沒有測試就 merge
```bash
gh pr merge <NUM> # 但 CI/CD 失敗  # ❌ 絕對不行
```

### ❌ 5. 沒有案主批准就 merge
```bash
gh pr merge <NUM> # 但案主還沒測試  # ❌ 絕對不行
```

---

## ✅ 完整流程摘要（記住這個！）

```
1. 確認 Issue
2. 創建 feature branch (fix/issue-X-xxx)
3. TDD 開發 (Red → Green → Refactor)
4. Commit (Related to #X)
5. Push feature branch
6. ⚠️ **創建 PR** (fix/issue-X-xxx → staging) ← 強制步驟！
7. 等待 CI/CD 通過
8. 在 Issue 提供測試指引
9. 等待案主批准
10. ⚠️ **Merge PR** (gh pr merge) ← 強制步驟！
11. 在 Issue 通知部署完成
12. 創建 Release PR (staging → main)
13. Merge to production
```

---

## 📊 檢查點：如何驗證流程正確？

### ✅ 檢查點 1: 是否有 PR？
```bash
gh pr list --head fix/issue-<NUM>-xxx
```
- 應該看到一個 PR
- **如果沒有 → 流程錯誤！**

### ✅ 檢查點 2: PR 是否 merge？
```bash
gh pr view <PR_NUM> --json mergedAt
```
- `mergedAt` 應該有值
- **如果是 null → 流程錯誤！**

### ✅ 檢查點 3: PR 中是否有 CI/CD 結果？
```bash
gh pr checks <PR_NUM>
```
- 應該看到 GitHub Actions 執行結果
- **如果沒有 → 流程錯誤！**

### ✅ 檢查點 4: Issue 是否有測試指引？
```bash
gh issue view <NUM> --json comments
```
- 應該看到測試指引留言
- **如果沒有 → 流程不完整！**

---

## 🚨 如果違反流程怎麼辦？

### 情況 1: 已經直接 commit 到 staging
**補救措施**：
1. ❌ **不要**創建 retrospective PR（只是自欺欺人）
2. ✅ **認錯**：在 Issue 說明違反了流程
3. ✅ **記取教訓**：下次嚴格遵守
4. ✅ **繼續前進**：讓案主測試 staging

### 情況 2: 忘記創建 PR
**補救措施**：
1. ❌ **不要** merge 到 staging
2. ✅ **立即創建 PR**
3. ✅ **等待 CI/CD**
4. ✅ **正常流程繼續**

---

## 📝 Checklist 使用方式

**每次處理 Issue 時**：
1. 打開這個檔案
2. 逐項檢查 ✅
3. 完成一項打勾一項
4. **絕對不跳過任何步驟**

**如果不確定**：
- 寧可多問一次
- 寧可多檢查一次
- **不要自作主張跳過步驟**

---

**記住：流程存在是有原因的！**
- PR = Code Review + CI/CD Gate
- Issue = 業務追蹤
- 兩者缺一不可！
