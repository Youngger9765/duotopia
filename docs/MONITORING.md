# Duotopia 监控和性能分析工具指南

**最后更新**: 2025-12-12

本文档说明 Duotopia 项目中可用的免费 GCP 监控工具及其使用方法。

---

## 📊 可用工具概览

| 工具 | 用途 | 免费额度 | 当前用量 | 成本 |
|------|------|---------|---------|------|
| Cloud Trace | 分布式追踪 | 250 万 spans/月 | ~3.2 万/月 | TWD 0 |
| Error Reporting | 错误聚合 | 无限 | - | TWD 0 |
| Cloud Profiler | 代码性能分析 | 无限 | - | TWD 0 |
| Cloud Logging | 日志存储 | 50 GB/月 | ~3 GB/月 | TWD 0 |
| Cloud Monitoring | 指标监控 | 150 MB/月 | ~7 MB/月 | TWD 0 |

**总成本**: TWD 0（全部在免费额度内）

---

## 🔍 Cloud Trace（分布式追踪）

### 用途
追踪每个 API 请求的完整生命周期，找出性能瓶颈。

### 访问
https://console.cloud.google.com/traces/list?project=duotopia-472708

### 使用场景

#### 1. 优化 API 响应时间
```
示例：学生录音评分接口慢
1. 打开 Cloud Trace
2. 搜索 /api/student/{id}/submit
3. 查看瀑布图：
   ├─ [10ms] 数据库查询
   ├─ [450ms] Azure STT 评分 ⚠️ 瓶颈
   └─ [50ms] 保存结果
4. 优化方向：缓存 Azure STT 结果
```

#### 2. 验证缓存命中率
```
对比缓存命中 vs 未命中：
命中: [5ms] 检查 GCS → [2ms] 返回
未命中: [5ms] 检查 GCS → [450ms] Azure API → [10ms] 保存
```

### 代码集成（可选）

如果需要自定义 traces：
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# 自动追踪所有 FastAPI 请求
FastAPIInstrumentor.instrument_app(app)

# 手动添加 span
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("azure_stt_call"):
    result = azure_stt_client.recognize(audio)
```

---

## 🐛 Error Reporting（错误报告）

### 用途
自动聚合和分类应用错误，比手动查 BigQuery 更方便。

### 访问
https://console.cloud.google.com/errors?project=duotopia-472708

### 使用场景

#### 1. 监控外部 API 错误
```
自动聚合：
- Azure Speech API rate limit errors (发生 15 次)
- OpenAI timeout errors (发生 8 次)
- Supabase connection errors (发生 2 次)
```

#### 2. 追踪 bug 修复进度
```
Issue #123: "学生无法提交录音"
1. 查看 Error Reporting
2. 找到相关错误组
3. 修复后标记为 "已解决"
4. 监控是否再次出现
```

---

## 🔥 Cloud Profiler（代码性能分析）

### 用途
找出代码中哪些函数最耗 CPU/内存。

### 访问
https://console.cloud.google.com/profiler?project=duotopia-472708

### 使用场景

#### 1. 优化 CPU 使用（减少 Cloud Run 成本）
```
火焰图显示：
- azure_stt_recognize: 45% CPU
- openai_translate: 30% CPU
- json_serialize: 15% CPU
- db_query: 10% CPU

优化方向：缓存 Azure/OpenAI 调用
```

#### 2. 内存泄漏检测
```
Memory Profiler 显示：
- 音档缓存占用持续增长 ⚠️
- 需要实施 LRU 清理策略
```

---

## 📝 Cloud Logging（日志查询）

### 访问
https://console.cloud.google.com/logs/query?project=duotopia-472708

### 常用查询

#### 查看 Cloud Run 错误日志
```
resource.type="cloud_run_revision"
severity>=ERROR
timestamp>="2025-12-10"
```

#### 查看特定学生的录音日志
```
resource.type="cloud_run_revision"
jsonPayload.student_id="123"
httpRequest.requestUrl=~"/api/student/123/submit"
```

---

## 📈 Cloud Monitoring（告警和仪表板）

### 访问
https://console.cloud.google.com/monitoring?project=duotopia-472708

### 建议设置的告警

#### 1. API 响应时间告警
```
触发条件: 95th percentile > 1000ms
通知方式: Email
```

#### 2. 错误率告警
```
触发条件: Error rate > 1%
通知方式: Email + Slack
```

#### 3. Cloud Run CPU 使用率告警
```
触发条件: CPU utilization > 80%
通知方式: Email
```

---

## 💰 成本监控

### 当前免费额度使用情况

| 工具 | 免费额度 | 当前用量 | 使用率 | 状态 |
|------|---------|---------|--------|------|
| Cloud Trace | 250 万 spans | 3.2 万 | 1.3% | ✅ 安全 |
| Cloud Logging | 50 GB | 3 GB | 6% | ✅ 安全 |
| Cloud Monitoring | 150 MB | 7 MB | 4.7% | ✅ 安全 |

### 扩展预估

**如果用户数 × 10（2,550 位学生）**：
- Cloud Trace: 32 万 spans（仍在免费额度内）
- Cloud Logging: 30 GB（仍在免费额度内）
- Cloud Monitoring: 70 MB（仍在免费额度内）

**结论**: 即使 10 倍增长也完全免费 ✅

---

## 🎯 最佳实践

### 性能优化流程

1. **发现问题**（Cloud Monitoring）
   - 设置告警：响应时间 > 1s
   - 收到告警通知

2. **定位瓶颈**（Cloud Trace）
   - 查看慢请求的 trace
   - 找出耗时最长的 span

3. **代码分析**（Cloud Profiler）
   - 查看函数级别的 CPU/内存使用
   - 找出优化目标

4. **实施优化**
   - 添加缓存
   - 优化查询
   - 减少外部调用

5. **验证效果**（Cloud Trace + Monitoring）
   - 对比优化前后的指标
   - 更新性能基准

### 错误处理流程

1. **自动发现**（Error Reporting）
   - 新错误自动聚合
   - Email 通知

2. **问题分析**（Cloud Logging）
   - 查看详细日志
   - 复现步骤

3. **修复验证**（Error Reporting）
   - 部署修复
   - 监控错误是否消失

---

## 📚 相关资源

- [Cloud Trace 文档](https://cloud.google.com/trace/docs)
- [Error Reporting 文档](https://cloud.google.com/error-reporting/docs)
- [Cloud Profiler 文档](https://cloud.google.com/profiler/docs)
- [Cloud Monitoring 文档](https://cloud.google.com/monitoring/docs)

---

**维护者**: 技术团队
**更新频率**: 每季度审查
