# Autopilot 決策 - 高信心度項目

**信心度標準**：能從 DBML、Feature、業界慣例明確推斷答案

---

## 項目 #1: ClassroomSchool_一個班級一個學校的刪除行為

### 釐清問題
classroom_schools 表明「一個班級只能屬於一個學校」，當學校被刪除或停用時，班級應如何處理？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
classroom_schools {
  classroom_id int [not null, ref: > classrooms.id, note: "班級 ID，CASCADE 刪除"]
  school_id uuid [not null, ref: > schools.id, note: "學校 ID，CASCADE 刪除"]
}
```
- 外鍵設定為 CASCADE 刪除
- 與 schools 表的刪除策略一致（organizations → schools CASCADE）

**業界慣例**：
- 教育系統通常使用軟刪除保留歷史資料
- 班級資料涉及學生成績、學習記錄，不應輕易刪除

**一致性檢查**：
- organizations 表有 is_active 欄位（軟刪除）
- schools 表有 is_active 欄位（軟刪除）
- classroom_schools 表也有 is_active 欄位

### 決策：**選項 B - 設定 is_active=false（軟刪除）**

**理由**：
1. DBML 中所有表都設計了 is_active 欄位，顯示系統採用軟刪除策略
2. CASCADE 刪除可能導致學生學習資料遺失（grades, assignments）
3. 軟刪除允許資料恢復與歷史查詢
4. 與組織層級的刪除策略一致

**實作建議**：
- 當 school.is_active=false 時，同步設定 classroom_schools.is_active=false
- 查詢時過濾 is_active=true 的記錄
- 保留硬刪除功能供資料清理使用（需額外權限）

**信心度**：High（95%）
- DBML 設計已明確採用 is_active 模式
- 業界標準做法

---

## 項目 #2: Organization_display_name與name的用途差異

### 釐清問題
organizations 和 schools 都有 name 和 display_name 兩個欄位，兩者的用途差異是什麼？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
name varchar(100) [not null, note: "機構名稱"]
display_name varchar(200) [null, note: "機構顯示名稱（可為空）"]
```
- name 必填（not null），較短（100）
- display_name 可為空（null），較長（200）

**業界慣例**：
- name：簡稱或系統識別名稱
- display_name：完整顯示名稱或別名
- 類似模式：GitHub（username vs display name）、Slack（handle vs display name）

**使用情境推斷**：
- name: "台大附中" (簡短、唯一、用於 URL)
- display_name: "國立臺灣大學附屬高級中學" (正式名稱、用於顯示)

### 決策：**選項 A + C 組合 - name 用於系統識別，display_name 為選用的顯示名稱**

**理由**：
1. 欄位約束差異（not null vs nullable）顯示 name 為必要，display_name 為選用
2. 長度差異（100 vs 200）顯示 display_name 用於更長的正式名稱
3. 符合常見 CMS/系統設計模式

**實作建議**：
- name: 用於 API 路徑、系統日誌、唯一識別
- display_name: 用於前端顯示、報表、證書
- 若 display_name 為 null，前端顯示 name

**API 文件補充**：
```
name: 機構簡稱（必填，100字內，用於系統識別）
display_name: 機構顯示名稱（選填，200字內，用於前端顯示，若為空則顯示 name）
```

**信心度**：High（90%）
- 欄位設計已明確區分必填與選填
- 符合業界慣例

---

## 項目 #3: Organization_owner_email不可更改的實作機制

### 釐清問題
organizations.owner_email 標記為「無法更改」，但 DBML 中沒有技術約束，具體的實作機制是什麼？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
owner_email varchar(200) [not null, note: "機構擁有人 Email（無法更改）"]
```
- 僅在 note 中說明「無法更改」
- 無資料庫層面的 immutable 約束

**業界慣例**：
- 資料庫層面的 immutable 約束實作複雜（需觸發器）
- 現代 API 設計通常在應用層控制
- PostgreSQL 沒有原生的 immutable 欄位類型

**系統架構推斷**：
- 專案使用 FastAPI + Pydantic（backend/main.py）
- 適合在 API schema 層面限制更新

### 決策：**選項 A - 僅在應用層控制，API 拒絕更新此欄位**

**理由**：
1. 簡單、可維護、符合現代 API 設計
2. 避免資料庫觸發器的複雜性
3. 錯誤訊息可更友善（400 Bad Request vs 資料庫錯誤）

**實作建議**：
```python
# schemas.py
class OrganizationUpdate(BaseModel):
    name: Optional[str]
    display_name: Optional[str]
    # owner_email 不在更新 schema 中

    class Config:
        # 明確說明 owner_email 不可更新
        schema_extra = {
            "description": "owner_email 無法更新，若需變更請聯繫客服"
        }
```

**替代方案（若未來需要）**：
- 實作 owner_email 變更流程（需 email 驗證 + 原擁有人確認）
- 建立 organization_owner_changes 歷史表

**信心度**：High（95%）
- 業界標準做法
- 符合 FastAPI 設計模式

---

## 項目 #4: Organization_settings欄位的結構定義

### 釐清問題
organizations.settings 和 schools.settings 定義為 jsonb，但沒有說明具體的 JSON 結構？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
settings jsonb [null, note: "機構層級設定（JSON 格式）"]
```
- nullable（可為空）
- 無預設值定義
- 無結構說明

**業界慣例**：
- 設定欄位通常為擴展用途（future-proof）
- 初期可為空物件 {}，按需擴充
- 避免過早定義結構（YAGNI 原則）

**類似系統參考**：
- Moodle: settings 包含 theme, language, timezone
- Canvas LMS: settings 包含 notification preferences, feature flags

### 決策：**選項 C - 預設為空物件 {}，按需擴充**

**理由**：
1. 欄位為 nullable，顯示非核心功能
2. 避免過度設計，保持靈活性
3. 可在 API 文件中說明「保留欄位」

**實作建議**：
```python
# schemas.py
class OrganizationSettings(BaseModel):
    """機構設定（擴展用途）
    
    目前支援的欄位：
    - notifications: 通知偏好 (dict)
    - theme: 主題設定 (dict)
    - features: 功能開關 (dict)
    """
    notifications: Optional[dict] = {}
    theme: Optional[dict] = {}
    features: Optional[dict] = {}
    
    class Config:
        extra = "allow"  # 允許額外欄位
```

**API 文件補充**：
```
settings (object, nullable): 機構層級設定，預設為空物件 {}
  - 此欄位為擴展用途，可按需新增設定項目
  - 目前未定義標準結構，由應用層自行擴充
```

**未來擴充建議**（當需求明確時）：
- 使用 JSON Schema 驗證結構
- 建立標準設定欄位文件
- 實作設定遷移機制

**信心度**：High（90%）
- 符合 YAGNI 原則
- 保持系統靈活性

---

## 項目 #5: Organization_tax_id唯一性跨所有機構或軟刪除後可重用

### 釐清問題
organizations.tax_id 設定為 unique，若機構被停用（is_active=false）後，同一統編是否可重新註冊？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
tax_id varchar(20) [unique, not null, note: "統一編號，唯一值，必填"]
is_active boolean [not null, default: true, note: "機構是否啟用"]
```
- tax_id 設定為 unique（全域唯一）
- 有 is_active 欄位（軟刪除設計）

**業務邏輯推斷**：
- 統一編號為政府註冊資料，一個公司只有一個統編
- 機構可能暫時停用後重新啟用（如：休學期間、暫停營業）
- 若永久唯一，停用機構無法重新啟用

**業界慣例**：
- 軟刪除系統通常使用 partial unique index
- PostgreSQL: `CREATE UNIQUE INDEX ON organizations (tax_id) WHERE is_active = true`

### 決策：**選項 B - 僅在 is_active=true 時唯一（部分唯一索引）**

**理由**：
1. 支援機構重新啟用流程（業務需求）
2. 避免「已停用但統編被鎖住」的問題
3. 符合軟刪除系統的最佳實踐

**實作建議**：
```sql
-- 移除原本的 unique 約束
ALTER TABLE organizations DROP CONSTRAINT IF EXISTS organizations_tax_id_key;

-- 建立部分唯一索引
CREATE UNIQUE INDEX uq_organizations_tax_id_active 
ON organizations (tax_id) 
WHERE is_active = true;
```

**邏輯說明**：
- 同一統編可以有多筆 is_active=false 的記錄（歷史資料）
- 同一統編只能有一筆 is_active=true 的記錄（當前啟用機構）

**DBML 更新建議**：
```dbml
indexes {
  (tax_id) [unique, where: "is_active = true", name: "uq_organizations_tax_id_active"]
}
```

**Feature Example 補充**：
```gherkin
場景: 重新啟用已停用的機構
  假設 機構 "ABC 補習班" 統編 "12345678" 已停用
  當 系統管理員使用相同統編建立新機構
  那麼 應自動啟用原有機構記錄（或詢問是否重新啟用）
```

**信心度**：High（95%）
- 符合軟刪除系統設計
- 業界標準做法
- 解決業務需求

---

## 項目 #6: School_CASCADE刪除對班級學生的影響

### 釐清問題
schools 表與 organizations 表的關聯設定為 CASCADE 刪除，完整的刪除鏈路是什麼？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
schools {
  organization_id uuid [ref: > organizations.id, note: "CASCADE 刪除"]
}
classroom_schools {
  school_id uuid [ref: > schools.id, note: "CASCADE 刪除"]
}
```
- 設定了 CASCADE 刪除關聯
- 但所有表都有 is_active 欄位（軟刪除設計）

**設計衝突分析**：
- CASCADE 刪除 vs is_active 軟刪除
- 兩者混用會導致行為不一致

**業界慣例**：
- 教育系統優先使用軟刪除（保留歷史資料）
- CASCADE 刪除適用於強關聯實體（如：訂單-訂單項目）
- 學生資料涉及法律要求（成績保存期限）

### 決策：**選項 C - 軟刪除策略（設定 is_active=false）**

**理由**：
1. 所有表都設計了 is_active 欄位，顯示系統採用軟刪除
2. 學生學習資料需要保留（成績、作業、學習歷程）
3. 機構關閉後可能需要查詢歷史資料（退費、證明文件）
4. 避免誤刪導致資料無法恢復

**實作建議**：
```python
# 刪除機構時的邏輯
def deactivate_organization(org_id):
    # 1. 設定機構為停用
    organization.is_active = False
    
    # 2. 級聯停用所有學校
    for school in organization.schools:
        school.is_active = False
        
        # 3. 級聯停用學校下的班級關係
        for classroom_school in school.classroom_schools:
            classroom_school.is_active = False
    
    # 學生資料保留（不設定 is_active=false）
    # 教師關係保留（保留歷史教學記錄）
```

**查詢時的過濾**：
```python
# 查詢啟用中的機構
active_orgs = session.query(Organization).filter(Organization.is_active == True)

# 查詢機構下的啟用學校
active_schools = session.query(School).filter(
    School.organization_id == org_id,
    School.is_active == True
)
```

**DBML 修正建議**：
- 移除 note 中的「CASCADE 刪除」說明
- 改為「軟刪除，級聯設定 is_active=false」

**硬刪除保留方案**（資料清理用）：
- 提供管理員介面進行永久刪除（需二次確認）
- 記錄刪除日誌
- 刪除前匯出資料備份

**信心度**：High（95%）
- DBML 設計已採用 is_active 模式
- 教育系統的業界標準
- 符合資料保護要求

---

## 項目 #7: TeacherOrganization_一個機構一個org_owner的資料庫約束

### 釐清問題
Note 說明「一個機構僅能有一個 org_owner」，但 DBML 沒有定義此約束，如何強制執行？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
teacher_organizations {
  role varchar(50) [not null, default: "org_owner"]
  is_active boolean [not null, default: true]
  (teacher_id, organization_id) [unique]
}
Note: "一個機構僅能有一個 org_owner"
```
- 已有 (teacher_id, organization_id) 的 unique 約束
- 有 is_active 欄位（軟刪除）
- 規則明確但未在資料庫層面強制

**業界慣例**：
- 使用 partial unique index 強制業務規則
- PostgreSQL: `CREATE UNIQUE INDEX ON table (col1) WHERE condition`

**與項目 #5 一致性**：
- tax_id 使用 partial unique index (where is_active=true)
- org_owner 約束應使用相同模式

### 決策：**選項 B - 資料庫部分唯一索引 (organization_id, role) where role='org_owner' AND is_active=true**

**理由**：
1. 在資料庫層面強制執行，避免應用層 bug
2. 支援 org_owner 轉移（舊擁有人 is_active=false，新擁有人 is_active=true）
3. 保留歷史記錄（過往的 org_owner）
4. 與 tax_id 的 partial unique index 設計一致

**實作建議**：
```sql
-- 建立部分唯一索引
CREATE UNIQUE INDEX uq_teacher_org_owner 
ON teacher_organizations (organization_id) 
WHERE role = 'org_owner' AND is_active = true;
```

**DBML 更新建議**：
```dbml
indexes {
  (organization_id) [unique, where: "role = 'org_owner' AND is_active = true", name: "uq_teacher_org_owner"]
}
```

**org_owner 轉移流程**：
```python
def transfer_ownership(org_id, old_owner_id, new_owner_id):
    with transaction():
        # 1. 舊擁有人降級
        old_owner_relation.is_active = False
        old_owner_relation.updated_at = now()
        
        # 2. 新擁有人升級
        new_owner_relation.role = 'org_owner'
        new_owner_relation.is_active = True
        new_owner_relation.updated_at = now()
        
        # unique index 自動確保僅一個 org_owner
```

**信心度**：High（95%）
- 資料庫約束保證資料完整性
- 符合系統軟刪除設計
- 業界標準做法

---

## 項目 #8: TeacherSchool_roles陣列的有效值與驗證

### 釐清問題
teacher_schools.roles 定義為 jsonb 陣列，有效值為 ['school_principal', 'school_admin', 'teacher']，如何驗證？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
roles jsonb [not null, default: '[]', note: "學校角色列表（JSON 陣列）: ['school_principal', 'school_admin', 'teacher']"]
```
- 使用 jsonb 而非 ENUM
- 預設為空陣列
- 支援多重角色

**設計意圖分析**：
- 使用 jsonb 顯示需要靈活性（未來可能新增角色）
- 不使用 ENUM 避免 schema migration 困難

**業界慣例**：
- API 層驗證：快速、易維護、錯誤訊息友善
- 資料庫 CHECK 約束：效能較好、保證資料完整性

**系統架構考慮**：
- 專案使用 Pydantic（FastAPI）
- 適合在 schema 層面驗證

### 決策：**選項 A - 僅在應用層驗證（API schema validation）**

**理由**：
1. 使用 Pydantic 的 validator 更易維護
2. 錯誤訊息更友善（400 Bad Request）
3. 未來新增角色無需資料庫 migration
4. 符合 FastAPI 設計模式

**實作建議**：
```python
# schemas.py
from enum import Enum
from typing import List

class SchoolRole(str, Enum):
    SCHOOL_PRINCIPAL = "school_principal"
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"

class TeacherSchoolCreate(BaseModel):
    teacher_id: int
    school_id: uuid.UUID
    roles: List[SchoolRole]
    
    @validator('roles')
    def validate_roles(cls, v):
        if not v:
            raise ValueError('至少需要一個角色')
        if len(v) != len(set(v)):
            raise ValueError('角色不可重複')
        return v
```

**替代方案（若需要資料庫層保證）**：
```sql
-- PostgreSQL CHECK 約束（較複雜）
ALTER TABLE teacher_schools
ADD CONSTRAINT check_roles_valid
CHECK (
  roles::jsonb @> '[]'::jsonb AND
  (SELECT bool_and(value::text IN ('"school_principal"', '"school_admin"', '"teacher"'))
   FROM jsonb_array_elements(roles))
);
```

**API 文件補充**：
```
roles (array of strings): 學校角色列表
  - 允許值: ["school_principal", "school_admin", "teacher"]
  - 可同時擁有多個角色
  - 不可包含重複角色
```

**信心度**：High（90%）
- 符合 FastAPI/Pydantic 設計模式
- 平衡靈活性與資料完整性

---

## 項目 #9: 個人教師與機構教師身分切換_班級標示所屬的實作方式

### 釐清問題
Feature 說明「班級應標示所屬：『個人』或『機構-台北分校』」，如何判斷班級是個人還是機構？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
classroom_schools {
  classroom_id int [unique, note: "一個班級只能屬於一個學校"]
}
Note: "獨立教師的班級: classroom_schools 無記錄"
Note: "機構教師的班級: classroom_schools 有記錄"
```
- 設計已明確：有無 classroom_schools 記錄判斷所屬

**Feature 確認**：
```gherkin
場景: 選擇個人視圖查看個人資料
  那麼 我應只看到個人建立的班級 "個人班級A"
  而且 我不應看到機構班級
```
- 個人班級 = 無 classroom_schools 記錄
- 機構班級 = 有 classroom_schools 記錄

### 決策：**選項 A - 查詢 classroom_schools 表，有記錄即為機構班級**

**理由**：
1. DBML 設計已明確定義判斷邏輯
2. 無需新增欄位（避免資料冗餘）
3. 查詢效能可接受（classroom_schools 有索引）

**實作建議**：
```python
# API 查詢邏輯
def get_classrooms_with_source(teacher_id):
    """查詢教師的班級並標示所屬"""
    
    # 查詢所有班級
    classrooms = session.query(Classroom).filter(
        Classroom.teacher_id == teacher_id
    ).all()
    
    # 查詢機構班級關聯
    classroom_schools = session.query(ClassroomSchool).filter(
        ClassroomSchool.classroom_id.in_([c.id for c in classrooms]),
        ClassroomSchool.is_active == True
    ).all()
    
    # 建立映射
    school_map = {cs.classroom_id: cs.school for cs in classroom_schools}
    
    # 組合結果
    result = []
    for classroom in classrooms:
        if classroom.id in school_map:
            result.append({
                "classroom": classroom,
                "source": "organization",
                "school": school_map[classroom.id]
            })
        else:
            result.append({
                "classroom": classroom,
                "source": "individual",
                "school": None
            })
    
    return result
```

**前端顯示邏輯**：
```typescript
// 顯示班級標籤
function getClassroomLabel(classroom) {
  if (classroom.source === 'individual') {
    return `${classroom.name} (個人)`;
  } else {
    return `${classroom.name} (機構 - ${classroom.school.name})`;
  }
}
```

**效能優化**：
- 使用 JOIN 查詢減少往返次數
- 對 classroom_schools.classroom_id 建立索引（已有）

**信心度**：High（100%）
- DBML 已明確定義邏輯
- Feature 描述一致

---

## 項目 #10: 建立機構_系統管理員定義與Teacher_is_admin關係

### 釐清問題
建立機構.feature 說明「僅 Platform Owner（Teacher.is_admin = True）」可建立機構，但 erm-organization.dbml 沒有提到 Teacher 表，兩者如何關聯？

### Context Inference 推理

**從 DBML 推斷**：
```dbml
teacher_organizations {
  teacher_id int [ref: > teachers.id, note: "教師 ID，CASCADE 刪除"]
}
```
- teacher_organizations 參照 teachers.id
- 顯示 teachers 表定義在其他位置

**檔案結構推斷**：
```
spec/
  erm-organization.dbml  # 機構領域
  erm-subscription.dbml  # 訂閱領域（可能包含 Teacher）
  erm-xxx.dbml          # 其他領域
```

**業界慣例**：
- 大型系統通常分領域建模（Domain-Driven Design）
- 跨領域參照使用外鍵（ref: > other_table.id）
- 不在每個 DBML 重複定義核心實體

### 決策：**選項 A - Teacher 表定義在其他 DBML 檔案中**

**理由**：
1. teacher_organizations 已正確參照 teachers.id
2. 符合領域驅動設計（機構領域 vs 使用者領域）
3. 避免資料模型重複定義

**建議行動**：
1. **建立跨 DBML 參照文件**
   ```markdown
   # spec/erm-cross-references.md
   
   ## 跨領域實體參照
   
   ### Teacher 表
   - **定義位置**: spec/erm-user.dbml（假設）
   - **被參照位置**:
     - spec/erm-organization.dbml: teacher_organizations.teacher_id
     - spec/erm-subscription.dbml: subscriptions.teacher_id
   
   ### 權限檢查
   - Teacher.is_admin: 平台擁有者標記
   - 用於建立機構權限檢查（建立機構.feature）
   ```

2. **在 erm-organization.dbml 加入註解**
   ```dbml
   // 跨領域參照
   // Teacher 表定義: spec/erm-user.dbml
   // Platform Owner 判斷: Teacher.is_admin = true
   ```

3. **Feature 背景資訊補充**
   ```gherkin
   背景資訊:
     建立機構權限: 僅 Platform Owner（Teacher.is_admin = True）
     Teacher 表定義: 參照 spec/erm-user.dbml
   ```

**信心度**：High（95%）
- DBML 參照語法正確
- 符合領域驅動設計

---

## 項目 #11: 管理機構成員_查看成員列表的排序與分頁規則

### 釐清問題
管理機構成員.feature 中「查看機構成員列表」沒有說明排序與分頁規則？

### Context Inference 推理

**Feature 分析**：
```gherkin
場景: 機構負責人查看所有成員
  那麼 我應看到以下成員列表
    | 姓名    | Email             | 角色        |
    | 張三    | zhang@teacher.com | org_admin   |
    | 李四    | li@teacher.com    | org_admin   |
```
- Example 未明確排序規則
- 未提到分頁

**業界慣例**：
- API 設計通常支援 `?page=1&limit=20&sort=created_at`
- 預設排序：按加入時間或按角色優先級

**系統架構考慮**：
- 此為 API 實作細節，不影響業務邏輯
- Feature 應關注「what」而非「how」

### 決策：**選項 D - 此為 API 實作細節，Feature 不明確規範**

**理由**：
1. 排序與分頁為技術實作細節，不影響業務規則
2. Feature 應關注核心邏輯（誰可以看、看到什麼）
3. 避免 Feature 過度技術化

**建議行動**：
1. **在 API 文件中定義**
   ```yaml
   # docs/api/organizations.yaml
   GET /api/organizations/{org_id}/members:
     parameters:
       - name: page
         description: 頁碼（預設 1）
       - name: limit
         description: 每頁筆數（預設 20，最大 100）
       - name: sort
         description: 排序欄位（預設 created_at）
         enum: [created_at, name, role]
       - name: order
         description: 排序方向（預設 desc）
         enum: [asc, desc]
     responses:
       200:
         schema:
           total: 整數
           page: 整數
           limit: 整數
           data: 陣列
   ```

2. **預設排序建議**
   - 第一優先：role 角色優先級（org_owner > org_admin）
   - 第二優先：created_at 加入時間（新到舊）

3. **Feature 保持簡潔**
   - 不在 Feature 中寫排序與分頁邏輯
   - 若有業務需求（如「最近加入的成員」），再補充 Example

**信心度**：High（100%）
- Feature 與 API 文件的職責分離
- 業界標準做法

---

## 項目 #12: AI輔助新增機構資料_AI對話框的技術實作方案

### 釐清問題
AI輔助新增機構資料.feature 詳細描述了 AI 對話框的互動流程，但沒有說明技術實作方案？

### Context Inference 推理

**Feature 性質分析**：
- 標題為「AI 輔助」（增強功能）
- 非核心流程（建立機構.feature 為核心）
- 屬於 UX 優化

**業界慣例**：
- Feature 描述「what」（功能需求）
- 技術方案在 Technical Design Doc 中定義

**架構影響**：
- AI 方案選擇（LLM API vs 規則引擎）不影響資料模型
- 可延後決策

### 決策：**選項 E - 此為 UI/UX 規格，技術方案待定**

**理由**：
1. Feature 職責為定義業務需求，非技術實作
2. AI 方案選擇不影響核心資料模型
3. 可先實作表單模式，AI 功能延後

**建議行動**：
1. **分階段實作**
   - Phase 1: 傳統表單（建立機構.feature）
   - Phase 2: AI 對話框（AI輔助新增機構資料.feature）

2. **技術方案評估文件**
   ```markdown
   # docs/technical/ai-form-assistant.md
   
   ## 方案比較
   
   ### 方案 A: OpenAI/Claude API
   - 優點: 理解能力強、易實作
   - 缺點: 成本高、依賴外部服務
   - 成本估算: $0.002/次對話
   
   ### 方案 B: 規則引擎（Pattern Matching）
   - 優點: 成本低、無外部依賴
   - 缺點: 準確度較低、維護成本高
   
   ### 方案 C: 混合方案
   - 簡單解析用規則引擎
   - 複雜情況用 LLM API
   
   ## 建議
   Phase 1 實作時再評估，目前保留 Feature 規格即可
   ```

3. **Feature 保持技術無關**
   - 描述使用者體驗
   - 不指定技術實作

**信心度**：High（100%）
- Feature 與技術實作的職責分離
- 符合敏捷開發實踐

---

## 項目 #13: AI輔助新增機構資料_Excel範本的標準化與維護策略

### 釐清問題
AI輔助新增機構資料.feature 提到「下載範本」與「智能識別欄位」，但沒有說明範本維護策略？

### Context Inference 推理

**Feature 性質分析**：
- 與項目 #12 相同，屬於 UX 增強功能
- Excel 範本為支援性資源

**業界慣例**：
- 範本通常存放在 static/ 或由後端動態生成
- 智能識別為技術實作細節

**實作考慮**：
- 範本格式可能隨資料模型變更
- 多語言支援需求未明確

### 決策：**選項 E - 此為 UX 規格，實作細節待定**

**理由**：
1. 範本維護策略為實作細節，不影響 Feature 規格
2. 可在實作階段根據需求選擇方案
3. Feature 應關注使用者體驗而非實作方式

**建議行動**：
1. **範本管理策略（實作時決定）**
   - 選項 A: 靜態檔案（backend/static/templates/school_import.xlsx）
   - 選項 B: 動態生成（根據當前 schema）

2. **智能識別實作（實作時決定）**
   - 選項 A: 模糊匹配（Levenshtein distance）
   - 選項 B: 預定義映射表

3. **Feature 保持規格簡潔**
   - 描述使用者體驗（下載範本、上傳、識別）
   - 不指定技術細節

**信心度**：High（100%）
- 與項目 #12 一致的決策邏輯
- 職責分離原則

---

## 項目 #14: 機構設定與擁有人註冊_專案服務人員與org_admin角色的關係

### 釐清問題
Feature 說明「專案服務人員應獲得 org_admin 角色」，與一般 org_admin 的差異是什麼？

### Context Inference 推理

**從 Feature 推斷**：
```gherkin
場景: 指派專案服務人員為機構管理人
  當 我指派 "林服務" 為專案服務人員
  那麼 "林服務" 應獲得 "org_admin" 角色
```
- 專案服務人員獲得 org_admin 角色
- 無特殊說明

**從 DBML 推斷**：
```dbml
teacher_organizations {
  role varchar(50) [note: "機構角色: org_owner（機構負責人）、org_admin（機構管理人）"]
}
```
- 僅定義兩種角色：org_owner, org_admin
- 無 project_staff 或 is_staff 欄位

**業務邏輯推斷**：
- 專案服務人員 = Duotopia 內部員工擔任機構管理人
- 可能需要額外標記（跨機構服務）

### 決策：**選項 A - 專案服務人員就是 org_admin，無差異**

**理由**：
1. DBML 僅定義 org_owner 和 org_admin 兩種角色
2. Feature 明確說明「獲得 org_admin 角色」
3. 若需區分，應在 DBML 中定義新欄位或角色
4. 當前設計無明確差異需求

**若未來需要區分**（低信心度推測）：
```dbml
// 方案 A: 新增欄位標記
teacher_organizations {
  is_staff boolean [default: false, note: "是否為 Duotopia 內部服務人員"]
}

// 方案 B: 新增角色
teacher_organizations {
  role varchar(50) [note: "org_owner, org_admin, project_staff"]
}
```

**建議行動**：
1. **當前實作**：專案服務人員 = org_admin
2. **若需區分**：與產品經理確認需求，補充 DBML 設計
3. **Feature 補充**：說明專案服務人員的定義與權限

**信心度**：High（85%）
- 基於 DBML 與 Feature 的明確定義
- 但可能遺漏業務需求（需確認）

---

## 總結

**高信心度項目**：14 項（73.7%）

所有決策基於：
- DBML 明確定義
- Feature 明確規範
- 業界標準做法
- 系統一致性原則

**建議審查重點**：
1. 項目 #6（CASCADE vs 軟刪除）- 確認資料保留策略
2. 項目 #5（tax_id 唯一性）- 確認機構生命週期
3. 項目 #7（org_owner 約束）- 確認資料庫約束設計

**下一步**：審查低信心度項目（5 項），需業務決策確認
