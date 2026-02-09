# 學生身分整合系統 - 功能規格文檔

## 業務背景

### 問題描述

在 DuoTopia 平台中，同一位學生可能在不同情況下被創建多個帳號：

1. 隸屬於某機構 A 的 1 分校
2. 同時隸屬於機構 A 的 2 分校
3. 又隸屬於機構 B 的 1 校
4. 又隸屬於某個個人教師

這些帳號在不同時間被創建，實際上是同一位學生。

### 業務目標

1. **能辨識他們是同一個人**：透過 Email 認證識別
2. **學生使用 AI 點數時能夠扣到對應機構或對應的個人教師**：點數使用記錄仍針對各自的 Student ID
3. **生成學生學習報告時，以機構或個人教師為單位**：若同一個學生有不同的學習數據在不同的機構或老師身上是正常的

---

## 解決方案設計

### 核心策略

**主帳號 + 連結帳號模式**

- 創建 `StudentIdentity` 表作為「統一身分」
- 每個 Email 對應一個 `StudentIdentity`
- 一個 `StudentIdentity` 可以關聯多個 `Student` 帳號
- 其中一個 `Student` 為「主帳號」，用於登入
- 其他 `Student` 為「連結帳號」，保留所有學習資料和機構關係

### 整合觸發時機

**Email 認證時自動整合**

- 學生完成 Email 驗證時，系統自動檢查是否有相同 Email 的 `StudentIdentity`
- 若有，將此 `Student` 加入既有 `StudentIdentity`
- 若無，創建新 `StudentIdentity`

### 密碼處理策略

**智能選擇密碼（整合時）**

整合時根據以下規則選擇密碼：

1. 如果 `StudentIdentity` 已有修改過的密碼，保持不變
2. 如果 `StudentIdentity` 是預設密碼，但新 `Student` 有修改過，採用新 `Student` 的密碼
3. 如果都是預設密碼（birthdate），保持 `StudentIdentity` 的密碼
4. 如果都修改過，比較修改時間，採用最新的

**密碼統一原則（登入時）**

整合後，學生的密碼完全統一：

- 已整合學生（`password_migrated_to_identity = true`）：所有登入方式都使用 `StudentIdentity.password_hash`
- 未整合學生（`password_migrated_to_identity = false`）：仍使用 `Student.password_hash`（向後兼容）

### 登入流程設計

**兩種登入流程並存，確保平滑過渡**

**流程 1：新流程（Email 直接登入）**

- 學生直接輸入：Email + Password
- 適用對象：已綁定並驗證 Email 的學生
- 登入目標：主帳號（primary_student）
- 優點：最簡單快速

**流程 2：舊流程（4 步驟登入，完全兼容）**

1. 輸入老師 Email → 驗證老師存在
2. 選擇班級 → 顯示該老師的班級列表
3. 選擇自己的名字 → 顯示該班級的學生列表
4. 輸入密碼 → 驗證密碼並登入

舊流程特性：

- 適用對象：**所有學生**（包括未綁定 Email 的學生）
- 保持前端介面不變，完全向後兼容
- **密碼驗證邏輯**：
  - 未整合學生：使用 `Student.password_hash`
  - 已整合學生：使用 `StudentIdentity.password_hash`（統一密碼，舊密碼失效）

### 1Campus SSO 整合策略

**整合定位：Option A - 1Campus 為主要學校登入方式**

- 1Campus 帳號作為**學校學生的主要登入方式**
- 學生可額外綁定個人 Email（如 Gmail）作為次要登入方式
- 補習班的個人教師學生仍使用傳統 Email 註冊/登入

**登入流程擴充：新增流程 3（1Campus SSO 登入）**

1. 學生點擊「學校帳號登入」
2. 重導向到 1Campus OAuth 授權頁面
3. 學生輸入縣市帳號密碼（如 `taipei.s123@1campus.net`）
4. 授權成功後，系統收到：
   - `studentAcc`（Email 格式的帳號，如 `taipei.s123@1campus.net`）
   - `studentID`（待確認：可能是身分證字號或教育部學號）
   - `schoolDsns`（學校代碼）
5. 系統處理：
   - 若 `studentAcc` 已存在 → 直接登入
   - 若 `studentAcc` 首次登入 → 創建 Student + StudentIdentity
   - 若 `studentID` 與其他帳號相同 → **觸發合併提示（見下方）**

### 學生身分識別機制

**核心識別欄位：`studentID`（來自 1Campus）**

- **待確認**：1Campus API 回傳的 `studentID` 是否為身分證字號
- **備案**：若 1Campus 不提供身分證字號，需在系統內增加選填欄位

**StudentIdentity 增加屬性**：

- `national_id_hash`：身分證字號的 SHA-256 hash（選填）
- `one_campus_student_id`：1Campus 的 studentID（選填）

**識別優先順序**：

1. **優先使用** `one_campus_student_id`（或 `national_id_hash`）比對
2. **次要使用** `verified_email` 比對
3. **輔助判斷** 生日 + 姓名組合（較弱）

### 帳號合併觸發與確認流程

**觸發時機：系統自動偵測**

當學生登入時（Email 登入或 1Campus 登入），系統自動檢查：

```
檢查條件（任一符合即觸發）：
1. 其他 StudentIdentity 的 one_campus_student_id 相同
2. 其他 StudentIdentity 的 national_id_hash 相同且非空
3. 其他 StudentIdentity 的 verified_email 相同
```

**確認流程：學生端確認（非教師操作）**

```
學生登入成功後：
├─ 系統偵測到疑似重複帳號
├─ 顯示提示視窗：
│  ┌────────────────────────────────────────┐
│  │ 🔗 偵測到您可能已有其他學習帳號         │
│  │                                        │
│  │ 我們發現以下帳號可能屬於同一位學生：   │
│  │ • taipei.s123@1campus.net (台北市○○國中) │
│  │ • john@gmail.com (補習班)              │
│  │                                        │
│  │ 合併後的效果：                         │
│  │ ✅ 統一密碼管理                        │
│  │ ✅ 可用任一帳號登入                    │
│  │ ✅ 學習記錄保持獨立（分校/機構分開）   │
│  │                                        │
│  │ [確認合併]  [暫時不要]                 │
│  └────────────────────────────────────────┘
│
├─ 學生點擊「確認合併」
│  └─ 執行合併邏輯（同 Email 驗證合併）
│
└─ 學生點擊「暫時不要」
   └─ 略過，下次登入時仍會提示
```

**重要原則**：

- ✅ 系統自動偵測疑似重複帳號
- ✅ 由**學生本人**在登入後確認是否合併
- ❌ **不需要**教師手動標記或判斷
- ⚠️ 合併操作不可逆（需謹慎）

### 跨縣市轉學處理

**場景**：學生從基隆市轉學到台北市

**1Campus 行為**：

- 舊帳號：`keelung.s123@1campus.net`（基隆市教網中心）
- 新帳號：`taipei.s456@1campus.net`（台北市教網中心）
- **兩個帳號完全不同**，無自動關聯

**DuoTopia 處理策略**：

1. **依賴 studentID 識別**：
   - 若 `studentID` 為身分證字號 → 兩個帳號的 `one_campus_student_id` 相同
   - 系統自動偵測並提示學生合併
   - 合併後，兩個 1Campus 帳號都能登入（指向同一 StudentIdentity）

2. **舊帳號狀態**：
   - 1Campus 可能保留舊帳號（但無法登入，因為已轉出該縣市）
   - 也可能刪除舊帳號（由各縣市教網中心決定）
   - DuoTopia 不需處理 1Campus 的帳號狀態

3. **學習記錄保留**：
   - 基隆市的學習記錄保留在原 Student #123
   - 台北市的學習記錄保留在新 Student #456
   - 兩者透過 StudentIdentity 關聯，但資料獨立

**範例流程**：

```
學生小明在基隆讀國中：
├─ 用 keelung.s123@1campus.net 登入
├─ 創建 Student #123
├─ 創建 StudentIdentity (one_campus_student_id = "A123456789")
└─ 學習記錄儲存在 Student #123

小明轉學到台北：
├─ 1Campus 給新帳號：taipei.s456@1campus.net
├─ 小明用新帳號登入 DuoTopia
├─ 系統創建 Student #456
├─ 系統偵測：one_campus_student_id = "A123456789" 已存在
├─ 提示小明：「偵測到您可能已有基隆的學習記錄，是否合併？」
├─ 小明確認合併
└─ Student #456 關聯到既有 StudentIdentity
    ├─ 基隆學習記錄：Student #123（保留）
    └─ 台北學習記錄：Student #456（新增）
```

---

## 資料模型設計

### 新增實體：StudentIdentity

**業務定義**：
整合同一位學生在不同機構/教師下創建的多個 Student 帳號，透過 Email 驗證或身分識別資訊識別為同一人。

**核心屬性**：

- `verified_email`：已驗證的 Email（唯一識別碼，可為空）
- `primary_student_id`：主帳號 ID（學生登入時使用）
- `password_hash`：統一密碼
- `password_changed`：是否修改過密碼
- `merge_source`：整合來源（email_verification / one_campus_sso / manual_merge）

**新增身分識別屬性（用於跨帳號識別）**：

- `national_id_hash`：身分證字號的 SHA-256 hash（選填，用於識別同一學生）
- `one_campus_student_id`：1Campus 系統的 studentID（選填，來自 OAuth 回傳資料）

**識別邏輯**：

- 系統比對 `one_campus_student_id` 或 `national_id_hash`（若非空）
- 發現相同值時，提示學生確認是否合併帳號
- 由學生本人決定是否執行合併

詳細設計請參考：[erm-student-identity.dbml](./erm-student-identity.dbml)

### 修改現有實體：Student

**新增屬性**：

- `identity_id`：關聯的 StudentIdentity ID
- `is_primary_account`：是否為主帳號
- `password_migrated_to_identity`：密碼是否已遷移到 Identity

**業務規則**：

- 整合後，`Student` 變成連結帳號
- 學習資料、機構關係仍保留在此 `Student` 記錄
- 密碼管理移交給 `StudentIdentity`

---

## 功能規格

### 1. Email 認證時自動整合學生身分

**功能描述**：
當學生完成 Email 驗證時，系統自動檢查並整合同一 Email 的多個學生帳號。

**業務規則**：

- 首次 Email 認證時創建新 StudentIdentity
- 相同 Email 認證時整合到既有 StudentIdentity
- 智能密碼選擇策略
- 整合後資料保留驗證
- Email 驗證失敗時不整合

詳細驗收標準請參考：[student-identity-merge-on-email-verification.feature](./features/student-identity/student-identity-merge-on-email-verification.feature)

### 2. 學生使用統一身分登入

**功能描述**：
系統支援兩種登入流程並存，確保平滑過渡且兼容所有學生：

**新流程（Email 直接登入）**：

- 學生直接輸入 Email + Password
- 適用於已綁定並驗證 Email 的學生
- 登入到主帳號（primary_student）
- 最簡單快速的登入方式

**舊流程（4 步驟登入，完全兼容）**：

1. 輸入老師 Email
2. 選擇班級
3. 選擇自己的名字
4. 輸入密碼

舊流程特性：

- 適用於**所有學生**（包括未綁定 Email 的學生）
- 保持前端流程不變，向後完全兼容
- **密碼統一原則**：若學生已整合到 StudentIdentity（`password_migrated_to_identity = true`），則**必須使用統一密碼**，舊密碼將失效

**業務規則**：

- **新流程**：使用 Email 登入到主帳號
- **舊流程**：支援 4 步驟登入（老師Email→班級→學生→密碼）
  - 未整合學生：使用自己的 `Student.password_hash`
  - 已整合學生：使用 `StudentIdentity.password_hash`（統一密碼）
- 向後兼容：API 層面仍支援 Student ID 登入（`/api/auth/student/login`）
- 主帳號異常時的容錯處理

**密碼驗證邏輯**：

```
/api/auth/student/login (舊流程最終呼叫)：
├─ 找到 Student (by ID)
├─ 檢查 password_migrated_to_identity
│  ├─ true → 使用 StudentIdentity.password_hash 驗證（統一密碼）
│  └─ false → 使用 Student.password_hash 驗證（向後兼容）
└─ 驗證成功 → 返回 token

新增 Email 登入 API：
├─ 找到 StudentIdentity (by verified_email)
├─ 使用 StudentIdentity.password_hash 驗證
├─ 登入到 primary_student
└─ 返回 token
```

詳細驗收標準請參考：[student-login-with-identity.feature](./features/student-identity/student-login-with-identity.feature)

### 3. 整合後的點數扣除與學習報告

**功能描述**：
學生完成身分整合後，AI 點數仍扣除到各自的機構/教師，學習報告以機構/教師為單位獨立呈現。

**業務規則**：

- 點數扣除針對各自的機構/教師
- 學習報告以機構/教師為單位獨立呈現
- 學生可查看跨機構的統一學習檔案（可選功能）
- 整合不影響既有資料查詢邏輯

詳細驗收標準請參考：[point-deduction-and-reports-after-merge.feature](./features/student-identity/point-deduction-and-reports-after-merge.feature)

### 4. 1Campus SSO 整合與帳號合併

**功能描述**：
學校學生可使用教育部 1Campus 單一登入系統登入，系統自動偵測疑似重複帳號並提示學生確認合併。

**業務規則**：

- 1Campus 為學校學生的主要登入方式
- 系統透過 `one_campus_student_id` 或 `national_id_hash` 識別同一學生
- 偵測到疑似重複帳號時，在學生端顯示提示並由學生確認合併
- 跨縣市轉學時，系統自動識別並提示合併
- 支援外籍學生居留證號
- 合併操作不可逆

詳細驗收標準請參考：[student-1campus-sso-integration.feature](./features/student-identity/student-1campus-sso-integration.feature)

---

## 業務關係圖

```
StudentIdentity (統一身分)
├─ primary_student_id = 101  (主帳號)
├─ verified_email = "john@email.com"
└─ linked_students (關聯帳號):
   ├─ Student #101 (A機構-1分校) ← 主帳號
   │  ├─ 學習資料 (StudentItemProgress)
   │  ├─ 機構關係 (StudentSchool)
   │  └─ 點數使用記錄 (PointUsageLog.student_id = 101)
   │
   ├─ Student #205 (A機構-2分校)
   │  ├─ 學習資料 (StudentItemProgress)
   │  ├─ 機構關係 (StudentSchool)
   │  └─ 點數使用記錄 (PointUsageLog.student_id = 205)
   │
   ├─ Student #308 (B機構-1校)
   │  └─ ... (同上)
   │
   └─ Student #412 (個人教師C)
      └─ ... (同上)
```

---

## 資料保留原則

### ✅ 保持獨立的資料

| 資料類型 | 關聯方式                                                                     | 說明                            |
| -------- | ---------------------------------------------------------------------------- | ------------------------------- |
| 學習進度 | `StudentItemProgress.student_assignment_id` → `StudentAssignment.student_id` | 每個 Student 的學習資料獨立     |
| 練習記錄 | `PracticeSession.student_id`                                                 | 每個 Student 的練習記錄獨立     |
| 機構關係 | `StudentSchool.student_id`                                                   | 每個 Student 的機構關係獨立     |
| 班級關係 | `ClassroomStudent.student_id`                                                | 每個 Student 的班級關係獨立     |
| 點數使用 | `PointUsageLog.student_id`                                                   | 點數扣除仍針對各自的 Student ID |
| 作業指派 | `StudentAssignment.student_id`                                               | 作業仍針對各自的 Student ID     |

### 🔄 整合的資料

| 資料類型 | 整合方式                         | 說明                     |
| -------- | -------------------------------- | ------------------------ |
| 登入認證 | `StudentIdentity.password_hash`  | 所有連結帳號共用統一密碼 |
| Email    | `StudentIdentity.verified_email` | 統一的 Email 識別        |

---

## 查詢行為設計

### 機構/教師查詢（不受整合影響）

**原則**：機構和教師查詢學生時，仍使用各自的 `Student` 記錄。

範例：

```sql
-- A機構查看學生列表（不受整合影響）
SELECT s.*
FROM students s
JOIN student_schools ss ON s.id = ss.student_id
WHERE ss.school_id IN (SELECT id FROM schools WHERE organization_id = 'A機構')
```

### 學生自我查詢（可跨機構）

**原則**：學生登入後，可選擇查看單一帳號資料或統一檔案。

範例：

```sql
-- 學生查看統一學習檔案
SELECT s.*, COUNT(sip.id) as learning_records_count
FROM students s
LEFT JOIN student_item_progress sip ON sip.student_assignment_id IN (
  SELECT id FROM student_assignments WHERE student_id = s.id
)
WHERE s.identity_id = 1
GROUP BY s.id
```

---

## 實作建議（供工程師參考）

### Phase 1: 資料表建立

- 創建 `student_identities` 表
- 在 `students` 表新增欄位
- 建立 Migration

### Phase 2: Email 驗證整合流程

- 實作 Email 認證時的整合邏輯
- 實作智能密碼合併
- 測試重複 Email 整合情境

### Phase 3: 登入邏輯升級

**新流程（Email 直接登入）**：

- 新增 API：`POST /api/auth/student/email-login`
- 接收 `{ email, password }`
- 查詢 StudentIdentity，驗證密碼，返回 primary_student 的 token

**舊流程（4步驟登入）保持兼容**：

- 保留現有 API：
  - `POST /api/public/validate-teacher`
  - `GET /api/public/teacher-classrooms`
  - `GET /api/public/classroom-students/{classroom_id}`
  - `POST /api/auth/student/login`（修改密碼驗證邏輯）
- **關鍵修改**：`/api/auth/student/login` 密碼驗證邏輯
  ```python
  if student.password_migrated_to_identity:
      # 已整合：使用 StudentIdentity 的密碼
      identity = student.identity
      password_hash_to_verify = identity.password_hash
  else:
      # 未整合：使用 Student 自己的密碼（向後兼容）
      password_hash_to_verify = student.password_hash
  ```

**測試重點**：

- 已整合學生使用舊流程時，舊密碼應無法登入
- 未整合學生使用舊流程時，仍可正常登入
- 已整合學生使用新流程時，可用 Email 登入

### Phase 3.5: 1Campus SSO 整合

**OAuth 認證流程**：

- 新增 API：`GET /api/auth/1campus/authorize`（重導向到 1Campus OAuth）
- 新增 API：`GET /api/auth/1campus/callback`（接收 OAuth 回調）
- OAuth 回調處理：

  ```python
  # 1. 接收 OAuth 授權碼並換取 access token
  # 2. 呼叫 1Campus API 取得學生資料
  oauth_data = {
      'studentAcc': 'taipei.s123@1campus.net',
      'studentID': 'A123456789',  # 待確認：是否為身分證字號
      'schoolDsns': 'tp001'
  }

  # 3. 查詢或創建 Student + StudentIdentity
  identity = find_or_create_identity(
      verified_email=oauth_data['studentAcc'],
      one_campus_student_id=oauth_data['studentID']
  )

  # 4. 檢查疑似重複帳號
  duplicates = check_duplicate_identities(
      one_campus_student_id=oauth_data['studentID'],
      exclude_id=identity.id
  )

  # 5. 若有重複，標記需顯示合併提示（在前端處理）
  if duplicates:
      return {
          'token': generate_token(identity.primary_student),
          'show_merge_prompt': True,
          'duplicate_accounts': format_duplicates(duplicates)
      }
  ```

**疑似重複帳號偵測邏輯**：

```python
def check_duplicate_identities(one_campus_student_id, national_id_hash, verified_email, exclude_id):
    """
    檢查是否有其他 StudentIdentity 符合以下任一條件：
    1. one_campus_student_id 相同且非空
    2. national_id_hash 相同且非空
    3. verified_email 相同
    """
    duplicates = []

    if one_campus_student_id:
        duplicates += StudentIdentity.query.filter(
            StudentIdentity.one_campus_student_id == one_campus_student_id,
            StudentIdentity.id != exclude_id
        ).all()

    if national_id_hash:
        duplicates += StudentIdentity.query.filter(
            StudentIdentity.national_id_hash == national_id_hash,
            StudentIdentity.id != exclude_id
        ).all()

    # 去重並返回
    return list(set(duplicates))
```

**帳號合併 API**：

- 新增 API：`POST /api/student/merge-identity`（學生確認合併）
- 接收參數：`{ target_identity_id, source_identity_id }`
- 合併邏輯：
  ```python
  def merge_identities(target_id, source_id):
      target = StudentIdentity.query.get(target_id)
      source = StudentIdentity.query.get(source_id)

      # 1. 將 source 的所有 Student 轉移到 target
      for student in source.linked_students:
          student.identity_id = target.id
          student.password_migrated_to_identity = True

      # 2. 更新 target 的識別資訊（補充缺失的欄位）
      if not target.one_campus_student_id and source.one_campus_student_id:
          target.one_campus_student_id = source.one_campus_student_id
      if not target.national_id_hash and source.national_id_hash:
          target.national_id_hash = source.national_id_hash

      # 3. 智能密碼合併（同既有邏輯）
      merge_passwords(target, source)

      # 4. 記錄合併來源
      target.merge_source = 'one_campus_sso'

      # 5. 軟刪除 source
      source.is_active = False

      db.session.commit()
  ```

**身分證字號處理**：

- 新增 API：`POST /api/student/update-national-id`（學生選填身分證字號）
- 加密處理：

  ```python
  import hashlib

  def hash_national_id(national_id: str) -> str:
      """
      將身分證字號轉為 SHA-256 hash
      支援台灣身分證（1英+9數）與外籍居留證（2英+8數）
      """
      # 統一轉為大寫並移除空白
      normalized = national_id.upper().strip()

      # 驗證格式（可選）
      if not validate_national_id_format(normalized):
          raise ValueError("Invalid national ID format")

      # 使用 SHA-256 + 固定 salt（存在環境變數）
      salt = os.getenv('NATIONAL_ID_SALT')
      return hashlib.sha256(f"{normalized}{salt}".encode()).hexdigest()
  ```

**測試重點**：

- 首次 1Campus 登入創建正確的 Student + StudentIdentity
- OAuth 回調處理錯誤情況（授權失敗、網路錯誤等）
- 疑似重複帳號正確偵測（基於 one_campus_student_id、national_id_hash）
- 學生確認合併後，兩個帳號都能登入
- 跨縣市轉學情境正確處理
- 身分證字號 hash 唯一性驗證
- 外籍學生居留證號格式支援

### Phase 4: 後台管理功能（可選）

- 管理員手動合併/拆分 Student Identities
- 查看整合歷史
- 異常處理

### Phase 5: 前端調整

**登入頁面改版（三種流程並存）**：

- 新增「學校帳號登入」選項（1Campus SSO）
  - 按鈕：「使用教育部帳號登入」
  - 點擊後重導向到 1Campus OAuth 授權頁面
  - 適合在學校就讀的學生
- 新增「Email 登入」選項（簡單快速）
  - 輸入框：Email、Password
  - 適合已綁定 Email 的學生（補習班或個人註冊）
- 保留「傳統登入」選項（完全兼容）
  - 保持現有 4 步驟流程不變
  - 適合所有學生（包括未綁定 Email 的）

**帳號合併提示視窗**：

登入後，若後端返回 `show_merge_prompt: true`，顯示 Modal：

```jsx
<Modal>
  <Icon>🔗</Icon>
  <Title>偵測到您可能已有其他學習帳號</Title>

  <Description>我們發現以下帳號可能屬於同一位學生：</Description>

  <AccountList>
    {duplicateAccounts.map((account) => (
      <Account>
        <Email>{account.email}</Email>
        <Source>{account.source}</Source> {/* 如：台北市○○國中、補習班 */}
      </Account>
    ))}
  </AccountList>

  <BenefitsList>
    <Title>合併後的效果：</Title>
    <Benefit>✅ 統一密碼管理</Benefit>
    <Benefit>✅ 可用任一帳號登入</Benefit>
    <Benefit>✅ 學習記錄保持獨立（分校/機構分開）</Benefit>
  </BenefitsList>

  <Warning>⚠️ 合併後無法復原，請確認這些帳號都屬於您本人</Warning>

  <Actions>
    <Button onClick={handleMerge} primary>
      確認合併
    </Button>
    <Button onClick={handleSkip}>暫時不要</Button>
  </Actions>
</Modal>
```

**身分證字號填寫介面（選填）**：

若 1Campus 未提供 `studentID`，或學生使用個人 Email 註冊，可在個人設定頁面增加選填欄位：

```jsx
<Form>
  <Label>身分證字號（選填）</Label>
  <Description>
    填寫後，系統可協助識別您在不同學校或補習班的帳號是否為同一人
  </Description>
  <Input
    type="text"
    placeholder="A123456789 或 AB12345678（居留證）"
    maxLength="10"
  />
  <Note>🔒 您的身分證字號將經過加密處理，僅用於帳號識別，不會明文儲存</Note>
  <Button>儲存</Button>
</Form>
```

**其他前端功能（可選）**：

- 學生可查看統一學習檔案（跨機構總覽）
- Email 驗證流程優化
- 密碼修改提示（提醒學生整合後密碼已統一）
- 帳號管理頁面（查看已連結的帳號列表）

---

## 技術決策權歸屬

**⚠️ 重要說明**：本規格文檔僅定義業務需求和驗收標準，以下技術細節由工程師決定：

| 業務需求（Owner 定義） | 技術決策（工程師決定）                         |
| ---------------------- | ---------------------------------------------- |
| Email 必須唯一識別學生 | 使用 UNIQUE 索引還是應用層檢查                 |
| 整合後密碼統一管理     | password_hash 的加密演算法、Salt 策略          |
| 主帳號唯一性           | 使用唯一約束、觸發器還是應用層檢查             |
| 關聯多個 Student 帳號  | 使用外鍵關聯、JSONB 陣列還是其他方式           |
| 智能密碼選擇           | 在 Service 層、資料庫 Trigger 還是其他位置實作 |
| 資料查詢效能           | 索引策略、查詢優化、快取策略                   |

---

## 驗收標準

所有功能必須通過對應的 Feature 檔案中定義的測試案例：

1. ✅ [student-identity-merge-on-email-verification.feature](./features/student-identity/student-identity-merge-on-email-verification.feature)
2. ✅ [student-login-with-identity.feature](./features/student-identity/student-login-with-identity.feature)
3. ✅ [point-deduction-and-reports-after-merge.feature](./features/student-identity/point-deduction-and-reports-after-merge.feature)
4. ✅ [student-1campus-sso-integration.feature](./features/student-identity/student-1campus-sso-integration.feature)

---

## 附錄

### 相關文件

- [業務實體參考模型 (DBML)](./erm-student-identity.dbml)
- [formulation.md 規格產出原則](../../spec/bdd-prompts/formulation.md)
- [OWNER_BUG_FIX_GUIDE.md 職責範圍](../../docs/OWNER_BUG_FIX_GUIDE.md)

### 討論記錄

本規格基於以下討論產出：

- 討論日期：2026-02-09
- 參與人員：Owner
- 討論主題：學生在不同機構/教師下的帳號整合策略、1Campus SSO 整合
- 決策摘要：
  - 整合時機：Email 認證時自動整合 ✅
  - 資料策略：主帳號 + 連結帳號模式 ✅
  - 密碼處理：智能選擇密碼 ✅
  - **1Campus SSO 整合：選擇 Option A（主要學校登入方式）✅**
  - **身分識別機制：新增 `national_id_hash` 和 `one_campus_student_id` 欄位 ✅**
  - **帳號合併確認：系統自動偵測 + 學生端確認（非教師操作）✅**
  - **跨縣市轉學：透過 studentID 識別並提示合併 ✅**
