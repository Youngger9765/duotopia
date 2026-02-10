# Autopilot 決策 - 低信心度項目

**信心度標準**：需要業務決策或產品經理確認，技術上有多種可行方案

---

## 項目 #15: 建立機構_缺少成功與失敗的完整邊界條件Example

### 釐清問題
建立機構.feature 僅有 2 個 Example（成功建立、一般教師拒絕），缺少邊界條件測試案例

### Context Inference 推理

**從 Discovery.md 規範**：
> **B3. 例子覆蓋度**（必須做到，不可妥協）  
> 關鍵 Rule 必須有明確 Example，尤其是邊界條件

**當前 Feature 狀態**：
- ✓ 成功建立
- ✓ 權限拒絕
- ✗ 統編重複
- ✗ 必填欄位缺失
- ✗ Email 格式錯誤
- ✗ 欄位長度超限

**DBML 約束**：
```dbml
tax_id varchar(20) [unique, not null]
owner_email varchar(200) [not null]
owner_phone varchar(50) [not null]
```

**不確定性**：
- 哪些邊界條件「必須」在 Feature 中測試？
- 哪些可以在單元測試中覆蓋？
- Feature 應該多詳細？

### 決策選項

| 選項 | 描述 | 優點 | 缺點 |
|------|------|------|------|
| A | 補充所有邊界條件 Example | 覆蓋度最高 | Feature 檔案過長 |
| B | 僅補充關鍵邊界條件（統編重複） | 平衡可讀性與覆蓋度 | 部分邊界條件未覆蓋 |
| C | 建立獨立的驗證規則 Rule | 清晰分離業務與驗證 | 增加 Feature 複雜度 |
| D | 邊界條件在單元測試中覆蓋 | Feature 保持簡潔 | 不符合 B3 規範 |

### 建議決策：**選項 C - 建立獨立的驗證規則 Rule**

**理由**（Medium Confidence）：
1. 符合 Discovery.md B3 規範（例子覆蓋度）
2. 驗證規則與業務邏輯分離，提高可讀性
3. 統一管理所有驗證情境

**實作建議**：

```gherkin
規則: 機構資料驗證

  場景大綱: 驗證機構資料完整性
    假設 我是系統管理員
    當 我嘗試建立機構，使用以下資料
      | 欄位         | 值        |
      | name         | <name>    |
      | tax_id       | <tax_id>  |
      | owner_email  | <email>   |
      | owner_phone  | <phone>   |
    那麼 應回應 <status>
    而且 若失敗，錯誤訊息應為 <error_message>
    
    範例:
      | name       | tax_id     | email              | phone        | status  | error_message                |
      | ABC補習班  | 12345678   | owner@abc.com      | 0912345678   | 201     | -                            |
      |            | 12345678   | owner@abc.com      | 0912345678   | 400     | 機構名稱為必填欄位           |
      | ABC補習班  |            | owner@abc.com      | 0912345678   | 400     | 統一編號為必填欄位           |
      | ABC補習班  | 12345678   |                    | 0912345678   | 400     | 擁有人 Email 為必填欄位      |
      | ABC補習班  | 12345678   | owner@abc.com      |              | 400     | 擁有人手機為必填欄位         |
      | ABC補習班  | 12345678   | invalid-email      | 0912345678   | 400     | Email 格式不正確             |
      | ABC補習班  | 12345678   | owner@abc.com      | 123          | 400     | 手機號碼格式不正確           |
      | A          | 12345678   | owner@abc.com      | 0912345678   | 400     | 機構名稱至少 2 個字          |
      | ABC補習班  | 12345      | owner@abc.com      | 0912345678   | 400     | 統一編號必須為 8 位數字      |

  場景: 統編重複檢查
    假設 我是系統管理員
    而且 已存在機構，統編為 "12345678"
    當 我嘗試建立新機構，統編為 "12345678"
    那麼 應回應 409 Conflict
    而且 錯誤訊息應為 "統一編號已被使用"
```

**為什麼不是選項 A**：
- Feature 檔案會過長（20+ Example）
- 可讀性下降

**為什麼不是選項 D**：
- Discovery.md 明確要求「例子覆蓋度（必須做到，不可妥協）」
- 邊界條件應在 Feature 中可見

**信心度**：Medium（60%）
- 依據 Discovery.md 規範
- 但需確認團隊對「Feature 詳細程度」的偏好

**需要確認**：
1. 團隊是否接受 Scenario Outline 模式？
2. 驗證規則是否應獨立成 Rule？
3. 格式驗證細節（Email regex, phone format）

---

## 項目 #16: 建立機構_缺少機構資料完整性驗證規則

### 釐清問題
建立機構.feature 僅檢查「系統管理員權限」與「機構名稱重複」，缺少欄位格式驗證規則

### Context Inference 推理

**與項目 #15 的關係**：
- 項目 #15 關注「是否補充 Example」
- 項目 #16 關注「驗證規則定義」

**不確定性**：
- 驗證規則應在哪裡定義？（Feature vs API schema vs DBML）
- 格式驗證的細節程度？（如：Email regex, tax_id 格式）

### 決策選項

| 選項 | 描述 | 優點 | 缺點 |
|------|------|------|------|
| A | 在 Feature 背景資訊中明確列出所有驗證規則 | 清晰完整 | Feature 檔案過長 |
| B | 在 API 文件中定義，Feature 僅測試關鍵案例 | Feature 保持簡潔 | 規則分散在多處 |
| C | 建立獨立的驗證規則文件（spec/validation/） | 集中管理 | 新增文件維護負擔 |
| D | 在 DBML note 中補充格式說明 | 接近資料定義 | DBML 職責過重 |

### 建議決策：**選項 A - 在 Feature 背景資訊中明確列出驗證規則**

**理由**（Low Confidence）：
1. Gherkin 的 Background 適合定義規則
2. 開發者可直接查看完整規範
3. 配合項目 #15 的 Scenario Outline

**實作建議**：

```gherkin
功能: 建立機構
  作為 系統管理員
  我希望能夠建立新的教育機構
  以便機構使用 Duotopia 平台

  背景資訊:
    建立機構權限: 僅 Platform Owner（Teacher.is_admin = True）
    
    資料驗證規則:
      必填欄位:
        - name: 機構名稱
        - tax_id: 統一編號
        - owner_name: 擁有人姓名
        - owner_email: 擁有人 Email
        - owner_phone: 擁有人手機
      
      格式驗證:
        - tax_id: 8 位數字（台灣統一編號格式）
        - owner_email: 標準 Email 格式（RFC 5322）
        - owner_phone: 台灣手機號碼格式（09\d{8}）
        - contact_email: 標準 Email 格式（若提供）
      
      長度限制:
        - name: 2-100 字元
        - display_name: 2-200 字元
        - owner_name: 2-100 字元
      
      唯一性約束:
        - tax_id: 全域唯一（is_active=true 時）
```

**為什麼不是選項 B**：
- Discovery.md 強調 Feature 完整性
- 規則分散會降低可讀性

**為什麼不是選項 C**：
- 增加維護負擔
- Gherkin 本身適合定義規則

**信心度**：Low（40%）
- 團隊對「Feature 詳細程度」的偏好未知
- 可能認為過於技術化

**需要確認**：
1. 團隊是否接受在 Feature 中定義格式驗證？
2. tax_id 格式是否為 8 位數字？（台灣統一編號）
3. phone 格式是否僅支援台灣手機？（國際化需求？）

---

## 項目 #17: 機構擁有人管理流程_教師授權數扣除與釋放邏輯

### 釐清問題
Feature 說明新增教師時「已使用教師授權數應為 1」，但沒有說明移除教師、停用教師時授權數如何處理

### Context Inference 推理

**從 Feature 推斷**：
```gherkin
場景: 新增已註冊的教師到機構
  那麼 已使用教師授權數應為 "1"
```
- 新增教師 → 授權數 +1
- 未說明移除/停用邏輯

**業務邏輯推測**：
- 授權數 = 計費基礎
- 停用 vs 刪除的差異？

**不確定性**：
- 停用教師（is_active=false）是否釋放授權？
- 刪除教師是否釋放授權？
- 授權數如何計算（COUNT vs 欄位儲存）？

### 決策選項

| 選項 | 描述 | 計費影響 | 資料保留 |
|------|------|---------|---------|
| A | 停用教師釋放授權（COUNT is_active=true） | 停用即不計費 | 保留歷史 |
| B | 停用教師仍佔用授權（COUNT all） | 停用仍計費 | 保留歷史 |
| C | 僅刪除教師才釋放授權 | 需刪除才釋放 | 遺失歷史 |
| D | 授權數手動調整（不自動計算） | 彈性計費 | 保留歷史 |

### 建議決策：**選項 A - 停用教師釋放授權（COUNT is_active=true）**

**理由**（Low Confidence）：
1. 符合 SaaS 計費邏輯（啟用教師才計費）
2. 保留歷史資料（教學記錄）
3. 機構可彈性管理成本

**實作建議**：

**DBML 補充**：
```dbml
Table organizations {
  teacher_limit int [not null, default: 5, note: "教師授權數上限"]
  // teacher_used 不儲存，即時計算
}
```

**授權數計算邏輯**：
```python
def get_teacher_usage(organization_id):
    """計算已使用教師授權數"""
    return session.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == organization_id,
        TeacherOrganization.is_active == True  # 僅計算啟用中的
    ).count()

def can_add_teacher(organization_id):
    """檢查是否可新增教師"""
    org = get_organization(organization_id)
    used = get_teacher_usage(organization_id)
    return used < org.teacher_limit
```

**Feature 補充 Example**：
```gherkin
場景: 移除教師後授權數釋放
  假設 機構有 "5" 個教師授權數
  而且 已新增教師 "張三"
  而且 已使用教師授權數為 "1"
  當 我移除教師 "張三"
  那麼 已使用教師授權數應為 "0"

場景: 停用教師後授權數釋放
  假設 機構有 "5" 個教師授權數
  而且 已新增教師 "張三"
  當 我停用教師 "張三"（設定 is_active=false）
  那麼 已使用教師授權數應為 "0"
  而且 教師 "張三" 的歷史資料應保留
```

**為什麼不是選項 B**：
- 停用後仍計費不合理（教師無法使用系統）

**為什麼不是選項 C**：
- 刪除會遺失歷史教學記錄

**信心度**：Low（50%）
- 需要產品經理確認計費邏輯
- 可能有特殊業務需求（如：最低承諾人數）

**需要確認**：
1. 計費方式：按啟用教師數 vs 按最高峰值？
2. 停用教師是否可重新啟用？
3. 是否有「最低承諾教師數」限制？

---

## 項目 #18: 機構擁有人管理流程_點數系統的資料模型定義

### 釐清問題
Feature 提到「機構有 '117000' 點剩餘點數」，但 DBML 中沒有定義點數系統

### Context Inference 推理

**從 Feature 推斷**：
```gherkin
背景:
  而且 機構有 "117000" 點剩餘點數
```
- 機構有點數餘額
- 未說明點數用途、充值、扣除邏輯

**業務邏輯推測**：
- 點數可能用於購買教材、功能、服務
- 可能有充值記錄需求
- 可能有消費記錄需求

**不確定性**：
- 點數是單純餘額還是需要交易記錄？
- 是否需要點數變動歷史？
- 是否需要過期機制？

### 決策選項

| 選項 | 描述 | 優點 | 缺點 |
|------|------|------|------|
| A | organizations 表新增 points 欄位 | 簡單 | 無交易記錄 |
| B | 建立 organization_credits 表（餘額+交易記錄） | 完整歷史 | 複雜度高 |
| C | 建立 credit_transactions 表（僅交易） | 靈活 | 計算餘額需彙總 |
| D | 點數系統在其他 DBML 中定義 | 領域分離 | 跨檔案參照 |

### 建議決策：**選項 B - 建立 organization_credits 表**

**理由**（Low Confidence）：
1. 點數涉及計費，需要完整記錄
2. 支援查詢交易歷史（充值、消費）
3. 支援審計與對帳

**實作建議**：

**DBML 補充**：
```dbml
// ============================================
// 6. OrganizationCredit (機構點數)
// ============================================
Table organization_credits {
  id int [pk, increment, note: "主鍵"]
  organization_id uuid [not null, ref: > organizations.id, note: "所屬機構"]
  
  // 點數餘額
  balance int [not null, default: 0, note: "當前點數餘額"]
  
  // 時間戳記
  created_at timestamp [not null, default: `now()`]
  updated_at timestamp [null]
  
  indexes {
    organization_id [unique, name: "uq_org_credits"]
  }
  
  Note: '''
  核心規則:
  - 一個機構僅一筆點數記錄
  - balance 為當前餘額，由 credit_transactions 彙總維護
  - 不可為負數（需在應用層檢查）
  '''
}

// ============================================
// 7. CreditTransaction (點數交易記錄)
// ============================================
Table credit_transactions {
  id int [pk, increment, note: "主鍵"]
  organization_id uuid [not null, ref: > organizations.id, note: "所屬機構"]
  
  // 交易資訊
  type varchar(50) [not null, note: "交易類型: recharge（充值）, consume（消費）, refund（退款）"]
  amount int [not null, note: "點數變動（正數為增加，負數為減少）"]
  balance_after int [not null, note: "交易後餘額"]
  
  // 交易說明
  description text [null, note: "交易說明"]
  reference_type varchar(50) [null, note: "關聯類型（如：order, material_purchase）"]
  reference_id varchar(100) [null, note: "關聯 ID"]
  
  // 時間戳記
  created_at timestamp [not null, default: `now()`]
  
  indexes {
    organization_id [name: "idx_credit_txn_org"]
    (organization_id, created_at) [name: "idx_credit_txn_org_time"]
  }
}
```

**交易流程**：
```python
def add_credits(org_id, amount, description):
    """充值點數"""
    with transaction():
        credit = get_organization_credit(org_id)
        credit.balance += amount
        
        create_transaction({
            "organization_id": org_id,
            "type": "recharge",
            "amount": amount,
            "balance_after": credit.balance,
            "description": description
        })

def consume_credits(org_id, amount, description, reference):
    """消費點數"""
    with transaction():
        credit = get_organization_credit(org_id)
        
        if credit.balance < amount:
            raise InsufficientCreditsError()
        
        credit.balance -= amount
        
        create_transaction({
            "organization_id": org_id,
            "type": "consume",
            "amount": -amount,
            "balance_after": credit.balance,
            "description": description,
            "reference_type": reference.type,
            "reference_id": reference.id
        })
```

**為什麼不是選項 A**：
- 無法查詢交易歷史
- 計費系統需要完整記錄

**為什麼不是選項 C**：
- 每次查詢餘額需彙總（效能問題）

**信心度**：Low（40%）
- 點數系統的業務需求不明確
- 可能有更複雜的需求（如：點數過期、分級定價）

**需要確認**：
1. 點數的用途？（購買教材、功能、服務？）
2. 是否需要過期機制？
3. 是否需要點數贈送/轉移功能？
4. 充值方式？（信用卡、轉帳、發票？）

---

## 項目 #19: 管理機構成員_移除成員後資料如何處理

### 釐清問題
Feature 說明移除成員時「teacher_organizations.is_active 更新為 false」，但沒有說明該教師在學校的角色、建立的班級/教材如何處理

### Context Inference 推理

**從 Feature 推斷**：
```gherkin
場景: 成功移除機構管理人
  那麼 "張三" 在 teacher_organizations 表中對應記錄的 "is_active" 應更新為 "false"
```
- 移除機構角色（軟刪除）
- 未說明連鎖影響

**DBML 關聯分析**：
```
teacher_organizations (機構角色)
  ↓
teacher_schools (學校角色)
  ↓
classrooms (班級)
```

**業務邏輯推測**：
- 移除機構成員 ≠ 刪除教師帳號
- 教師可能在其他機構仍有角色
- 教師建立的資料是否保留？

**不確定性**：
- 是否同時移除學校角色？
- 班級/教材歸屬如何處理？
- 學生資料如何處理？

### 決策選項

| 選項 | 描述 | 資料保留 | 業務影響 |
|------|------|---------|---------|
| A | 僅移除機構角色，學校角色保留 | 完整保留 | 邏輯矛盾（無機構角色但有學校角色） |
| B | CASCADE 移除所有相關角色與資料 | 部分刪除 | 可能導致資料遺失 |
| C | 移除角色但保留歷史資料（班級、教材） | 完整保留 | 資料歸屬需重新分配 |
| D | 分階段移除（需確認無班級才可移除） | 完整保留 | 操作複雜 |

### 建議決策：**選項 C - 移除角色但保留歷史資料**

**理由**（Low Confidence）：
1. 教師建立的班級/教材為機構資產
2. 學生學習記錄需要保留
3. 移除成員 ≠ 刪除資料

**實作建議**：

```python
def remove_organization_member(org_id, teacher_id):
    """移除機構成員"""
    with transaction():
        # 1. 移除機構角色
        teacher_org = get_teacher_organization(teacher_id, org_id)
        teacher_org.is_active = False
        
        # 2. 移除所有學校角色
        teacher_schools = get_teacher_schools(teacher_id, org_id)
        for ts in teacher_schools:
            ts.is_active = False
        
        # 3. 班級/教材保留，但標記為「已離職教師建立」
        # - 可選：重新分配給其他教師
        # - 可選：設定為「機構共用」
        
        # 4. 學生資料完整保留
```

**Feature 補充 Example**：
```gherkin
場景: 移除成員後班級與學生資料保留
  假設 教師 "張三" 在機構建立了班級 "一年A班"
  而且 "一年A班" 有學生 "王小明"
  當 我移除教師 "張三"
  那麼 班級 "一年A班" 應保留
  而且 學生 "王小明" 的學習資料應保留
  而且 班級 "一年A班" 應標記為「已離職教師建立」
  而且 機構擁有人應能重新分配班級給其他教師
```

**替代方案（需確認）**：
```gherkin
場景: 移除成員前檢查資料
  假設 教師 "張三" 在機構建立了班級 "一年A班"
  當 我嘗試移除教師 "張三"
  那麼 應提示 "該教師仍有班級，請先重新分配或刪除班級"
  而且 移除操作應失敗
```

**為什麼不是選項 A**：
- 無機構角色但有學校角色邏輯矛盾

**為什麼不是選項 B**：
- CASCADE 刪除會遺失學生學習資料

**信心度**：Low（30%）
- 需要產品經理確認資料歸屬邏輯
- 可能有複雜的業務需求

**需要確認**：
1. 班級/教材是否為機構資產？
2. 移除成員時是否允許有班級存在？
3. 是否需要重新分配功能？
4. 學生資料的保留期限？

---

## 項目 #20: 管理機構成員_編輯角色範例缺少驗證規則

### 釐清問題
管理機構成員.feature 的「編輯成員角色」Rule 中，Example 顯示「將機構管理人提升為機構負責人」，但沒有說明原本的 org_owner 如何處理

### Context Inference 推理

**從 Feature 推斷**：
```gherkin
場景: 機構負責人將機構管理人提升為機構負責人
  當 我編輯 "張三" 的角色為 "org_owner"
  那麼 "張三" 應獲得 "org_owner" 角色
```
- 未說明原 org_owner 的處理

**DBML 約束**：
```
Note: "一個機構僅能有一個 org_owner"
```
- 強制約束：同時僅能有一個 org_owner

**業務邏輯推測**：
- org_owner 轉移 = 權限轉移
- 需要確認流程（防止誤操作）

**不確定性**：
- 自動降級 vs 拒絕操作？
- 是否需要二次確認？
- 是否需要原 org_owner 同意？

### 決策選項

| 選項 | 描述 | 安全性 | 使用體驗 |
|------|------|--------|---------|
| A | 自動將原 org_owner 降級為 org_admin | 方便 | 可能誤操作 |
| B | 拒絕操作，需先移除原 org_owner | 安全 | 操作繁瑣 |
| C | 兩階段確認（確認轉移 + 確認降級） | 平衡 | 稍微複雜 |
| D | 需要原 org_owner 同意（Email 確認） | 最安全 | 最複雜 |

### 建議決策：**選項 C - 兩階段確認**

**理由**（Low Confidence）：
1. 平衡安全性與使用體驗
2. 防止誤操作
3. 符合重要操作的 UX 慣例

**實作建議**：

```python
def transfer_ownership(org_id, new_owner_id, current_user_id):
    """轉移機構擁有人"""
    # 1. 檢查權限（僅 org_owner 可轉移）
    current_owner = get_organization_owner(org_id)
    if current_owner.teacher_id != current_user_id:
        raise PermissionDeniedError()
    
    # 2. 檢查新擁有人是否為機構成員
    new_owner_relation = get_teacher_organization(new_owner_id, org_id)
    if not new_owner_relation or not new_owner_relation.is_active:
        raise NotOrganizationMemberError()
    
    # 3. 執行轉移（原子操作）
    with transaction():
        # 舊擁有人降級
        current_owner.role = 'org_admin'
        current_owner.updated_at = now()
        
        # 新擁有人升級
        new_owner_relation.role = 'org_owner'
        new_owner_relation.updated_at = now()
        
        # 記錄操作日誌
        log_ownership_transfer(org_id, current_user_id, new_owner_id)
```

**Feature 補充 Example**：
```gherkin
場景: 轉移機構擁有人權限（完整流程）
  假設 我是機構 "ABC補習班" 的機構負責人
  而且 "張三" 是機構管理人
  當 我嘗試將 "張三" 提升為機構負責人
  那麼 應顯示確認訊息 "轉移機構擁有人權限後，您將降級為機構管理人，確定繼續？"
  當 我確認轉移
  那麼 "張三" 應獲得 "org_owner" 角色
  而且 我應降級為 "org_admin" 角色
  而且 應發送通知給 "張三" 和我

場景: 非機構負責人無法轉移擁有人權限
  假設 我是機構 "ABC補習班" 的機構管理人
  當 我嘗試將其他成員提升為機構負責人
  那麼 應回應 403 Forbidden
  而且 錯誤訊息應為 "僅機構負責人可轉移擁有人權限"
```

**前端 UI 建議**：
```
確認對話框:
┌─────────────────────────────────────┐
│  ⚠️  轉移機構擁有人權限               │
├─────────────────────────────────────┤
│  您即將轉移機構擁有人權限給 張三      │
│                                     │
│  轉移後:                             │
│  ✓ 張三將獲得完整機構管理權限         │
│  ✓ 您將降級為機構管理人               │
│  ✓ 此操作無法撤銷                    │
│                                     │
│  [ 取消 ]  [ 確認轉移 ]              │
└─────────────────────────────────────┘
```

**為什麼不是選項 A**：
- 無確認流程容易誤操作

**為什麼不是選項 D**：
- 過於複雜（Email 確認流程長）

**信心度**：Low（50%）
- 需要 UX 設計師確認流程
- 可能有更好的轉移流程

**需要確認**：
1. 是否需要原 org_owner 的 Email 確認？
2. 轉移後是否發送通知？
3. 是否記錄操作日誌？
4. 是否支援撤銷轉移？

---

## 項目 #21: ✅ 個人教師與機構教師身分切換_未被指派班級教師無法切換的邏輯

### 釐清問題
原始問題：Feature 中「未被指派為班級老師的機構教師查看後台」時「應看不到『切換到機構後台』的選項」，與其他規則矛盾

### Context Inference 推理

**Feature 檔案已修正**（2026年1月7日）：
- 從「切換後台」改為「視圖切換」
- 新邏輯：在個人教師後台內切換視圖
- 「個人視圖」vs「機構視圖 - <學校名稱>」

**新 Feature 內容**：
```gherkin
場景: 選擇機構視圖但未被指派班級
  假設 我在個人教師後台
  而且 我已加入機構 "ABC 教育集團"
  而且 我已被指派到 "台北分校"
  但是 我尚未被指派為任何班級的老師
  當 我選擇視圖 "機構視圖 - 台北分校"
  那麼 我應看到提示訊息 "您尚未被指派任何班級"
  而且 我應只看到機構教材
  而且 我不應看到任何班級
  而且 我不應看到任何學生
```

### 決策：**✅ 已透過 Feature 修正解決，跳過**

**理由**：
1. Feature 已改為「視圖切換」架構
2. 加入機構即可切換視圖，無需班級
3. 未被指派班級時顯示提示訊息
4. 原始邏輯矛盾已不存在

**處理方式**：
- 在決策日誌中註記「✅ 已透過 Feature 修正解決，跳過」
- 不需要額外決策

**信心度**：High（100%）
- Feature 檔案已明確修正

---

## 總結

**低信心度項目**：5 項（實際需決策）+ 1 項（已解決）

### 需業務決策的項目
1. **項目 #15 & #16**：建立機構的驗證規則與 Example 覆蓋度
   - 需確認：Feature 詳細程度偏好
   
2. **項目 #17**：教師授權數扣除與釋放邏輯
   - 需確認：計費方式、停用邏輯

3. **項目 #18**：點數系統的資料模型定義
   - 需確認：點數用途、交易記錄需求

4. **項目 #19**：移除成員後資料處理
   - 需確認：資料歸屬、重新分配流程

5. **項目 #20**：org_owner 轉移流程
   - 需確認：轉移流程、確認機制

### 已解決的項目
- **項目 #21**：個人教師與機構教師身分切換（Feature 已修正）

**建議行動**：
1. 召開業務會議討論項目 #17、#18、#19、#20
2. 與團隊討論 Feature 詳細程度偏好（項目 #15、#16）
3. 確認後補充 DBML 與 Feature Example
