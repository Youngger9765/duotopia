# 大重構清理計畫

## 🎯 清理策略

### 🗑️ **要刪除的檔案（實驗性/過時）**

#### 1. **實驗性 Alembic Migration**
```
❌ alembic/versions/20250917_1151_3419c62b5255_*
❌ alembic/versions/20250917_1154_71a9b9a902fc_*
```
**原因**：這些是實驗性 migration，要重新建立乾淨的

#### 2. **實驗性腳本**
```
❌ scripts/migrate_content_data.py
```
**原因**：舊的遷移邏輯，新架構不需要

#### 3. **重複的模型檔案**
```
❌ models/content_items.py （已刪除）
```
**原因**：重複了 models.py 中的定義

### 📚 **要保留並整理的檔案**

#### 1. **有價值的分析文件**
```
✅ docs/content-redesign/
├── ASSIGNMENT_RISK_ASSESSMENT.md
├── CONTENT_ANALYSIS_COMPLETE.md
├── DATABASE_COMPLEXITY_ANALYSIS.md
├── IMPLEMENTATION_CHECKLIST.md
├── IMPLEMENTATION_PLAN.md
├── PROPOSED_DB_REDESIGN.md
├── TDD_CONTRACT.md
├── TEACHER_WORKFLOW_IMPACT.md
├── WHATS_NEW.md
├── ALEMBIC_MIGRATION_GUIDE.md
└── MIGRATION_STRATEGY_ANALYSIS.md
```
**處理**：保留，但需要更新為最終版本

### 🔧 **要更新的檔案**

#### 1. **models.py**
**現狀**：已加入新模型，但可能需要清理
**處理**：保留新模型，確保沒有重複定義

#### 2. **移動的檔案**
```
❓ ASSIGNMENT_FLOW_DIAGRAM.md
```
**處理**：檢查是否已移到 docs/，如果是則正常

## 🚀 **執行清理**

### **第一步：刪除實驗性檔案**
```bash
# 刪除實驗性 migration
rm alembic/versions/20250917_1151_3419c62b5255_*
rm alembic/versions/20250917_1154_71a9b9a902fc_*

# 刪除舊的遷移腳本
rm -rf scripts/migrate_content_data.py

# 檢查是否還有其他實驗檔案
find . -name "*content_item*" -o -name "*migration*" | grep -v docs/
```

### **第二步：確認 models.py 狀態**
```bash
# 檢查 models.py 是否有重複定義
grep -n "class ContentItem\|class StudentItemProgress" models.py

# 確認沒有語法錯誤
python -c "import models; print('✅ models.py 正常')"
```

### **第三步：整理文件結構**
```bash
# 確認文件都在正確位置
ls docs/content-redesign/

# 檢查是否有遺漏的檔案
git status --ignored
```

## 🎯 **最終目標**

清理後的狀態：
```
✅ 乾淨的 git 狀態
✅ 只有有價值的分析文件
✅ models.py 包含正確的新模型
✅ 沒有實驗性/重複檔案
✅ 準備好進行大重構
```

## 💡 **下一步**

清理完成後：
1. Commit 這個乾淨的狀態
2. 重置 Alembic 歷史
3. 建立全新的 initial migration
4. 重新建立完整的 TDD 測試
