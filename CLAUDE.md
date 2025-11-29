# CLAUDE.md - Duotopia Project Configuration

## 🚨 CRITICAL MANDATORY RULES - READ FIRST

### **CRITICAL RULE #1**: YOU MUST USE GENERAL-PURPOSE AGENT
**For ANY coding task beyond simple file reading or questions, YOU MUST use:**
```
Task(subagent_type="general-purpose", prompt="[your task]", ...)
```

**NO EXCEPTIONS** for these tasks:
- Writing/editing ANY code
- Running tests
- Fixing bugs
- Implementing features
- Code review
- Deployments
- Git operations
- Performance optimization
- Security checks

**ONLY EXCEPTIONS** (direct tool use allowed):
- Reading a single file (`Read` tool)
- Answering conceptual questions
- Explaining existing code

### **CRITICAL RULE #2**: GENERAL-PURPOSE AGENT ROUTING
The general-purpose agent MUST handle these tasks:

```
If task contains "test" or "测试" → test-runner
If task contains "review" or "审查" → code-reviewer
If task contains "#" or "issue" or "bug" → git-issue-pr-flow
If task contains "deploy" or "部署" → git-issue-pr-flow
If task contains "security" or "安全" → code-reviewer (security mode)
If task is complex/multi-step → Combine multiple agents
Otherwise → Analyze context and choose
```

### **CRITICAL RULE #3**: NO DIRECT EXECUTION
**FORBIDDEN**: Using Edit/Write/Bash tools directly for coding tasks
**MANDATORY**: Route through general-purpose agent FIRST

## 📚 Documentation Structure

### Agent Documentation (Primary Reference)
- **[agent-manager.md](./.claude/agents/agent-manager.md)** - 核心原则、验证标准、完成检查清单
- **[git-issue-pr-flow.md](./.claude/agents/git-issue-pr-flow.md)** - PDCA 工作流程、Git 操作、Issue/PR 管理
- **[test-runner.md](./.claude/agents/test-runner.md)** - 测试指南、覆盖率要求、最佳实践
- **[code-reviewer.md](./.claude/agents/code-reviewer.md)** - 代码审查、安全检查、性能分析
- **[task-router.md](./.claude/agents/task-router.md)** - 任务路由助手

### Project Documents
- **[PRD.md](./PRD.md)** - 产品需求文档
- **[CICD.md](./CICD.md)** - 部署与 CI/CD
- **[TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)** - 详细测试指南
- **[DEPLOYMENT_STATUS.md](./docs/DEPLOYMENT_STATUS.md)** - 部署状态

## 🤖 MANDATORY AGENT SYSTEM

### @general-purpose 🧠 **[MANDATORY FOR ALL CODING]**
**CRITICAL**: This is NOT optional. YOU MUST use this for ALL coding tasks.

**Automatic Invocation Required For**:
- ✅ ANY code changes (create/edit/delete)
- ✅ ALL test operations
- ✅ ANY bug fixes
- ✅ ALL feature implementations
- ✅ ANY deployments
- ✅ ALL Git operations
- ✅ ANY performance/security tasks

**How It Works**:
1. YOU invoke general-purpose agent via Task tool
2. Agent analyzes full context
3. Executes task with best practices
4. Returns complete results

**ENFORCEMENT**: If you try to use Edit/Write/Bash directly for coding, YOU ARE VIOLATING PROJECT RULES

### @agent-git-issue-pr-flow
**Auto-trigger keywords**: issue, fix, bug, #N, 部署, staging, approval
- Complete PDCA workflow management
- TDD enforcement
- Per-Issue Test Environment
- AI-powered approval detection

### @agent-code-reviewer
**Auto-trigger keywords**: review, check code, quality
- Security vulnerability scanning
- Performance analysis
- Best practices validation
- Code smell detection

### @agent-test-runner
**Auto-trigger keywords**: test, pytest, npm test
- Automatic test type detection
- Coverage reporting
- Failure analysis
- Performance benchmarking

### @agent-task-router
**Internal use only** - AI-powered task routing assistant
- Suggests appropriate agents based on task
- Lightweight Haiku model for efficiency

### @agent-error-reflection 🔍 **[CONTINUOUS LEARNING]**
**Auto-trigger**: Errors, test failures, user corrections
- Automatic error detection and pattern recognition
- Learning from mistakes to prevent recurrence
- Performance metrics tracking
- Weekly improvement reports

**Commands**:
- `/reflect [error-description]` - Manual error reflection
- `/weekly-review` - Generate weekly improvement report

**Learning Files**:
- `.claude/learning/error-patterns.json` - Error pattern database
- `.claude/learning/improvements.json` - Improvement tracking
- `.claude/learning/performance-metrics.json` - Performance metrics
- `.claude/learning/user-preferences.json` - User preferences

**Key Features**:
- Never repeat the same mistake twice
- Automatic pattern detection
- Proactive error prevention
- Continuous improvement tracking
- Data-driven decision making

## 🪝 Active Hooks

### user-prompt-submit
Suggests relevant agents/tools before task execution

### PostToolUse(Write|Edit)
Auto-formats code after modifications

### PreToolUse(Bash(git commit*))
Validates code quality before commits

### Stop
Runs quality checks at end of each turn

### error-reflection.py (Stop hook)
Automatically detects errors and triggers learning reflection

## 🤖 @claude GitHub Bot 使用指南

### 如何让 @claude 遵循项目流程

当在 GitHub Issue 中使用 @claude bot 时，必须提供明确指示以确保遵循 git-issue-pr-flow 流程。

#### ✅ 正确的指示格式

```
@claude 请按照以下步骤修复此 Issue：

1. **使用固定分支**: 在 `claude/issue-26` 分支上工作（不要创建带时间戳的新分支）
2. **检查既有分支**: 如果分支已存在，请先 pull 最新代码再修改
3. **遵循 PDCA 流程**:
   - Plan: 分析问题根因，提出修复方案
   - Do: 实施修复并编写测试
   - Check: 推送到分支触发 Per-Issue Test Environment
   - Act: 等待测试反馈，必要时迭代改进
4. **不要自动创建 PR**: 推送代码后等待人工审查再创建 PR

参考文档: .claude/agents/git-issue-pr-flow.md
```

#### ❌ 错误的指示（会导致分支堆积）

```
@claude 请修复此问题
```

这会导致 @claude 创建带时间戳的新分支（如 `claude/issue-26-20251129-1639`），每次修复都会堆积新分支。

#### 🔑 关键要点

1. **明确指定分支名**: 告诉 @claude 使用 `claude/issue-XX` 格式
2. **要求检查既有分支**: 避免重复创建
3. **引用 git-issue-pr-flow.md**: 确保 @claude 知道遵循 PDCA 流程
4. **分步骤指示**: 明确每个阶段的产出要求

### @claude 分支清理

如果 @claude 已经创建了多个带时间戳的分支，可以手动清理：

```bash
# 列出所有 claude/issue-XX-* 分支
git fetch --prune
git branch -r | grep "claude/issue-26-"

# 删除多余的旧分支（保留最新的）
git push origin --delete claude/issue-26-20251129-1546
git push origin --delete claude/issue-26-20251129-1613
git push origin --delete claude/issue-26-20251129-1626
```

当 Issue 关闭时，cleanup workflow 会自动删除所有相关分支。

### 最佳实践示例

#### 初次修复
```
@claude 请在 `claude/issue-26` 分支上修复此 Issue。

请按照 .claude/agents/git-issue-pr-flow.md 中的 PDCA 流程：
1. Plan: 分析所有留言反馈，理解需求（保留上方提示，移除下方重复提示）
2. Do: 实施修复
3. Check: 推送到 claude/issue-26 触发部署
4. Act: 等待测试反馈

不要创建带时间戳的分支，不要自动创建 PR。
```

#### 后续迭代
```
@claude 请在既有的 `claude/issue-26` 分支上继续修复。

根据最新反馈：
- Preview 环境也要隐藏测试提示
- 检查代码是否 clean

请 pull 最新代码后再修改，然后推送触发重新部署。
```

## 🚨 Quick Reference

### Must Follow Rules
1. **Test before declaring completion** - Never hastily judge "fix complete"
2. **Use general-purpose agent for ALL coding** - No exceptions
3. **Never commit/push without user command** - Wait for explicit command
4. **Never hardcode secrets** - Use .env files and environment variables
5. **Use feature branches, not staging** - Never commit directly to staging
6. **Check README/CLAUDE.md/package.json first** - Understand project standards
7. **Learn from every error** - Use error reflection system to prevent recurrence
8. **指导 @claude bot** - 在 Issue 中使用 @claude 时，明确指定使用固定分支和遵循 PDCA 流程

### Command Shortcuts
```bash
# Testing
npm run test:api:all
npm run typecheck
npm run lint
npm run build

# Git workflow (via agent)
create-feature-fix <issue> <desc>
deploy-feature <issue>
update-release-pr
check-approvals
```

## 🎯 Agent Selection Matrix

| Task Type | Recommended Agent | Trigger Words |
|-----------|------------------|---------------|
| ALL Coding Tasks | @general-purpose | ALL coding keywords |
| Bug fixes | @general-purpose → git-issue-pr-flow | issue, fix, #N |
| Code review | @code-reviewer | review, quality |
| Testing | @test-runner | test, pytest |
| Deployment | @general-purpose → git-issue-pr-flow | deploy, staging |
| Error reflection | @error-reflection | /reflect, /weekly-review |
