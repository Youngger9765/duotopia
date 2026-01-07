# Autopilot Clarify 執行總結

**執行時間**：2026年1月7日  
**處理範圍**：Organization 領域剩餘 20 個釐清項目（排除 3 個已手動處理）

---

## 執行統計

### 項目處理結果
- **總項目數**：23 項
- **已手動處理（跳過）**：3 項
  1. 機構擁有人密碼設定安全性問題.md（已實施 token-based 方案）
  2. TeacherSchool_permissions覆蓋預設角色權限的邏輯.md（已決策建立 teacher_classroom_permissions 表）
  3. 個人教師後台與機構教師後台的切換機制.md（已修正 Feature 檔案）
- **本次處理**：20 項
  - ✅ 已因 Feature 修正而解決：1 項
  - 📋 Autopilot 決策：19 項

### 決策信心度分佈
- **高信心度（High Confidence）**：14 項（73.7%）
  - 能從 DBML、Feature、業界慣例明確推斷
- **低信心度（Low Confidence）**：5 項（26.3%）
  - 需要業務決策或產品經理確認

### 需人工審查項目
- **關鍵審查項**：8 項
  - 涉及資料庫設計、業務規則、安全性的重要決策

---

## 處理方法論

### Context Inference 策略
1. **資料模型推斷**：從 DBML 結構、欄位類型、約束推斷設計意圖
2. **業界慣例應用**：參考常見的軟刪除、CASCADE、權限管理模式
3. **跨檔案一致性**：確保 Feature 與 DBML 的對應關係
4. **保守決策原則**：不確定時選擇可逆、低風險的選項

### 信心度評分標準
- **High**：DBML/Feature 已有明確說明，或業界有標準做法
- **Medium**：可從多個線索合理推斷，但有多種可能
- **Low**：需要業務決策，技術上無明確答案

---

## 主要發現

### 1. Feature 修正已解決的問題
- **個人教師與機構教師身分切換_未被指派班級教師無法切換的邏輯.md**
  - Feature 已從「切換後台」改為「視圖切換」
  - 新邏輯：只要加入機構即可切換視圖，未被指派班級時顯示提示訊息
  - 原始矛盾已不存在

### 2. 資料模型缺失項（需補充 DBML）
1. **點數系統**：Feature 提到但 DBML 缺失
2. **教師授權數**：Feature 提到但 DBML 缺失
3. **Teacher 表**：Feature 提到 Teacher.is_admin 但未在 organization DBML 中定義

### 3. Feature 需補充的內容
1. **建立機構.feature**：缺少驗證規則與邊界條件 Example
2. **管理機構成員.feature**：缺少 org_owner 轉移的完整流程
3. **機構擁有人管理流程.feature**：缺少授權數釋放邏輯說明

---

## 後續行動建議

### 立即行動（High Priority）
1. **審查高信心度決策**（14 項）
   - 確認 CASCADE 刪除策略
   - 確認軟刪除與唯一性約束設計
   - 確認權限驗證策略

2. **業務決策項**（5 項低信心度）
   - 點數系統資料模型設計
   - 教師授權數扣除與釋放邏輯
   - org_owner 轉移流程
   - 專案服務人員角色定義

### 後續補充（Medium Priority）
1. **補充 DBML**
   - 新增 organization_credits 表（點數系統）
   - 新增 teacher_limit/teacher_used 欄位（授權數）
   - 補充 settings 欄位結構說明

2. **補充 Feature Example**
   - 建立機構：驗證規則與邊界條件
   - 管理機構成員：org_owner 轉移流程
   - 機構擁有人管理流程：授權數釋放邏輯

3. **建立跨 DBML 參照文件**
   - 說明 Teacher 表定義位置
   - 說明跨領域實體關聯

---

## 決策文件索引

1. **autopilot-decisions-high-confidence.md**
   - 14 項高信心度決策
   - 基於 DBML、Feature、業界慣例推斷
   - 建議直接採用，但需審查確認

2. **autopilot-decisions-low-confidence.md**
   - 5 項低信心度決策
   - 需要業務決策或產品經理確認
   - 提供建議方案與理由

3. **autopilot-review-checklist.md**
   - 8 項關鍵審查項
   - 需技術主管或架構師確認
   - 影響系統核心設計

---

## 風險提示

### 高風險決策（需特別注意）
1. **CASCADE 刪除鏈路**（項目 #6）
   - 決策：完整 CASCADE 刪除 organization → schools → classrooms → students
   - 風險：可能導致大量資料遺失
   - 建議：考慮軟刪除或分階段刪除

2. **tax_id 唯一性與軟刪除**（項目 #5）
   - 決策：使用 partial unique index (where is_active=true)
   - 風險：機構重新啟用邏輯需仔細設計
   - 建議：明確定義機構生命週期流程

3. **org_owner 數量約束**（項目 #7）
   - 決策：使用資料庫 partial unique index 強制執行
   - 風險：轉移流程需額外邏輯處理
   - 建議：實作原子化轉移交易

---

## 總結

Autopilot Clarify 成功處理 20 個項目，其中：
- **1 項**因 Feature 修正已解決
- **14 項**給出高信心度決策（可直接採用）
- **5 項**給出低信心度決策（需業務確認）
- **8 項**需關鍵審查（影響核心設計）

建議優先審查高信心度決策中的 CASCADE 刪除策略、唯一性約束設計，確保資料安全與業務邏輯正確性。低信心度項目需召開業務會議確認產品方向。
