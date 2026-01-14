# 機構模組規格 - 最終決策文件

**決策日期**: 2026-01-12
**決策者**: Young (Backend Lead)
**相關 Issue**: #151, #112

---

## 決策摘要

本文件記錄針對 Autopilot 產生的 23 個釐清項目中，6 個需要技術主管審查的關鍵決策。

**決策結果**:
- ✅ 5 項同意 Autopilot 建議
- ⏸️ 1 項暫緩實作（點數系統）

---

## 🔴 高優先級決策（3 項）

### 1️⃣ CASCADE 刪除 vs 軟刪除策略

**項目編號**: #6
**Autopilot 建議**: 選項 C - 軟刪除策略（設定 `is_active=false`）

**✅ 決策**: **同意 Autopilot 建議 - 採用軟刪除**

**理由**:
- 教育系統應保留學生學習歷史資料
- 所有資料表已設計 `is_active` 欄位（DBML 規格）
- 符合教育系統業界標準（防止資料永久遺失）
- 效能影響可接受（需在 `is_active` 欄位建立索引）

**實作要點**:
```sql
-- 所有刪除操作改為軟刪除
UPDATE organizations SET is_active = false WHERE id = ?;
UPDATE schools SET is_active = false WHERE id = ?;

-- 查詢需加上 is_active 過濾
SELECT * FROM organizations WHERE is_active = true;

-- 建立索引提升效能
CREATE INDEX idx_organizations_is_active ON organizations(is_active);
CREATE INDEX idx_schools_is_active ON schools(is_active);
```

**注意事項**:
- 所有 API 查詢預設只返回 `is_active=true` 的資料
- 需提供管理介面查看「已停用」的資料
- 考慮定期清理機制（可選，非必要）

---

### 2️⃣ tax_id 唯一性與軟刪除設計

**項目編號**: #5
**Autopilot 建議**: 選項 B - 使用 partial unique index (`WHERE is_active=true`)

**✅ 決策**: **同意 Autopilot 建議 - Partial Unique Index**

**理由**:
- 支援機構暫時停用後重新啟用的業務流程
- 避免統編被永久鎖住（符合 SaaS 系統慣例）
- 符合軟刪除系統最佳實踐

**實作要點**:
```sql
-- 移除原本的 unique 約束
ALTER TABLE organizations DROP CONSTRAINT IF EXISTS organizations_tax_id_key;

-- 建立部分唯一索引（僅對 is_active=true 生效）
CREATE UNIQUE INDEX uq_organizations_tax_id_active
ON organizations (tax_id)
WHERE is_active = true;
```

**業務規則**:
- 同一統編在「啟用狀態」下只能有一個機構
- 停用機構後，該統編可用於建立新機構或重新啟用
- 重新啟用流程：檢查舊資料 → 恢復 `is_active=true` vs 建立新機構

**注意事項**:
- API 需明確處理「統編已被使用」的錯誤訊息
- 前端需提示使用者：該統編可能對應已停用的機構

---

### 3️⃣ org_owner 數量約束的資料庫實作

**項目編號**: #7
**Autopilot 建議**: 選項 B - 使用資料庫 partial unique index 強制執行

**✅ 決策**: **同意 Autopilot 建議 - 資料庫層約束**

**理由**:
- 在資料庫層面保證資料完整性（防止併發錯誤）
- 支援 org_owner 轉移流程（需配合 transaction）
- 比應用層驗證更可靠

**實作要點**:
```sql
CREATE UNIQUE INDEX uq_teacher_org_owner
ON teacher_organizations (organization_id)
WHERE role = 'org_owner' AND is_active = true;
```

**轉移流程設計**（原子化交易）:
```python
async def transfer_ownership(org_id, old_owner_id, new_owner_id):
    async with db.transaction():
        # Step 1: 停用舊擁有人角色
        await db.execute(
            "UPDATE teacher_organizations SET is_active = false "
            "WHERE organization_id = ? AND teacher_id = ? AND role = 'org_owner'",
            org_id, old_owner_id
        )

        # Step 2: 設定新擁有人（此時 unique constraint 不會違反）
        await db.execute(
            "INSERT INTO teacher_organizations (organization_id, teacher_id, role, is_active) "
            "VALUES (?, ?, 'org_owner', true)",
            org_id, new_owner_id
        )
```

**注意事項**:
- 需使用 database transaction 保證原子性
- 錯誤訊息需友善（不要暴露資料庫約束名稱）
- 建議記錄 org_owner 變更歷史（audit log）

---

## 🟡 中優先級決策（3 項）

### 4️⃣ 點數系統資料模型設計

**項目編號**: #18
**Autopilot 建議**: 選項 B - 建立 organization_credits 表（餘額 + 交易記錄）

**⏸️ 決策**: **暫緩實作 - 待業務需求明確**

**理由**:
- 點數系統的業務需求尚未完整定義
- 過早設計可能導致大幅返工
- #112 核心功能不依賴點數系統

**待確認的業務需求**:
- [ ] 點數系統的計費模型（預付 vs 後付？）
- [ ] 點數是否有過期機制？
- [ ] 是否有分級定價（不同點數包）？
- [ ] 充值與消費的完整流程？
- [ ] 是否需要發票整合？

**建議**:
- 在 Feature 檔案中標記為 `TODO: Points System`
- 與產品經理確認完整需求後再實作
- 可先用簡單的 `balance` 欄位（如果需要）

**後續實作時的參考**:
```sql
-- 待需求確認後再建立
CREATE TABLE organization_credits (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    balance INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    amount INTEGER NOT NULL,
    type VARCHAR(20), -- 'purchase', 'usage', 'refund'
    description TEXT,
    created_at TIMESTAMP
);
```

---

### 5️⃣ 教師授權數扣除與釋放邏輯

**項目編號**: #17
**Autopilot 建議**: 選項 A - 停用教師釋放授權（COUNT `is_active=true`）

**✅ 決策**: **同意 Autopilot 建議 - 按啟用教師數計費**

**理由**:
- 符合靈活的 SaaS 計費邏輯
- 機構可控制成本（停用不需要的教師）
- 保留歷史資料（符合軟刪除策略）

**實作要點**:
```python
def get_active_teacher_count(organization_id):
    """取得機構的啟用教師數（用於計費）"""
    return db.execute(
        "SELECT COUNT(*) FROM teacher_organizations "
        "WHERE organization_id = ? AND is_active = true",
        organization_id
    ).scalar()

def check_teacher_limit(organization_id):
    """檢查是否超過授權數"""
    org = get_organization(organization_id)
    active_count = get_active_teacher_count(organization_id)

    if active_count >= org.teacher_limit:
        raise QuotaExceededError("已達教師授權上限")
```

**業務規則建議**（需與產品/財務確認）:
- 計費方式：按**月結時的啟用教師數**計費（非峰值）
- 最低承諾數：建議設定（例如最少 3 位教師）
- 停用教師可重新啟用（不需重新授權）

**需確認**:
- [ ] 計費週期（月付 vs 年付）
- [ ] 是否有教師數階梯定價
- [ ] 超過授權數的處理方式（阻擋 vs 超額計費）

---

### 6️⃣ 移除機構成員後的資料處理

**項目編號**: #19
**Autopilot 建議**: 選項 C - 移除角色但保留歷史資料

**✅ 決策**: **同意 Autopilot 建議 - 保留歷史資料**

**理由**:
- 教師批改記錄應永久保留（教學品質追蹤）
- 學生學習歷史不應受教師異動影響
- 符合教育系統資料保存規範

**實作要點**:
```python
async def remove_teacher_from_organization(org_id, teacher_id):
    """移除教師與機構的關聯（軟刪除）"""
    # 停用角色關聯
    await db.execute(
        "UPDATE teacher_organizations SET is_active = false "
        "WHERE organization_id = ? AND teacher_id = ?",
        org_id, teacher_id
    )

    # 保留以下資料（不刪除）：
    # - teacher 表的教師基本資料
    # - assignments 表的作業批改記錄
    # - student_submissions 表的批改分數
    # - audit_logs 表的操作記錄
```

**資料處理規則**:
- ✅ 保留：教師批改記錄、作業設計、學生成績
- ✅ 保留：教師的歷史課程與教材
- ⚠️ 移除：機構成員列表中的顯示（`is_active=false`）
- ⚠️ 移除：該教師對機構資源的存取權限（Casbin policy）

**前端顯示**:
- 成員列表：不顯示已移除的教師
- 歷史記錄：顯示「（已移除）」標記
- 作業批改人：保留姓名，註明「前任教師」

**注意事項**:
- 移除成員時需同步更新 Casbin policy
- 建議記錄移除操作的 audit log（誰、何時移除）

---

## 📊 決策統計

| 優先級 | 決策數 | 同意 Autopilot | 暫緩 | 修改建議 |
|--------|--------|----------------|------|----------|
| 🔴 高 | 3 | 3 | 0 | 0 |
| 🟡 中 | 3 | 2 | 1 | 0 |
| **總計** | **6** | **5** | **1** | **0** |

**Autopilot 決策品質評估**: ⭐⭐⭐⭐⭐ 5/5
- 所有建議都符合系統設計原則
- 唯一暫緩的項目是因業務需求不明確，非技術問題

---

## 🚀 後續行動項

### 立即執行（高優先級）

1. **更新 DBML 規格**
   - [ ] 移除 CASCADE 刪除 note，改為「軟刪除策略」說明
   - [ ] 標註 `tax_id` 使用 partial unique index
   - [ ] 標註 `org_owner` 的 unique constraint

2. **資料庫 Migration**
   ```sql
   -- Migration: 建立 partial unique indexes

   -- 1. tax_id 唯一性
   ALTER TABLE organizations DROP CONSTRAINT IF EXISTS organizations_tax_id_key;
   CREATE UNIQUE INDEX uq_organizations_tax_id_active
   ON organizations (tax_id) WHERE is_active = true;

   -- 2. org_owner 唯一性
   CREATE UNIQUE INDEX uq_teacher_org_owner
   ON teacher_organizations (organization_id)
   WHERE role = 'org_owner' AND is_active = true;

   -- 3. 效能索引
   CREATE INDEX idx_organizations_is_active ON organizations(is_active);
   CREATE INDEX idx_schools_is_active ON schools(is_active);
   CREATE INDEX idx_teacher_organizations_is_active ON teacher_organizations(is_active);
   ```

3. **API 實作調整**
   - [ ] 所有查詢預設過濾 `is_active=true`
   - [ ] 刪除 API 改為軟刪除
   - [ ] 錯誤訊息友善化（唯一性約束違反）

### 本週執行（中優先級）

4. **業務需求確認**
   - [ ] 與產品經理確認點數系統需求（項目 #18）
   - [ ] 與財務確認教師授權計費模型（項目 #17）
   - [ ] 確認機構重新啟用 vs 建立新機構的流程（項目 #5）

5. **文件更新**
   - [ ] 更新 API 文件（軟刪除行為說明）
   - [ ] 更新 Feature 檔案（反映最終決策）
   - [ ] 建立 org_owner 轉移流程文件

### 延後執行

6. **點數系統**（待需求明確）
   - Feature 檔案標記為 `TODO: Points System`
   - 與產品經理排程需求會議

---

## ✅ 決策確認

**技術主管簽核**: Young (Backend Lead)
**日期**: 2026-01-12
**狀態**: ✅ 已完成審查，可進入實作階段

**備註**:
- 本決策文件涵蓋 #151 的所有關鍵審查項目
- 點數系統（#18）暫緩不影響 #112 核心功能開發
- 所有高優先級決策已完成，可開始資料庫設計與 API 實作

---

**相關文件**:
- Autopilot 執行報告: `.clarify/AUTOPILOT-EXECUTION-REPORT.md`
- 高信心度決策: `.clarify/autopilot-decisions-high-confidence.md`
- 低信心度決策: `.clarify/autopilot-decisions-low-confidence.md`
- 審查檢查清單: `.clarify/autopilot-review-checklist.md`
