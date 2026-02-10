# Issue #241: 教師邀請流程改善與 1Campus SSO 整合

> **Issue**: https://github.com/Youngger9765/duotopia/issues/241
> **狀態**: 規劃中
> **優先級**: 高（影響機構邀請功能可用性）

## 📋 問題描述

### 當前問題

機構管理員邀請未註冊教師時，系統會創建帳號並生成隨機密碼，但**沒有發送邀請郵件**，導致被邀請的教師：
- ❌ 不知道自己被邀請
- ❌ 無法獲得登入憑證（密碼）
- ❌ 無法登入並使用平台

**根本原因**: [backend/routers/organizations.py:906](../../backend/routers/organizations.py#L906) 的 TODO 註釋顯示邀請郵件功能尚未實現。

### 未來需求

教育部要求整合 **1Campus SSO** 認證系統，需要支援：
- 教育雲帳號登入（SSO）
- 本地帳號（email + password）
- 混合認證（帳號綁定）

---

## 🎯 解決方案

### 整體策略：分階段實施

考慮到未來 SSO 整合需求，採用**混合認證架構**，分 4 個階段實施：

1. **Phase 1**: 立即修復（1 週內）- 解決當前無法邀請問題
2. **Phase 2**: SSO 整合準備（2-4 週）- 支援雙認證系統
3. **Phase 3**: 完整 SSO 功能（1-2 個月）- SSO 登入與綁定
4. **Phase 4**: 優化與管理（持續）- 管理功能與優化

---

## 📂 文檔結構

```
spec/issue-241-teacher-invitation-sso/
├── README.md                           # 本文件（概覽）
├── 01-CURRENT_FLOW_ANALYSIS.md         # 現狀流程分析
├── 02-PHASE1_IMMEDIATE_FIX.md          # Phase 1: 立即修復方案
├── 03-PHASE2_SSO_PREPARATION.md        # Phase 2: SSO 準備
├── 04-PHASE3_SSO_INTEGRATION.md        # Phase 3: SSO 整合
├── 05-PHASE4_OPTIMIZATION.md           # Phase 4: 優化管理
├── 06-DATA_MODEL_CHANGES.md            # 資料模型變更
├── 07-API_SPECIFICATIONS.md            # API 規格
└── 08-1CAMPUS_SSO_REFERENCE.md         # 1Campus SSO 參考文檔
```

---

## 🚀 快速開始

### 最小可行方案（MVP）

如果需要快速解決當前問題，請參考：
- **短期方案**: [02-PHASE1_IMMEDIATE_FIX.md](./02-PHASE1_IMMEDIATE_FIX.md) → **方案 B**（顯示臨時密碼）
- **中期方案**: [02-PHASE1_IMMEDIATE_FIX.md](./02-PHASE1_IMMEDIATE_FIX.md) → **方案 A**（郵件邀請）

### 完整實施路徑

如果要考慮未來 SSO 整合，請按順序閱讀：
1. [01-CURRENT_FLOW_ANALYSIS.md](./01-CURRENT_FLOW_ANALYSIS.md) - 了解現狀
2. [06-DATA_MODEL_CHANGES.md](./06-DATA_MODEL_CHANGES.md) - 資料模型調整
3. [02-PHASE1_IMMEDIATE_FIX.md](./02-PHASE1_IMMEDIATE_FIX.md) - 開始實施

---

## 📊 決策矩陣

### 邀請情境與處理方式

| 被邀請教師狀態 | 機構管理員知道 | Phase 1 處理 | Phase 2+ 處理 |
|--------------|-------------|------------|-------------|
| ✅ 有 1Campus 帳號 | 知道 teacherID | Email 邀請 | 推播通知 + 自動綁定 |
| ✅ 有 1Campus 帳號 | 只知道 email | Email 邀請 | Email 邀請 → SSO 綁定 |
| ❌ 無 1Campus 帳號 | - | Email 邀請 | Email 邀請 → 本地帳號 |
| ❓ 不確定 | - | Email 邀請 | 混合策略（Email + 推播） |

---

## 🔧 技術架構

### 資料模型擴充

```python
class Teacher(Base):
    # 現有欄位
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # ← 改為 nullable

    # 新增 SSO 欄位
    sso_provider = Column(String(50), nullable=True)      # '1campus', 'google', None
    sso_account = Column(String(255), nullable=True)      # SSO 帳號
    sso_teacher_id = Column(String(100), nullable=True)   # 1Campus teacherID
    auth_method = Column(String(20), default='local')     # 'local', 'sso', 'hybrid'
```

### 認證流程

```
┌─────────────────────┐
│   教師登入請求      │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ 檢查認證方式 │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌──────────┐
│ 本地密碼 │ │ SSO 認證 │
└────┬────┘ └────┬─────┘
     │           │
     └─────┬─────┘
           │
           ▼
    ┌──────────────┐
    │  發放 Token  │
    └──────────────┘
```

---

## 📈 實施時程

| 階段 | 時程 | 主要交付 | 依賴 |
|-----|------|---------|------|
| **Phase 1** | 1 週 | 郵件邀請 + 資料模型調整 | 無 |
| **Phase 2** | 2-4 週 | 混合邀請表單 + 推播整合 | Phase 1 |
| **Phase 3** | 1-2 個月 | SSO 登入 + 帳號綁定 | Phase 1, 2 + 1Campus 授權 |
| **Phase 4** | 持續 | 管理介面 + 優化 | Phase 3 |

---

## 🔗 相關資源

### 外部文檔
- [1Campus 系統整合 API](https://devapi.1campus.net/doc/jasmine)
- [1Campus 訊息推播 API](https://devapi.1campus.net/doc/dandelion)

### 內部文檔
- [PRD.md](../../PRD.md) - 產品需求文檔
- [ORG_IMPLEMENTATION_SPEC.md](../../ORG_IMPLEMENTATION_SPEC.md) - 組織層級規格
- [backend/routers/organizations.py](../../backend/routers/organizations.py#L717-L915) - 邀請端點實現
- [backend/services/email_service.py](../../backend/services/email_service.py) - 郵件服務

### 相關測試
- [backend/tests/test_organization_teachers.py](../../backend/tests/test_organization_teachers.py)
- [backend/tests/integration/api/test_organization_spec_decisions.py](../../backend/tests/integration/api/test_organization_spec_decisions.py)

---

## 👥 利害關係人

| 角色 | 關注點 | 優先級 |
|-----|--------|--------|
| **機構管理員** | 能順利邀請教師 | P0 |
| **被邀請教師** | 能收到通知並登入 | P0 |
| **教育部 SSO 用戶** | SSO 登入體驗 | P1 |
| **開發團隊** | 架構可擴展性 | P1 |
| **營運團隊** | 管理與追蹤邀請狀態 | P2 |

---

## ⚠️ 風險與假設

### 風險
1. **郵件發送失敗** - 需要重試機制和狀態追蹤
2. **SSO 帳號綁定衝突** - 需要明確的綁定規則
3. **TOCTOU 競態條件** - 已在現有代碼中處理（SELECT FOR UPDATE）
4. **1Campus API 變更** - 需要版本管理和降級策略

### 假設
1. 1Campus SSO 整合時程由教育部決定（預估 3-6 個月內）
2. 所有教師都有可用的 email 地址
3. SMTP 服務穩定可用
4. 1Campus 推播服務僅作為補充，不能完全取代 email

---

## 📝 變更記錄

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|---------|------|
| 2026-02-10 | 1.0 | 初始版本：問題分析與解決方案規劃 | Claude |

---

## 🎯 成功指標

### Phase 1 成功指標
- [ ] 100% 被邀請教師收到邀請通知（email 或臨時密碼）
- [ ] 邀請後 24 小時內登入率 > 60%
- [ ] 郵件發送成功率 > 95%

### Phase 3 成功指標
- [ ] SSO 登入成功率 > 98%
- [ ] 帳號綁定成功率 > 95%
- [ ] 雙認證系統並存無衝突

### 整體成功指標
- [ ] 邀請流程完成率（從邀請到首次登入）> 80%
- [ ] 教師滿意度（NPS）> 8/10
- [ ] 零安全漏洞

---

## 📞 聯絡資訊

如有疑問，請參考：
- **技術問題**: 見各階段文檔中的 FAQ 章節
- **產品決策**: 參考 [決策記錄](./02-PHASE1_IMMEDIATE_FIX.md#決策記錄)
- **進度追蹤**: GitHub Issue #241
