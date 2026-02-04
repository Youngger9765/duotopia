# Issue #208 Implementation TODO

**Branch**: `feat/issue-208-org-points-deduction`
**Spec**: `docs/issues/208-complete-spec.md`

---

## 📊 Progress Overview

- ⏰ Phase 1: Service 建立 (0%)
- ⏰ Phase 2: Speech Assessment 整合 (0%)
- ⏰ Phase 3: 其他活動整合 (0%)
- ⏰ 等待開發

---

## ⏰ Phase 1: Service 建立

### OrganizationPointsService
- [ ] **建立 Service 檔案**
  - 檔案: `backend/services/organization_points_service.py`
  - [ ] 定義 `UNIT_CONVERSION` 常數
  - [ ] 定義 `QUOTA_BUFFER_PERCENTAGE = 0.20`

- [ ] **convert_unit_to_points 方法**
  - [ ] 實作單位換算邏輯
  - [ ] 支援: 秒、字、張、分鐘
  - [ ] 單元測試

- [ ] **check_points 方法**
  - [ ] 檢查機構點數是否足夠
  - [ ] 返回 bool
  - [ ] 單元測試

- [ ] **get_points_info 方法**
  - [ ] 返回 total, used, remaining, status
  - [ ] 單元測試

- [ ] **deduct_points 方法**
  - [ ] 參數: organization_id, teacher_id, student_id, assignment_id, feature_type, unit_count, unit_type, feature_detail
  - [ ] 檢查機構存在
  - [ ] 換算為點數
  - [ ] 計算緩衝限制 (total * 1.20)
  - [ ] 超過緩衝 → HTTPException 402
  - [ ] 在緩衝區間 → 記錄 warning
  - [ ] 更新 organization.used_points
  - [ ] 建立 OrganizationPointsLog 記錄
  - [ ] 單元測試

### 單元測試
- [ ] **檔案**: `backend/tests/unit/test_organization_points_service.py`
  - [ ] test_convert_unit_to_points_seconds
  - [ ] test_convert_unit_to_points_characters
  - [ ] test_convert_unit_to_points_images
  - [ ] test_convert_unit_to_points_minutes
  - [ ] test_convert_unit_to_points_invalid_unit
  - [ ] test_check_points_sufficient
  - [ ] test_check_points_insufficient
  - [ ] test_check_points_no_org
  - [ ] test_get_points_info
  - [ ] test_deduct_points_success
  - [ ] test_deduct_points_buffer_warning
  - [ ] test_deduct_points_hard_limit_exceeded
  - [ ] test_deduct_points_creates_log

---

## ⏰ Phase 2: Speech Assessment 整合

### 修改 speech_assessment.py
- [ ] **Import 新 Service**
  - 檔案: `backend/routers/speech_assessment.py`
  - [ ] `from services.organization_points_service import OrganizationPointsService`

- [ ] **修改扣點邏輯** (Line ~912)
  - [ ] 取得 assignment.classroom
  - [ ] 判斷 classroom.organization_id
  - [ ] 機構班級 → OrganizationPointsService.deduct_points()
  - [ ] 個人班級 → QuotaService.deduct_quota() (維持現有)

- [ ] **錯誤處理**
  - [ ] 機構點數不足 → 友善提示學生
  - [ ] 記錄到 BigQuery (可選)

### 整合測試
- [ ] **檔案**: `backend/tests/integration/test_org_points_deduction_e2e.py`
  - [ ] test_speech_assessment_deducts_org_points
  - [ ] test_speech_assessment_deducts_teacher_quota_for_non_org
  - [ ] test_org_points_buffer_allows_overage
  - [ ] test_org_points_hard_limit_blocks
  - [ ] test_org_points_log_created

---

## ⏰ Phase 3: 其他活動整合 (Optional)

### Vocabulary 活動
- [ ] 找到 vocabulary 活動提交位置
- [ ] 加入點數扣除邏輯
- [ ] 測試

### Listening 活動
- [ ] 找到 listening 活動提交位置
- [ ] 加入點數扣除邏輯
- [ ] 測試

---

## 🚀 Deployment Steps

### Pre-deployment Checklist
- [ ] Phase 1 tasks completed
- [ ] Phase 2 tasks completed
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Code review approved

### Preview Environment
- [ ] Create PR from `feat/issue-208-org-points-deduction` to `staging`
- [ ] Preview deployed and running
- [ ] E2E verification completed
- [ ] **等待案主測試確認**

### Staging Deployment
- [ ] Merge to staging
- [ ] Monitor CI/CD
- [ ] Manual verification
- [ ] Monitor for 24-48 hours

### Production Deployment
- [ ] Get approval from stakeholders
- [ ] Create PR from staging to main
- [ ] Merge to main
- [ ] Monitor production
- [ ] Smoke test

---

## 📝 Notes

### 參考實作
- 個人老師扣點: `backend/services/quota_service.py`
- 整合位置: `backend/routers/speech_assessment.py:912`

### 設計決策
1. **換算規則**: 與個人模式相同 (秒=1, 字=0.1, 張=10)
2. **緩衝機制**: 20% buffer，與個人模式相同
3. **扣點判斷**: 根據 assignment.classroom.organization_id

### Dependencies
- Issue #198 已完成，資料庫結構已就緒
- `Organization.total_points`, `used_points` 欄位已存在
- `OrganizationPointsLog` 表已存在

---

**Last Updated**: 2026-02-04
**Created By**: Claude (via Happy)
