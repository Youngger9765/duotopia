# 機構教材簡化方案 - Bug/Feature Specification

**Issue**: 移除學校教材層級，簡化為機構教材  
**建立日期**: 2026-02-10  
**狀態**: 📋 規劃中  
**類型**: 功能簡化 / Bug 修復  
**優先級**: P1 - 高

---

## 📋 問題描述

### 現狀

系統目前擁有三層教材架構：

1. **個人教材** - 教師個人創建
2. **機構教材** - 機構層級共享（organization_id）
3. **學校教材** - 學校層級共享（school_id）

### 問題

1. **架構冗餘**：學校教材與機構教材功能重疊
2. **使用者困惑**：教師不清楚何時使用學校教材 vs 機構教材
3. **維護成本**：前端需維護兩套類似的教材選擇邏輯

### 解決方案

**前端簡化方案**（推薦）：

- 在派發作業的 AssignmentDialog 中隱藏「學校教材」Tab
- 只顯示「機構教材」Tab
- Backend API 和資料庫結構保持不變
- 可隨時回滾

---

## 📚 相關文件

### 1. 風險評估報告 ⭐⭐⭐⭐⭐

**檔案**: [FRONTEND_MATERIALS_RISK_ASSESSMENT.md](./FRONTEND_MATERIALS_RISK_ASSESSMENT.md)

**內容摘要**:

- 9 個維度的深度風險分析
- **關鍵發現**: 只有 1 個阻塞性風險（權限問題）
- 10 個風險點中，9 個無風險或低風險
- 完整的解決方案、測試計畫和實施指南

**重點結論**:

```
✅ 資料完整性：無風險（作業已解耦）
✅ 跨機構洩露：無風險（三層防護）
✅ 向後相容：完全相容（可隨時回滾）
🔴 權限問題：高風險（需 Backend 修改 4-5h）
```

### 2. 前端簡化方案

**檔案**: [FRONTEND_MATERIALS_SIMPLIFICATION.md](./FRONTEND_MATERIALS_SIMPLIFICATION.md)

**內容摘要**:

- 7 個需要修改的檔案位置
- 詳細的實作步驟（MVP 3h vs 完整版 5.5h）
- 與使用者的聯合盤點結果

**核心修改**:

- [AssignmentDialog.tsx](../../frontend/src/components/AssignmentDialog.tsx) - 移除學校教材 Tab，新增機構教材 Tab
- [SchoolDetailPage.tsx](../../frontend/src/pages/organization/SchoolDetailPage.tsx) - 移除學校教材入口
- [sidebarConfig.tsx](../../frontend/src/config/sidebarConfig.tsx) - 移除教師側邊欄的學校教材選項

### 3. 完整移除方案評估

**檔案**: [REMOVE_SCHOOL_MATERIALS_IMPACT_ASSESSMENT.md](./REMOVE_SCHOOL_MATERIALS_IMPACT_ASSESSMENT.md)

**內容摘要**:

- Backend 完全移除 school_id 的影響評估
- 7 大影響層面（資料庫、API、權限、測試等）
- 3 種遷移策略比較
- **結論**: 過於複雜，不建議採用

### 4. 資料分析 SQL

**檔案**: [analyze_school_materials_usage.sql](./analyze_school_materials_usage.sql)

**內容摘要**:

- 10 個 SQL 查詢
- 分析學校教材的使用狀況
- 用於驗證遷移前的資料狀態

---

## 🎯 實施計畫

### 階段 1: Backend 權限修改（阻塞項）⭐⭐⭐⭐⭐

**預估工時**: 3 小時

**必須完成**:

1. ✅ 新增 `check_read_organization_materials_permission()` 函數
   - 位置: `backend/utils/permissions.py`
   - 邏輯: 允許所有機構成員讀取（不限於 org_owner/org_admin）

2. ✅ 修改 `get_programs_by_scope()` 函數
   - 位置: `backend/services/program_service.py`
   - 新增 `read_only` 參數（預設 True）
   - 根據模式使用不同的權限檢查

3. ✅ 更新 `/api/programs` 端點
   - 位置: `backend/routers/programs.py`
   - 新增 `read_only: bool = Query(True)` 參數
   - 傳遞至服務層

4. ✅ 撰寫單元測試
   - 測試一般老師可讀取機構教材
   - 測試一般老師無法修改機構教材
   - 測試非機構成員無法訪問

**驗收標準**:

```python
# 一般老師讀取機構教材（應成功）
GET /api/programs?scope=organization&organization_id={id}&read_only=true
→ 200 OK

# 一般老師管理機構教材（應失敗）
POST /api/organizations/{org_id}/programs
→ 403 Forbidden
```

### 階段 2: Frontend 修改（依賴階段 1）⭐⭐⭐⭐

**預估工時**: 1 小時

**修改清單**:

1. ✅ AssignmentDialog.tsx
   - 移除 `loadSchoolPrograms()` 函數
   - 新增 `loadOrganizationPrograms()` 函數
   - 更新 Tab UI（學校 → 機構）

2. ✅ SchoolDetailPage.tsx
   - 移除「學校教材」卡片區塊

3. ✅ sidebarConfig.tsx
   - 移除教師側邊欄的「學校教材」選項

**驗收標準**:

- ✅ 派發作業時能看到「機構教材」Tab
- ✅ 能成功載入機構教材列表
- ✅ 能選擇教材派發作業
- ✅ 一般老師可正常使用

### 階段 3: 測試與驗證 ⭐⭐⭐

**預估工時**: 1 小時

**測試項目**:

- [ ] 權限測試：一般老師、org_admin、org_owner
- [ ] 功能測試：派發作業完整流程
- [ ] 邊界測試：非機構成員、跨機構訪問
- [ ] 回歸測試：現有功能不受影響

---

## 📊 風險總結

| 風險類別   | 等級  | 阻塞 | 緩解措施                 |
| ---------- | ----- | ---- | ------------------------ |
| 權限錯誤   | 🔴 高 | ✅   | Backend 權限修改（4-5h） |
| 資料完整性 | 🟢 無 | ❌   | 無需處理（已解耦）       |
| 跨機構洩露 | 🟢 無 | ❌   | 現有檢查已足夠           |
| 教師工作流 | 🟡 低 | ❌   | 更新 UI 說明             |
| 向後相容   | 🟢 無 | ❌   | 完全相容                 |

**總結**: 10 個風險點中，只有 1 個需要處理的阻塞項。

---

## ✅ 決策建議

### 推薦方案

**✅ 採用前端簡化方案 + Backend 權限修改**

**理由**:

1. 開發成本低（4-5 小時 vs 8-12 天）
2. 風險可控（可隨時回滾）
3. 無需資料遷移
4. 完全向後相容

### 實施順序

1. **優先**: 完成 Backend 權限修改（3h）
2. **接著**: 測試驗證權限邏輯（1h）
3. **最後**: 部署 Frontend 變更（1h）

**總預估時間**: 5 小時  
**成功率**: 95%+

---

## 📝 變更記錄

| 日期       | 版本 | 說明                 | 作者           |
| ---------- | ---- | -------------------- | -------------- |
| 2026-02-10 | v1.0 | 初版規格書與風險評估 | GitHub Copilot |

---

## 📎 相關連結

- [機構模組 ERD](../erm-organization.dbml)
- [原始需求討論](../../docs/ORG_PRD.md)
- [API 文件](../../docs/API_ORGANIZATION_HIERARCHY.md)
