# /reflect Command

## Purpose
Manually trigger error reflection and learning analysis.

## Usage
```
/reflect [error-description]
```

## Parameters
- `error-description` (optional): Description of the error to analyze

## Behavior

### Without Description
Analyzes recent interaction for errors and patterns:
1. Reviews last conversation turn
2. Detects any error patterns
3. Checks against historical patterns
4. Provides reflection and recommendations

### With Description
Performs targeted error analysis:
1. Records the described error
2. Classifies by severity and category
3. Searches for similar past errors
4. Generates comprehensive reflection report
5. Updates error patterns database
6. Suggests prevention strategies

## Output Format

```markdown
## Error Reflection Report

**Error ID**: E{timestamp}
**Severity**: {CRITICAL|HIGH|MEDIUM|LOW}
**Category**: {category}

### What Happened
{Clear description of the error}

### Root Cause Analysis
1. {Primary root cause}
2. {Contributing factors}
3. {Pattern recognition}

### Impact Assessment
- {Impact on user}
- {Impact on project}
- {Impact on trust/quality}

### Similar Past Errors
- Pattern P{id}: {description} ({occurrences} times)
- Pattern P{id}: {description} ({occurrences} times)

### Lessons Learned
1. {Specific lesson}
2. {Specific lesson}
3. {Specific lesson}

### Prevention Strategies

**Immediate Actions**:
- [ ] {Action item 1}
- [ ] {Action item 2}

**Short-term Improvements**:
- [ ] {Improvement 1}
- [ ] {Improvement 2}

**Long-term Changes**:
- [ ] {Systemic change 1}
- [ ] {Systemic change 2}

### Updated Prevention Rules
- ✅ {New rule added to prevent this error}
- ✅ {Updated workflow/checklist}
- ✅ {Enhanced validation}

### Metrics Update
- Total occurrences of this pattern: {count}
- Last occurred: {date}
- Trend: {improving|stable|worsening}
- Prevention effectiveness: {percentage}%
```

## Examples

### Example 1: Workflow Error
```
/reflect Declared bug fix complete without running tests
```

Output:
```markdown
## Error Reflection Report

**Error ID**: E20251129103000
**Severity**: CRITICAL
**Category**: Workflow

### What Happened
Declared bug fix complete without running the test suite. Tests were actually failing.

### Root Cause Analysis
1. Hasty judgment after seeing code change
2. Skipped mandatory verification step
3. Pattern: 3rd occurrence of premature completion

### Impact Assessment
- User had to correct and point out the issue
- Wasted time on incomplete fix
- Damaged trust and credibility
- Delayed actual bug resolution

### Similar Past Errors
- Pattern P001: Workflow - Premature completion (3 times)
- Pattern P002: Workflow - Skipped verification (2 times)

### Lessons Learned
1. Code change ≠ bug fixed. Must verify with tests.
2. Completion checklist is MANDATORY, not optional
3. This pattern is recurring - need systemic fix

### Prevention Strategies

**Immediate Actions**:
- [x] Run full test suite now: `npm run test:api:all`
- [x] Check test results before any completion claim

**Short-term Improvements**:
- [ ] Add "Test Status: ✅ PASS" to all completion messages
- [ ] Update agent-manager.md completion checklist
- [ ] Add test verification to error-reflection hook

**Long-term Changes**:
- [ ] Implement automatic test run before completion
- [ ] Add test-status check to all agent workflows
- [ ] Create pre-completion validation hook

### Updated Prevention Rules
- ✅ NEVER declare completion without test verification
- ✅ ALWAYS show test results in completion message
- ✅ Added to agent-manager.md: "Test Status Check" step

### Metrics Update
- Total occurrences of this pattern: 3
- Last occurred: 2025-11-29
- Trend: worsening (was 1/week, now 2/week)
- Prevention effectiveness: 0% (needs immediate action)

**ACTION REQUIRED**: This is a critical recurring pattern. Implementing systemic prevention now.
```

### Example 2: Security Issue
```
/reflect Found hardcoded API key in code
```

Output:
```markdown
## Error Reflection Report

**Error ID**: E20251129104500
**Severity**: CRITICAL
**Category**: Security

### What Happened
API key was hardcoded directly in source code instead of using environment variables.

### Root Cause Analysis
1. Convenience over security
2. Missing security checklist validation
3. No pre-commit security scan

### Impact Assessment
- Potential security breach if code pushed to public repo
- API key exposure risk
- Violation of security best practices
- Could lead to unauthorized access

### Similar Past Errors
- Pattern P010: Security - Exposed secrets (1 time)

### Lessons Learned
1. NEVER hardcode secrets - always use .env
2. Security checks must be automatic, not manual
3. Need pre-commit security validation

### Prevention Strategies

**Immediate Actions**:
- [x] Remove hardcoded API key
- [x] Add to .env file
- [x] Update .gitignore
- [x] Rotate API key (security best practice)

**Short-term Improvements**:
- [ ] Add pre-commit hook for secret scanning
- [ ] Update code-reviewer.md with security checklist
- [ ] Add automatic .env validation

**Long-term Changes**:
- [ ] Implement automatic secret detection in CI/CD
- [ ] Add security training to agent workflows
- [ ] Create security-first coding guidelines

### Updated Prevention Rules
- ✅ ALWAYS check for hardcoded secrets before commit
- ✅ ALWAYS use environment variables for sensitive data
- ✅ Added to security checklist: "Secret scanning"

### Metrics Update
- Total occurrences of this pattern: 1
- Last occurred: 2025-11-29
- Trend: new pattern
- Prevention effectiveness: N/A (first occurrence)

**ACTION REQUIRED**: Implementing pre-commit security scan to prevent recurrence.
```

## Integration with Error Reflection System

### Automatic Updates
The `/reflect` command automatically:
1. Updates `error-patterns.json` with new pattern data
2. Records improvement in `improvements.json`
3. Updates `performance-metrics.json` metrics
4. Triggers prevention strategy implementation

### Pattern Matching
- Searches historical patterns for similar errors
- Calculates recurrence frequency
- Identifies trends (improving/worsening)
- Suggests proven prevention strategies

### Learning Persistence
- All reflections saved to learning database
- Patterns available to all agents
- Continuous improvement tracking
- Effectiveness measurement

## Best Practices

### When to Use
- ✅ After any error or mistake
- ✅ When user provides correction
- ✅ After test failures
- ✅ When workflow violated
- ✅ After security issue detected
- ✅ When performance degraded

### How to Use Effectively
1. Be specific in error description
2. Include context and conditions
3. Review generated reflection carefully
4. Implement suggested prevention strategies
5. Update relevant documentation
6. Track improvement over time

### Common Patterns to Reflect On
- Premature completion declarations
- Skipped verification steps
- Test failures
- Security vulnerabilities
- Performance issues
- Code quality problems
- Workflow violations
- Integration failures

## See Also
- `/weekly-review` - Generate weekly reflection report
- `error-reflection-agent.md` - Full agent documentation
- `agent-manager.md` - Completion checklist
- `code-reviewer.md` - Quality and security checks
