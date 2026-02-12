# 功能規格：新增 Point-Based Trial 永久試用方案

**日期：2026年2月8日**  
**優先級：Medium**  
**預估工時：2-3小時**

---

## 📋 需求概述

### 目標

新增 **Point-Based Trial**（永久試用，僅限制配額）方案，並將其設為新註冊用戶的預設試用方案。

### 為什麼

- 目前 30-Day Trial 方案有時間限制，用戶在30天後無法使用
- 新方案允許用戶無時間限制地試用，只要配額未用完就能繼續使用
- 更符合用戶留存策略

### 範圍

- 新增方案定義
- 修改 email 驗證後的自動開通邏輯
- 更新測試數據
- **不修改資料表結構**

---

## 🎯 功能需求

### 1. 新方案定義

| 項目           | 30-Day Trial               | Point-Based Trial          |
| -------------- | -------------------------- | -------------------------- |
| **方案名稱**   | `"30-Day Trial"`           | `"Point-Based Trial"`      |
| **配額總量**   | 4,000 秒                   | 4,000 秒                   |
| **試用天數**   | 30 天                      | 永久（無限期）             |
| **配額用完後** | 可能過期或無法使用         | 無法使用，需充值           |
| **支付方式**   | `payment_method = "trial"` | `payment_method = "trial"` |

### 2. 新註冊用戶流程

```
用戶註冊 → Email 驗證成功 → 自動開通試用
         (現有流程)          (修改此步驟)
```

**修改內容：**

- 修改前：開通 "30-Day Trial"（30天，10000秒）
- 修改後：開通 "Point-Based Trial"（永久，4000秒）

**時間設定：**

- `start_date = now`
- `end_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)`

---

## 💻 實作細節

### 修改檔案 1：`backend/routers/admin_subscriptions.py`

**位置：** `get_plan_quota()` 函數

**修改內容：**
在 `plan_quotas` 字典中新增一行：

```python
# 修改前
plan_quotas = {
    "30-Day Trial": 4000,
    "Tutor Teachers": 10000,
    "School Teachers": 25000,
    "Demo Unlimited Plan": 999999,
    "VIP": 0,
}

# 修改後
plan_quotas = {
    "30-Day Trial": 4000,
    "Point-Based Trial": 4000,  # ✨ 新增
    "Tutor Teachers": 10000,
    "School Teachers": 25000,
    "Demo Unlimited Plan": 999999,
    "VIP": 0,
}
```

**說明：**

- 在 Admin 後台創建訂閱時，"Point-Based Trial" 方案會使用 4000 秒作為預設配額
- Admin 仍可手動覆蓋這個值

---

### 修改檔案 2：`backend/services/email_service.py`

**位置：** `verify_teacher_email_token()` 方法中的 `SubscriptionPeriod` 創建邏輯

**修改內容：**

```python
# 修改前（約第 445-456 行）
new_period = SubscriptionPeriod(
    teacher_id=teacher.id,
    plan_name="30-Day Trial",          # ← 修改此行
    amount_paid=0,
    quota_total=10000,                 # ← 修改此行
    quota_used=0,
    start_date=now,
    end_date=now + timedelta(days=30), # ← 修改此行
    payment_method="trial",
    payment_status="completed",
    status="active",
)

# 修改後
new_period = SubscriptionPeriod(
    teacher_id=teacher.id,
    plan_name="Point-Based Trial",     # ✨ 新方案名稱
    amount_paid=0,
    quota_total=4000,                  # ✨ 減少配額
    quota_used=0,
    start_date=now,
    end_date=datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc),  # ✨ 永久有效
    payment_method="trial",
    payment_status="completed",
    status="active",
)
```

**需要新增的 import：**

```python
from datetime import datetime, timezone  # 確保已導入
```

**說明：**

- 新用戶 email 驗證後會自動獲得 "Point-Based Trial" 方案
- 配額為 4,000 秒（約 66 分鐘）
- 到期日設為 2099-12-31，實質上等於永久有效

---

### 修改檔案 3：`backend/seed_data/stage_01_users.py`

**位置：** Trial 老師的訂閱週期創建部分（約第 78-93 行）

**修改內容：**

```python
# 修改前
trial_period = SubscriptionPeriod(
    teacher_id=trial_teacher.id,
    plan_name="30-Day Trial",
    amount_paid=0,
    quota_total=18000,  # 30天 * 10分鐘/天 * 60秒 = 18000秒
    quota_used=0,
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=30),
    payment_method="trial",
    payment_status="completed",
    status="active",
)

# 修改後
trial_period = SubscriptionPeriod(
    teacher_id=trial_teacher.id,
    plan_name="Point-Based Trial",  # ✨ 新方案名稱
    amount_paid=0,
    quota_total=4000,               # ✨ 減少配額
    quota_used=0,
    start_date=datetime.now(),
    end_date=datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc),  # ✨ 永久有效
    payment_method="trial",
    payment_status="completed",
    status="active",
)
```

**說明：**

- 更新測試帳號的試用方案為新方案
- 確保測試環境與實際環境一致

---

## 🧪 測試方案

### 單元測試

```python
# 驗證：Point-Based Trial 方案配額正確
def test_point_based_trial_quota():
    from admin_subscriptions import get_plan_quota
    assert get_plan_quota("Point-Based Trial") == 4000
```

### 集成測試

1. **新用戶註冊流程**
   - 新註冊一個用戶
   - 完成 email 驗證
   - 驗證自動創建的訂閱期：
     - ✅ `plan_name == "Point-Based Trial"`
     - ✅ `quota_total == 4000`
     - ✅ `end_date == datetime(2099, 12, 31, ...)`
     - ✅ `status == "active"`

2. **配額限制測試**
   - 使用試用用戶創建內容消耗配額
   - 驗證配額扣除邏輯正常
   - 當 `quota_used >= quota_total` 時無法繼續使用
   - 顯示需要升級提示

3. **現有用戶不受影響**
   - 確認已有的 30-Day Trial 訂閱繼續運作
   - 確認已有的付費訂閱繼續運作

4. **Admin 後台操作**
   - Admin 仍可手動創建 "30-Day Trial" 方案
   - Admin 仍可手動創建 "Point-Based Trial" 方案
   - 配額值可正確覆蓋

---

## ✅ 驗收標準

- [x] 新用戶註冊後自動獲得 "Point-Based Trial" 方案
- [x] 配額為 4,000 秒
- [x] 無時間限制（end_date = 2099-12-31）
- [x] 現有 30-Day Trial 訂閱保持不變
- [x] Admin 可繼續手動創建任何方案
- [x] UI 正常顯示配額和到期日
- [x] 所有相關測試通過
- [x] 種子數據更新完畢

---

## 📊 影響範圍

### 受影響的模塊

- ✅ 訂閱系統（新增方案定義）
- ✅ Email 驗證流程（修改試用方案）
- ✅ 測試數據（更新 trial_teacher）

### 不受影響

- ❌ 資料表結構（無需 migration）
- ❌ 現有訂閱記錄
- ❌ Admin 後台核心邏輯
- ❌ 配額檢查邏輯

---

## ⚠️ 風險評估

### 低風險

- 修改位置明確、局限
- 無需資料庫 migration
- 新舊邏輯完全相容
- 現有用戶不受影響

### 注意事項

- 確保 datetime 導入正確
- 驗證 timezone 設定無誤（UTC）
- 測試 seed_data 重新運行

---

## 📝 實作 Checklist

- [ ] 修改 `admin_subscriptions.py` 中的 `get_plan_quota()`
- [ ] 修改 `email_service.py` 中的 `verify_teacher_email_token()`
- [ ] 修改 `seed_data/stage_01_users.py` 中的 trial_teacher 訂閱
- [ ] 確認所有 import 正確
- [ ] 本地測試新用戶註冊流程
- [ ] 運行 seed_data 更新測試環境
- [ ] 執行相關單元測試
- [ ] 執行集成測試
- [ ] 部署到 staging 環境
- [ ] Owner 驗收測試

---

## 📞 提問清單

若工程師有疑問，可提出以下問題供 Owner 確認：

1. 現有的 "30-Day Trial" 訂閱是否完全保留？
2. 是否需要在 UI 上區分兩種試用方案？
3. 升級付費時，是否自動轉移剩餘點數？（建議參考現有邏輯）
4. 是否需要發送通知給新試用用戶？

---

## 版本歷史

| 版本 | 日期       | 修改內容            |
| ---- | ---------- | ------------------- |
| v1.0 | 2026-02-08 | 初版 - 需求規格文件 |
