# 釐清問題

UI 上是否需要明確區分 "30-Day Trial" 和 "Point-Based Trial" 兩種試用方案？

# 定位

**Feature:** Point-Based Trial 方案  
**規則：** 用戶端 UI 展示邏輯

相關規格位置：  
[FEATURE_SPEC_POINT_BASED_TRIAL.md](../../features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md#L90)（提問清單第2項）

# 多選題

| 選項  | 描述                                         |
| ----- | -------------------------------------------- |
| A     | 分別展示 - 在訂閱頁面顯示方案名稱與差異      |
| B     | 統一展示 - 都歸為「試用方案」，隱藏方案名稱  |
| C     | 動態展示 - 新用戶只看到 Point-Based Trial    |
| D     | 詳情展示 - 在設置/帳戶信息中顯示完整方案訊息 |
| Short | 參考 UI 設計稿                               |

# 影響範圍

- **UI 模塊：**
  - 訂閱詳情頁面
  - 方案升級流程
  - 帳戶設置頁面
  - Dashboard（如顯示配額概覽）
- **Frontend 檔案：**
  - 訂閱相關 React 組件
  - 文案/標籤定義
- **測試案例：** UI 測試、用戶體驗測試

# 優先級

**Medium** - 此決策影響：

- 用戶体驗清晰度（用戶是否能理解自己的方案類型）
- Frontend 實作複雜度
- 但不影響後端邏輯或資料結構

# 備註

規格中提及 "現有 30-Day Trial 訂閱保持不變"，但未說明系統中是否會同時存在兩種方案的用戶，以及 UI 如何呈現這種混合狀況。

---

# 解決記錄

- **回答**：C - 兩者都要區分（個人教師 UI 與 Admin 後台皆顯示方案名稱）
- **更新的規格檔**：spec/individual-teacher/features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md
- **變更內容**：
  - 明確新增：個人教師訂閱頁與 Admin 後台皆需顯示方案名稱與差異
  - 移除提問清單中的 UI 區分釐清項
