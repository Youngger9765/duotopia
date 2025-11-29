# /weekly-review Command

## Purpose
Generate comprehensive weekly error reflection and improvement report.

## Usage
```
/weekly-review [week-offset]
```

## Parameters
- `week-offset` (optional): Number of weeks back (default: 0 for current week)
  - `0` or omitted: Current week
  - `1`: Last week
  - `2`: Two weeks ago

## Behavior

### Data Collection
1. Aggregates all errors from specified week
2. Calculates improvement metrics
3. Identifies top error patterns
4. Measures effectiveness of prevention strategies
5. Compares week-over-week trends

### Analysis
1. Pattern frequency analysis
2. Severity distribution
3. Category breakdown
4. Repeat error identification
5. Improvement trend calculation

### Report Generation
Creates comprehensive markdown report with:
- Executive summary
- Key metrics and trends
- Top error patterns
- Improvements implemented
- Recommendations for next week
- Celebration of wins

## Output Format

```markdown
# Weekly Error Reflection Report
**Week of**: {start-date} to {end-date}
**Generated**: {timestamp}

---

## 📊 Executive Summary

**Overall Performance**: {🟢 Excellent | 🟡 Good | 🟠 Needs Improvement | 🔴 Critical}

| Metric | This Week | Last Week | Change | Target | Status |
|--------|-----------|-----------|--------|--------|--------|
| Total Tasks | {count} | {count} | {±%} | - | - |
| Errors Detected | {count} | {count} | {±%} | < 5 | {status} |
| Repeat Errors | {count} | {count} | {±%} | 0 | {status} |
| Error Rate | {rate} | {rate} | {±%} | < 0.02 | {status} |
| Test Coverage | {%} | {%} | {±%} | > 90% | {status} |

**Key Achievement**: {most significant improvement}

---

## 🎯 Top Error Patterns

### 1. Pattern P{id}: {description}
- **Category**: {category}
- **Severity**: {severity}
- **Occurrences This Week**: {count}
- **Trend**: {📈 Increasing | 📊 Stable | 📉 Decreasing}
- **Total Historical**: {count}

**Recent Instances**:
- {date}: {brief description}
- {date}: {brief description}

**Prevention Strategies Applied**:
- ✅ {strategy 1}
- ✅ {strategy 2}
- 🔄 {strategy in progress}

**Effectiveness**: {percentage}% error reduction

---

### 2. Pattern P{id}: {description}
{Same format as above}

---

### 3. Pattern P{id}: {description}
{Same format as above}

---

## ✅ Key Improvements This Week

### 1. {Improvement Title}
**Implemented**: {date}
**Related Pattern**: P{id}
**Impact**: {description of impact}

**Results**:
- Errors prevented: {count}
- Time saved: {hours/minutes}
- Quality improvement: {metric}

**Status**: {🟢 Effective | 🟡 Monitoring | 🔴 Needs Adjustment}

---

### 2. {Improvement Title}
{Same format as above}

---

## 📈 Metrics Deep Dive

### Error Rate Trend
```
Week -4: ████████░░ 0.08
Week -3: ██████░░░░ 0.06
Week -2: ████░░░░░░ 0.04
Week -1: ███░░░░░░░ 0.03
This Week: ██░░░░░░░░ 0.02 ✅ TARGET MET!
```

### Category Breakdown
| Category | Count | % of Total | Trend vs Last Week |
|----------|-------|------------|-------------------|
| Workflow | {count} | {%} | {📉/📊/📈} {±%} |
| Testing | {count} | {%} | {📉/📊/📈} {±%} |
| Security | {count} | {%} | {📉/📊/📈} {±%} |
| Logic | {count} | {%} | {📉/📊/📈} {±%} |
| Integration | {count} | {%} | {📉/📊/📈} {±%} |

### Severity Distribution
| Severity | Count | % of Total | Trend |
|----------|-------|------------|-------|
| Critical | {count} | {%} | {📉/📊/📈} |
| High | {count} | {%} | {📉/📊/📈} |
| Medium | {count} | {%} | {📉/📊/📈} |
| Low | {count} | {%} | {📉/📊/📈} |

### Repeat Errors Analysis
**Repeat Errors This Week**: {count}
**Repeat Rate**: {percentage}%

{If repeat errors > 0:}
**Patterns That Repeated**:
- P{id}: {description} - {count} times
- P{id}: {description} - {count} times

**Root Causes**:
1. {cause}
2. {cause}

**Required Actions**:
- [ ] {action}
- [ ] {action}

---

## 🎉 Wins & Celebrations

### Patterns Eliminated
- ✅ P{id}: {description} - Zero occurrences! (Previously {count}/week)
- ✅ P{id}: {description} - Eliminated for {weeks} weeks straight!

### Milestones Achieved
- ✅ {milestone description}
- ✅ {milestone description}

### Quality Improvements
- Test coverage increased to {%} (up from {%})
- Average time-to-fix reduced to {minutes} (down from {minutes})
- Zero critical errors for {days} days

---

## 🎯 Areas for Focus Next Week

### Priority 1: {Focus Area}
**Why**: {reason}
**Goal**: {specific measurable goal}
**Actions**:
1. {action}
2. {action}

### Priority 2: {Focus Area}
{Same format}

### Priority 3: {Focus Area}
{Same format}

---

## 💡 Recommendations

### Process Improvements
1. **{Recommendation}**
   - Impact: {High|Medium|Low}
   - Effort: {High|Medium|Low}
   - Priority: {High|Medium|Low}
   - Details: {explanation}

2. **{Recommendation}**
   {Same format}

### Documentation Updates
- [ ] Update {file}: {what to update}
- [ ] Add {content} to {file}
- [ ] Create {new documentation}

### Tool/Automation Additions
- [ ] {tool/automation suggestion}
- [ ] {tool/automation suggestion}

---

## 📋 Next Week Goals

**Primary Objectives**:
1. {Objective 1} - Target: {measurable target}
2. {Objective 2} - Target: {measurable target}
3. {Objective 3} - Target: {measurable target}

**Success Criteria**:
- [ ] {criterion}
- [ ] {criterion}
- [ ] {criterion}

**Stretch Goals**:
- {stretch goal}
- {stretch goal}

---

## 📚 Learning Summary

### Most Valuable Lesson
> {Quote or summary of the most important lesson learned this week}

### Knowledge Gained
- {learning point}
- {learning point}
- {learning point}

### Skills Improved
- {skill area}
- {skill area}

---

## 🔄 Continuous Improvement Actions

**Implemented This Week**:
- ✅ {action} - {result}
- ✅ {action} - {result}

**Planned for Next Week**:
- 🔄 {action}
- 🔄 {action}

**Backlog**:
- ⏳ {action}
- ⏳ {action}

---

## 📊 Historical Comparison

### 4-Week Trend
| Week | Tasks | Errors | Repeat | Rate | Coverage |
|------|-------|--------|--------|------|----------|
| -3 | {n} | {n} | {n} | {n} | {n}% |
| -2 | {n} | {n} | {n} | {n} | {n}% |
| -1 | {n} | {n} | {n} | {n} | {n}% |
| Current | {n} | {n} | {n} | {n} | {n}% |

**Overall Trend**: {📈 Improving | 📊 Stable | 📉 Declining}

---

## 🎯 Performance Against Targets

| Target | Goal | Current | Status | Notes |
|--------|------|---------|--------|-------|
| Error Rate | < 0.02 | {rate} | {🟢/🟡/🔴} | {notes} |
| Repeat Errors | 0 | {count} | {🟢/🟡/🔴} | {notes} |
| Test Coverage | > 90% | {%} | {🟢/🟡/🔴} | {notes} |
| Time to Fix | < 10 min | {min} | {🟢/🟡/🔴} | {notes} |

---

## 📝 Notes & Observations

{Any additional notes, patterns, or observations worth recording}

---

**Report Generated by**: Error Reflection Agent
**Next Review**: {date}
```

## Examples

### Example 1: Strong Week
```
/weekly-review
```

Output:
```markdown
# Weekly Error Reflection Report
**Week of**: 2025-11-25 to 2025-12-01
**Generated**: 2025-12-01 17:00:00

---

## 📊 Executive Summary

**Overall Performance**: 🟢 Excellent

| Metric | This Week | Last Week | Change | Target | Status |
|--------|-----------|-----------|--------|--------|--------|
| Total Tasks | 20 | 18 | +11% | - | - |
| Errors Detected | 2 | 5 | -60% | < 5 | 🟢 |
| Repeat Errors | 0 | 2 | -100% | 0 | 🟢 |
| Error Rate | 0.01 | 0.03 | -67% | < 0.02 | 🟢 |
| Test Coverage | 92% | 88% | +4% | > 90% | 🟢 |

**Key Achievement**: Zero repeat errors - first time ever!

---

## 🎯 Top Error Patterns

### 1. Pattern P003: Logic - Off-by-one errors
- **Category**: Logic
- **Severity**: Medium
- **Occurrences This Week**: 0
- **Trend**: 📉 Decreasing (was 2/week)
- **Total Historical**: 5

**Prevention Strategies Applied**:
- ✅ Added boundary condition checklist
- ✅ Implemented unit tests for edge cases
- ✅ Code review focus on loop conditions

**Effectiveness**: 100% - Zero occurrences for 2 weeks!

---

## 🎉 Wins & Celebrations

### Patterns Eliminated
- ✅ P001: Workflow - Premature completion - Zero occurrences!
- ✅ P003: Logic - Off-by-one errors - Eliminated for 2 weeks!

### Milestones Achieved
- ✅ First week with zero repeat errors
- ✅ Test coverage exceeded 90% target
- ✅ Error rate below target (0.01 vs 0.02)

### Quality Improvements
- Test coverage increased to 92% (up from 88%)
- Average time-to-fix reduced to 8 min (down from 12 min)
- Zero critical errors for 14 days

---

## 🎯 Areas for Focus Next Week

### Priority 1: Maintain Zero Repeat Errors
**Why**: First time achievement - want to make it permanent
**Goal**: Complete week with zero repeat errors
**Actions**:
1. Continue strict adherence to completion checklist
2. Maintain automatic test verification
3. Regular pattern review

---

**Report Generated by**: Error Reflection Agent
**Next Review**: 2025-12-08
```

### Example 2: Challenging Week
```
/weekly-review
```

Output:
```markdown
# Weekly Error Reflection Report
**Week of**: 2025-11-18 to 2025-11-24
**Generated**: 2025-11-24 17:00:00

---

## 📊 Executive Summary

**Overall Performance**: 🟠 Needs Improvement

| Metric | This Week | Last Week | Change | Target | Status |
|--------|-----------|-----------|--------|--------|--------|
| Total Tasks | 15 | 18 | -17% | - | - |
| Errors Detected | 8 | 5 | +60% | < 5 | 🔴 |
| Repeat Errors | 3 | 2 | +50% | 0 | 🔴 |
| Error Rate | 0.05 | 0.03 | +67% | < 0.02 | 🔴 |
| Test Coverage | 85% | 88% | -3% | > 90% | 🟡 |

**Key Challenge**: Repeat errors increased - need immediate action

---

## 🎯 Top Error Patterns

### 1. Pattern P001: Workflow - Premature completion
- **Category**: Workflow
- **Severity**: Critical
- **Occurrences This Week**: 3
- **Trend**: 📈 Increasing (was 1/week)
- **Total Historical**: 8

**Recent Instances**:
- 2025-11-23: Declared fix complete without running tests
- 2025-11-22: Skipped verification step
- 2025-11-20: Hasty completion judgment

**Prevention Strategies Applied**:
- 🔄 Added completion checklist (not consistently followed)
- 🔄 Test verification reminder (being ignored)

**Effectiveness**: 0% - Pattern getting worse

**CRITICAL**: This pattern is accelerating. Requires immediate systemic fix.

---

## 🎯 Areas for Focus Next Week

### Priority 1: Eliminate Premature Completion Pattern
**Why**: Critical recurring issue damaging quality and trust
**Goal**: Zero occurrences of P001
**Actions**:
1. Make test verification MANDATORY (not optional)
2. Add automatic test run before any completion claim
3. Implement pre-completion validation hook
4. Review every completion with checklist

### Priority 2: Increase Test Coverage
**Why**: Dropped below target
**Goal**: Return to 90%+ coverage
**Actions**:
1. Add tests for all new features
2. Fill gaps in existing coverage
3. Focus on critical paths

---

## 💡 Recommendations

### Process Improvements
1. **Mandatory Test Verification**
   - Impact: High
   - Effort: Low
   - Priority: Critical
   - Details: Never allow completion without test verification

2. **Automatic Pre-Completion Validation**
   - Impact: High
   - Effort: Medium
   - Priority: High
   - Details: Add hook to validate before completion

---

**Report Generated by**: Error Reflection Agent
**Next Review**: 2025-12-01

**IMMEDIATE ACTION REQUIRED**: Pattern P001 needs systemic fix NOW.
```

## Integration

### Automatic Scheduling
- Weekly reviews auto-generated every Sunday
- Notification sent to user
- Report saved to learning directory
- Trends tracked over time

### Data Sources
- `error-patterns.json` - Pattern history
- `improvements.json` - Improvement tracking
- `performance-metrics.json` - Metrics data
- Git commit history
- Test coverage reports

### Follow-up Actions
Generated report includes:
- Actionable recommendations
- Specific next-week goals
- Documentation updates needed
- Process improvements required

## Best Practices

### Review Process
1. Read full report carefully
2. Celebrate wins and progress
3. Identify critical issues
4. Prioritize next week's focus
5. Implement recommended improvements
6. Update relevant documentation

### Making Reviews Valuable
- Be honest about challenges
- Celebrate even small wins
- Focus on trends, not single incidents
- Use data to drive decisions
- Make reports actionable
- Track progress over time

## See Also
- `/reflect` - Manual error reflection
- `error-reflection-agent.md` - Full agent documentation
- `performance-metrics.json` - Raw metrics data
