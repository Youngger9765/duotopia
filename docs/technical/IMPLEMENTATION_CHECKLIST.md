# Content 重構實施檢查清單

## 📊 完整影響範圍總結

### 🗄️ **資料庫層面** (已完成)
- [x] 創建 ContentItem 表 (122 筆記錄)
- [x] 創建 StudentItemProgress 表 (95 筆記錄)
- [x] 資料遷移完成
- [x] 建立索引和約束

### 🔧 **後端 API 需要修改** (8 個檔案)

#### 🔴 **高優先級 - 核心功能**
1. **routers/students.py**
   - [ ] `POST /api/students/upload-recording` - 錄音上傳 (已部分修復)
   - [ ] `GET /api/students/assignments/{id}/activities` - 學習介面資料
   - [ ] `POST /api/students/assignments/{id}/submit` - 作業提交

2. **routers/teachers.py**
   - [ ] `GET /api/teachers/assignments/{id}/progress` - 檢視學生進度
   - [ ] `POST /api/teachers/contents` - 創建課程內容
   - [ ] `PUT /api/teachers/contents/{id}` - 編輯課程內容

3. **routers/speech_assessment.py**
   - [ ] AI 評分結果儲存邏輯

#### 🟡 **中優先級 - 重要功能**
4. **routers/assignments.py**
   - [ ] `POST /api/assignments` - 作業創建
   - [ ] `GET /api/assignments/{id}` - 作業詳情

5. **routers/programs.py**
   - [ ] `GET /api/programs/{id}/lessons/{id}/contents` - 課程內容列表

#### 🟢 **低優先級 - 輔助功能**
6. **routers/admin.py** - 管理功能
7. **routers/files.py** - 檔案處理
8. **routers/unassign.py** - 取消指派

### 🎨 **前端需要修改** (10+ 個檔案)

#### 🔴 **最重要 - 學生介面**
1. **StudentActivityPage.tsx**
   - [ ] 資料結構從陣列改為物件
   - [ ] API 回應格式調整
   - [ ] 狀態管理邏輯更新

#### 🟡 **重要 - 其他介面**
2. **AssignmentDetail.tsx** - 作業詳情頁
3. **TeacherAssignmentDetailPage.tsx** - 老師檢視頁
4. **utils/api.ts** - API 介面定義

#### 🟢 **測試檔案**
5. 所有 API 測試檔案需要更新

## 🧪 **TDD 測試合約**

### **必須實作的測試**
- [ ] Contract 1: 學生錄音上傳流程
- [ ] Contract 2: 學生檢視活動資料
- [ ] Contract 3: AI 評分儲存邏輯
- [ ] Contract 4: 老師檢視學生進度
- [ ] Contract 5: 老師創建課程內容

## 📋 詳細實施計畫

### **Phase 1: 後端 API 重構** ⏱️ 2-3 天

#### **Day 1: 核心學生 API**
- [ ] 修改 `upload-recording` API 使用 StudentItemProgress
- [ ] 修改 `activities` API 回傳 ContentItem 結構
- [ ] 測試錄音上傳和資料顯示

#### **Day 2: 老師和評分 API**
- [ ] 修改 `progress` API 顯示每題詳細進度
- [ ] 修改 AI 評分儲存邏輯
- [ ] 修改課程內容 CRUD API

#### **Day 3: 其他 API 和測試**
- [ ] 修改作業相關 API
- [ ] 完成所有後端測試
- [ ] API 文件更新

### **Phase 2: 前端介面調整** ⏱️ 2 天

#### **Day 4: 主要學習介面**
- [ ] 更新 StudentActivityPage.tsx 資料結構
- [ ] 調整 API 呼叫邏輯
- [ ] 測試學生學習流程

#### **Day 5: 其他介面和測試**
- [ ] 更新老師檢視介面
- [ ] 更新 API 型別定義
- [ ] 前端測試通過

### **Phase 3: 整合測試** ⏱️ 1 天

#### **Day 6: 完整驗證**
- [ ] 所有 TDD 合約測試通過
- [ ] E2E 測試完整流程
- [ ] 效能測試確認提升
- [ ] 手動測試驗證

## 🚨 **風險控制**

### **關鍵風險點**
1. **StudentActivityPage.tsx** - 最複雜的前端組件
2. **activities API** - 資料格式大幅改變
3. **資料一致性** - 新舊結構並存期間

### **風險緩解策略**
- [ ] 建立完整的測試覆蓋
- [ ] 保留原始 JSONB 欄位作為備份
- [ ] 分階段部署，可快速回滾
- [ ] 密切監控線上指標

## 📊 **成功指標**

### **技術指標**
- [ ] 所有測試通過 (100%)
- [ ] API 回應時間提升 > 50%
- [ ] 資料查詢效能提升 > 3x
- [ ] 零資料遺失

### **業務指標**
- [ ] 學生錄音上傳成功率 > 99%
- [ ] AI 評分正確對應率 100%
- [ ] 老師檢視功能正常
- [ ] 零陣列同步錯誤

## 🎯 **驗收標準**

### **功能驗收**
- [ ] 學生可以正常錄音、檢視進度
- [ ] 老師可以檢視每個學生每題的詳細進度
- [ ] AI 評分正確儲存和顯示
- [ ] 課程內容創建和編輯正常

### **效能驗收**
- [ ] 首頁載入時間 < 2 秒
- [ ] 錄音上傳回應 < 3 秒
- [ ] 進度查詢回應 < 1 秒

### **穩定性驗收**
- [ ] 24 小時穩定運行
- [ ] 並發 100 用戶正常使用
- [ ] 錯誤率 < 0.1%

## 🔧 **實作工具**

### **開發工具**
```bash
# 執行測試
npm run test:api:all
npm run test:e2e
npm run test:performance

# 檢查覆蓋率
npm run test:coverage

# 代碼品質檢查
npm run lint
npm run typecheck
```

### **監控工具**
- API 回應時間監控
- 資料庫查詢效能監控
- 錯誤率追蹤
- 用戶行為分析

## 📝 **完成檢查**

### **開發完成標準**
- [ ] 所有程式碼已撰寫
- [ ] 所有測試已通過
- [ ] 程式碼已 review
- [ ] 文件已更新

### **部署準備**
- [ ] 資料庫遷移腳本準備
- [ ] 環境變數確認
- [ ] 回滾計畫準備
- [ ] 監控告警設定

### **上線後確認**
- [ ] 功能正常運作
- [ ] 效能指標達標
- [ ] 無錯誤發生
- [ ] 用戶反饋正面

---

**這份檢查清單涵蓋了重構的所有面向，確保不遺漏任何重要項目。**
