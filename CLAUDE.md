# CLAUDE.md - Duotopia Project Configuration

## 🚨 CRITICAL MANDATORY RULES - READ FIRST

### **CRITICAL RULE #1**: YOU MUST USE AGENT-MANAGER
**For ANY coding task beyond simple file reading or questions, YOU MUST use:**
```
Task(subagent_type="agent-manager", prompt="[your task]", ...)
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

### **CRITICAL RULE #2**: AGENT-MANAGER DECISION TREE
The agent-manager MUST follow this EXACT routing:

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
**MANDATORY**: Route through agent-manager FIRST

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

### @agent-manager 🧠 **[MANDATORY COORDINATOR]**
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
1. YOU invoke agent-manager via Task tool
2. Agent-manager analyzes full context
3. Routes to appropriate specialized agent(s)
4. Returns consolidated results

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

## 🪝 Active Hooks

### user-prompt-submit
Suggests relevant agents/tools before task execution

### PostToolUse(Write|Edit)
Auto-formats code after modifications

### PreToolUse(Bash(git commit*))
Validates code quality before commits

### Stop
Runs quality checks at end of each turn

## 🚨 Quick Reference

### Must Follow (from agent-manager.md)
1. **Test before declaring completion** - Never hastily judge "fix complete"
2. **Use @agent-git-issue-pr-flow for issues** - All GitHub Issue operations
3. **Never commit/push without user command** - Wait for explicit command
4. **Never hardcode secrets** - Use .env files and environment variables
5. **Use feature branches, not staging** - Never commit directly to staging
6. **Check README/CLAUDE.md/package.json first** - Understand project standards

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
| Bug fixes | @agent-git-issue-pr-flow | issue, fix, #N |
| Code review | @agent-code-reviewer | review, quality |
| Testing | @agent-test-runner | test, pytest |
| Deployment | @agent-git-issue-pr-flow | deploy, staging |
| General | Let hooks suggest | - |
