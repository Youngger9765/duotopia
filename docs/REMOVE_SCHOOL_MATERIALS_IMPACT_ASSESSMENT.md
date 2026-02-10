# 移除學校教材層級影響評估報告

**評估日期**: 2026-02-10  
**評估標的**: 移除機構中的學校教材層級，保留機構教材給各分校共同使用  
**文件狀態**: ⚠️ 影響評估報告

---

## 📊 執行摘要

### 評估結論

**建議**: ⚠️ **慎重考慮** - 影響範圍廣泛，需要完整的遷移計劃

**主要風險**:

- 現有學校教材數據遷移問題
- 需要大量代碼重構（Backend + Frontend）
- 可能影響使用者工作流程
- 測試覆蓋需全面重新檢查

**預估工作量**: 8-12 個工作日（含測試與文檔更新）

---

## 🏗️ 現況分析

### 目前的教材層級架構

```
┌─────────────────────────────────────────────────────────────┐
│                     教材層級結構 (現有)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1️⃣ 機構教材 (Organization Materials)                       │
│     • 使用欄位: organization_id (非 NULL)                    │
│     • 使用欄位: school_id = NULL                             │
│     • 權限: org_owner, org_admin                             │
│     • 用途: 給該機構所有學校共用                             │
│     • API: /api/organizations/{org_id}/programs             │
│                                                               │
│  2️⃣ 學校教材 (School Materials) ⚠️ 預計移除                │
│     • 使用欄位: school_id (非 NULL)                          │
│     • 使用欄位: organization_id (非 NULL, 繼承自學校)        │
│     • 權限: org_owner, org_admin, school_admin              │
│     • 用途: 給特定學校專用                                   │
│     • API: /api/schools/{school_id}/programs                │
│                                                               │
│  3️⃣ 老師教材 (Teacher Materials)                            │
│     • 使用欄位: teacher_id (非 NULL)                         │
│     • 使用欄位: classroom_id (可為 NULL，template 時)        │
│     • 權限: 該老師本人                                       │
│     • 用途: 老師個人教材或班級專用教材                       │
│     • API: /api/programs?scope=teacher                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 學校教材的使用情況

#### 數據庫層級 (`backend/models/program.py`)

```python
class Program(Base):
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=True)
    school_id = Column(UUID, ForeignKey("schools.id"), nullable=True)  # ⚠️ 使用中

    # 判斷條件：
    # - organization_id NOT NULL + school_id NULL = 機構教材
    # - school_id NOT NULL = 學校教材
    # - teacher_id NOT NULL + classroom_id NOT NULL = 班級教材
    # - teacher_id NOT NULL + classroom_id NULL = 老師模板教材
```

#### Backend API 路由

1. **專屬路由**: `backend/routers/school_programs.py` (1004 行)
   - 6 個完整的 CRUD + Copy 端點
   - 權限檢查邏輯
   - 深度複製功能

2. **統一 API**: `backend/routers/programs.py`
   - 支援 `scope=school&school_id={id}` 參數
   - List/Create/Update/Delete/Reorder 操作

3. **服務層**: `backend/services/program_service.py`
   - 學校教材的權限檢查
   - 查詢過濾邏輯

#### Frontend 前端頁面

1. **機構管理員頁面**: `frontend/src/pages/organization/SchoolMaterialsPage.tsx`
   - 261 行完整實現
   - 顯示學校專屬教材
   - 提供 CRUD 操作介面

2. **老師頁面**: `frontend/src/pages/teacher/SchoolMaterialsPage.tsx`
   - 讓老師查看所屬學校的教材
   - 複製到自己的班級

3. **路由配置**:
   - `/organization/schools/:schoolId/materials`
   - `/teacher/school-materials`

#### 測試覆蓋

- `test_school_scope_programs.py` - 統一 API 測試
- `test_school_programs_api.py` - 專屬 API 測試
- `integration/api/test_school_programs.py` - 整合測試

---

## 🎯 變更目標

### 變更後的架構

```
┌─────────────────────────────────────────────────────────────┐
│                   教材層級結構 (變更後)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1️⃣ 機構教材 (Organization Materials) ✅ 保留並強化         │
│     • 使用欄位: organization_id (非 NULL)                    │
│     • 使用欄位: school_id = NULL (必須)                      │
│     • 權限: org_owner, org_admin                             │
│     • 用途: 給該機構所有學校共用 (原本功能不變)              │
│     • API: /api/organizations/{org_id}/programs             │
│     • 特性:                                                  │
│       - 所有分校都能查看和複製                               │
│       - 統一管理，避免版本分歧                               │
│                                                               │
│  2️⃣ 老師教材 (Teacher Materials) ✅ 保留                    │
│     • 使用欄位: teacher_id (非 NULL)                         │
│     • 使用欄位: classroom_id (可為 NULL)                     │
│     • 權限: 該老師本人                                       │
│     • 用途: 老師個人教材或班級專用教材                       │
│     • API: /api/programs?scope=teacher                      │
│                                                               │
│  ❌ 學校教材 (School Materials) - 已移除                    │
│     原有功能整合到機構教材                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 業務邏輯變更

**原本的工作流程**:

```
機構管理員 → 建立機構教材（全校共用）
          → 建立各學校專屬教材（單一學校）
學校管理員 → 只能管理本校專屬教材
          → 可查看機構教材並複製
老師      → 從學校教材複製到班級
          → 從機構教材複製到班級
```

**變更後的工作流程**:

```
機構管理員 → 建立機構教材（全校共用）✅
          → （無法建立學校專屬教材）❌
學校管理員 → （無法管理學校教材）❌
          → 只能查看機構教材並複製
老師      → 從機構教材複製到班級 ✅
          → 建立個人教材模板 ✅
```

---

## 📋 影響範圍詳細分析

### 1. 數據庫層級影響

#### 1.1 資料遷移策略

**現有學校教材數據處理** (Critical ⚠️):

```sql
-- 檢查現有學校教材數量
SELECT COUNT(*) FROM programs
WHERE school_id IS NOT NULL;

-- 選項 A: 提升為機構教材（建議）
UPDATE programs
SET school_id = NULL
WHERE school_id IS NOT NULL
  AND organization_id IS NOT NULL;

-- 選項 B: 降級為老師教材（保留個性化）
UPDATE programs
SET school_id = NULL,
    source_metadata = jsonb_set(
        COALESCE(source_metadata, '{}'),
        '{original_school_id}',
        to_jsonb(school_id::text)
    )
WHERE school_id IS NOT NULL;

-- 選項 C: 軟刪除（不建議，會遺失數據）
UPDATE programs
SET is_active = false,
    deleted_at = NOW()
WHERE school_id IS NOT NULL;
```

**欄位處理方案**:

```sql
-- 選項 1: 保留欄位但標記為廢棄（向後相容）✅ 建議
ALTER TABLE programs
ADD COLUMN IF NOT EXISTS _deprecated_school_id UUID;

UPDATE programs
SET _deprecated_school_id = school_id,
    school_id = NULL
WHERE school_id IS NOT NULL;

-- 選項 2: 完全移除欄位（破壞性變更）⚠️
ALTER TABLE programs DROP COLUMN school_id;

-- 選項 3: 加入約束確保不再使用（推薦過渡方案）✅
ALTER TABLE programs
ADD CONSTRAINT check_no_school_materials
CHECK (school_id IS NULL);
```

#### 1.2 Migration 腳本

需要新增 Alembic migration:

```python
# alembic/versions/xxxx_remove_school_materials.py
"""Remove school materials level

Revision ID: xxxx
Revises: yyyy
Create Date: 2026-02-10
"""

def upgrade():
    # 1. 數據遷移
    op.execute("""
        UPDATE programs
        SET school_id = NULL,
            source_metadata = CASE
                WHEN school_id IS NOT NULL
                THEN jsonb_set(
                    COALESCE(source_metadata, '{}'),
                    '{migrated_from_school_id}',
                    to_jsonb(school_id::text)
                )
                ELSE source_metadata
            END
        WHERE school_id IS NOT NULL
    """)

    # 2. 加入約束
    op.create_check_constraint(
        'check_no_school_materials',
        'programs',
        'school_id IS NULL'
    )

def downgrade():
    # 回滾邏輯
    op.drop_constraint('check_no_school_materials', 'programs')
```

### 2. Backend API 層級影響

#### 2.1 需要移除的檔案

```
backend/routers/school_programs.py              (1004 行) ❌ 完全移除
backend/tests/test_school_programs_api.py       ❌ 移除或重寫
backend/tests/test_school_scope_programs.py     ❌ 移除或重寫
backend/tests/integration/api/test_school_programs.py  ❌ 移除
```

#### 2.2 需要修改的檔案

##### `backend/routers/programs.py`

```python
# 移除 scope=school 支援
@router.get("/api/programs")
async def list_programs(
    scope: str = Query("teacher", regex="^(teacher|organization)$"),  # 移除 school
    school_id: str = Query(None),  # ❌ 移除此參數
    organization_id: str = Query(None),
    # ...
):
    if scope == "school":  # ❌ 移除此分支
        raise HTTPException(
            status_code=400,
            detail="School scope is no longer supported. Use organization scope instead."
        )
```

**影響的端點**:

- `GET /api/programs?scope=school` ❌
- `POST /api/programs?scope=school` ❌
- `PUT /api/programs/{id}?scope=school` ❌
- `DELETE /api/programs/{id}?scope=school` ❌
- `POST /api/programs/reorder?scope=school` ❌

##### `backend/services/program_service.py`

```python
# 移除學校教材查詢邏輯
def list_programs_by_scope(...):
    if scope == "school":  # ❌ 移除
        # ... 300+ 行邏輯需要移除

    elif scope == "organization":  # ✅ 保留並強化
        # ... 確保機構教材查詢正確
```

##### `backend/utils/permissions.py`

```python
def can_manage_program(teacher_id, program, db):
    # 移除學校教材權限檢查
    if program.school_id:  # ❌ 移除此分支
        return has_school_materials_permission(...)
```

##### `backend/models/program.py`

```python
class Program(Base):
    school_id = Column(UUID, ...)  # ⚠️ 需要處理策略（保留/移除/約束）
```

#### 2.3 依賴關係檢查

需要 grep 搜尋所有引用:

```bash
# 搜尋 school_id 使用
grep -r "program.school_id" backend/
grep -r "scope.*school" backend/
grep -r "school.*material" backend/
grep -r "/schools/.*/programs" backend/
```

**已知引用位置** (根據搜尋結果):

- `routers/programs.py` - 多處引用
- `routers/classroom_schools.py` - 引用 `program.school_id`
- `services/program_service.py` - 查詢邏輯
- `services/resource_materials_service.py` - 過濾邏輯
- `utils/permissions.py` - 權限檢查
- 多個測試文件

### 3. Frontend 前端層級影響

#### 3.1 需要移除的檔案

```
frontend/src/pages/organization/SchoolMaterialsPage.tsx  (261 行) ❌
frontend/src/pages/teacher/SchoolMaterialsPage.tsx       ❌
frontend/src/components/shared/SchoolProgramCreateDialog.tsx  ❌ (如果存在)
```

#### 3.2 需要修改的檔案

##### `frontend/src/routes/organizationRoutes.tsx`

```tsx
// 移除學校教材路由
{
  path: "schools/:schoolId/materials",  // ❌ 移除
  element: <SchoolMaterialsPage />
}
```

##### `frontend/src/config/sidebarConfig.tsx`

```tsx
// 移除側邊欄項目
{
  id: "school-materials",  // ❌ 移除
  label: "學校教材",
  path: "/teacher/school-materials"
}
```

##### `frontend/src/App.tsx`

```tsx
// 移除路由定義
<Route
  path="/teacher/school-materials" // ❌ 移除
  element={<SchoolMaterialsPage />}
/>
```

##### `frontend/src/components/TeacherLayout.tsx`

```tsx
// 已經有過濾邏輯，確認是否完整
items: group.items.filter((item) => item.id !== "school-materials"),
```

##### `frontend/src/components/LessonDialog.tsx`

```tsx
// 移除學校教材的 API 路徑邏輯
/** Custom API base path for school-level materials */  // ❌ 移除註解和相關代碼
apiBasePath?: string;
```

#### 3.3 需要加強的功能

**機構教材頁面增強** (`frontend/src/pages/organization/MaterialsPage.tsx`):

```tsx
// 需要強化以下功能：
// 1. 更清楚的說明「此教材所有分校共用」
// 2. 顯示哪些學校的老師正在使用此教材
// 3. 複製統計（被複製到多少個班級）

// 新增提示組件
<Alert>
  <InfoIcon />
  <AlertTitle>機構共享教材</AlertTitle>
  <AlertDescription>
    此教材包將提供給所有分校使用。各分校老師可複製到自己的班級進行個性化調整。
  </AlertDescription>
</Alert>
```

### 4. 權限系統影響

#### 4.1 Casbin 策略調整

**需要移除的策略**:

```csv
# conf/policy.csv
# 這些策略需要檢查是否還需要：
p, school_admin, manage_materials, write, org-*    # ⚠️ 需確認
```

**需要確保的策略**:

```csv
# 確保機構教材權限正確
p, org_owner, manage_materials, write, org-*       # ✅ 保留
p, org_admin, manage_materials, write, org-*       # ✅ 保留
```

#### 4.2 權限檢查邏輯

```python
# backend/services/casbin_service.py
def check_manage_materials_permission(teacher_id, organization_id, db):
    """
    檢查是否有管理機構教材的權限

    變更: 移除學校層級檢查
    """
    # ❌ 移除: 檢查是否為 school_admin
    # ✅ 保留: 檢查是否為 org_owner/org_admin
```

### 5. 測試覆蓋影響

#### 5.1 需要移除的測試

```
backend/tests/test_school_programs_api.py                      ❌
backend/tests/test_school_scope_programs.py                    ❌
backend/tests/integration/api/test_school_programs.py          ❌
```

#### 5.2 需要更新的測試

```python
# backend/tests/test_programs_api.py
class TestProgramsAPI:
    def test_list_programs_scope_school(self):  # ❌ 移除或改為測試失敗
        """Should reject scope=school"""
        response = client.get("/api/programs?scope=school&school_id=xxx")
        assert response.status_code == 400
        assert "no longer supported" in response.json()["detail"]
```

#### 5.3 需要新增的測試

```python
# backend/tests/test_organization_materials_enhanced.py
class TestOrganizationMaterialsEnhanced:
    """測試機構教材在移除學校層級後的完整功能"""

    def test_org_materials_visible_to_all_schools(self):
        """機構教材對所有分校的老師都可見"""

    def test_school_admin_cannot_create_school_materials(self):
        """school_admin 不能建立學校專屬教材"""

    def test_migrate_old_school_materials(self):
        """測試舊學校教材的遷移邏輯"""
```

### 6. 文檔更新影響

#### 6.1 需要更新的文檔

```
docs/API_ORGANIZATION_HIERARCHY.md     - 移除學校教材章節
docs/MATERIALS_ARCHITECTURE.md          - 更新架構圖
docs/TESTING_GUIDE.md                   - 更新測試說明
ORG_PRD.md                              - 更新需求文檔
README.md                               - 更新功能說明
```

#### 6.2 需要新增的文檔

```
docs/MIGRATION_REMOVE_SCHOOL_MATERIALS.md   - 遷移指南
docs/SCHOOL_MATERIALS_DEPRECATION.md        - 棄用公告
CHANGELOG.md                                - 記錄重大變更
```

### 7. 使用者體驗影響

#### 7.1 學校管理員 (school_admin)

**Before (移除前)**:

- ✅ 可建立學校專屬教材
- ✅ 可管理本校教材
- ✅ 可查看機構教材並複製

**After (移除後)**:

- ❌ 不能建立學校專屬教材 (功能喪失)
- ❌ 不能管理原有學校教材
- ✅ 可查看機構教材並複製 (保留)
- ⚠️ 需要請求 org_admin 將需求加入機構教材

**影響評估**: ⚠️ **中度負面影響** - 權限降低

#### 7.2 機構管理員 (org_owner/org_admin)

**Before (移除前)**:

- ✅ 可建立機構教材
- ✅ 可建立各學校專屬教材
- ✅ 分別管理

**After (移除後)**:

- ✅ 可建立機構教材 (保留)
- ❌ 不能建立學校專屬教材
- ✅ 統一管理更簡化 (正面影響)

**影響評估**: ✅ **輕微正面影響** - 管理簡化

#### 7.3 一般老師 (teacher)

**Before (移除前)**:

- ✅ 可查看本校教材
- ✅ 可查看機構教材
- ✅ 可複製到班級

**After (移除後)**:

- ❌ 不能查看學校教材 (已移除)
- ✅ 可查看機構教材 (保留)
- ✅ 可複製到班級 (保留)

**影響評估**: ⚠️ **輕度負面影響** - 選擇減少

---

## ⚠️ 風險評估

### 高風險項目 🔴

1. **數據遺失風險**
   - 現有學校教材若未妥善遷移可能遺失
   - 建議: 完整備份 + 多選項遷移策略

2. **破壞性 API 變更**
   - 移除 `/api/schools/{id}/programs` 端點
   - 影響已整合的第三方客戶端（如果有）
   - 建議: 保留端點並返回 410 Gone + 遷移指引

3. **使用者工作流程中斷**
   - school_admin 喪失建立專屬教材能力
   - 建議: 提前溝通 + 提供替代方案

### 中風險項目 🟡

4. **測試覆蓋不足**
   - 移除測試後可能遺漏邊緣案例
   - 建議: 完整的回歸測試

5. **權限系統複雜度**
   - Casbin 策略需要仔細調整
   - 建議: 階段性部署 + 權限日誌

### 低風險項目 🟢

6. **前端路由移除**
   - 影響範圍明確且可控
   - 建議: 加 404 頁面提示

7. **文檔更新**
   - 純文字變更，無系統風險
   - 建議: 結構化更新清單

---

## 📝 實施建議

### 分階段執行計劃

#### Phase 1: 準備階段 (2-3 天)

- [ ] 完整備份生產數據庫
- [ ] 統計現有學校教材數量和使用情況
- [ ] 與使用者溝通變更計劃
- [ ] 準備遷移腳本和回滾方案

#### Phase 2: 數據遷移 (1-2 天)

- [ ] 在測試環境執行遷移
- [ ] 驗證數據完整性
- [ ] 執行生產環境遷移
- [ ] 保留備份 30 天

#### Phase 3: Backend 重構 (2-3 天)

- [ ] 移除 school_programs.py
- [ ] 更新 programs.py 移除 scope=school
- [ ] 更新權限檢查邏輯
- [ ] 更新測試用例

#### Phase 4: Frontend 重構 (1-2 天)

- [ ] 移除學校教材頁面
- [ ] 更新路由配置
- [ ] 加強機構教材頁面
- [ ] 更新 UI 文案

#### Phase 5: 測試與部署 (2-3 天)

- [ ] 完整回歸測試
- [ ] 使用者驗收測試 (UAT)
- [ ] 更新文檔
- [ ] 釋出版本

### 替代方案

#### 選項 A: 完全移除 (本報告評估方案)

- **優點**: 架構簡化，維護成本降低
- **缺點**: 破壞性變更，使用者適應成本
- **建議場景**: 學校教材使用率低 (<10%)

#### 選項 B: 保留但標記為 Deprecated

```python
@router.get("/api/schools/{school_id}/programs")
@deprecated(
    reason="School-level materials are deprecated. Use organization materials instead.",
    version="2.0.0"
)
async def list_school_programs(...):
    # 保留功能但回傳警告
    warnings.warn(DeprecationWarning("..."))
```

- **優點**: 平滑過渡，向後相容
- **缺點**: 需要維護舊代碼
- **建議場景**: 學校教材使用率中等 (10-50%)

#### 選項 C: 功能轉換 (學校 → 標籤系統)

```python
# 將學校教材轉換為帶標籤的機構教材
class Program(Base):
    organization_id = Column(UUID, ...)
    tags = Column(JSON)  # {"target_schools": ["uuid1", "uuid2"]}
    visibility = Column(String)  # "all_schools" | "specific_schools"
```

- **優點**: 保留功能性，增加靈活性
- **缺點**: 需要額外開發
- **建議場景**: 學校教材使用率高 (>50%)

---

## 📊 決策矩陣

| 評估維度       | 完全移除    | Deprecated | 標籤系統     |
| -------------- | ----------- | ---------- | ------------ |
| **開發成本**   | 中 (8-10天) | 低 (2-3天) | 高 (15-20天) |
| **維護成本**   | 低 ✅       | 中         | 中           |
| **使用者影響** | 高 ⚠️       | 低 ✅      | 低 ✅        |
| **架構簡化度** | 高 ✅       | 低         | 中           |
| **風險等級**   | 高 ⚠️       | 低 ✅      | 中           |
| **建議指數**   | ⭐⭐⭐      | ⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐   |

---

## 🎯 最終建議

### 優先級排序

1. **首選方案: 選項 C - 標籤系統** ⭐⭐⭐⭐⭐
   - 保留功能性，提升靈活度
   - 使用者無痛升級
   - 未來可擴展到更多場景

2. **次選方案: 選項 B - Deprecated** ⭐⭐⭐⭐
   - 快速實施，風險最低
   - 給使用者緩衝時間
   - 2-3 版本後再完全移除

3. **備選方案: 選項 A - 完全移除** ⭐⭐⭐
   - 僅在學校教材零使用時考慮
   - 需要完整的溝通計畫

### 決策流程圖

```
開始評估
    ↓
查詢現有學校教材數量
    ↓
┌─────────────────────────────────┐
│ 學校教材數量 = 0 ?              │
└─────────────────────────────────┘
    ↓ Yes                    No ↓
直接移除           ┌──────────────────────┐
                   │ 使用率 < 10% ?       │
                   └──────────────────────┘
                       ↓ Yes        No ↓
                   選項 A        ┌────────────────┐
                   完全移除      │ 使用率 > 50% ? │
                                └────────────────┘
                                   ↓ Yes    No ↓
                                選項 C       選項 B
                                標籤系統  Deprecated
```

---

## 📞 後續行動建議

### 立即執行 (本週)

1. 執行 SQL 查詢統計學校教材使用情況

   ```sql
   SELECT COUNT(*),
          COUNT(DISTINCT school_id),
          COUNT(DISTINCT teacher_id)
   FROM programs
   WHERE school_id IS NOT NULL AND is_active = true;
   ```

2. 與主要使用者溝通，收集反饋

3. 基於使用情況選擇實施方案

### 短期執行 (2週內)

1. 準備詳細的技術實施文檔
2. 開發環境測試遷移腳本
3. 建立完整的測試計畫

### 中期執行 (1個月內)

1. 執行選定的實施方案
2. 完整的回歸測試
3. 使用者培訓和文檔更新

---

## 📚 參考資料

- [API_ORGANIZATION_HIERARCHY.md](./API_ORGANIZATION_HIERARCHY.md)
- [MATERIALS_ARCHITECTURE.md](./MATERIALS_ARCHITECTURE.md)
- [ORG_PRD.md](../ORG_PRD.md)
- [backend/routers/school_programs.py](../backend/routers/school_programs.py)
- [backend/models/program.py](../backend/models/program.py)

---

**評估者**: GitHub Copilot  
**審核狀態**: ⏳ 待決策  
**下次審核**: 執行 SQL 統計後
