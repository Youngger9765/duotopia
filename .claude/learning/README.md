# Error Reflection Learning Database

This directory contains the persistent learning data for the Error Reflection System.

## Files

### error-patterns.json
Tracks all error patterns detected and their statistics.

**Structure**:
- `patterns[]`: Array of error pattern objects
  - `id`: Unique pattern identifier (P001, P002, etc.)
  - `category`: Error category (workflow, testing, security, etc.)
  - `severity`: Severity level (critical, high, medium, low)
  - `description`: Pattern description
  - `occurrences`: Total number of times this pattern occurred
  - `last_seen`: Timestamp of last occurrence
  - `root_causes[]`: Identified root causes
  - `prevention_strategies[]`: Strategies to prevent this pattern
  - `related_patterns[]`: Related pattern IDs

- `statistics`: Aggregate statistics
  - `total_errors`: Total error count
  - `by_category{}`: Breakdown by category
  - `by_severity{}`: Breakdown by severity

### improvements.json
Records all improvements made based on error learnings.

**Structure**:
- `improvements[]`: Array of improvement objects
  - `id`: Unique improvement identifier (I001, I002, etc.)
  - `date`: Implementation date
  - `related_pattern`: Pattern ID this improvement addresses
  - `description`: What was improved
  - `implementation`: How it was implemented
  - `effectiveness`: Measured effectiveness percentage
  - `errors_prevented`: Count of errors prevented
  - `status`: Current status (active, inactive, superseded)

### user-preferences.json
Stores learned user preferences and project standards.

**Structure**:
- `preferences{}`: User communication and workflow preferences
- `workflows{}`: Preferred workflows and tools
- `quality_standards{}`: Quality thresholds and requirements

### performance-metrics.json
Tracks performance metrics and trends over time.

**Structure**:
- `metrics{}`: Current metric values
  - `error_rate`: Errors per task ratio
  - `repeat_errors`: Count of repeated errors
  - `time_to_fix`: Average time to resolve errors
  - `test_coverage`: Test coverage percentage

- `weekly_summary{}`: Current week summary
- `historical[]`: Historical data points

## Usage

### Automatic Updates
These files are automatically updated by:
- `error-reflection.py` hook (on error detection)
- `/reflect` command (manual reflection)
- `/weekly-review` command (weekly aggregation)

### Manual Review
You can review these files anytime to understand:
- What errors have occurred
- What patterns exist
- What improvements have been made
- How performance is trending

### Data Integrity
- Files are JSON formatted
- Auto-created if missing
- Validated on each update
- Timestamped for tracking

## Best Practices

### DO
✅ Review patterns regularly
✅ Use patterns to inform future work
✅ Celebrate improvements
✅ Track trends over time
✅ Use data to drive decisions

### DON'T
❌ Manually edit these files (use commands instead)
❌ Delete historical data
❌ Ignore recurring patterns
❌ Forget to analyze trends

## Integration

These files are used by:
- **error-reflection-agent.md**: Primary consumer of pattern data
- **agent-manager.md**: Checks patterns before task execution
- **code-reviewer.md**: Validates against known error patterns
- **test-runner.md**: Tracks test failure patterns
- **git-issue-pr-flow.md**: References patterns in issue analysis

## Maintenance

### Weekly
- Run `/weekly-review` to generate summary
- Review top patterns
- Implement suggested improvements

### Monthly
- Archive old data if needed
- Analyze long-term trends
- Update prevention strategies
- Celebrate progress

## Privacy & Security

- All data is local to this project
- No external transmission
- Sensitive information should NOT be logged
- User preferences are project-specific

## Version History

- **v1.0.0** (2025-11-29): Initial implementation
  - Basic error pattern tracking
  - Improvement recording
  - Performance metrics
  - User preferences
