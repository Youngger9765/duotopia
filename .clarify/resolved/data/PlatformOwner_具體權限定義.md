# 釐清問題

專案擁有人的具體權限有哪些？

# 定位

角色定義：專案擁有人（Platform Owner）的權限欄位。

# 多選題

| 選項  | 描述                                                                               |
| ----- | ---------------------------------------------------------------------------------- |
| Short | 列舉具體權限項目（如：manage_all_orgs, view_platform_analytics, system_config...） |

Format: Short answer (comma-separated permission list)

# 影響範圍

- Platform Owner 角色的功能範圍
- 與專案助理的權限差異定義
- 系統管理功能的設計
- 平台級 API 的權限驗證
- 機構管理功能的權限設計

# 優先級

High

---

# 解決記錄

- **回答**：根據現有專案實作，Platform Owner (is_admin=true) 具有以下權限：

**機構管理**：
- manage_organizations（創建/編輯/刪除/關閉/開啟機構）
- view_all_organizations（查看所有機構資訊）

**用戶管理**：
- view_all_teachers（查看所有教師帳號）
- view_all_students（查看所有學生帳號）
- manage_user_accounts（管理用戶帳號狀態）

**訂閱與財務管理**：
- view_all_subscriptions（查看所有訂閱記錄）
- manage_subscriptions（創建/編輯/取消訂閱）
- process_refunds（處理退款）
- view_transaction_analytics（查看交易分析）
- view_billing_summary（查看帳單摘要）
- view_billing_anomalies（查看帳單異常）

**平台數據分析**：
- view_platform_analytics（平台級數據分析）
- view_learning_analytics（學習數據分析）
- view_subscription_stats（訂閱統計）
- view_extension_history（延展歷史記錄）

**系統配置與維護**：
- database_operations（資料庫重建/seed）
- view_database_stats（資料庫統計）
- system_monitoring（系統監控：音頻上傳/AI分析狀態）
- view_error_logs（查看錯誤日誌）
- retry_statistics（重試統計）
- health_check（系統健康檢查）

**開發與測試**：
- test_audio_upload（測試音頻上傳）
- test_ai_analysis（測試AI分析）

- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：在「系統管理類 > 專案擁有人」章節補充具體權限列表
- **參考來源**：
  - backend/routers/admin.py（資料庫、訂閱管理）
  - backend/routers/admin_subscriptions.py（訂閱操作、分析）
  - backend/routers/admin_billing.py（帳單相關）
  - backend/routers/admin_monitoring.py（系統監控）
  - backend/routers/admin_audio_errors.py（錯誤追蹤）
  - backend/routers/organizations.py（機構 CRUD）
