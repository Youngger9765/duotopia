# Load Testing Suite for Audio Upload
## Comprehensive Performance Testing for Duotopia

This directory contains a complete load testing framework for testing audio upload functionality under high concurrency across different environments.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running Tests](#running-tests)
6. [Test Scenarios](#test-scenarios)
7. [Monitoring & Results](#monitoring--results)
8. [Environment-Specific Testing](#environment-specific-testing)
9. [Interpreting Results](#interpreting-results)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

This load testing suite helps you:
- **Identify performance bottlenecks** in audio upload workflow
- **Determine maximum concurrent user capacity** for each environment
- **Compare performance** between PROD (VM) and Staging (Cloud Run)
- **Validate optimizations** after configuration changes
- **Prevent production incidents** by testing before deployment

### Architecture

```
┌─────────────────────┐
│   Locust Runner     │  Simulates concurrent users
│  (locustfile.py)    │
└──────────┬──────────┘
           │
           ├─► POST /api/students/upload-recording
           ├─► GET  /api/students/profile
           └─► GET  /api/students/assignments

           ↓

┌─────────────────────┐
│  Target Environment │
│  (Staging/Prod/VM)  │
└──────────┬──────────┘
           │
           ├─► FastAPI Backend
           ├─► GCS Storage
           └─► PostgreSQL (Supabase)

           ↓

┌─────────────────────┐
│  Monitoring Tools   │
│  - Database stats   │
│  - Response times   │
│  - Error tracking   │
└─────────────────────┘
```

### Key Metrics Tracked

- **Response Time**: p50, p95, p99 latencies
- **Throughput**: Requests per second (RPS)
- **Error Rate**: Failed uploads percentage
- **Database**: Active connections, slow queries, locks
- **Resource Usage**: CPU, memory (if monitoring enabled)

---

## Quick Start

### Prerequisites

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Generate test audio samples
python generate_audio_samples.py

# 3. Set environment variables (see Configuration section)
export TEST_ENV=staging
export TEST_STUDENT_EMAIL=your-test-student@example.com
export TEST_STUDENT_PASSWORD=your-password
```

### Run Your First Test

```bash
# Normal load test (20 users) against staging with web UI
./run_tests.sh --env staging --scenario normal --web

# Open browser to http://localhost:8089 and click "Start"
```

### Quick Headless Test

```bash
# Run 5-minute test without web UI
./run_tests.sh --env staging --scenario normal --headless
```

---

## Installation

### Step 1: Install System Dependencies

**macOS**:
```bash
brew install ffmpeg  # For generating audio samples
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Step 2: Install Python Dependencies

```bash
cd backend/tests/load_testing
pip install -r requirements.txt
```

**Required packages**:
- `locust>=2.20.0` - Load testing framework
- `psycopg2-binary>=2.9.0` - PostgreSQL monitoring
- `requests>=2.31.0` - HTTP client

### Step 3: Generate Test Audio Files

```bash
python generate_audio_samples.py
```

This creates 4 audio samples in `audio_samples/`:
- `small_3sec_50kb.webm` - 3 seconds, ~50KB
- `medium_10sec_200kb.webm` - 10 seconds, ~200KB
- `large_20sec_500kb.webm` - 20 seconds, ~500KB
- `max_30sec_2mb.webm` - 30 seconds, ~2MB

**Note**: If ffmpeg is not installed, the script generates dummy binary files instead (sufficient for load testing).

### Step 4: Configure Environment Variables

Create a `.env` file or export variables:

```bash
# Staging environment
export TEST_ENV=staging
export STAGING_BASE_URL=https://duotopia-staging-backend-xxx.run.app
export TEST_STUDENT_EMAIL=test-student@duotopia.co
export TEST_STUDENT_PASSWORD=test-password
export TEST_TEACHER_EMAIL=test-teacher@duotopia.co
export TEST_TEACHER_PASSWORD=test-password
export STAGING_DATABASE_URL=postgresql://user:pass@host:5432/db

# Production environment (if testing)
export PRODUCTION_BASE_URL=https://duotopia.co
export PROD_TEST_STUDENT_EMAIL=load-test-student@duotopia.co
export PROD_TEST_STUDENT_PASSWORD=load-test-password
```

---

## Configuration

### Environment Configuration (`config.py`)

Three environments are supported:

#### 1. Staging (Cloud Run)
- **Purpose**: Safe testing environment
- **Infrastructure**: Google Cloud Run, 0.5 CPU, 256MB RAM
- **Database**: Supabase Staging
- **Concurrency**: 1 request/instance, auto-scaling

#### 2. Production (VM)
- **Purpose**: Real-world capacity testing
- **Infrastructure**: Google Compute Engine VM
- **Database**: Supabase Production
- **Risk**: Impacts real users ⚠️

#### 3. Local
- **Purpose**: Development and debugging
- **Infrastructure**: Local Docker containers
- **Database**: Local PostgreSQL

### Test Scenarios

Pre-configured scenarios in `config.py`:

| Scenario | Users | Spawn Rate | Duration | Purpose |
|----------|-------|------------|----------|---------|
| **normal** | 20 | 2/sec | 5 min | Typical usage |
| **peak** | 50 | 5/sec | 5 min | High traffic period |
| **stress** | 100 | 10/sec | 10 min | Beyond normal capacity |
| **spike** | 50 | 50/sec | 3 min | Sudden burst |
| **endurance** | 30 | 3/sec | 30 min | Sustained load |
| **breaking** | 200 | 20/sec | 10 min | Find system limits |

### Custom Configuration

Override scenario defaults:

```bash
./run_tests.sh --env staging --users 75 --rate 15 --time 8m --headless
```

---

## Running Tests

### Method 1: Web UI (Interactive)

```bash
./run_tests.sh --env staging --scenario normal --web
```

1. Open browser to `http://localhost:8089`
2. Enter number of users and spawn rate
3. Click "Start"
4. Monitor real-time charts
5. Stop test when desired

**Advantages**:
- Interactive control
- Real-time charts
- Manual test duration control

### Method 2: Headless (Automated)

```bash
./run_tests.sh --env staging --scenario stress --headless
```

**Advantages**:
- Automated execution
- Consistent test duration
- CI/CD integration ready
- CSV and HTML reports

### Direct Locust Commands

Advanced users can run Locust directly:

```bash
# Export environment
export TEST_ENV=staging

# Run with web UI
locust -f locustfile.py --host https://duotopia-staging-backend-xxx.run.app

# Run headless
locust -f locustfile.py \
    --headless \
    --users 50 \
    --spawn-rate 5 \
    --run-time 5m \
    --html results/report.html \
    --csv results/data
```

---

## Test Scenarios

### Scenario 1: Normal Load (Baseline)

**Purpose**: Establish baseline performance

```bash
./run_tests.sh --env staging --scenario normal --headless
```

**Expected Results**:
- Success rate: >95%
- p95 latency: <10s
- No database connection issues

**What to Look For**:
- Average response time
- Resource usage patterns
- No errors under typical load

### Scenario 2: Peak Load

**Purpose**: Test high-traffic periods (e.g., after homework assignment)

```bash
./run_tests.sh --env staging --scenario peak --headless
```

**Expected Results**:
- Success rate: >90%
- p95 latency: <15s
- Some queueing acceptable

**What to Look For**:
- Degradation compared to normal load
- Auto-scaling behavior (Cloud Run)
- Database connection count

### Scenario 3: Stress Test

**Purpose**: Push system beyond normal capacity

```bash
./run_tests.sh --env staging --scenario stress --headless
```

**Expected Results**:
- Success rate: >80%
- p95 latency: <30s
- Some failures expected

**What to Look For**:
- Where does system start failing?
- What fails first? (DB, GCS, CPU, memory)
- Error types (429, 503, timeouts)

### Scenario 4: Spike Test

**Purpose**: Simulate sudden traffic burst

```bash
./run_tests.sh --env staging --scenario spike --headless
```

**Expected Results**:
- Initial spike may cause high latency
- System recovers after auto-scaling
- Success rate >85% overall

**What to Look For**:
- Cold start latency (Cloud Run)
- Time to scale up
- Queue depth during spike

### Scenario 5: Endurance Test

**Purpose**: Validate stability over time

```bash
./run_tests.sh --env staging --scenario endurance --headless
```

**Expected Results**:
- Consistent performance over 30 minutes
- No memory leaks
- No connection pool leaks

**What to Look For**:
- Performance degradation over time
- Memory growth
- Database connection stability

### Scenario 6: Breaking Point

**Purpose**: Find absolute system limits

```bash
./run_tests.sh --env staging --scenario breaking --headless
```

**Expected Results**:
- System fails at some point
- Identify exact failure threshold
- Document failure mode

**What to Look For**:
- Maximum concurrent users before failure
- What breaks first?
- How does system fail? (graceful or catastrophic)

---

## Monitoring & Results

### Real-Time Monitoring

While test is running:

1. **Locust Web UI** (if using --web):
   - Charts, statistics, failures
   - `http://localhost:8089`

2. **Database Monitoring**:
   ```bash
   # In separate terminal
   python -c "
   from monitoring import DatabaseMonitor
   import asyncio
   from config import get_config

   config = get_config('staging')
   monitor = DatabaseMonitor(config.database_url)

   async def run():
       await monitor.monitor_continuously(interval_seconds=5)

   asyncio.run(run())
   "
   ```

3. **Backend Logs**:
   ```bash
   # Cloud Run logs (staging)
   gcloud logging read "resource.type=cloud_run_revision \
       AND resource.labels.service_name=duotopia-staging-backend" \
       --limit 50 --format json

   # VM logs (production)
   ssh vm-prod "tail -f /var/log/duotopia-backend/app.log"
   ```

### Results Output

After test completes, find results in:

```
results/
└── staging_normal_20251210_143022/
    ├── report.html          # Visual report with charts
    ├── results_stats.csv    # Request statistics
    ├── results_failures.csv # Failure details
    └── results_stats_history.csv  # Time-series data
```

### Key Files

**report.html**: Open in browser for visual analysis
- Response time charts
- RPS over time
- Failure distribution
- Percentile graphs

**results_stats.csv**: CSV with aggregated metrics
- Request count
- Failure count
- Min/max/avg/median response times
- Percentiles (50th, 66th, 75th, 80th, 90th, 95th, 98th, 99th)
- Requests per second

**results_failures.csv**: Details of each failure
- Timestamp
- HTTP method and endpoint
- Status code
- Error message

---

## Environment-Specific Testing

### Testing Staging (Recommended First)

**Advantages**:
- Safe to test aggressively
- No real user impact
- Same architecture as preview environments

**Limitations**:
- Lower resources (0.5 CPU, 256MB RAM)
- Different performance characteristics
- Cold start latency (scale-to-zero)

**Recommended Tests**:
1. Start with normal load
2. Gradually increase to peak
3. Run spike test to test auto-scaling
4. Endurance test for stability

```bash
# Run all staging tests
./run_tests.sh --env staging --scenario normal --headless
./run_tests.sh --env staging --scenario peak --headless
./run_tests.sh --env staging --scenario spike --headless
./run_tests.sh --env staging --scenario endurance --headless
```

### Testing Production (Caution Required)

**⚠️ WARNINGS**:
- Impacts real users
- Creates real data in database
- Uses real GCS storage (costs)
- May trigger rate limiting

**Best Practices**:
1. **Time Selection**: Test during low-traffic hours (late night, early morning)
2. **Gradual Ramp-Up**: Start small, increase slowly
3. **Monitor Real Users**: Watch for impact on legitimate traffic
4. **Rollback Plan**: Be ready to stop test immediately
5. **Communication**: Notify team before testing

**Recommended Approach**:
```bash
# Start conservatively
./run_tests.sh --env production --users 10 --rate 2 --time 3m --headless

# If successful, increase gradually
./run_tests.sh --env production --users 20 --rate 3 --time 5m --headless
./run_tests.sh --env production --scenario normal --headless
```

**Stop Immediately If**:
- Error rate exceeds 10%
- Real user complaints received
- Database connections exceed 80% of limit
- Any critical errors in logs

---

## Interpreting Results

### Success Criteria

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Success Rate | >95% | 90-95% | <90% |
| p95 Latency | <5s | 5-10s | >10s |
| p99 Latency | <10s | 10-15s | >15s |
| Error Rate | <2% | 2-5% | >5% |
| RPS | Match target | 80% of target | <80% |

### Common Failure Patterns

#### 1. Database Connection Pool Exhaustion

**Symptoms**:
- Error: "QueuePool limit exceeded"
- Error rate spikes at specific concurrency (e.g., 20 users)
- Slow queries pile up

**Solution**:
- Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
- Verify DB connection release in code
- Check for connection leaks

#### 2. GCS Upload Timeouts

**Symptoms**:
- Errors: "Connection timeout", "Upload failed"
- High latency (>10s) even at low concurrency
- Works fine locally but fails in cloud

**Solution**:
- Check GCS authentication
- Verify network connectivity
- Consider increasing timeout
- Wrap GCS upload in thread pool

#### 3. Cloud Run Cold Starts

**Symptoms**:
- First requests very slow (>5s)
- Latency improves after warm-up
- Spikes cause extreme latency

**Solution**:
- Set `min-instances=1` to avoid scale-to-zero
- Accept cold start latency during spike tests
- Consider higher CPU allocation for faster starts

#### 4. Memory Exhaustion (OOM)

**Symptoms**:
- Container restarts during test
- Error 503 "Service Unavailable"
- Memory usage climbs steadily

**Solution**:
- Increase container memory allocation
- Check for memory leaks in code
- Reduce file upload buffer size
- Implement streaming upload

#### 5. Rate Limiting

**Symptoms**:
- Error 429 "Too Many Requests"
- Consistent at specific RPS threshold
- Affects all users equally

**Solution**:
- Check rate limit configuration
- Increase limits if intentional
- Implement exponential backoff in client

### Comparing Staging vs Production

**Expected Differences**:

| Metric | Staging (Cloud Run) | Production (VM) |
|--------|---------------------|-----------------|
| Max Users | ~10-20 | ~50-100 |
| p95 Latency | Higher (5-15s) | Lower (3-8s) |
| Throughput | Lower (5-10 RPS) | Higher (20-50 RPS) |
| Cold Start | Yes (~2-5s) | No |
| Auto-scaling | Yes | No |
| Failure Mode | 503 (overload) | Slow degradation |

**Interpretation**:
- Staging will always be slower (by design)
- Focus on **relative performance** not absolute numbers
- Staging identifies code issues, production identifies capacity

---

## Troubleshooting

### Problem: Authentication Failures

**Symptoms**: "Authentication failed" errors, no requests succeed

**Solutions**:
1. Verify credentials:
   ```bash
   echo $TEST_STUDENT_EMAIL
   echo $TEST_STUDENT_PASSWORD
   ```

2. Test login manually:
   ```bash
   curl -X POST https://your-backend/api/students/validate \
       -H "Content-Type: application/json" \
       -d '{"email":"test@example.com","password":"password"}'
   ```

3. Create test accounts if needed:
   ```sql
   -- In database
   INSERT INTO students (email, name, password_hash)
   VALUES ('test@example.com', 'Test Student', '<bcrypt-hash>');
   ```

### Problem: No Test Data (Assignment/Content IDs)

**Symptoms**: "Assignment not found" errors

**Solutions**:
1. Set explicit IDs:
   ```bash
   export TEST_ASSIGNMENT_ID=123
   export TEST_CONTENT_ITEM_ID=456
   ```

2. Create test assignment via API or admin panel

3. Use existing assignment ID from database:
   ```sql
   SELECT sa.id as assignment_id, ci.id as content_item_id
   FROM student_assignments sa
   JOIN assignment_contents ac ON ac.student_assignment_id = sa.id
   JOIN contents c ON c.id = ac.content_id
   JOIN content_items ci ON ci.content_id = c.id
   WHERE sa.student_id = <test_student_id>
   LIMIT 1;
   ```

### Problem: Database Monitoring Fails

**Symptoms**: No connection stats, monitoring errors

**Solutions**:
1. Verify database URL:
   ```bash
   echo $STAGING_DATABASE_URL
   ```

2. Check connection:
   ```bash
   psql "$STAGING_DATABASE_URL" -c "SELECT 1"
   ```

3. Grant pg_stat_activity permissions:
   ```sql
   GRANT pg_read_all_stats TO your_user;
   ```

### Problem: Locust Won't Start

**Symptoms**: "Command not found" or import errors

**Solutions**:
1. Verify installation:
   ```bash
   pip list | grep locust
   locust --version
   ```

2. Reinstall dependencies:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Check Python path:
   ```bash
   which python
   python --version  # Should be 3.11+
   ```

### Problem: Results Not Saved

**Symptoms**: No CSV/HTML files in results directory

**Solutions**:
1. Check results directory exists:
   ```bash
   mkdir -p results
   ```

2. Verify write permissions:
   ```bash
   chmod -R 755 results/
   ```

3. Use absolute path in command:
   ```bash
   locust --csv $PWD/results/test --html $PWD/results/report.html
   ```

---

## Best Practices

### Before Testing

1. **Backup Production Data** (if testing prod)
2. **Notify Team** of testing schedule
3. **Set Up Monitoring** (database, logs, metrics)
4. **Prepare Test Accounts** with valid assignments
5. **Review Recent Changes** that might affect performance

### During Testing

1. **Monitor Real-Time Metrics** (don't just look at Locust UI)
2. **Watch Database Connections** closely
3. **Check Application Logs** for errors
4. **Note Exact Failure Thresholds** (e.g., "failed at 47 concurrent users")
5. **Take Screenshots** of key metrics for reports

### After Testing

1. **Document Findings** in `/docs/LOAD_TESTING_RESULTS_{date}.md`
2. **Save All Results** (CSV, HTML, logs)
3. **Calculate Capacity Recommendations**
4. **Create Optimization Tickets** for issues found
5. **Retest After Optimizations** to validate improvements

---

## Next Steps

1. **Run Baseline Tests**: Start with staging normal load
2. **Analyze Results**: Review metrics and identify bottlenecks
3. **Optimize Code/Config**: Implement fixes (see LOAD_TESTING_ANALYSIS.md)
4. **Re-Test**: Validate improvements
5. **Document Capacity**: Update PRD with maximum concurrent users

---

## Reference

- **Main Analysis Document**: `/docs/LOAD_TESTING_ANALYSIS.md`
- **Locust Documentation**: https://docs.locust.io/
- **Load Testing Best Practices**: https://www.nginx.com/blog/load-testing-best-practices/

---

## Support

For questions or issues:
1. Review `/docs/LOAD_TESTING_ANALYSIS.md` for bottleneck analysis
2. Check this README's Troubleshooting section
3. Review Locust logs: `locust.log`
4. Contact DevOps/Backend team
