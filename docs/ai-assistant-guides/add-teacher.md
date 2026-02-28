# 新增機構教師

## 角色限制

- `org_owner`（機構擁有者）
- `org_admin`（機構管理員）

> 通用規則見 [common-rules.md](./common-rules.md)

## 功能規則

- 教師屬於組織層級，可選擇性指派到分校

## 對話流程

### Step 0：確認組織（上下文感知）

根據用戶當前頁面自動判斷：

| 用戶所在頁面 | URL 範例 | 已知資訊 | AI 行為 |
|-------------|---------|---------|--------|
| 某分校頁面 | `/organization/schools/5` | 組織 + 分校 | 直接確認：「您目前在 {組織名} / {分校名}，要在 {組織名} 新增教師嗎？」 |
| 某組織頁面 | `/organization/3` | 組織 | 直接確認：「要在 {組織名} 新增教師嗎？」 |
| 其他頁面 | `/organization/dashboard` | 無 | 列出用戶可管理的組織讓用戶選擇 |

- 只有一個組織 → 直接帶入，不詢問

**確認組織後，立即檢查教師額度**：

呼叫 `GET /api/organizations/{org_id}` 取得 `teacher_authorization_count`（授權上限）和目前教師數。

- 未滿額 → 顯示額度資訊後進入 Step 1：「目前教師 8/10 位，還可新增 2 位。」
- 已滿額 → 阻止進入流程：「⚠️ {組織名} 教師名額已滿（10/10），無法新增。請聯繫管理員調整授權數。」
- 無上限設定（`teacher_authorization_count` 為 null）→ 不顯示額度，直接進入 Step 1

### Step 1：收集教師資料（自由輸入）

AI 提示：
> 請提供教師的**姓名**和 **Email**。
> 也可以標註角色（不標註預設為「教師」）。
> 可一次提供多位，例如：
> ```
> 王小明 wang@gmail.com 管理員
> 李大華 lee@gmail.com
> 陳美玲 chen@gmail.com
> ```

**LLM 解析規則**：
- 必須解析出：姓名、email
- 可選解析：角色（「管理員」→ `org_admin`、「教師」或未標註 → `teacher`）
- email 格式驗證：必須包含 `@` 和 `.`
- 如果缺少姓名或 email → 回報哪些資料不完整，請用戶補充
- 如果同一個 email 出現多次 → 提醒用戶並去重

### Step 2：AI 整理 + 用戶確認

AI 將解析結果以表格呈現，並標註驗證狀態：

```
即將在【{組織名}】新增以下教師：

| # | 姓名   | Email            | 角色       | 狀態 |
|---|--------|------------------|-----------|------|
| 1 | 王小明 | wang@gmail.com   | 機構管理員 | ✓   |
| 2 | 李大華 | lee@gmail.com    | 教師       | ✓   |
| 3 | 陳美玲 | chen@gmail.com   | 教師       | ✓   |

請確認，或告訴我需要修改的地方。
```

**額度超出檢查**：

如果新增人數超過剩餘額度，在表格下方提醒：

```
⚠️ 目前教師 8/10 位，剩餘額度 2 位，但清單有 3 位。
請移除部分教師，或聯繫管理員調整授權數。
```

- 超出額度 → 不允許確認，必須減少人數
- 無上限設定 → 不檢查

**Email 格式驗證**：

如果有 email 格式不正確，在表格中標註並阻止執行：

```
| # | 姓名   | Email            | 角色 | 狀態               |
|---|--------|------------------|------|--------------------|
| 1 | 王小明 | wanggmail.com    | 教師 | ⚠️ Email 格式不正確 |
| 2 | 李大華 | lee@gmail.com    | 教師 | ✓                  |

⚠️ 第 1 筆 Email 格式有誤，請修正後才能執行。
```

- 有任何一筆 email 格式不正確 → 不允許確認，必須修正
- 驗證規則：符合標準 email 格式（含 `@` 和域名部分含 `.`）

**用戶可執行的修改**：
- 修改角色：「李大華改成管理員」
- 刪除某位：「把陳美玲移除」
- 新增更多：「再加一個 林志明 lin@gmail.com」
- 修改 email：「王小明的 email 改成 wang@gmail.com」

修改後重新顯示表格，直到所有驗證通過且用戶確認。

### Step 3：逐一執行 + 逐一問分校指派

對確認清單中的每位教師依序執行：

```
正在新增教師 (1/3)...

✅ 王小明 (wang@gmail.com) 已新增為機構管理員
→ 是否指派到分校？
  [台北本校] [信義分校] [兒童部] [略過]
```

用戶選擇後，繼續下一位：

```
✅ 李大華 (lee@gmail.com) 已新增為教師
→ 是否指派到分校？
  [台北本校] [信義分校] [兒童部] [略過]
```

**錯誤處理**：
- 如果 email 已存在於該組織 → 顯示「⚠️ wang@gmail.com 已是該組織成員，已略過」，繼續下一位
- 如果 API 失敗 → 顯示「❌ 新增失敗：{錯誤原因}」，繼續下一位
- 組織已達教師上限 → 顯示「❌ 組織教師名額已滿，剩餘教師無法新增」，停止執行

### Step 4：完成摘要

```
新增完成！

✅ 成功：2 位
  - 王小明 (wang@gmail.com) → 機構管理員 → 台北本校
  - 李大華 (lee@gmail.com) → 教師 → 信義分校

⚠️ 略過：1 位
  - 陳美玲 (chen@gmail.com) → 已是組織成員

📧 新帳號的教師會收到認證信和密碼設定信。
   已有帳號的教師下次登入即可看到機構。
```

## 資料欄位定義

| 欄位 | 型別 | 必填 | 預設值 | 驗證規則 |
|------|------|------|--------|---------|
| name | string | 必填 | - | 1-100 字元 |
| email | string | 必填 | - | 合法 email 格式，max 200 字元 |
| role | string | 選填 | `teacher` | `teacher` \| `org_admin` |

## API 對應

### 查詢教師額度

```
GET /api/organizations/{org_id}

Response 重點欄位:
{
  "teacher_limit": 10    // 授權上限（null = 無限制）
}
```

```
GET /api/organizations/{org_id}/teachers

Response: TeacherInfo[]
- 計算 is_active: true 的數量 = 目前使用數
- 目前使用數 / teacher_limit = 額度使用狀態
```

### 邀請教師到組織

```
POST /api/organizations/{org_id}/teachers/invite

Request Body:
{
  "email": "wang@gmail.com",
  "name": "王小明",
  "role": "teacher"  // 或 "org_admin"
}

Success Response (200):
{
  "id": 1,
  "teacher_id": 42,
  "organization_id": "uuid",
  "role": "teacher",
  "is_active": true,
  "created_at": "2026-02-27T..."
}

Error Cases:
- 409: 教師已在組織中
- 403: 無權限
- 400: 教師名額已滿
```

### 指派教師到分校

```
POST /api/schools/{school_id}/teachers

Request Body:
{
  "teacher_id": 42,       // 從 invite 回應取得
  "roles": ["teacher"]    // "teacher" | "school_director" | "school_admin"
}

Success Response (200):
{
  "id": 1,
  "teacher_id": 42,
  "school_id": 5,
  "roles": ["teacher"],
  "is_active": true
}

Error Cases:
- 409: 教師已在該分校
- 404: 分校不存在
- 403: 無權限
```

## 角色對照表

| 用戶輸入 | 系統角色值 | 顯示名稱 |
|---------|-----------|---------|
| 管理員、機構管理員、admin | `org_admin` | 機構管理員 |
| 教師、老師、teacher、（未標註） | `teacher` | 教師 |

## 上下文資料來源

| 資料 | 來源 |
|------|------|
| 用戶可管理的組織列表 | `GET /api/organizations` |
| 組織下的分校列表 | `GET /api/organizations/{org_id}/schools` |
| 當前頁面的組織/分校 | 前端 URL 路由參數 |
