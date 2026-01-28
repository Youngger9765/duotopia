# Generalize Worktree Skill Plan

> 從 staging 分支: `feature/generalize-worktree-skill`
> 建立日期: 2026-01-27

## 需求分析

### 現狀

目前 `/handle-issue` skill 僅支援處理 GitHub issues：
- 輸入必須是 issue number（例如 `42`, `#42`, `42 43`）
- Branch 命名固定為 `fix/issue-<N>-<description>`
- Worktree 路徑固定為 `.worktrees/issue-<N>`
- 必須從 GitHub 取得 issue 資訊才能運作

### 目標

讓 worktree 隔離開發功能更通用：

1. **支援任意問題描述**：使用者可以用自然語言描述要處理的任務
2. **保留 GitHub issue 支援**：偵測到 issue number 時走原本邏輯
3. **統一觸發方式**：
   - `幫我開 worktree 處理 issue #42, #43` → GitHub issue 模式
   - `幫我開 worktree 處理：實作使用者登出功能` → 通用任務模式

## 設計方案

### 方案 A：擴展現有 handle-issue skill

**優點**：
- 改動最小
- 不需要建立新 skill

**缺點**：
- Skill 名稱 `handle-issue` 語意不符
- 一個 skill 承擔兩種不同邏輯

### 方案 B：建立新的通用 `/worktree` skill（推薦）

**優點**：
- 語意清晰：`/worktree` 表示「使用 worktree 隔離開發」
- 可以根據輸入智慧判斷模式
- `/handle-issue` 可以作為 `/worktree` 的 alias

**缺點**：
- 需要建立新 skill 檔案
- 可能需要重構部分程式碼

### 方案 C：建立兩個獨立 skill

- `/handle-issue` - 專門處理 GitHub issues
- `/worktree` - 處理通用任務

**優點**：
- 職責分離清晰

**缺點**：
- 程式碼重複
- 使用者需要記住兩個命令

## 推薦方案：B

### 新 Skill 設計

```
.claude/skills/
├── worktree/
│   ├── SKILL.md              # 主要 skill 定義
│   └── scripts/
│       ├── setup-worktree.sh     # 通用 worktree 設定
│       ├── setup-issue-worktree.sh  # issue 專用（現有改名）
│       └── cleanup-worktree.sh   # 清理（通用）
└── handle-issue/              # 可保留作為 alias 或刪除
```

### 輸入格式判斷邏輯

```
輸入 $ARGUMENTS
    │
    ├─ 匹配 /^#?\d+(\s+#?\d+)*$/ → GitHub Issue 模式
    │   例如: "42", "#42", "42 43", "#42 #43"
    │
    └─ 其他文字 → 通用任務模式
        例如: "實作使用者登出功能"
```

### Branch 命名規則

| 模式 | Branch 格式 | 範例 |
|------|------------|------|
| GitHub Issue | `fix/issue-<N>-<slug>` | `fix/issue-42-add-logout-button` |
| 通用任務 | `fix/YYYYMMDD-NNN-<slug>` | `fix/20260127-001-implement-user-logout` |

> 通用任務的 `<slug>` 由 AI 分析使用者需求後產生適當描述

### Worktree 路徑

| 模式 | 路徑格式 | 範例 |
|------|---------|------|
| GitHub Issue | `.worktrees/issue-<N>` | `.worktrees/issue-42` |
| 通用任務 | `.worktrees/task-<id>` | `.worktrees/task-20260127-001` |

### SKILL.md 主要結構

```markdown
---
name: worktree
description: |
  Create isolated worktree for development. Use when user mentions:
  - "開 worktree", "用 worktree", "worktree 處理"
  - "handle issue", "fix issue", "work on issue"
  - issue numbers like "#42" with worktree context
  Supports GitHub issues or custom task descriptions.
argument-hint: "<issue-number(s)> | <task-description>"
disable-model-invocation: false  # 允許自動觸發
---

# Worktree Skill

Detect input type:
1. If matches issue pattern (#N, N, multiple) → GitHub Issue Mode
2. Otherwise → General Task Mode (analyze description, generate branch name)

## GitHub Issue Mode
[現有 handle-issue 邏輯]
Branch: fix/issue-<N>-<slug>

## General Task Mode
[新增邏輯]
- Generate task ID: YYYYMMDD-NNN
- Analyze user's request to generate descriptive slug
- Create branch: fix/YYYYMMDD-NNN-<slug>
- Create worktree: .worktrees/task-YYYYMMDD-NNN
- Present plan
- Implement after approval
```

### 自動觸發機制

Skill description 包含觸發詞，讓 Claude 自動判斷何時使用：
- `開 worktree`、`用 worktree`、`worktree 處理`
- `handle issue`、`fix issue`、`work on issue`
- 提到 issue number 並有 worktree 相關語境

設定 `disable-model-invocation: false` 允許模型根據使用者意圖自動呼叫。

## 實作步驟

### Phase 1: 準備工作

1. [ ] 建立新目錄結構 `.claude/skills/worktree/`
2. [ ] 刪除舊的 `.claude/skills/handle-issue/` 目錄

### Phase 2: 核心 Skill 開發

3. [ ] 建立 `worktree/SKILL.md` - 主要 skill 定義
   - 包含自動觸發描述
   - 設定 `disable-model-invocation: false`
   - 實作輸入判斷邏輯（issue vs 通用任務）

4. [ ] 建立 `worktree/scripts/setup-worktree.sh`
   - 支援 issue 模式：`./setup-worktree.sh --issue 42`
   - 支援 task 模式：`./setup-worktree.sh --task "description"`
   - Task ID 自動產生：YYYYMMDD-NNN

5. [ ] 建立 `worktree/scripts/cleanup-worktree.sh`
   - 支援清理 issue worktree
   - 支援清理 task worktree

### Phase 3: 更新文件

6. [ ] 更新 CLAUDE.md 的 skills 表格
   - 移除 `/handle-issue`
   - 新增 `/worktree` 說明

### Phase 4: 測試

7. [ ] 手動測試 GitHub issue 模式
8. [ ] 手動測試通用任務模式
9. [ ] 測試自動觸發功能

## 使用範例

### GitHub Issue 模式

```
使用者: /worktree 42
使用者: /worktree #42 #43
使用者: 幫我開 worktree 處理 issue #42

# 自動觸發（不需要 /worktree 命令）
使用者: 幫我用 worktree 處理 issue #42
使用者: 開 worktree 處理 #42, #43
```

### 通用任務模式

```
使用者: /worktree 實作使用者登出功能
使用者: /worktree fix the navbar alignment issue

# 自動觸發（不需要 /worktree 命令）
使用者: 幫我開 worktree 處理：優化首頁載入速度
使用者: 用 worktree 隔離開發新的付款功能
使用者: 開 worktree 處理這個問題：navbar 在手機版會跑版
```

### Branch 命名範例

| 使用者輸入 | 分析結果 | Branch 名稱 |
|-----------|---------|------------|
| `issue #42` (title: "Add logout button") | Issue 模式 | `fix/issue-42-add-logout-button` |
| `優化首頁載入速度` | Task 模式, 類型: 優化 | `fix/20260127-001-optimize-homepage-loading` |
| `navbar 在手機版會跑版` | Task 模式, 類型: bug | `fix/20260127-002-navbar-mobile-layout` |
| `新增使用者偏好設定` | Task 模式, 類型: feature | `fix/20260127-003-add-user-preferences` |

## 決定事項（已確認）

1. **Skill 名稱**：`/worktree` ✅
2. **舊 `/handle-issue`**：刪除 ✅
3. **Task ID 格式**：`YYYYMMDD-NNN` ✅
4. **自動觸發**：不需要明確使用 `/worktree` 命令，偵測到相關意圖自動觸發 ✅
5. **Branch 命名**：
   - GitHub Issue: `fix/issue-<N>-<description>`
   - 通用任務: `fix/YYYYMMDD-NNN-<description>`（根據需求分析產生描述）

## 相關檔案

- [.claude/skills/handle-issue/SKILL.md](.claude/skills/handle-issue/SKILL.md) - 現有 skill
- [.claude/skills/handle-issue/scripts/setup-worktree.sh](.claude/skills/handle-issue/scripts/setup-worktree.sh)
- [.claude/skills/handle-issue/scripts/cleanup-worktree.sh](.claude/skills/handle-issue/scripts/cleanup-worktree.sh)
- [CLAUDE.md](CLAUDE.md) - Skills 清單
