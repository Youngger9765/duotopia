# Migration 簡化說明

## 變更內容

將 3 個配額系統 migrations 合併為 1 個：

### 舊的 Migrations（已刪除）
1. `20251104_1640_83420cb2e590_add_subscription_periods_and_point_.py` - 創建資料表
2. `20251105_0608_f42b27a78bec_sync_quota_models_with_codebase_changes.py` - 調整索引
3. `20251105_0620_add_performance_indexes.py` - 新增性能索引

### 新的 Migration
- `20251104_1640_add_quota_system.py` - 合併的配額系統 migration

## Staging 環境部署步驟

由於 migration 已經簡化，staging 環境需要重置資料庫：

### 方法 1：手動重置（推薦）

```bash
# 1. 連接到 Staging Cloud SQL
gcloud sql connect duotopia-staging-0827 --user=postgres

# 2. 刪除 alembic_version 表中的舊記錄
DELETE FROM alembic_version WHERE version_num IN ('83420cb2e590', 'f42b27a78bec', '20251105_0620');

# 3. 刪除配額系統相關資料表（如果存在）
DROP TABLE IF EXISTS point_usage_logs CASCADE;
DROP TABLE IF EXISTS subscription_periods CASCADE;

# 4. 退出 psql
\q
```

### 方法 2：完整重建（如果可以接受資料遺失）

```bash
# 在 Cloud Run 部署時會自動執行 Base.metadata.create_all()
# 然後執行 seed_data.py 重新載入測試資料
```

### 方法 3：使用 Alembic Downgrade/Upgrade

```bash
# 在 backend 目錄
alembic downgrade b6fb1f60db50  # 降級到配額系統之前
alembic upgrade head             # 執行新的合併 migration
```

## 驗證

部署後驗證配額系統功能：

```bash
# 1. 檢查資料表是否正確創建
psql> \dt subscription_periods
psql> \dt point_usage_logs

# 2. 檢查索引
psql> \di ix_subscription_periods_*
psql> \di ix_point_usage_logs_*

# 3. 執行測試
npm run test:api:all
```

## 注意事項

- ⚠️ 這個變更會**遺失**現有的配額使用記錄（如果有）
- ✅ 測試資料會通過 `seed_data.py` 重新創建
- ✅ 不影響其他功能（訂閱、作業等）

## 為什麼要簡化？

1. **減少 migration 數量**：3個 → 1個
2. **避免 main 分支有太多 migrations**
3. **更清晰的版本歷史**
4. **easier to review and understand**
