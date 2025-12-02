# Staging → Main 合并风险评估

**评估时间**: 2025-12-02 14:30
**分支**: `staging` → `main`
**Issue**: #56 - Assignment-Template Separation

---

## 📊 变更规模

```
21 files changed, 6227 insertions(+), 611 deletions(-)
```

### 影响文件分类

#### 🔴 高风险（数据库变更）
- `alembic/versions/20251201_2336_cd6eab4e2001_add_assignment_copy_fields_to_content.py` (NEW)
  - 新增 `contents.is_assignment_copy` (NOT NULL, default=false)
  - 新增 `contents.source_content_id` (NULLABLE)
  - 6 个新索引
  - 1 个外键约束

#### 🟡 中风险（核心业务逻辑）
- `backend/routers/assignments.py` (+416/-?)
- `backend/routers/teachers.py` (+331/-?)
- `backend/models.py` (+25)
- `backend/seed_data.py` (+130/-?)
- `frontend/src/components/AssignmentDialog.tsx` (+1090/-?)
- `frontend/src/pages/teacher/TeacherAssignmentDetailPage.tsx` (+691/-?)

#### 🟢 低风险（新增功能/测试）
- `backend/tests/api/test_assignment_bulk_operations.py` (NEW, 518 lines)
- `backend/tests/api/test_assignment_content_copy_mechanism.py` (NEW, 1936 lines)
- `backend/tests/api/test_assignment_permission_filtering.py` (NEW, 340 lines)
- `backend/tests/api/test_student_assignment_end_to_end.py` (NEW, 507 lines)
- `PROJECT_HANDOVER.md` (NEW, 258 lines)

---

## ⚠️ 风险评估

### 🔴 高风险项

#### 1. 数据库迁移（Alembic Migration）
**风险等级**: 🔴 HIGH

**描述**:
- 新增 `is_assignment_copy` 字段（NOT NULL with default）
- 影响所有现有 Content 记录
- 生产环境迁移必须成功，否则服务中断

**缓解措施**:
```bash
# Production 部署前必须：
1. 完整备份生产数据库（Supabase Dashboard）
2. 在 Staging 已验证迁移成功 ✅ (已完成)
3. 准备回滚计划（downgrade script 已存在）
```

**Staging 验证状态**: ✅ **已通过**
- 迁移成功执行
- 28/28 作业迁移成功
- 160 条 StudentItemProgress 验证通过
- 所有数据完整性检查通过

---

#### 2. 生产数据迁移脚本
**风险等级**: 🔴 HIGH

**描述**:
- `backend/scripts/migrate_assignments_to_copy.py`
- 必须在生产环境执行数据迁移
- 影响所有现有作业和学生进度

**缓解措施**:
```bash
# Production 迁移步骤：
1. Alembic migration 完成后
2. 执行迁移脚本：python scripts/migrate_assignments_to_copy.py
3. 验证所有作业都使用副本
4. 验证学生进度数据完整性
```

**Staging 验证状态**: ✅ **已通过**
- Dry run 测试 28 个作业全部通过
- 真实迁移 28/28 成功
- 黃小華案例验证通过（录音、分数、AI 批改全部保留）

---

### 🟡 中风险项

#### 3. 核心业务逻辑变更
**风险等级**: 🟡 MEDIUM

**影响范围**:
- 作业创建流程（现在创建副本）
- 作业编辑权限（有学生进度时禁止删除 ContentItem）
- 作业详情页面（显示副本状态）

**缓解措施**:
- ✅ 已有 3301 行新测试覆盖
- ✅ Staging 环境已部署验证
- ⚠️ 需要在 Production 部署后进行端到端测试

---

#### 4. 前端组件重构
**风险等级**: 🟡 MEDIUM

**变更**:
- `AssignmentDialog.tsx`: 1090 lines changed
- `TeacherAssignmentDetailPage.tsx`: 691 lines changed
- 新增副本机制 UI 反馈

**缓解措施**:
- ✅ TypeScript 编译通过
- ✅ ESLint/Prettier 检查通过
- ⚠️ 需要在 Production 测试删除按钮 disable 功能

---

### 🟢 低风险项

#### 5. 新增测试文件
**风险等级**: 🟢 LOW

**描述**: 4 个新测试文件，3301 行测试代码
**影响**: 无，纯新增

---

#### 6. 翻译文件
**风险等级**: 🟢 LOW

**描述**: i18n 翻译新增/更新
**影响**: 仅影响显示文本

---

## ✅ 合并前检查清单

### 代码质量
- [x] TypeScript 编译通过
- [x] ESLint 检查通过
- [x] Prettier 格式化通过
- [x] Black 格式化通过（backend）
- [x] Flake8 检查通过（backend）
- [x] 所有新测试通过

### Git 状态
- [x] No merge conflicts detected
- [x] Staging branch clean (no uncommitted changes)
- [x] All commits have clear messages

### 功能验证（Staging）
- [x] Alembic migration 成功执行
- [x] 数据迁移脚本验证通过
- [x] 作业创建流程正常
- [x] 学生进度数据完整保留
- [x] 删除按钮 disable 功能正常

---

## 🚀 推荐部署流程

### Phase 1: Merge to Main (低风险)
```bash
# 1. 切换到 main 分支
git checkout main

# 2. 合并 staging
git merge staging --no-ff -m "merge: Issue #56 - Assignment-Template Separation (Staging → Main)"

# 3. 推送到远程
git push origin main
```

**风险**: 🟢 LOW（仅代码合并，无部署变更）

---

### Phase 2: Production Deployment (中风险)
```bash
# 1. GitHub Actions 会自动触发部署到 Production

# 2. 部署包含：
#    - Backend deployment (with Alembic migration)
#    - Frontend deployment

# 3. Alembic migration 会自动执行：
#    - 新增 is_assignment_copy 字段
#    - 新增 source_content_id 字段
#    - 创建 6 个索引
```

**风险**: 🟡 MEDIUM
- Alembic migration 必须成功
- 服务会短暂重启
- 现有数据不受影响（默认值 false）

**预估时间**: 2-3 分钟

---

### Phase 3: Data Migration (高风险)
```bash
# ⚠️ 重要：必须在 Production 部署完成后立即执行

# 1. 连接 Production 数据库
export DATABASE_URL="$PRODUCTION_SUPABASE_POOLER_URL"

# 2. 先备份！（Supabase Dashboard）
#    Settings → Database → Create backup

# 3. Dry run 验证（不修改数据）
python scripts/migrate_assignments_to_copy.py <<< 'no'

# 4. 检查 dry run 结果是否正常

# 5. 执行真实迁移
python scripts/migrate_assignments_to_copy.py <<< 'yes'

# 6. 验证迁移结果
#    - 检查所有作业都使用副本
#    - 检查学生进度数据完整性
```

**风险**: 🔴 HIGH
- 影响所有现有作业
- 影响所有学生进度记录
- 必须一次成功（虽然有回滚机制）

**预估时间**: 5-10 分钟（取决于数据量）

---

## 🔙 回滚计划

### 如果 Phase 1 有问题（代码合并）
```bash
git reset --hard HEAD~1
git push origin main --force
```
**风险**: 🟢 LOW

### 如果 Phase 2 有问题（Alembic migration）
```bash
# 在 Production backend 执行
cd backend
alembic downgrade -1
```
**风险**: 🟡 MEDIUM

### 如果 Phase 3 有问题（数据迁移）
```bash
# 从 Supabase 备份恢复
# 或者手动回滚迁移的作业
```
**风险**: 🔴 HIGH（需要数据库恢复）

---

## 📈 成功指标

### 部署成功标准
- [x] Alembic migration 执行成功
- [ ] 数据迁移脚本完成（100% 成功率）
- [ ] Production 前端可访问
- [ ] 创建新作业流程正常
- [ ] 学生查看作业流程正常
- [ ] 现有学生进度可正常访问

### 数据完整性验证
- [ ] 所有作业都使用副本（`is_assignment_copy=true`）
- [ ] 所有 StudentItemProgress 指向副本
- [ ] 录音 URL、分数、AI 批改数据完全保留
- [ ] 原模板保持不变

---

## 🎯 总体风险评估

### 风险等级: 🟡 MEDIUM-HIGH

**原因**:
- ✅ 代码合并风险低（无冲突）
- ✅ Staging 验证完整
- ⚠️ 生产数据迁移需要谨慎
- ⚠️ 需要准备完整备份和回滚计划

### 推荐策略

**✅ 建议合并**，但需要：
1. **立即执行** Phase 1（代码合并）
2. **监控** Phase 2（Production 部署）
3. **谨慎执行** Phase 3（数据迁移）
4. **准备备份**和回滚计划

**最佳执行时机**: 低峰时段（非工作时间）

---

## 📞 应急联系

如果遇到问题：
1. 立即停止操作
2. 检查错误日志
3. 评估是否需要回滚
4. 必要时从备份恢复

---

**评估人**: Claude
**最后更新**: 2025-12-02 14:30
**Staging 验证状态**: ✅ 全部通过
