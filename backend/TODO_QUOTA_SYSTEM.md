# 配額系統實作待辦事項 (Quota System TODO)

## 📊 當前狀態 (2025-11-04)

### ✅ 已完成 (Phase 1 - 核心架構)

#### 1. 資料模型設計
- [x] `SubscriptionPeriod` 資料表
  - 訂閱週期追蹤
  - quota_total, quota_used 欄位
  - payment_method, status 管理
- [x] `PointUsageLog` 資料表
  - 配額使用記錄
  - 支援多種單位 (秒/字/張)
  - feature_type 分類
- [x] Alembic migration (`20251104_1640_83420cb2e590`)

#### 2. QuotaService 核心邏輯
- [x] `convert_unit_to_seconds()` - 單位換算
  - 秒: 1:1
  - 字: 1 字 = 0.1 秒 (500 字 = 50 秒)
  - 張: 1 張 = 10 秒
  - 分鐘: 1 分鐘 = 60 秒
- [x] `check_quota()` - 配額檢查
- [x] `deduct_quota()` - 扣除配額
- [x] `get_quota_info()` - 取得配額資訊
- [x] 配額不足錯誤處理 (HTTP 402)

#### 3. 測試覆蓋
- [x] 11 個 QuotaService 單元測試 ✅
- [x] 17 個訂閱系統整合測試 ✅
  - 6 個 subscription_period 測試
  - 4 個 quota_integration 測試
  - 7 個 subscription_scenarios 測試

#### 4. 付款流程整合
- [x] 付款時創建 SubscriptionPeriod
- [x] 設定 quota_total (1800/4000 秒)
- [x] 標記舊週期為 expired
- [x] 自動續訂扣款創建新週期

---

## 🚧 待完成 (Phase 2 - 功能整合)

### ❌ 核心功能缺失 (高優先級)

#### 1. 錄音功能整合配額扣除
**檔案**: `routers/speech_assessment.py`

**需要修改的端點**:
```python
# 1. 錄音上傳 - 扣除錄音時長
@router.post("/api/speech/upload")
async def upload_recording(...):
    # ❌ 缺少：扣除配額
    # TODO: 
    # 1. 計算錄音時長 (秒)
    # 2. QuotaService.deduct_quota(teacher, duration, "秒", "speech_recording")
    # 3. 配額不足時返回 402 錯誤
    pass

# 2. AI 評分 - 扣除評分時長
@router.post("/api/speech/assess")
async def assess_pronunciation(...):
    # ❌ 缺少：扣除配額
    # TODO:
    # 1. 使用錄音時長
    # 2. QuotaService.deduct_quota(teacher, duration, "秒", "speech_assessment")
    pass
```

**測試需求**:
- [ ] 測試錄音扣配額
- [ ] 測試評分扣配額
- [ ] 測試配額不足時阻止錄音
- [ ] 測試配額記錄正確

#### 2. 文字批改功能配額扣除
**檔案**: `routers/text_correction.py` (如果存在)

**需要實作**:
```python
@router.post("/api/text/correct")
async def correct_text(...):
    # 計算字數
    word_count = len(text)
    
    # 扣除配額 (500 字 = 50 秒)
    QuotaService.deduct_quota(
        teacher=teacher,
        unit_count=word_count,
        unit_type="字",
        feature_type="text_correction"
    )
```

**測試需求**:
- [ ] 測試文字批改扣配額
- [ ] 測試 500 字 = 50 秒換算正確
- [ ] 測試配額不足阻止批改

#### 3. 前端配額顯示整合
**檔案**: 
- `frontend/src/pages/teacher/TeacherSubscription.tsx`
- `frontend/src/components/QuotaIndicator.tsx` (新建)

**需要實作**:
```typescript
// 1. 錄音前檢查配額
async function beforeRecording() {
  const quota = await checkQuota();
  if (quota.remaining < estimatedDuration) {
    showQuotaExceededModal();
    return false;
  }
  return true;
}

// 2. 即時顯示剩餘配額
<QuotaIndicator 
  total={1800}
  used={500}
  remaining={1300}
/>

// 3. 配額不足提示升級
<QuotaExceededModal 
  onUpgrade={() => navigate('/pricing')}
/>
```

**測試需求**:
- [ ] E2E 測試：錄音前檢查配額
- [ ] E2E 測試：配額不足顯示提示
- [ ] E2E 測試：配額即時更新

---

## 🔧 進階功能 (Phase 3 - 優化)

### 1. 方案變更機制
**狀態**: ❌ 已被移除 (commit `17938e7`)

**需要重新實作**:
```python
# routers/subscription.py

@router.post("/subscription/change-plan")
async def change_plan(
    new_plan: str,  # "Tutor Teachers" or "School Teachers"
    teacher: Teacher,
    db: Session
):
    """
    方案變更邏輯：
    
    情境 1: Tutor (1800) → School (4000) 升級
    - 已用 500 秒
    - 補差價: (660-330) * 剩餘天數/30
    - 新週期: quota_used = 500, quota_total = 4000
    
    情境 2: School (4000) → Tutor (1800) 降級
    - 已用 500 秒 → OK
    - 已用 2000 秒 → 拒絕 (超過新額度)
    """
    pass
```

**測試需求**:
- [ ] 測試升級方案
- [ ] 測試降級方案 (配額足夠)
- [ ] 測試降級方案 (配額不足，拒絕)
- [ ] 測試補差價計算正確

### 2. 配額加購機制
**需求**: 配額用完時可單獨購買額外配額

```python
@router.post("/subscription/buy-quota")
async def buy_quota(
    seconds: int,  # 購買秒數
    teacher: Teacher,
    db: Session
):
    """
    加購配額：
    - 價格: 0.18 元/秒 (330元/1800秒)
    - 最小購買: 300 秒 (54元)
    - 加到當前週期 quota_total
    """
    price = seconds * 0.18
    # TapPay 付款...
    # 增加 quota_total
    pass
```

### 3. 配額使用統計
**檔案**: `routers/analytics.py` (新建)

```python
@router.get("/analytics/quota-usage")
async def get_quota_usage(
    teacher: Teacher,
    start_date: datetime,
    end_date: datetime
):
    """
    配額使用統計：
    - 每日使用量
    - 功能分佈 (錄音 vs 評分 vs 文字)
    - 學生使用排行
    - 作業使用排行
    """
    usage_logs = db.query(PointUsageLog).filter(...)
    return {
        "daily_usage": [...],
        "feature_breakdown": {
            "speech_recording": 800,
            "speech_assessment": 600,
            "text_correction": 200
        },
        "top_students": [...]
    }
```

### 4. 效能優化

**問題**: `Teacher.current_period` 是 property，每次呼叫都 query

**優化方案**:
```python
# Option 1: 加 cache
from functools import lru_cache

@property
@lru_cache(maxsize=128)
def current_period(self):
    ...

# Option 2: Eager loading
teacher = db.query(Teacher).options(
    joinedload(Teacher.subscription_periods)
).filter_by(id=teacher_id).first()

# Option 3: 加 index
# CREATE INDEX idx_period_teacher_status 
# ON subscription_periods(teacher_id, status);
```

**測試需求**:
- [ ] 壓力測試: 1000 次 current_period 呼叫
- [ ] 測試 N+1 query 是否存在
- [ ] 測試 index 效果

### 5. 配額預警機制

```python
# services/quota_alert_service.py

def check_quota_alert(teacher: Teacher):
    """
    配額預警：
    - 剩餘 < 10% → 發 email 提醒
    - 剩餘 < 5% → 顯示 toast 通知
    - 剩餘 = 0 → 強制顯示升級頁面
    """
    quota_info = QuotaService.get_quota_info(teacher)
    remaining_percent = quota_info["quota_remaining"] / quota_info["quota_total"]
    
    if remaining_percent < 0.1:
        send_email_alert(teacher)
    if remaining_percent < 0.05:
        send_push_notification(teacher)
```

---

## 🧪 測試待補完

### E2E 測試
- [ ] 完整錄音 → 扣配額 → 檢查餘額流程
- [ ] 配額不足 → 阻止錄音 → 提示升級流程
- [ ] 付款 → 創建週期 → 配額重置流程
- [ ] 自動續訂 → 創建新週期 → 配額歸零流程

### Edge Case 測試
- [ ] 配額扣到負數處理
- [ ] 同時多個 active period 處理
- [ ] 10/31 訂閱只用 1 天
- [ ] 週期過期但仍有剩餘配額
- [ ] concurrent requests 扣配額 (race condition)

### 金流測試
- [ ] TapPay Sandbox 測試付款
- [ ] 自動續訂扣款測試
- [ ] 退款測試 (如需支援)
- [ ] 付款失敗處理

---

## 📋 資料一致性處理

### 問題: 兩套系統並存
```python
# Teacher model 有:
subscription_end_date  # 舊系統
subscription_type      # 舊系統

# SubscriptionPeriod 有:
end_date              # 新系統
plan_name             # 新系統
```

### 解決方案 (擇一)

**Option 1: 標記 deprecated**
```python
class Teacher:
    subscription_end_date = Column(...)  # Deprecated: 使用 current_period.end_date
    subscription_type = Column(...)       # Deprecated: 使用 current_period.plan_name
```

**Option 2: 使用 property 同步**
```python
@property
def subscription_end_date(self):
    """向後相容 - 從 current_period 讀取"""
    period = self.current_period
    return period.end_date if period else None

@subscription_end_date.setter
def subscription_end_date(self, value):
    """寫入時同步更新 current_period"""
    period = self.current_period
    if period:
        period.end_date = value
```

**Option 3: Migration 移除舊欄位**
```python
# alembic migration
def upgrade():
    op.drop_column('teachers', 'subscription_end_date')
    op.drop_column('teachers', 'subscription_type')
```

**建議**: Option 2 (向後相容，逐步遷移)

---

## 🚀 部署檢查清單

### 上線前必須完成
- [ ] 所有測試通過 (unit + integration + E2E)
- [ ] Migration 已測試 (staging)
- [ ] 向後相容確認 (不影響現有用戶)
- [ ] Feature Flag 設定 (`USE_QUOTA_SYSTEM = False`)
- [ ] 錯誤處理完整 (402, 404, 500)
- [ ] 前端錯誤訊息友善
- [ ] 監控告警設定 (配額異常扣除)

### 上線後監控
- [ ] 監控 PointUsageLog 寫入量
- [ ] 監控 402 錯誤比例
- [ ] 監控配額扣除準確性
- [ ] 監控 current_period query 效能
- [ ] 使用者反饋收集

---

## 💰 成本控制

### 資料庫成本
- PointUsageLog 會快速增長
- 建議：30 天後歸檔到 BigQuery
- 建議：保留 summary 在 PostgreSQL

### API 成本
- 每次錄音/評分都 query + insert
- 建議：batch insert PointUsageLog
- 建議：cache current_period (Redis)

---

## 📝 文件待補充

- [ ] API 文件：配額相關端點
- [ ] 使用者文件：如何查看配額
- [ ] 管理者文件：如何手動調整配額
- [ ] 故障排除文件：配額異常處理

---

## ⏰ 預估時程

### Phase 1 (已完成): 2 天
- ✅ 資料模型設計
- ✅ QuotaService 實作
- ✅ 單元測試

### Phase 2 (待完成): 3-5 天
- 錄音功能整合 (1 天)
- 前端整合 (2 天)
- E2E 測試 (1-2 天)

### Phase 3 (優化): 2-3 天
- 方案變更 (1 天)
- 效能優化 (1 天)
- 監控告警 (1 天)

**總計**: 7-10 天

---

**更新時間**: 2025-11-04 17:50
**下一步**: 決定是否現在整合到錄音功能，或是先 commit Phase 1
