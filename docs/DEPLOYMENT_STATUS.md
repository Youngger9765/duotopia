# 部署狀態

最後更新：2025-12-10

## 🎯 Production 環境（主力）
- **部署平台**: Cloud Run (asia-east1)
- **環境狀態**: ✅ 運行中
- **域名**: https://duotopia.co
- **資料庫**: Supabase (免費層)
- **每日成本**: ~$0.30 (Cloud Run Scale-to-Zero)
- **月成本估算**: ~$5-10 (取決於流量)

### Production 服務 URL
- **前端**: https://duotopia.co (mapped to Cloud Run)
- **後端 API**: https://duotopia.co/api
- **API 文件**: https://duotopia.co/api/docs
- **健康檢查**: https://duotopia.co/api/health

### Production Cloud Run 內部 URL
- **Frontend**: https://duotopia-production-frontend-b2ovkkgl6a-de.a.run.app
- **Backend**: https://duotopia-production-backend-b2ovkkgl6a-de.a.run.app

### 最新部署
- **Backend Revision**: duotopia-production-backend-00138-trs
- **Frontend Revision**: duotopia-production-frontend-00121-xxx
- **部署時間**: 2025-12-10 12:41 UTC
- **Git Commit**: 96815ba - Migrate production deployment from VM to Cloud Run

## 🧪 Staging 環境
- **部署平台**: Cloud Run (asia-east1)
- **環境狀態**: ✅ 運行中
- **資料庫**: Supabase (免費層)
- **每日成本**: $0.00 (Scale-to-Zero)

### Staging 服務 URL
- **前端**: https://duotopia-staging-frontend-316409492201.asia-east1.run.app
- **後端**: https://duotopia-staging-backend-316409492201.asia-east1.run.app
- **API 文件**: https://duotopia-staging-backend-316409492201.asia-east1.run.app/docs

## 📊 測試帳號
- **教師**: demo@duotopia.com / demo123
- **學生**: 選擇教師後，使用預設密碼 20120101

## 💾 資料庫狀態
### Production Database
- **Supabase Project**: szjeagbrubcibunofzud
- **狀態**: ✅ 運行中
- **表格**: 18 個表格（含 RLS 保護）
- **成本**: $0/月（免費層）

### Staging Database
- **Supabase Project**: staging-xxx
- **狀態**: ✅ 運行中
- **表格**: 18 個表格（含 RLS 保護）
- **成本**: $0/月（免費層）

## 🔒 安全性
- **SSL/TLS**: ✅ Cloud Run 自動管理證書
- **JWT Secret**: ✅ 已更新為強密鑰
- **環境變數**: ✅ 使用 GitHub Secrets
- **資料庫連線**: ✅ 使用加密連線
- **Row Level Security**: ✅ 所有業務表已啟用 RLS

## ⚠️ VM 部署狀態（已廢棄）
- **VM 名稱**: duotopia-prod-vm
- **Static IP**: 34.81.38.211
- **狀態**: ⏸️ 保留運行（作為緊急回滾選項）
- **自動部署**: ❌ 已停用
- **計劃**: 📅 2 週後關閉

## 🔄 遷移狀態
- ✅ Production 已遷移至 Cloud Run
- ✅ 域名 duotopia.co 已映射到 Cloud Run
- ✅ SSL 證書自動管理
- ✅ GitHub Workflows 已更新
- ⏸️ VM 暫時保留（緊急回滾使用）
- 📅 預計 2025-12-24 關閉 VM

## 💰 成本對比（月估算）
| 環境 | 舊方案 (VM) | 新方案 (Cloud Run) | 節省 |
|------|------------|-------------------|------|
| Production | $13/月 | $5-10/月 | ~$5/月 |
| Staging | N/A | $0/月 | $0/月 |
| **總計** | **$13/月** | **$5-10/月** | **~38-62% 節省** |
