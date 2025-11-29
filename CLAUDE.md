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

## 🚨 Quick Reference

### Must Follow Rules
1. **Test before declaring completion** - Never hastily judge "fix complete"
2. **Use general-purpose agent for ALL coding** - No exceptions
3. **Never commit/push without user command** - Wait for explicit command
4. **Never hardcode secrets** - Use .env files and environment variables
5. **Use feature branches, not staging** - Never commit directly to staging
6. **Check README/CLAUDE.md/package.json first** - Understand project standards
7. **Learn from every error** - Use error reflection system to prevent recurrence

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
