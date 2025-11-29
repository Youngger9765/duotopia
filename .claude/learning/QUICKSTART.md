# Error Reflection System - Quick Start

## System Status

✅ **ACTIVE** - Error reflection system is fully operational

## What It Does

The error reflection system automatically:
1. Detects errors in Claude's output
2. Records error patterns in a learning database
3. Suggests prevention strategies
4. Tracks improvement metrics over time
5. Generates weekly improvement reports

## How It Works

### Automatic Detection (Always On)

Every time Claude completes a turn, the `error-reflection.py` hook:
- Scans output for error keywords
- Classifies errors by severity and category
- Updates pattern database
- Increments statistics
- Triggers reflection alert if errors found

### Error Keywords Monitored

**Testing Errors**:
- "test failed", "assertion error", "tests failed", "pytest failed"

**Workflow Violations**:
- "without running tests", "without verification", "skip test"
- "hasty judgment", "premature completion", "forgot to test"

**Runtime Errors**:
- "exception", "error:", "traceback", "fatal", "crash"

**Security Issues**:
- "security vulnerability", "exposed secret", "hardcoded password"
- "sql injection", "xss vulnerability"

**And more...**

## Commands You Can Use

### Manual Reflection

When you catch an error or want to document a lesson:

```bash
/reflect [error-description]
```

**Example**:
```bash
/reflect Forgot to run tests before declaring completion
```

This will:
- Record the error in the database
- Search for similar past errors
- Generate detailed reflection report
- Suggest prevention strategies
- Update learning files

### Weekly Review

Every week (recommended Sunday):

```bash
/weekly-review
```

This generates a comprehensive report including:
- Total tasks and errors this week
- Top error patterns
- Week-over-week trends
- Improvements implemented
- Wins and celebrations
- Focus areas for next week
- Specific recommendations

You can also review past weeks:
```bash
/weekly-review 1    # Last week
/weekly-review 2    # Two weeks ago
```

## Learning Database

All learnings are stored in `.claude/learning/`:

### error-patterns.json
- Records all error patterns detected
- Tracks occurrence frequency
- Stores prevention strategies
- Links related patterns

**Current Status**: Pattern P001 - Testing error (1 occurrence)

### improvements.json
- Documents all improvements made
- Tracks effectiveness
- Measures errors prevented

**Current Status**: Empty (system just initialized)

### performance-metrics.json
- Error rate tracking
- Repeat error count
- Time-to-fix metrics
- Test coverage trends

**Current Metrics**:
- Error Rate: 0.01 (Target: < 0.02) ✅
- Repeat Errors: 0 (Target: 0) ✅
- Errors Caught: 1

### user-preferences.json
- Communication preferences
- Workflow preferences
- Quality standards

**Current Standards**:
- Min Test Coverage: 80%
- Required Checks: tests, typecheck, lint
- Security Scan: Enabled

## What to Expect

### Week 1
- System learns baseline patterns
- 10-30% error reduction
- Initial metrics established

### Month 1
- 30-50% error reduction
- 5-10 patterns identified
- Prevention strategies working

### Month 2
- 50%+ error reduction
- Repeat errors near zero
- Proactive error prevention

### Month 3+
- Continuous improvement
- Near-zero critical errors
- Self-learning system

## How to Help the System Learn

### DO
✅ Use `/reflect` when you catch errors
✅ Be specific in error descriptions
✅ Review weekly reports
✅ Implement suggested strategies
✅ Celebrate improvements

### DON'T
❌ Ignore error reflection alerts
❌ Skip weekly reviews
❌ Manually edit learning JSON files
❌ Delete historical data
❌ Dismiss small errors as unimportant

## Viewing Learning Data

### See All Patterns
```bash
cat .claude/learning/error-patterns.json | python3 -m json.tool
```

### Check Current Metrics
```bash
cat .claude/learning/performance-metrics.json | python3 -m json.tool
```

### Review Improvements
```bash
cat .claude/learning/improvements.json | python3 -m json.tool
```

## Integration with Other Agents

The error reflection system works with all other agents:

- **@general-purpose**: Checks patterns before tasks
- **@git-issue-pr-flow**: References patterns in issue analysis
- **@test-runner**: Logs test failure patterns
- **@code-reviewer**: Validates against known error patterns

## Troubleshooting

### Hook Not Running?

Check hook registration:
```bash
cat .claude/settings.local.json | grep -A 10 "Stop"
```

Should show:
```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "..error-reflection.py...",
        "timeout": 3
      }
    ]
  }
]
```

### Check Hook Errors

If the hook fails silently, check the error log:
```bash
cat .claude/learning/hook-errors.log
```

### Test Hook Manually

```bash
echo '{"output": "test failed", "prompt": "test"}' | python3 .claude/hooks/error-reflection.py
```

Should output an error detection alert.

## Getting the Most Value

1. **Let it run** - The hook runs automatically, no action needed
2. **Review alerts** - When you see error detection, read the suggestions
3. **Use /reflect** - Document errors you notice
4. **Weekly reviews** - Run `/weekly-review` every Sunday
5. **Implement strategies** - Apply the suggested prevention measures
6. **Track progress** - Watch metrics improve over time

## Privacy & Security

- All data stored locally in `.claude/learning/`
- No external transmission
- No sensitive data logged
- Project-specific learnings

## Next Steps

1. ✅ System is initialized and running
2. ⏳ Wait for first automatic error detection
3. ⏳ Try `/reflect` with a test error
4. ⏳ Run `/weekly-review` at end of first week
5. ⏳ Implement first improvement suggestions
6. ⏳ Track progress in metrics

## Support

For detailed documentation, see:
- `error-reflection-agent.md` - Full agent documentation
- `reflect.md` - Command reference
- `weekly-review.md` - Weekly review details
- `README.md` - Database documentation

---

**Status**: ✅ Active and Learning
**Initialized**: 2025-11-29
**First Pattern Detected**: 2025-11-29 (P001 - Testing error)
**Next Review**: 2025-12-01 (Sunday)
