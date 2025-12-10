# Load Testing Setup Guide
## Step-by-Step Instructions for First-Time Setup

This guide will walk you through setting up the load testing environment from scratch.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher installed
- [ ] Access to staging/production environments
- [ ] Test account credentials
- [ ] PostgreSQL client (optional, for monitoring)
- [ ] Git repository cloned

---

## Step 1: Install System Dependencies

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ffmpeg for audio sample generation
brew install ffmpeg

# Install PostgreSQL client (optional, for monitoring)
brew install postgresql@15
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Install ffmpeg
sudo apt-get install -y ffmpeg

# Install PostgreSQL client (optional)
sudo apt-get install -y postgresql-client-15

# Install build tools (required for psycopg2)
sudo apt-get install -y build-essential python3-dev libpq-dev
```

### Windows

```bash
# Using Chocolatey
choco install ffmpeg
choco install postgresql

# Or download installers:
# ffmpeg: https://ffmpeg.org/download.html
# PostgreSQL: https://www.postgresql.org/download/windows/
```

---

## Step 2: Set Up Python Environment

### Option A: Using Virtual Environment (Recommended)

```bash
# Navigate to load testing directory
cd backend/tests/load_testing

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Option B: Using System Python

```bash
cd backend/tests/load_testing
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check Locust is installed
locust --version
# Expected: locust 2.20.0 or higher

# Check Python packages
pip list | grep -E "locust|psycopg2|requests"
```

---

## Step 3: Create Test Accounts

You need test accounts in your target environment to run load tests.

### Create Staging Test Accounts

#### Option 1: Using Admin Panel (Recommended)

1. Log in to staging admin panel: `https://duotopia-staging-frontend-xxx.run.app/admin`
2. Navigate to "Users" → "Create Teacher"
3. Create test teacher:
   - Email: `test-teacher@duotopia.co`
   - Name: `Load Test Teacher`
   - Password: (use strong password)
4. Create test student:
   - Email: `test-student@duotopia.co`
   - Name: `Load Test Student`
   - Password: (use strong password)

#### Option 2: Using Database

```sql
-- Connect to staging database
psql "$STAGING_DATABASE_URL"

-- Create test teacher
INSERT INTO teachers (email, name, password_hash, created_at)
VALUES (
    'test-teacher@duotopia.co',
    'Load Test Teacher',
    '$2b$12$...',  -- Generate with bcrypt
    NOW()
);

-- Create test student
INSERT INTO students (email, name, password_hash, created_at)
VALUES (
    'test-student@duotopia.co',
    'Load Test Student',
    '$2b$12$...',
    NOW()
);
```

#### Generate bcrypt hash:
```python
import bcrypt
password = "your-password"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
```

---

## Step 4: Create Test Data

The test accounts need assignments and content to upload recordings to.

### Create Test Assignment

1. Log in as test teacher
2. Create a classroom: "Load Test Classroom"
3. Add test student to classroom
4. Create a program/lesson/content with at least 1 content item
5. Assign to classroom
6. Note the assignment ID and content item ID

### Get Test Data IDs

```sql
-- Find student assignment ID
SELECT sa.id as assignment_id
FROM student_assignments sa
JOIN students s ON s.id = sa.student_id
WHERE s.email = 'test-student@duotopia.co'
LIMIT 1;

-- Find content item ID
SELECT ci.id as content_item_id
FROM content_items ci
JOIN contents c ON c.id = ci.content_id
JOIN assignment_contents ac ON ac.content_id = c.id
JOIN student_assignments sa ON sa.id = ac.student_assignment_id
JOIN students s ON s.id = sa.student_id
WHERE s.email = 'test-student@duotopia.co'
LIMIT 1;
```

Save these IDs - you'll need them in the next step.

---

## Step 5: Configure Environment

### Create .env File

```bash
cd backend/tests/load_testing

# Copy example config
cp .env.example .env

# Edit .env with your preferred editor
nano .env  # or vim, code, etc.
```

### Fill in Your Configuration

```bash
# Staging environment
TEST_ENV=staging
STAGING_BASE_URL=https://your-staging-backend-url.run.app

# Your test account credentials
TEST_TEACHER_EMAIL=test-teacher@duotopia.co
TEST_TEACHER_PASSWORD=your-actual-password

TEST_STUDENT_EMAIL=test-student@duotopia.co
TEST_STUDENT_PASSWORD=your-actual-password

# IDs from Step 4
TEST_ASSIGNMENT_ID=123  # Replace with actual ID
TEST_CONTENT_ITEM_ID=456  # Replace with actual ID

# Database monitoring (optional)
STAGING_DATABASE_URL=postgresql://user:pass@host:5432/db
ENABLE_DB_MONITORING=true
```

### Verify Configuration

```bash
# Load environment
set -a
source .env
set +a

# Test credentials
echo "Testing authentication..."
curl -X POST "$STAGING_BASE_URL/api/students/validate" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_STUDENT_EMAIL\",\"password\":\"$TEST_STUDENT_PASSWORD\"}"

# Should return access token if successful
```

---

## Step 6: Generate Test Audio Files

```bash
cd backend/tests/load_testing

# Generate audio samples
python generate_audio_samples.py
```

**Expected Output**:
```
🎵 Generating test audio samples...

✅ ffmpeg is installed
📁 Output directory: /path/to/audio_samples

Generating small_3sec_50kb.webm...
  Description: Short phrase (3 seconds)
  Duration:    3 seconds
  Target size: 50 KB
  Bitrate:     133 kbps
  ✅ Generated: 51.2 KB

Generating medium_10sec_200kb.webm...
  ...

✅ All samples generated!
```

### Verify Files Created

```bash
ls -lh audio_samples/
# Should show 4 .webm files
```

**If ffmpeg is not installed**, the script will generate dummy binary files instead. This is sufficient for load testing.

---

## Step 7: Run Your First Test

### Test 1: Smoke Test (1 User)

Verify everything works before running larger tests:

```bash
# Make script executable
chmod +x run_tests.sh

# Run single-user test for 1 minute
./run_tests.sh --env staging --users 1 --rate 1 --time 1m --headless
```

**Expected Output**:
```
========================================
  Duotopia Load Test
========================================
Environment:  staging
Scenario:     custom
Users:        1
Spawn Rate:   1 users/sec
Duration:     1m
========================================

[2025-12-10 14:30:22] Starting load test...
[2025-12-10 14:30:23] 👤 User 1 starting...
[2025-12-10 14:30:24] ✅ User authenticated: Student ID 123
[2025-12-10 14:30:25] ✅ Upload successful (200KB) in 3.45s
...
[2025-12-10 14:31:24] Test complete!

========================================
  Test Summary
========================================
Request Count: 15
Failure Count: 0
Median (ms):   3450
95th %ile (ms): 4200
Avg (ms):      3500
RPS:           0.25
========================================
```

### Test 2: Normal Load with Web UI

```bash
./run_tests.sh --env staging --scenario normal --web
```

1. Open browser to `http://localhost:8089`
2. Verify host is correct
3. Click "Start" with default values (20 users, 2/sec spawn rate)
4. Watch real-time charts
5. Stop after 2-3 minutes

### Test 3: Headless Automated Test

```bash
./run_tests.sh --env staging --scenario normal --headless
```

This will run for 5 minutes and generate HTML report.

---

## Step 8: Review Results

### Check Output Directory

```bash
cd results
ls -la

# Latest test results
cd staging_normal_20251210_143022/
```

### Open HTML Report

```bash
# macOS
open report.html

# Linux
xdg-open report.html

# Or just open in browser
firefox report.html
```

### Review Metrics

**Look for**:
- Success rate: Should be >95%
- Response time p95: Should be <10s for staging
- Error rate: Should be <5%
- Any failures in "Failures" tab

---

## Step 9: Troubleshooting Common Issues

### Issue: Authentication Fails

**Error**: `Authentication failed: 404` or `401 Unauthorized`

**Solutions**:
1. Verify credentials in .env file
2. Test login manually (see Step 5)
3. Check if test accounts exist in database
4. Ensure password is correct (not hashed)

### Issue: No Assignment Found

**Error**: `Assignment not found: 404`

**Solutions**:
1. Verify `TEST_ASSIGNMENT_ID` is correct
2. Check student has access to assignment
3. Create test assignment (see Step 4)

### Issue: Import Errors

**Error**: `ModuleNotFoundError: No module named 'locust'`

**Solutions**:
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify installation
pip list | grep locust
```

### Issue: Database Monitoring Fails

**Error**: `Failed to get connection stats`

**Solutions**:
1. Check `STAGING_DATABASE_URL` is correct
2. Verify database permissions:
   ```sql
   GRANT pg_read_all_stats TO your_user;
   ```
3. Disable monitoring:
   ```bash
   export ENABLE_DB_MONITORING=false
   ```

### Issue: Audio Files Not Generated

**Error**: `Failed to generate audio samples`

**Solutions**:
1. Install ffmpeg (see Step 1)
2. Or just use dummy files (script auto-generates if ffmpeg missing)
3. Verify directory permissions:
   ```bash
   chmod -R 755 audio_samples/
   ```

---

## Step 10: Next Steps

Now that setup is complete, you can:

1. **Run Different Scenarios**: Try peak, stress, spike tests
2. **Test Production** (carefully): Follow production testing guidelines
3. **Set Up Monitoring**: Enable database monitoring for deeper insights
4. **Analyze Bottlenecks**: Review `/docs/LOAD_TESTING_ANALYSIS.md`
5. **Optimize**: Implement recommendations and re-test

### Recommended Testing Sequence

```bash
# 1. Baseline (staging)
./run_tests.sh --env staging --scenario normal --headless

# 2. Peak load (staging)
./run_tests.sh --env staging --scenario peak --headless

# 3. Stress test (staging)
./run_tests.sh --env staging --scenario stress --headless

# 4. Spike test (staging)
./run_tests.sh --env staging --scenario spike --headless

# 5. Compare with production (carefully!)
./run_tests.sh --env production --scenario normal --headless
```

---

## Quick Reference

### Essential Commands

```bash
# List all scenarios
./run_tests.sh --help

# Run with web UI
./run_tests.sh --env staging --scenario normal --web

# Run headless
./run_tests.sh --env staging --scenario peak --headless

# Custom test
./run_tests.sh --env staging --users 30 --rate 5 --time 8m --headless

# Generate new audio samples
python generate_audio_samples.py

# View results
open results/*/report.html
```

### Environment Variables

```bash
# Set environment
export TEST_ENV=staging  # or production, local

# Override credentials
export TEST_STUDENT_EMAIL=other-student@example.com
export TEST_STUDENT_PASSWORD=other-password

# Disable monitoring
export ENABLE_DB_MONITORING=false
```

### File Locations

```
load_testing/
├── locustfile.py          # Main test scenarios
├── config.py              # Environment configurations
├── monitoring.py          # Database monitoring
├── run_tests.sh           # Test execution script
├── generate_audio_samples.py  # Audio sample generator
├── .env                   # Your credentials (don't commit!)
├── audio_samples/         # Test audio files
└── results/               # Test results
    └── staging_normal_*/
        ├── report.html    # Visual report
        └── results_*.csv  # Raw data
```

---

## Getting Help

1. **Read the README**: `backend/tests/load_testing/README.md`
2. **Check Analysis**: `/docs/LOAD_TESTING_ANALYSIS.md`
3. **Review Troubleshooting**: README.md#troubleshooting
4. **Check Logs**: `locust.log` in test directory
5. **Ask Team**: Slack or email with:
   - What you're trying to do
   - Error messages
   - Environment (staging/prod)
   - Steps to reproduce

---

## Congratulations!

You've successfully set up the load testing environment. You can now:
- Run performance tests on demand
- Identify bottlenecks before they hit production
- Validate optimizations
- Plan capacity for growth

Happy testing! 🚀
