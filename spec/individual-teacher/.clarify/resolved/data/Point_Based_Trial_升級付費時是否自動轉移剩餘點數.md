# 釐清問題

升級付費時，現有 Point-Based Trial 方案的剩餘點數是否應自動轉移到付費方案？

# 定位

**Feature:** Point-Based Trial 方案  
**規則：** 用戶升級付費訂閱時的配額轉移邏輯

相關規格位置：  
[FEATURE_SPEC_POINT_BASED_TRIAL.md](../../features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md#L90)（提問清單第3項）

# 多選題

| 選項  | 描述                                  |
| ----- | ------------------------------------- |
| A     | 自動轉移 - 剩餘點數完全計入新訂閱     |
| B     | 部分轉移 - 按比例轉移（如50%轉移）    |
| C     | 不轉移 - 過期作廢，新訂閱重新計算     |
| D     | 依方案類型決定 - 升級到某些方案時轉移 |
| Short | 參考現有 30-Day Trial 邏輯            |

# 影響範圍

- **實體：** SubscriptionPeriod、SubscriptionUpgrade（如存在）
- **功能規則：**
  - 訂閱升級時的配額計算邏輯
  - UI 展示（升級前提示剩餘點數）
  - 交易記錄/審計日誌
- **測試案例：** 升級場景的集成測試

# 優先級

**High** - 此決策會影響：

- 用戶體驗（升級時會損失配額或保留）
- 商業邏輯（影響用戶升級意願）
- 代碼實現邏輯的複雜度

# 備註

提問清單提到「建議參考現有邏輯」，但規格中未明確說明現有 30-Day Trial 升級時的處理方式。應先確認現有行為，再決定新方案的處理方式。

---

# 解決記錄

- **回答**：A - 自動轉移（剩餘點數全額計入新訂閱）
- **更新的規格檔**：spec/individual-teacher/features/subscription/FEATURE_SPEC_POINT_BASED_TRIAL.md
- **變更內容**：
  - 明確新增：升級付費時自動轉移剩餘點數
  - 移除提問清單中的升級轉移釐清項
