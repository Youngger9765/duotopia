# 前端教材選擇簡化方案

**方案名稱**: 派發作業介面：移除學校教材 + 新增機構教材  
**評估日期**: 2026-02-10  
**方案類型**: ✅ 前端層級變更（非破壞性）  
**盤點狀態**: ✅ 雙方盤點完成，結果一致

---

## 📑 目錄

- [方案摘要](#-方案摘要) - 核心變更與優勢評估
- [變更目標](#-變更目標) - 業務邏輯與使用者體驗
- [技術實施細節](#-技術實施細節)
  - [完整影響範圍盤點](#-完整影響範圍盤點) - 7 個位置詳細清單
  - [盤點比對結果](#-盤點比對結果) - 使用者 vs 系統盤點
  - [實施策略選擇](#實施策略選擇) - MVP vs 完整方案
  - [詳細變更清單](#詳細變更清單) - 逐行程式碼對照
- [WorkspaceContext 需求](#-需要新增的-props) - 資料結構確認
- [測試計畫](#-測試計劃) - 完整測試清單
- [實施計畫](#-實施計畫) - MVP vs 完整方案時程
- [UI/UX 改善](#-uiux-改善重點) - 圖示與文案優化
- [注意事項](#️-注意事項) - API、權限、相容性
- [未來優化](#-未來優化建議) - 短中長期規劃
- [決策建議](#-決策建議與盤點總結) - 執行建議與成功指標

---

## 📊 方案摘要

### 核心變更

- ❌ **移除**: 派發作業時的「學校教材」選項
- ✅ **新增**: 派發作業時的「機構教材」選項
- ✅ **保留**: 後端所有 API 和數據結構（零破壞）

### 優勢評估

| 評估維度       | 此方案                   | 完全移除方案      |
| -------------- | ------------------------ | ----------------- |
| **開發成本**   | ⭐⭐⭐⭐⭐ 極低 (1-2 天) | ⭐⭐ 高 (8-12 天) |
| **風險等級**   | ⭐⭐⭐⭐⭐ 極低          | ⭐ 高風險         |
| **數據影響**   | ⭐⭐⭐⭐⭐ 零影響        | ⭐ 需要遷移       |
| **向後相容**   | ⭐⭐⭐⭐⭐ 完全相容      | ⭐ 破壞性變更     |
| **使用者體驗** | ⭐⭐⭐⭐ 改善            | ⭐⭐ 需適應       |

**推薦指數**: ⭐⭐⭐⭐⭐ **強烈推薦**

---

## 🎯 變更目標

### 業務邏輯

**變更前的派發作業流程**:

```
老師進入班級 → 點擊「派發作業」→ 選擇教材來源：
├─ 個人教材（老師自己的模板教材）
├─ 學校教材（本校專屬教材）⚠️ 預計移除
└─ 班級課程（本班已複製的教材）
```

**變更後的派發作業流程**:

```
老師進入班級 → 點擊「派發作業」→ 選擇教材來源：
├─ 個人教材（老師自己的模板教材）
├─ 機構教材（所屬機構的共享教材）✨ 新增
└─ 班級課程（本班已複製的教材）
```

### 使用者體驗改善

1. **簡化認知負擔**
   - 原本: 個人 vs 學校 vs 班級（三個層級）
   - 改為: 個人 vs 機構 vs 班級（更清晰的層級）

2. **統一教材來源**
   - 機構教材 = 所有分校共用
   - 避免各學校建立重複教材

3. **更符合實際使用情境**
   - 大部分情況下，教材是機構統一管理
   - 學校層級的教材需求較少

---

## 🔧 技術實施細節

### 📋 完整影響範圍盤點

#### 核心變更位置（必須修改）🔴

##### 1. 指派作業對話框 - AssignmentDialog.tsx

**URL**: `https://duotopia.co/teacher/classroom/70` > 指派新作業  
**檔案**: `frontend/src/components/AssignmentDialog.tsx`  
**影響行數**: Line 258, 267-273, 322-324, 438-477, 1220-1250, 1498-1580

**變更內容**:

- 將「學校教材」Tab 改為「機構教材」
- 修改 API 呼叫從 `scope=school` 改為 `/api/organizations/{id}/programs`
- 更新載入邏輯、狀態管理、UI 元件

##### 2. 學校詳情頁 - SchoolDetailPage.tsx

**URL**: `https://duotopia.co/organization/schools/{id}`  
**檔案**: `frontend/src/pages/organization/SchoolDetailPage.tsx`  
**影響行數**: Line 368-386

**變更內容**:

- 移除整個「學校教材」Card 按鈕
- 不再導航至 `/organization/schools/${schoolId}/materials`

##### 3. 老師側邊欄 - sidebarConfig.tsx

**URL**: `https://duotopia.co/teacher/dashboard` > 側邊欄選單  
**檔案**: `frontend/src/config/sidebarConfig.tsx`  
**影響行數**: Line 64-67

**變更內容**:

- 將「學校教材」改為「機構教材」
- 建議更新圖示從 `BookOpen` 改為 `Building2`
- 路徑從 `/teacher/school-materials` 改為 `/teacher/organization-materials`

#### 連帶影響位置（建議修改）🟡

##### 4. 老師學校教材頁面 - SchoolMaterialsPage.tsx

**檔案**: `frontend/src/pages/teacher/SchoolMaterialsPage.tsx`  
**決策**: 整個頁面改為顯示機構教材或移除

**選項**:

- A) 重構為機構教材頁面（推薦）
- B) 完全移除並重定向

##### 5. 路由定義 - App.tsx 和 organizationRoutes.tsx

**檔案 A**: `frontend/src/App.tsx` (Line 22, 205-209)  
**檔案 B**: `frontend/src/routes/organizationRoutes.tsx` (Line 10, 77-78)

**變更內容**:

- 移除或重定向 `/teacher/school-materials` 路由
- 移除或重定向 `/organization/schools/:schoolId/materials` 路由
- 更新 import 語句

##### 6. 老師佈局過濾邏輯 - TeacherLayout.tsx

**檔案**: `frontend/src/components/TeacherLayout.tsx`  
**影響行數**: Line 107, 128-133

**變更內容**:

- 更新過濾邏輯從 `school-materials` 改為 `org-materials`
- 更新相關註解

#### 文案清理位置（次要優化）🟢

##### 7. 其他組件中的文字引用

- `CreateProgramDialog.tsx` - Line 82, 165, 187, 551
- `ClassroomMaterialsSidebar.tsx` - Line 111, 183
- `SchoolProgramCreateDialog.tsx` - Line 137, 177
- `LessonDialog.tsx` - Line 34, 99, 130 (註解)

**變更內容**: 將提示文字從「學校教材」改為「機構教材」

---

### 📊 盤點比對結果

| #   | 位置說明           | 使用者盤點 | 系統盤點 | 一致性   | 優先級 |
| --- | ------------------ | ---------- | -------- | -------- | ------ |
| 1   | 指派作業對話框     | ✅         | ✅       | **一致** | 🔴 P0  |
| 2   | 學校詳情頁按鈕     | ✅         | ✅       | **一致** | 🔴 P0  |
| 3   | 老師側邊欄選單     | ✅         | ✅       | **一致** | 🔴 P0  |
| 4   | 學校教材頁面       | -          | ✅       | 補充     | 🟡 P1  |
| 5   | 路由定義 (2處)     | -          | ✅       | 補充     | 🟡 P1  |
| 6   | TeacherLayout 過濾 | -          | ✅       | 補充     | 🟡 P1  |
| 7   | 其他文字/註解      | -          | ✅       | 補充     | 🟢 P2  |

**結論**: 核心 3 個位置完全一致 ✅，另外發現 4 個連帶影響位置需要處理。

---

### 實施策略選擇

#### 選項 A: 最小可行方案（MVP）⭐⭐⭐⭐

**範圍**: 只修改核心 3 個位置

- ✅ AssignmentDialog.tsx
- ✅ SchoolDetailPage.tsx
- ✅ sidebarConfig.tsx

**優點**: 快速上線，風險最低  
**缺點**: 留下死路由和未使用的頁面  
**預估時間**: 2-3 小時

#### 選項 B: 完整方案（推薦）⭐⭐⭐⭐⭐

**範圍**: 修改全部 7 個位置

- 核心 3 處（P0）
- 路由和頁面重構（P1）
- 過濾邏輯更新（P1）
- 文案清理（P2）

**優點**: 徹底解決，無技術債  
**缺點**: 開發時間較長  
**預估時間**: 4-6 小時

---

### 影響範圍總結

**完全不需要修改**:

- ✅ Backend API (零變更)
- ✅ Database Schema (零變更)
- ✅ 測試檔案 (零變更)

### 詳細變更清單

#### 1. 修改 Tab 顯示邏輯

**位置**: `AssignmentDialog.tsx` Line 268

**Before**:

```typescript
const showSchoolTab = mode === "organization" && selectedSchool !== null;
```

**After**:

```typescript
const showOrganizationTab =
  mode === "organization" && selectedOrganization !== null;
```

#### 2. 修改狀態管理

**位置**: `AssignmentDialog.tsx` Line 258, 273

**Before**:

```typescript
const [loadingSchoolPrograms, setLoadingSchoolPrograms] = useState(false);
const [schoolPrograms, setSchoolPrograms] = useState<Program[]>([]);
```

**After**:

```typescript
const [loadingOrganizationPrograms, setLoadingOrganizationPrograms] =
  useState(false);
const [organizationPrograms, setOrganizationPrograms] = useState<Program[]>([]);
```

#### 3. 修改 API 呼叫函數

**位置**: `AssignmentDialog.tsx` Line 439-477

**Before**:

```typescript
const loadSchoolPrograms = async () => {
  if (!selectedSchool) return;

  try {
    setLoadingSchoolPrograms(true);
    const params = new URLSearchParams();
    params.append("school_id", selectedSchool.id);
    params.append("scope", "school");

    const response = await apiClient.get<Program[]>(
      `/api/teachers/programs?${params.toString()}`,
    );

    setSchoolPrograms(response);
  } catch (error) {
    console.error("Failed to load school programs:", error);
    toast.error("載入學校教材失敗");
    setSchoolPrograms([]);
  } finally {
    setLoadingSchoolPrograms(false);
  }
};
```

**After**:

```typescript
const loadOrganizationPrograms = async () => {
  if (!selectedOrganization) return;

  try {
    setLoadingOrganizationPrograms(true);

    // 使用機構專屬的 API 端點
    const response = await apiClient.get<Program[]>(
      `/api/organizations/${selectedOrganization.id}/programs`,
    );

    setOrganizationPrograms(response);
  } catch (error) {
    console.error("Failed to load organization programs:", error);
    toast.error("載入機構教材失敗");
    setOrganizationPrograms([]);
  } finally {
    setLoadingOrganizationPrograms(false);
  }
};
```

#### 4. 修改 useEffect 載入邏輯

**位置**: `AssignmentDialog.tsx` Line 322-324

**Before**:

```typescript
if (showSchoolTab) {
  loadSchoolPrograms();
}
```

**After**:

```typescript
if (showOrganizationTab) {
  loadOrganizationPrograms();
}
```

#### 5. 修改 Tab UI

**位置**: `AssignmentDialog.tsx` Line 1220-1250

**Before**:

```tsx
<TabsList
  className={`grid w-full ${showSchoolTab ? "grid-cols-3" : "grid-cols-2"} mb-2`}
>
  <TabsTrigger value="template">
    <Globe className="h-4 w-4" />
    個人教材
  </TabsTrigger>
  {showSchoolTab && (
    <TabsTrigger value="school">
      <School className="h-4 w-4" />
      學校教材
    </TabsTrigger>
  )}
  <TabsTrigger value="classroom">
    <School className="h-4 w-4" />
    班級課程
  </TabsTrigger>
</TabsList>
```

**After**:

```tsx
<TabsList
  className={`grid w-full ${showOrganizationTab ? "grid-cols-3" : "grid-cols-2"} mb-2`}
>
  <TabsTrigger value="template">
    <Globe className="h-4 w-4" />
    個人教材
  </TabsTrigger>
  {showOrganizationTab && (
    <TabsTrigger value="organization">
      <Building2 className="h-4 w-4" />
      機構教材
    </TabsTrigger>
  )}
  <TabsTrigger value="classroom">
    <Users className="h-4 w-4" />
    班級課程
  </TabsTrigger>
</TabsList>
```

#### 6. 修改 TabContent 內容

**位置**: `AssignmentDialog.tsx` Line 1499-1580

**Before**:

```tsx
{showSchoolTab && (
  <TabsContent value="school" className="flex-1 mt-0 overflow-hidden min-h-0">
    <ScrollArea className="h-full border rounded-lg p-3">
      {loadingSchoolPrograms ? (
        // Loading state
      ) : schoolPrograms.length === 0 ? (
        // Empty state
      ) : (
        <div className="space-y-2">
          {schoolPrograms.map((program) => (
            // Program card
          ))}
        </div>
      )}
    </ScrollArea>
  </TabsContent>
)}
```

**After**:

```tsx
{
  showOrganizationTab && (
    <TabsContent
      value="organization"
      className="flex-1 mt-0 overflow-hidden min-h-0"
    >
      <ScrollArea className="h-full border rounded-lg p-3">
        {loadingOrganizationPrograms ? (
          <div className="flex flex-col items-center justify-center h-96">
            <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto" />
            <p className="mt-6 text-lg font-medium text-gray-700">
              載入機構教材中...
            </p>
          </div>
        ) : organizationPrograms.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-96">
            <Package className="h-16 w-16 text-gray-300 mb-4" />
            <p className="text-gray-500">尚無機構教材</p>
            <p className="text-sm text-gray-400 mt-2">
              請聯絡機構管理員建立共享教材
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {organizationPrograms.map((program) => (
              <Card key={program.id} className="overflow-hidden">
                {/* 與個人教材相同的呈現方式 */}
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </TabsContent>
  );
}
```

#### 7. 修改 activeTab 類型定義

**位置**: `AssignmentDialog.tsx` 多處

**Before**:

```typescript
const [activeTab, setActiveTab] = useState<"template" | "classroom" | "school">(
  "template",
);

setActiveTab(v as "template" | "classroom" | "school");
```

**After**:

```typescript
const [activeTab, setActiveTab] = useState<
  "template" | "classroom" | "organization"
>("template");

setActiveTab(v as "template" | "classroom" | "organization");
```

---

## 📦 需要新增的 Props

### WorkspaceContext 需求檢查

確認 `WorkspaceContext` 是否提供 `selectedOrganization`:

```typescript
// frontend/src/contexts/WorkspaceContext.tsx
interface WorkspaceContextType {
  selectedOrganization: { id: string; name: string } | null;
  selectedSchool: { id: string; name: string } | null;
  // ...
}
```

如果沒有，需要從 `selectedSchool` 中取得其 `organization_id`:

```typescript
const loadOrganizationPrograms = async () => {
  // 從 selectedSchool 取得 organization_id
  if (!selectedSchool?.organization_id) return;

  try {
    setLoadingOrganizationPrograms(true);
    const response = await apiClient.get<Program[]>(
      `/api/organizations/${selectedSchool.organization_id}/programs`,
    );
    setOrganizationPrograms(response);
  } catch (error) {
    console.error("Failed to load organization programs:", error);
    toast.error("載入機構教材失敗");
    setOrganizationPrograms([]);
  } finally {
    setLoadingOrganizationPrograms(false);
  }
};
```

---

## 🧪 測試計劃

### 手動測試清單

#### 1. 基本功能測試

- [ ] 派發作業時能看到「機構教材」Tab
- [ ] 機構教材能正確載入並顯示
- [ ] 能從機構教材中選擇內容加入購物車
- [ ] 能成功派發機構教材的作業

#### 2. 不同模式測試

- [ ] **一般老師模式**: 不顯示機構教材 Tab (只有個人+班級)
- [ ] **機構模式 + 有選擇學校**: 顯示機構教材 Tab (個人+機構+班級)
- [ ] **機構模式 + 未選擇學校**: 不顯示機構教材 Tab

#### 3. Edge Cases

- [ ] 機構無教材時顯示正確的空狀態
- [ ] 機構教材載入失敗時顯示錯誤訊息
- [ ] 切換 Tab 時狀態正確保留

#### 4. 回歸測試

- [ ] 個人教材功能正常
- [ ] 班級課程功能正常
- [ ] 購物車功能正常
- [ ] 派發作業流程完整

### 測試環境

```bash
# 啟動開發環境
cd frontend
npm run dev

# 測試帳號需求：
# 1. 屬於某個機構的老師帳號
# 2. 該機構至少有 1 個學校
# 3. 該機構至少有 1 個教材
```

---

## 📊 實施計畫

### 選項 A: MVP 方案（最小可行）

**範圍**: 核心 3 個位置（P0 優先級）

#### Phase 1: 準備階段 (30 分鐘)

- [x] 完成影響評估與盤點
- [ ] 確認 API 端點 `/api/organizations/{id}/programs` 可用
- [ ] 確認 WorkspaceContext 有 `selectedOrganization`

#### Phase 2: 開發階段 (2 小時)

- [ ] 修改 `AssignmentDialog.tsx`
  - [ ] 更新 Tab 顯示邏輯（school → organization）
  - [ ] 更新狀態管理
  - [ ] 更新 API 呼叫函數
  - [ ] 更新 UI 元件和文案
- [ ] 移除 `SchoolDetailPage.tsx` 中的學校教材按鈕
- [ ] 更新 `sidebarConfig.tsx` 側邊欄項目

#### Phase 3: 測試與部署 (30 分鐘)

- [ ] 基本功能測試
- [ ] 不同模式測試
- [ ] 本地驗證完成

**總預估時間**: 3 小時

---

### 選項 B: 完整方案（推薦）

**範圍**: 全部 7 個位置（P0 + P1 + P2）

#### Phase 1: 準備階段 (30 分鐘)

- [x] 完成影響評估與盤點
- [ ] 確認 API 端點存在且可用
- [ ] 確認 WorkspaceContext 資料結構
- [ ] 建立測試環境與測試帳號

#### Phase 2: 核心開發 (2 小時)

**P0 優先級** - 必須完成

- [ ] 修改 `AssignmentDialog.tsx`（核心功能）
- [ ] 移除 `SchoolDetailPage.tsx` 中的按鈕
- [ ] 更新 `sidebarConfig.tsx`

#### Phase 3: 連帶修改 (1.5 小時)

**P1 優先級** - 建議完成

- [ ] 重構或移除 `SchoolMaterialsPage.tsx`
  - 選項 A: 改為機構教材頁面
  - 選項 B: 移除並重定向
- [ ] 更新路由定義
  - [ ] `App.tsx` - 移除 `/teacher/school-materials`
  - [ ] `organizationRoutes.tsx` - 移除 `schools/:schoolId/materials`
- [ ] 更新 `TeacherLayout.tsx` 過濾邏輯

#### Phase 4: 文案清理 (30 分鐘)

**P2 優先級** - 可選完成

- [ ] 更新 `CreateProgramDialog.tsx` 提示文字
- [ ] 更新 `ClassroomMaterialsSidebar.tsx` 說明
- [ ] 更新 `SchoolProgramCreateDialog.tsx` Toast 訊息
- [ ] 清理 `LessonDialog.tsx` 註解

#### Phase 5: 測試與部署 (1 小時)

- [ ] 執行完整測試清單（基本+模式+Edge Cases+回歸）
- [ ] 修復發現的問題
- [ ] 程式碼審查
- [ ] 部署到測試環境
- [ ] 使用者驗收測試 (UAT)

**總預估時間**: 5.5 小時（約 1 個工作日）

---

### 建議執行方案

**推薦**: 選項 B（完整方案）✅

**理由**:

1. 時間成本差異不大（3h vs 5.5h）
2. 徹底解決問題，無技術債
3. 避免未來維護困擾
4. 使用者體驗更一致

---

## 🎨 UI/UX 改善重點

### 圖示選擇建議

```tsx
import { Building2, Globe, Users } from "lucide-react";

// 個人教材: Globe (地球，代表老師個人的世界)
<Globe className="h-4 w-4" />

// 機構教材: Building2 (建築物，代表機構)
<Building2 className="h-4 w-4" />

// 班級課程: Users (人群，代表班級學生)
<Users className="h-4 w-4" />
```

### 文案優化

| Tab      | 原文案   | 新文案       | 說明         |
| -------- | -------- | ------------ | ------------ |
| 個人教材 | 個人教材 | **我的教材** | 更親切       |
| 機構教材 | -        | **機構共享** | 強調共享性質 |
| 班級課程 | 班級課程 | **本班教材** | 更明確       |

### 空狀態提示優化

```tsx
// 機構教材為空時
<div className="text-center py-12">
  <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
  <h3 className="text-lg font-medium text-gray-700 mb-2">尚無機構共享教材</h3>
  <p className="text-sm text-gray-500 max-w-sm mx-auto">
    機構教材由機構管理員統一建立，所有分校的老師都可以使用。
    如需建立教材，請聯絡您的機構管理員。
  </p>
</div>
```

---

## ⚠️ 注意事項

### 1. API 端點確認

確認以下 API 端點存在且權限正確：

```bash
# 機構教材列表
GET /api/organizations/{org_id}/programs

# 回應範例
[
  {
    "id": 123,
    "name": "TOEIC 多益綠色證書 Part 1",
    "description": "...",
    "organization_id": "uuid",
    "school_id": null,  // 機構教材必須為 null
    "is_template": true,
    "lessons": [...]
  }
]
```

### 2. 權限檢查

確認一般老師能否讀取機構教材：

- ✅ 應該允許: 同機構的老師查看機構教材
- ❌ 應該禁止: 非該機構的老師查看

### 3. 資料一致性

機構教材的特徵：

```sql
-- 機構教材必須滿足
organization_id IS NOT NULL
AND school_id IS NULL
AND is_template = true
```

### 4. 向後相容性

- 舊的「學校教材」數據依然保留在資料庫
- 只是前端不再顯示在派發作業介面
- 機構管理員仍可在後台管理學校教材（如果需要）

---

## 🔄 未來優化建議

### 短期 (1-2 週)

1. 收集使用者反饋
2. 調整 UI/文案
3. 優化載入效能

### 中期 (1-2 月)

1. 如果學校教材使用率持續為 0，考慮完全移除
2. 新增機構教材使用統計
3. 提供「我的最愛」教材功能

### 長期 (3-6 月)

1. 實施標籤系統（參考原評估報告的選項 C）
2. 支援跨機構教材共享（需要權限設計）
3. 教材市集功能

---

## 📚 相關文件

- [完整影響評估報告](./REMOVE_SCHOOL_MATERIALS_IMPACT_ASSESSMENT.md) - 完全移除方案的評估
- [教材架構文件](./MATERIALS_ARCHITECTURE.md) - 整體教材系統架構
- [API 文件](./API_ORGANIZATION_HIERARCHY.md) - 組織層級 API 規格

---

## ✅ 決策建議與盤點總結

### 📋 盤點結果確認

**使用者盤點的 3 個核心位置** ✅:

1. ✅ `https://duotopia.co/teacher/classroom/70` > 指派新作業 - 改顯示機構教材
2. ✅ `https://duotopia.co/organization/schools/{id}` - 不顯示學校教材按鈕
3. ✅ `https://duotopia.co/teacher/dashboard` - 側邊欄「學校教材」改為「機構教材」

**系統補充的 4 個連帶位置**: 4. 🟡 學校教材頁面重構或移除 5. 🟡 路由定義更新（2 處）6. 🟡 TeacherLayout 過濾邏輯 7. 🟢 其他文案清理

**盤點一致性**: ✅ **完全一致**，核心需求明確，補充項目合理。

---

### 推薦執行方案

#### 🎯 方案選擇: 選項 B（完整方案）⭐⭐⭐⭐⭐

**執行範圍**:

- ✅ 核心 3 個位置（使用者盤點）
- ✅ 連帶 4 個位置（系統補充）
- ✅ 文案清理優化

**預估時間**: 5.5 小時（1 個工作日內完成）

**優勢**:

1. 徹底解決問題，無技術債
2. 時間成本可控（< 1 天）
3. 使用者體驗一致性最佳
4. 避免未來維護困擾

---

### 實施步驟建議

#### 第一步: 立即執行前端簡化（本週完成）⭐⭐⭐⭐⭐

- 執行完整方案（7 個位置）
- 快速改善使用者體驗
- 零後端風險
- 立即見效

#### 第二步: 觀察使用情況（1-2 個月）

- 統計機構教材使用率
- 收集使用者反饋
- 監控舊學校教材訪問量
- 評估是否需要進一步調整

#### 第三步: 基於數據決定（2-3 個月後）

- 如果學校教材使用率 = 0 → 考慮完全移除後端
- 如果有特殊需求 → 考慮標籤系統方案
- 如果現況良好 → 維持現狀

---

### 成功指標

**短期指標（1 週內）**:

- [ ] 所有核心功能正常運作
- [ ] 無使用者投訴或錯誤回報
- [ ] 機構教材載入速度 < 2 秒

**中期指標（1 個月內）**:

- [ ] 機構教材使用率 > 70%
- [ ] 使用者滿意度調查 > 4/5
- [ ] 學校教材舊路由訪問量 < 5%

**長期指標（3 個月內）**:

- [ ] 機構教材成為主要選擇
- [ ] 教材管理效率提升
- [ ] 決定是否完全移除學校教材

---

**評估者**: GitHub Copilot  
**盤點日期**: 2026-02-10  
**方案狀態**: ✅ **雙方盤點一致，強烈推薦立即執行**  
**預估完成**: 1 個工作日內
