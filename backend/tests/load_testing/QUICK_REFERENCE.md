# Load Testing Quick Reference Card

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install
pip install -r requirements.txt && python generate_audio_samples.py

# 2. Configure
cp .env.example .env && nano .env  # Add your credentials

# 3. Run
./run_tests.sh --env staging --scenario normal --headless
```

---

## 📋 Common Commands

### Basic Test Execution

```bash
# Web UI (interactive)
./run_tests.sh --env staging --scenario normal --web

# Headless (automated)
./run_tests.sh --env staging --scenario peak --headless

# Custom test
./run_tests.sh --env staging --users 30 --rate 5 --time 8m --headless
```

### All Test Scenarios

```bash
# 20 users, 5 minutes
./run_tests.sh --env staging --scenario normal --headless

# 50 users, 5 minutes
./run_tests.sh --env staging --scenario peak --headless

# 100 users, 10 minutes
./run_tests.sh --env staging --scenario stress --headless

# 50 users instantly, 3 minutes
./run_tests.sh --env staging --scenario spike --headless

# 30 users, 30 minutes
./run_tests.sh --env staging --scenario endurance --headless

# 200 users, 10 minutes (find limits)
./run_tests.sh --env staging --scenario breaking --headless
```

---

## 🔧 Environment Variables

```bash
# Set environment
export TEST_ENV=staging  # or production, local

# Override URLs
export STAGING_BASE_URL=https://your-backend-url.run.app

# Set credentials
export TEST_STUDENT_EMAIL=test@example.com
export TEST_STUDENT_PASSWORD=password123

# Set test data IDs
export TEST_ASSIGNMENT_ID=123
export TEST_CONTENT_ITEM_ID=456

# Monitoring
export ENABLE_DB_MONITORING=true
export DB_QUERY_INTERVAL=5
```

---

## 📊 Interpreting Results

### Good Performance

- ✅ Success rate >95%
- ✅ p95 latency <10s
- ✅ Error rate <2%
- ✅ No 503 errors
- ✅ Stable DB connections

### Warning Signs

- ⚠️ Success rate 90-95%
- ⚠️ p95 latency 10-15s
- ⚠️ Error rate 2-5%
- ⚠️ Occasional timeouts
- ⚠️ DB connections >15

### Critical Issues

- ❌ Success rate <90%
- ❌ p95 latency >15s
- ❌ Error rate >5%
- ❌ Frequent 503 errors
- ❌ DB connections >18

---

## 🐛 Quick Troubleshooting

### Authentication Fails
```bash
# Test login manually
curl -X POST $STAGING_BASE_URL/api/students/validate \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### No Assignment Found
```bash
# Set explicit IDs
export TEST_ASSIGNMENT_ID=123
export TEST_CONTENT_ITEM_ID=456
```

### Locust Not Found
```bash
# Reinstall
pip install --upgrade -r requirements.txt
locust --version  # Verify
```

### Database Errors
```bash
# Disable monitoring
export ENABLE_DB_MONITORING=false
```

---

## 📁 File Locations

```
load_testing/
├── run_tests.sh           # Main execution script
├── locustfile.py          # Test scenarios
├── config.py              # Configuration
├── .env                   # Your credentials
├── audio_samples/         # Test files
└── results/               # Test outputs
    └── */report.html      # Open in browser
```

---

## 🎯 Test Scenarios Summary

| Scenario | Users | Duration | Purpose |
|----------|-------|----------|---------|
| normal | 20 | 5m | Baseline |
| peak | 50 | 5m | High traffic |
| stress | 100 | 10m | Beyond capacity |
| spike | 50 | 3m | Sudden burst |
| endurance | 30 | 30m | Stability |
| breaking | 200 | 10m | Find limits |

---

## 📖 Documentation

- **Setup**: `SETUP_GUIDE.md`
- **Full Guide**: `README.md`
- **Analysis**: `/docs/LOAD_TESTING_ANALYSIS.md`
- **Summary**: `/docs/LOAD_TESTING_IMPLEMENTATION_SUMMARY.md`

---

## ⚠️ Production Testing

**Before testing production**:
1. Schedule during low-traffic hours
2. Notify team
3. Start with 10 users
4. Monitor real users
5. Stop if error rate >10%

```bash
# Production test (CAREFUL!)
./run_tests.sh --env production --users 10 --rate 2 --time 3m --headless
```

---

## 📞 Help

1. Check `README.md` Troubleshooting section
2. Review `SETUP_GUIDE.md`
3. Check logs: `locust.log`
4. Contact DevOps team
