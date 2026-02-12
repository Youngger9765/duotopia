# Issue #208: 機構點數自動扣點整合

**優先級**: 🟡 Medium
**負責人**: TBD
**狀態**: Planning
**分支**: `feat/issue-208-org-points-deduction`

---

## 📋 Overview

整合機構點數系統與學生活動，當學生提交作業/完成活動時，自動扣除機構點數。

**依賴**:
- Issue #198 - 機構點數系統基礎建設 ✅ (已完成)

**參考**:
- 個人老師扣點機制: `backend/services/quota_service.py`
- SPEC: `spec/features/subscription/.clarify/resolved/data/PointsTransaction_使用記錄時機.md`

---

## 🎯 Goals

### 核心目標
1. 學生提交口說作業時，自動扣除機構點數
2. 學生完成單字/聽力活動時，自動扣除機構點數
3. 扣點記錄包含完整追蹤資訊
4. 點數不足時有適當的緩衝與處理機制

---

## ✅ 需求確認 (2026-02-04) - 已全部確認

### 1. 換算規則
**決策**: 與個人模式相同（根據 unit_type 換算）

```python
UNIT_CONVERSION = {
    "秒": 1,      # 1 秒 = 1 點（口說評分用）
    "字": 0.1,   # 1 字 = 0.1 點（文字校正用）
    "張": 10,    # 1 張圖 = 10 點（圖片校正用）
    "分鐘": 60,  # 1 分鐘 = 60 點
}
```

### 2. 緩衝機制
**決策**: 需要 20% buffer

```python
QUOTA_BUFFER_PERCENTAGE = 0.20  # 允許超額 20%
```

### 3. 扣點對象判斷
**決策**: 根據作業所屬班級 (Classroom) 判斷

```python
classroom = assignment.classroom
if classroom.organization_id:
    # 機構班級 → 扣機構點數
    OrganizationPointsService.deduct_points(...)
else:
    # 個人老師班級 → 扣老師配額
    QuotaService.deduct_quota(...)
```

### 4. 批次結算
**決策**: 初期只做即時扣點 (A)，不實作 B/C/D 批次結算

### 5. 退回作業
**決策**: 不返還已扣點數（簡化實作）

---

## 📐 Technical Design

### 1. 新增 Service 類別

**檔案**: `backend/services/organization_points_service.py`

```python
class OrganizationPointsService:
    """機構點數管理服務"""

    # 單位換算規則（與個人模式相同）
    UNIT_CONVERSION = {
        "秒": 1,
        "字": 0.1,
        "張": 10,
        "分鐘": 60,
    }

    # 配額超額緩衝（允許超額 20%）
    QUOTA_BUFFER_PERCENTAGE = 0.20

    @staticmethod
    def convert_unit_to_points(unit_count: float, unit_type: str) -> int:
        """將不同單位換算為點數"""
        ...

    @staticmethod
    def check_points(organization: Organization, required_points: int) -> bool:
        """檢查點數是否足夠"""
        ...

    @staticmethod
    def get_points_info(organization: Organization) -> Dict[str, Any]:
        """取得點數資訊"""
        ...

    @staticmethod
    def deduct_points(
        db: Session,
        organization_id: UUID,
        teacher_id: int,
        student_id: Optional[int],
        assignment_id: Optional[int],
        feature_type: str,
        unit_count: float,
        unit_type: str,
        feature_detail: Optional[Dict[str, Any]] = None,
    ) -> OrganizationPointsLog:
        """扣除點數並記錄"""
        ...
```

### 2. 整合位置

**檔案**: `backend/routers/speech_assessment.py`

```python
# Line ~912 後，評分成功後扣除配額

if teacher and assignment:
    classroom = assignment.classroom

    if classroom and classroom.organization_id:
        # 🏢 機構班級 → 扣機構點數
        OrganizationPointsService.deduct_points(
            db=db,
            organization_id=classroom.organization_id,
            teacher_id=teacher.id,
            student_id=current_student.id,
            assignment_id=assignment.id,
            feature_type="speech_assessment",
            unit_count=duration_seconds,
            unit_type="秒",
            feature_detail={
                "reference_text": reference_text,
                "accuracy_score": assessment_result["accuracy_score"],
                "audio_size_bytes": len(audio_data),
            },
        )
    else:
        # 👤 個人老師班級 → 扣老師配額
        QuotaService.deduct_quota(...)
```

### 3. 資料庫欄位

已存在（Issue #198 已建立）:
- `Organization.total_points` - 總點數
- `Organization.used_points` - 已使用點數
- `Organization.last_points_update` - 最後更新時間
- `OrganizationPointsLog` - 使用記錄表

### 4. 錯誤處理

| 狀況 | HTTP Code | 處理方式 |
|------|-----------|----------|
| 無有效機構 | 404 | 拒絕操作 |
| 超過緩衝限制 | 402 | 拒絕操作，提示續費 |
| 在緩衝區間 | 200 | 允許但記錄警告 |

---

## 🔌 API Changes

### 現有 API (不變)
- `GET /api/organizations/{org_id}/points` - 查詢點數餘額
- `POST /api/organizations/{org_id}/points/deduct` - 手動扣點（Admin）
- `GET /api/organizations/{org_id}/points/history` - 使用記錄

### 新增內部呼叫
- `OrganizationPointsService.deduct_points()` - 自動扣點（學生活動觸發）

---

## 🧪 Testing Requirements

### 單元測試
**檔案**: `backend/tests/unit/test_organization_points_service.py`

- [ ] `test_convert_unit_to_points_seconds`
- [ ] `test_convert_unit_to_points_characters`
- [ ] `test_convert_unit_to_points_images`
- [ ] `test_check_points_sufficient`
- [ ] `test_check_points_insufficient`
- [ ] `test_deduct_points_success`
- [ ] `test_deduct_points_buffer_warning`
- [ ] `test_deduct_points_hard_limit_exceeded`

### 整合測試
**檔案**: `backend/tests/integration/test_org_points_deduction_e2e.py`

- [ ] `test_speech_assessment_deducts_org_points`
- [ ] `test_speech_assessment_deducts_teacher_quota_for_non_org`
- [ ] `test_org_points_buffer_allows_overage`
- [ ] `test_org_points_hard_limit_blocks`

---

## 📅 Implementation Phases

### Phase 1: Service 建立 (4-6h)
- [ ] 建立 `OrganizationPointsService` 類別
- [ ] 實作單位換算
- [ ] 實作點數檢查
- [ ] 實作扣點邏輯（含 20% buffer）
- [ ] 撰寫單元測試

### Phase 2: 整合 Speech Assessment (3-4h)
- [ ] 修改 `speech_assessment.py`
- [ ] 根據 classroom 判斷扣點對象
- [ ] 撰寫整合測試

### Phase 3: 其他活動整合 (2-3h)
- [ ] 整合 vocabulary 活動
- [ ] 整合 listening 活動
- [ ] 擴充測試覆蓋

---

## ✅ Acceptance Criteria

- [ ] 機構學生提交口說作業時，自動扣除機構點數
- [ ] 個人老師學生提交作業時，扣除老師配額（維持現有行為）
- [ ] 扣點記錄包含：學生 ID、作業 ID、活動類型、消耗點數
- [ ] 超過基本配額但未超過緩衝時，記錄警告但允許繼續
- [ ] 超過緩衝限制時，阻擋操作並提示
- [ ] 所有測試通過

---

## 🔗 Related

- Issue #198 - 機構點數系統基礎建設 ✅
- `backend/services/quota_service.py` - 個人老師扣點參考
- `spec/features/subscription/.clarify/resolved/data/PointsTransaction_使用記錄時機.md`

---

**Last Updated**: 2026-02-04
**Created By**: Claude (via Happy)
