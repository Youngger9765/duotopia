## 🎯 Purpose

<!-- 簡短描述這個 PR 的目的（一句話） -->

Related to #ISSUE_NUMBER

---

## 🔍 Problem Analysis（問題分析）

### Root Cause（根本原因）
<!-- 5 Why 分析 -->
1. **為什麼會發生？** →
2. **為什麼會這樣？** →
3. **為什麼？** →
4. **根本原因？** →
5. **為什麼系統允許？** → **根本原因：**

### Code Location（問題位置）
- **檔案**: `path/to/file.ts:LINE`
- **問題**: [說明邏輯錯誤]

---

## ✅ Solution（解決方案）

### Changes Made（修改內容）
- [ ] 修改 1：[說明]
- [ ] 修改 2：[說明]
- [ ] 修改 3：[說明]

### Technical Decisions（技術決策）
<!-- 為什麼這樣實作？有沒有考慮其他方案？ -->

---

## 🧪 Testing（測試）

### Test Coverage（測試覆蓋）
- [ ] **Unit Tests**: `tests/unit/test_xxx.py` - [測試內容]
- [ ] **Integration Tests**: `tests/integration/test_xxx.py` - [測試內容]
- [ ] **E2E Tests**: `tests/e2e/test_xxx.spec.ts` - [測試內容]

### Test Results（測試結果）
```bash
# Paste test output here
pytest tests/... -v
npm run test
```

### Manual Testing（手動測試）
- [ ] 在本地環境測試通過
- [ ] 在 Per-Issue Test Environment 測試通過
- [ ] 無 Console 錯誤
- [ ] TypeScript 編譯通過
- [ ] ESLint 檢查通過

---

## 🛡️ Prevention（預防措施）

### Preventive Tests Added（新增預防性測試）
- [ ] 邊界條件測試
- [ ] 錯誤處理測試
- [ ] Regression 測試

### Documentation Updated（文件更新）
- [ ] 程式碼註解已更新
- [ ] API 文件已更新（如適用）
- [ ] README 已更新（如適用）

---

## 📊 Impact Analysis（影響範圍）

### Affected Components（受影響元件）
- [ ] Frontend: [元件名稱]
- [ ] Backend: [API 端點]
- [ ] Database: [是否涉及 schema 變更]

### Risk Assessment（風險評估）
- **嚴重程度**: 🟢 Low / 🟡 Medium / 🔴 High
- **影響用戶**: [說明]
- **資料風險**: 是/否
- **效能影響**: 是/否

### Rollback Plan（回滾計畫）
<!-- 如果部署後發現問題，如何回滾？ -->

---

## 📸 Screenshots（截圖）

### Before（修復前）
<!-- 如果是 UI 變更，提供修復前的截圖 -->

### After（修復後）
<!-- 如果是 UI 變更，提供修復後的截圖 -->

---

## ✅ Pre-Merge Checklist（合併前檢查）

### Code Quality（程式碼品質）
- [ ] 所有測試通過（Unit + Integration + E2E）
- [ ] TypeScript 編譯無錯誤
- [ ] ESLint 檢查通過
- [ ] No console.log 或 debug code
- [ ] 程式碼已 review 過

### CI/CD Status（自動化檢查）
- [ ] GitHub Actions 測試全部通過
- [ ] Build 成功
- [ ] No security vulnerabilities

### Documentation（文件）
- [ ] 程式碼註解清晰
- [ ] 複雜邏輯有說明
- [ ] TODO 已清理

### Issue Tracking（Issue 追蹤）
- [ ] Issue 中已提供測試連結
- [ ] 等待案主測試批准

---

## 🚀 Deployment Notes（部署注意事項）

<!--
部署時需要注意的事項：
- 環境變數變更
- Database migration
- 依賴更新
- 其他特殊設定
-->

---

## 📝 Additional Notes（其他備註）

<!-- 任何其他需要說明的資訊 -->

---

**🤖 Generated with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
**Co-Authored-By: Happy <yesreply@happy.engineering>**
