# Duotopia Backend 部署說明

## 🚀 目前部署策略（短期）

### Staging 環境
- **策略**: 每次部署都重建資料庫（rebuild）
- **原因**: 還沒有 production，可以自由重建
- **時機**: 等 production 上線後再改用 migration

### 部署流程

#### 1. 自動部署（推薦）
```bash
# 推送到 staging branch，GitHub Actions 會自動部署
git push origin staging
```

#### 2. 更新測試資料
```bash
# 1. 修改 seed_data.py
# 2. 提交並推送
git add backend/seed_data.py
git commit -m "更新測試資料"
git push origin staging

# 3. 部署完成後，資料庫會自動重建並載入新的測試資料
```

### 目前的資料初始化流程

1. **Cloud Run 啟動時**（在 main.py）：
   - 執行 `Base.metadata.create_all()` 建立所有資料表
   - 自動執行 seed_data.py（如果是 staging 環境）

2. **測試帳號**：
   - 教師：demo@duotopia.com / demo123
   - 學生：選擇學生後，密碼為生日（例：20120101）
   - 特殊：林靜香已更改密碼為 mynewpassword123

### 本地開發

```bash
# 1. 啟動資料庫
docker-compose up -d

# 2. 重置並初始化資料
cd backend
python seed_data.py

# 3. 啟動後端
uvicorn main:app --reload --port 8000
```

## 🔄 未來計畫（Production 上線後）

### 將改用 Alembic Migration
- **已準備**: Alembic 已設置完成
- **migration 檔案**: 在 `alembic/versions/` 資料夾
- **執行方式**:
  ```bash
  # 建立新的 migration
  alembic revision --autogenerate -m "描述"

  # 執行 migration
  alembic upgrade head

  # 回滾
  alembic downgrade -1
  ```

### Production 部署原則
1. 不能隨意重建資料庫
2. 所有 schema 變更都要透過 migration
3. 部署前先備份
4. 有 rollback 機制

## 📝 注意事項

1. **不要在 production 執行 seed_data.py**
2. **schema 變更記得同步更新 models.py**
3. **重要資料變更前先在 staging 測試**

## 🆘 常見問題

### Q: 如何在 staging 重置資料？
A: 推送任何改動到 staging branch，資料庫會自動重建

### Q: 如何新增測試使用者？
A: 修改 seed_data.py 然後推送到 staging

### Q: 本地資料庫連不上？
A: 確認 docker-compose 有啟動：`docker-compose up -d`

---
*最後更新：2024-08-27*
