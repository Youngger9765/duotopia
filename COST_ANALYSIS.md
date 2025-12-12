# Duotopia 成本分析报告

**报告日期**: 2025-12-12
**数据期间**: 2025-11-12 至 2025-12-11（30天）+ Azure 实际账单（12月1-12日）

---

## 💰 总成本概览

**月度总成本: TWD 2,938**

| 服务 | 月成本 | 占比 |
|------|--------|------|
| Azure Speech Service | **TWD 1,906** | 64.8% |
| Supabase Pro | **TWD 782** | 26.6% |
| Google Cloud Platform | **TWD 250** | 8.5% |

**每日成本**: TWD 97.9/天
**每位学生**: TWD 11.51/月（255 位活跃学生）
**每次录音**: TWD 0.422/次

---

## 🎤 Azure Speech Service 成本分析

**月度成本: TWD 1,906（64.8%）**

### 实际账单数据（来源：Azure Portal，12月1-12日）

| 服务 | 12天成本 | 月度预估 | 占比 |
|------|---------|---------|------|
| **STT + Pronunciation Assessment** | TWD 748.79 | **TWD 1,872** | 98.2% |
| **TTS (Neural)** | TWD 13.74 | **TWD 34** | 1.8% |
| **总计** | **TWD 762.53** | **TWD 1,906** | 100% |

### 使用量分析

**语音识别（STT）**:
- 评估次数: 8,306 次
- 音频时长: 16.2 小时
- 每小时成本: $2.14 USD
  - 基础 STT: $1.00/小时
  - Pronunciation Assessment: $1.00/小时（额外功能）

**语音合成（TTS）**:
- 新建题目: 2,303 个
- 字符数: 90,198 字符（远低于 50 万免费额度）
- 成本占比极低（1.8%）

### 成本合理性 ✅

Azure 成本高是因为：
1. **Pronunciation Assessment 功能**（逐字评分、发音准确度）
2. 这是**核心业务功能**，不可或缺
3. 成本结构**合理且预期内**

**单次录音成本**: TWD 0.274（Azure 部分）

---

## ☁️ Google Cloud Platform 成本明细

**月度成本: TWD 250（8.5%）**

### 服务明细

| 服务 | 月成本 | 说明 |
|------|--------|------|
| **Cloud Run** | TWD 168 | 16个服务运行（Production/Staging/Develop/Preview）|
| **Cloud Storage** | TWD 16 | 音频文件（1.61 GB）|
| **Artifact Registry** | TWD 13 | Docker 镜像存储（119个版本）|
| **BigQuery** | TWD 5 | 日志存储 |

### Cloud Run 配置

当前运行的 16 个服务（所有 minScale=0，闲置不计费）：
- Production: 2 个（512Mi + 1 CPU）
- Staging: 2 个（256Mi + 0.5 CPU）
- Develop: 2 个（256Mi + 0.5 CPU）
- Preview: 10 个（256Mi + 0.5 CPU）

### Cloud Run 成本明细

| 项目 | 用量 | 成本（TWD） |
|------|------|-----------|
| **CPU 时间** | 53.1 小时 | **TWD 142.60** |
| **网络流量** | 4.9 GB | **TWD 17.69** |
| **内存使用** | - | **TWD 7.95** |

---

## 📊 成本结构分析

### 固定成本（每月订阅）

**TWD 782/月**
- Supabase Pro: TWD 782

### 半静态成本（基础设施 + 缓慢增长）

**TWD 24/月**
- Artifact Registry: TWD 13（镜像存储）
- Cloud Storage: TWD 11（音频文件）

### 动态成本（随用户量线性增长）

**TWD 2,132/月**
- Azure STT + 评分: TWD 1,872（87.8%）
- Cloud Run CPU/Memory/Network: TWD 168（7.9%）
- Azure TTS: TWD 34（1.6%）
- Cloud Storage Operations: TWD 2（0.1%）
- Cloud Storage Data Transfer: TWD 3（0.1%）
- BigQuery Streaming: TWD 5（0.2%）

**总计: TWD 2,938/月**

---

## 📈 每次录音成本

### 实际数据基础

**过去 30 天（2025-11-12 至 2025-12-11）**:
- 总录音次数: **6,947 次**
- 总动态成本: **TWD 2,132**
- **平均成本**: **TWD 0.307/次录音**

### 成本拆分

**Azure Speech Service**:
- 月总成本: TWD 1,906
- 录音次数: 6,947 次
- **单次成本**: TWD 0.274/次

**Cloud Run + GCP 动态成本**:
- 月总成本: TWD 226（CPU + Memory + Network + Storage Ops + Data Transfer + BigQuery）
- 录音次数: 6,947 次
- **单次成本**: TWD 0.033/次

### 总成本（每次录音）

```
Azure Speech:    TWD 0.274
Cloud Run 等:    TWD 0.033
────────────────────────
总计:            TWD 0.307/次录音
```

---

## 🧮 每学生成本计算

### 实际数据（过去 30 天）

**活跃学生**: 255 人（有录音记录）
**总录音次数**: 6,947 次
**平均录音/学生**: 27.2 次/月

**成本结构**:
```
固定成本:      TWD 782
半静态成本:    TWD 24
动态成本:      TWD 2,132
────────────────────────
总计:          TWD 2,938/月

平均每学生:    TWD 11.51/月
平均每录音:    TWD 0.422/次
```

### 边际成本（新增一位学生）

假设新学生每月录音 27 次（平均水平）：

```
动态成本/学生 = 2,132 ÷ 255 = TWD 8.36/月
```

**边际成本**: **TWD 8.36/月/学生**（仅动态成本）

### 规模经济效应

| 学生数 | 固定成本/人 | 动态成本/人 | 总成本/人 |
|--------|-----------|-----------|----------|
| 255（当前） | TWD 3.15 | TWD 8.36 | **TWD 11.51** |
| 500 | TWD 1.61 | TWD 8.36 | **TWD 9.97** |
| 1,000 | TWD 0.81 | TWD 8.36 | **TWD 9.17** |
| 5,000 | TWD 0.16 | TWD 8.36 | **TWD 8.52** |

---

## 📊 实际使用数据（Supabase 查询结果）

**统计期间**: 2025-11-12 至 2025-12-11（30 天）

| 指标 | 数量 |
|------|------|
| **总注册学生** | 687 人 |
| **活跃学生（有录音）** | 255 人 |
| **总录音次数** | 6,947 次 |
| **平均录音/学生** | 27.2 次/月 |
| **平均录音/活跃学生** | 27.2 次/月 |

---

## 💡 商业模式建议

### 每位学生成本（基于 255 位活跃学生）

**总成本**: TWD 11.51/月/学生

**成本构成**:
- 固定成本分摊: TWD 3.15
- 动态成本: TWD 8.36

### 损益平衡点

假设收费 **TWD 199/月**：

```
固定成本: TWD 782
边际成本: TWD 8.36/学生

损益平衡 = 782 ÷ (199 - 8.36) = 5 位付费学生
```

**只需 5 位付费学生即可盈亏平衡** ✅

### 规模经济

| 付费学生数 | 月收入 | 月成本 | 月利润 | 利润率 |
|-----------|--------|--------|--------|--------|
| 5 | TWD 995 | TWD 824 | TWD 171 | 21% |
| 10 | TWD 1,990 | TWD 866 | TWD 1,124 | 130% |
| 50 | TWD 9,950 | TWD 1,200 | TWD 8,750 | 729% |
| 100 | TWD 19,900 | TWD 1,618 | TWD 18,282 | 1,130% |
| 255（当前全部）| TWD 50,745 | TWD 2,938 | TWD 47,807 | 1,627% |

**关键洞察**:
1. 固定成本 TWD 782/月，动态成本 TWD 8.36/学生
2. 5 位付费学生即可盈亏平衡
3. 当前 255 位学生若全部付费（TWD 199/月），月利润可达 TWD 47,807

---

## 🎯 成本优化建议

### 已完成优化 ✅

#### 1. 删除 VM（2025-12-10）
**节省**: TWD 48/月

**原因**:
- Compute Engine VM 已迁移至 Cloud Run
- 不再需要 e2-small 实例

**状态**: ✅ 已执行

#### 2. 关闭 Network Intelligence Center（2025-12-12）
**节省**: TWD 8/月

**原因**:
- 功能与免费的 Cloud Monitoring 重复
- 5天前自动启用，非主动使用
- 不影响生产环境运行

**状态**: ✅ 已执行

#### 3. 清理 Artifact Registry 废弃镜像（2025-12-12）
**节省**: TWD 6/月（预估，待 Google 完成物理删除）

**原因**:
- VM 架构于 12月7日迁移至 Cloud Run
- 留下 101 个废弃的 `duotopia-*-vm` 镜像（12月7-10日）
- 清理后仅保留 25 个活跃镜像（Production/Staging/Develop/Preview）

**当前状态**:
- 仓库大小: 9.7GB（物理删除后将降低）
- 镜像数量: 25 个活跃版本

**自动清理策略已启用**:
- 无标签镜像: 7天自动删除
- 有标签镜像: 30天自动删除
- 每个包保留最新 2 个版本

**价值**: 防止未来镜像堆积，减少存储成本

**状态**: ✅ 已执行，等待 Google 完成物理删除

#### 4. 启用免费监控工具（2025-12-12）
**成本**: TWD 0

**已启用**:
- Cloud Trace（分布式追踪）
- Error Reporting（错误报告）
- Cloud Profiler（代码性能分析）
- Recommender（成本优化建议）

**价值**: 比 Network Intelligence 更实用，且完全免费

**详细文档**: [MONITORING.md](./MONITORING.md)

### 可执行的优化（低优先级）

#### 1. 清理 Preview 环境
- 当前: 10 个服务
- 预估节省: TWD 20/月
- 风险: 低（minScale=0，闲置不计费）

检查并删除已关闭 Issue 的 Preview 环境：
```bash
# 检查 Issue 状态
gh issue view 61  # 如果已关闭，删除对应服务
gh issue view 74
gh issue view 87
gh issue view 88
gh issue view 95

# 删除服务（如果 Issue 已关闭）
gcloud run services delete duotopia-preview-issue-61-backend --region=asia-east1 --quiet
gcloud run services delete duotopia-preview-issue-61-frontend --region=asia-east1 --quiet
```

#### 2. Issue #87 - TTS 缓存
- TTS 当前成本: TWD 34/月（仅 1.8%）
- 优化后节省: TWD 30/月（90% 缓存命中率）
- **结论**: ROI 很低，建议低优先级

**原因**:
- TTS 成本占总成本不到 2%
- 实施缓存需要额外开发和维护成本
- 投入产出比不高

#### 3. 优化 Cloud Run CPU 使用
- 当前: 53.1 小时/月 = TWD 142.60
- 潜在节省: TWD 14/月（10%）
- 风险: 低

**建议**:
- 使用 Cloud Trace 监控哪些 API 端点消耗最多 CPU
- 使用 Cloud Profiler 优化长时间运行的任务
- 预计可优化 10%

---

## 📊 优化总结

| 优化项目 | 节省（TWD/月）| 风险 | 状态 |
|---------|--------------|------|------|
| 删除 VM | -48 | 低 | ✅ 已完成 2025-12-10 |
| 关闭 Network Intelligence | -8 | 低 | ✅ 已完成 2025-12-12 |
| 清理 Artifact Registry | -6 | 低 | ✅ 已完成 2025-12-12 |
| 清理 Preview 环境 | -20 | 低 | 待执行 |
| 优化 Cloud Run CPU | -14 | 低 | 长期优化 |
| **已完成优化** | **-62** | - | ✅ |
| **待执行优化潜力** | **-34** | - | - |

**当前成本**: TWD 2,938/月（TWD 97.9/天）
**优化后预估成本**: TWD 2,835/月（TWD 94.5/天）

**每学生成本**: TWD 11.12/月（255 学生，27.2 次/月/学生）

---

## 📋 成本监控建议

### 每周监控

1. Cloud Run CPU 使用时间（当前 53.1 小时/月）
2. Preview 环境数量（当前 10 个，应为 0）
3. Artifact Registry 镜像版本数（当前 25 个，自动清理策略已启用）

### 每月监控

1. Cloud Storage 增长率（当前 1.61 GB）
2. Azure Speech Service 使用量（当前 6,947 次/月）
3. 总成本趋势（当前 TWD 2,938/月）
4. 活跃学生数（当前 255 人）

### 告警设置

```bash
# 设置成本告警（建议 TWD 5,000/月）
gcloud billing budgets create \
  --billing-account=01471C-B12C4F-6AB7B9 \
  --display-name="Duotopia Monthly Budget" \
  --budget-amount=160USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## 🔗 相关资源

- [GCP Billing Dashboard](https://console.cloud.google.com/billing)
- [Azure Cost Analysis](https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/costanalysis)
- [Cloud Run Services](https://console.cloud.google.com/run)
- [Artifact Registry](https://console.cloud.google.com/artifacts)
- [BigQuery Billing Export](https://console.cloud.google.com/bigquery?p=duotopia-472708&d=billing_export)

---

## 📜 版本历史

### v2.4 - 2025-12-12 - Artifact Registry 清理完成

**成本优化**:
- 清理 101 个废弃 VM 镜像（2025-12-07至12-10）
- 节省 TWD 6/月（预估，待 Google 完成物理删除）
- 当前仅保留 25 个活跃镜像
- 仓库大小: 9.7GB（清理后将降低）

**自动清理策略**:
- 无标签镜像: 7天自动删除
- 有标签镜像: 30天自动删除
- 每个包保留最新 2 个版本

**影响**:
- 已完成优化: TWD -56 → TWD -62
- 优化后预估成本: TWD 2,841 → TWD 2,835
- 每学生成本: TWD 11.14 → TWD 11.12

### v2.3 - 2025-12-12 - 文档重写

**改进**:
- 移除所有删除线格式，避免混淆
- 主要内容仅显示当前正确数据
- 所有更正历史移至版本历史区块
- 清晰的段落结构和表格格式
- 专业、数据驱动的语气

### v2.2 - 2025-12-12 - Azure 成本分析修正

**发现**:
经查询 Azure Portal 实际账单，发现：
- STT + Pronunciation Assessment 占 98.2%（TWD 1,872/月）
- TTS 仅占 1.8%（TWD 34/月）
- 总成本 TWD 1,906/月（不是之前估算的 TWD 500）

**原因**:
Pronunciation Assessment 功能导致 STT 成本翻倍，但这是核心功能，成本合理。

**影响**:
- 总成本从 TWD 1,532 更新为 TWD 2,938
- 每学生成本从 TWD 6.00 更新为 TWD 11.51
- Issue #87（TTS 缓存）优先级降低（ROI 低）

### v2.1 - 2025-12-12 - 启用免费监控工具

**成本优化**:
- 关闭 Network Intelligence Center（节省 TWD 8/月）
- 总成本从 TWD 1,540 降至 TWD 1,532
- 每学生成本从 TWD 6.02 降至 TWD 6.00

**监控工具启用**（免费）:
- Cloud Trace - 分布式追踪
- Error Reporting - 错误聚合
- Cloud Profiler - 代码性能分析
- Recommender - 成本优化建议

**文档新增**:
- [MONITORING.md](./MONITORING.md) - 监控工具使用指南
- 更新 `.claude/agents/code-reviewer.md`
- 更新 `.claude/agents/test-runner.md`

### v2.0 - 2025-12-12 - 货币错误修正

**重大发现**: GCP 账单币别是 TWD（不是 USD）

**错误**: 之前分析错误地将 TWD 金额乘以 31.26 汇率
**修正**: 直接使用 TWD 金额

这导致：
- GCP 成本从错误的 TWD 8,054 修正为 TWD 250
- 总成本从错误的 TWD 9,149 修正为 TWD 1,540（后因 Azure 更新为 TWD 2,938）
- 每学生成本从错误的 TWD 71.6 修正为 TWD 6.02（后因 Azure 更新为 TWD 11.51）

**其他更新**:
- 更新实际使用数据（255 学生，6,947 次录音）
- 重新分类成本为固定/半静态/动态
- 更新商业模式建议
- 调整优化建议和预算告警阈值

### v1.0 - 2025-12-12 - 初版

初始版本，包含 GCP 货币错误（已在 v2.0 修正）

---

**最后更新**: 2025-12-12（v2.4 - Artifact Registry 清理完成）
**下次审查**: 2026-01-12
