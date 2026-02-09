# 釐清問題

當 Point-Based Trial 用戶配額用完後，系統應如何提示用戶？是否需要自動發送升級提醒郵件？

# 定位

**Entity:** SubscriptionPeriod  
**Attribute：** quota_used、quota_total（當 quota_used >= quota_total 時的行為）  
**Related Rules：** 配額檢查邏輯

相關規格位置：  
[FEATURE_SPEC_POINT_BASED_TRIAL.md](../../features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md#L113-L125)（集成測試「配額限制測試」段落）

# 多選題

| 選項 | 描述                                           |
| ---- | ---------------------------------------------- |
| A    | 即時提示 - 操作時直接显示 "配額已用完，請升級" |
| B    | 限額警告 - 配額剩餘 10% 時先發送提醒           |
| C    | 郵件通知 - 配額用完時自動發送升級提醒郵件      |
| D    | A+C 組合 - 既有即時提示，也發送郵件通知        |
| E    | 無額外提示 - 保持現有邏輯，用戶自主檢查        |

# 影響範圍

- **後端模塊：**
  - `backend/services/quota_service.py`（如存在）或相關配額檢查邏輯
  - `backend/services/email_service.py`（如需發送提醒郵件）
  - `backend/routers/*.py`（API 回應邏輯，需返回配額狀態）
- **前端模塊：**
  - UI 警告/提示組件
  - Dashboard 配額顯示
- **測試案例：**
  - 配額臨界值測試（剩餘 10%、0%）
  - Email 觸發邏輯測試

# 優先級

**High** - 此決策影響：

- 用戶體驗（用戶能否及時察覺配額不足）
- 商業轉化率（提醒力度直接影響升級意願）
- 後端邏輯複雜度（可能需新增配額監控機制）
- 資料表設計（可能需新增 "quota_warning_sent" 之類的欄位以避免重複發送）

# 備註

規格中提到 "當 quota_used >= quota_total 時無法繼續使用" 和 "顯示需要升級提示"，但未具體說明：

1. 誰負責顯示提示（前端、API 回應、還是後台自動郵件）
2. 提示時機（配額用完時立即提示，還是事先預警）
3. 提示頻率（一次還是重複）

# 相關問題

此問題與以下釐清項目相關聯：

- `Point_Based_Trial_是否需要發送通知給新試用用戶.md` - 通知系統整合

---

# 解決記錄

- **回答**：A - 即時提示 - 操作時直接在介面顯示「配額已用完，請升級」
- **更新的規格檔**：spec/individual-teacher/features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md
- **變更內容**：
  - 新增修改檔案 5：配額檢查邏輯，定義 `check_quota_available()` 函數
  - 定義 API 回應格式：HTTP 403 + QUOTA_EXCEEDED 錯誤訊息
  - 更新集成測試「配額限制測試」：明確驗證即時提示的顯示邏輯
  - API 回應包含 upgrade_url，引導用戶升級
  - 前端需顯示「配額已用完，請升級付費方案」提示，並包含升級按鈕
