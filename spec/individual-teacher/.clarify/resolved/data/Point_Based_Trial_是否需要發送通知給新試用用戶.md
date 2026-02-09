# 釐清問題

新用戶獲得 Point-Based Trial 方案後，是否需要發送特定通知或教程信息？

# 定位

**Feature:** Point-Based Trial 方案  
**規則：** Email/通知系統整合邏輯

相關規格位置：  
[FEATURE_SPEC_POINT_BASED_TRIAL.md](../../features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md#L90)（提問清單第4項）

# 多選題

| 選項  | 描述                                           |
| ----- | ---------------------------------------------- |
| A     | 發送 - 新增專門的 Email 通知 Point-Based Trial |
| B     | 復用 - 使用現有 30-Day Trial 的 Email 模板     |
| C     | 不發送 - 依賴 UI 提示或帮助文檔                |
| D     | 可選 - Admin 後台可配置是否發送                |
| Short | 無需額外通知                                   |

# 影響範圍

- **服務模塊：**
  - `backend/services/email_service.py`（需新增或修改 Email 模板邏輯）
  - 可能涉及 `backend/services/notification_service.py`（如存在）
- **資源文件：**
  - Email 模板文件
  - 翻譯/本地化文案
- **測試案例：**
  - Email 發送測試
  - 用戶工作流程集成測試

# 優先級

**Medium** - 此決策影響：

- 用戶啟蒙體驗（如何讓用戶了解新方案的差異）
- 郵件服務的修改範圍
- 後續維護的複雜度

# 備註

規格提及 "email 驗證後的自動開通邏輯" 需要修改，但未明確規定是否伴隨通知發送。若發送通知，Email 內容應清楚解釋 "永久試用但配額有限" 的概念。

---

# 解決記錄

- **回答**：Short - 無需額外通知
- **更新的規格檔**：spec/individual-teacher/features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md
- **變更內容**：
  - 明確新增：新試用用戶不發送額外通知，依 UI 提示/帮助文檔
  - 移除提問清單中的通知釐清項
