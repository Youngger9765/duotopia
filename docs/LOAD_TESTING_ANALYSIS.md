# Load Testing Analysis Report
## Audio Upload Functionality - Bottleneck Analysis

**Date**: 2025-12-10
**Analyst**: Claude Code
**Scope**: Audio upload endpoints for PROD (VM) and Staging (Cloud Run) environments

---

## Executive Summary

High-concurrency audio upload failures are likely caused by a combination of:
1. **Database connection pool exhaustion** (fixed but needs validation)
2. **GCS upload I/O blocking** (2-5 seconds per upload)
3. **Missing backpressure mechanisms** for concurrent uploads
4. **Cloud Run vs VM architectural differences**

**Recommended Testing Strategy**: Start at 10 concurrent users, increment by 10-20 until failures occur, identify exact threshold.

---

## Architecture Overview

### Upload Flow
```
Client → POST /api/students/upload-recording → FastAPI
  ↓
1. Validate request & auth (DB query ~50ms)
2. Close DB connection
3. Upload to GCS (2-5 seconds - BLOCKING)
4. Reopen DB connection
5. Update progress (DB write ~100ms)
  ↓
Response
```

### Key Bottlenecks Identified

#### 1. Database Connection Pool (FIXED - Needs Validation)
**File**: `/backend/database.py`

**Current Configuration**:
```python
pool_size = 10          # Base pool (was 15)
max_overflow = 10       # Additional connections (was 15)
pool_timeout = 10       # Wait timeout in seconds
pool_recycle = 3600     # Recycle every hour
```

**Analysis**:
- Total capacity: 20 connections per backend instance
- Supabase Free Tier limit: ~25 connections total
- **Previously Fixed**: Issue #5 reduced from 30 to 20 connections after production timeout errors
- **Risk**: Multiple backend instances would still exhaust pool (20 × N instances)

**Load Testing Goal**: Verify 20 connections is sufficient for high concurrency after Phase 2 fix (DB release before GCS upload)

#### 2. GCS Upload I/O Blocking
**File**: `/backend/services/audio_upload.py`

**Current Implementation**:
```python
async def upload_audio(self, file: UploadFile, ...):
    content = await file.read()  # Async read
    blob.upload_from_string(content, content_type=...)  # SYNC operation
```

**Analysis**:
- GCS upload is **synchronous** (blocks event loop)
- Duration: 2-5 seconds per 50KB-2MB file
- No thread pool or async wrapper for GCS operations
- Each upload holds a request slot until completion

**Calculation**:
- 20 concurrent uploads × 3 seconds average = 60 seconds total blocking time
- Throughput: ~6.7 uploads/second maximum (20 / 3s)
- If 50 users try to upload simultaneously → queue time increases

**Recommendation**: Consider `asyncio.to_thread()` or `ThreadPoolExecutor` for GCS uploads

#### 3. FastAPI/Uvicorn Worker Configuration
**File**: `/backend/main.py`

**Current Configuration**:
```python
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

**Analysis**:
- **No explicit worker count specified**
- Default: 1 worker (single process)
- No `--workers` parameter for multi-processing
- Cloud Run deployment likely uses single worker per container

**Implications**:
- All requests handled by single event loop
- Sync operations (GCS upload) block other requests
- No process-level parallelism

**Recommendation**: Test with `--workers=2` or `--workers=4` in VM environment

#### 4. Thread Pool Configuration
**File**: `/backend/core/thread_pool.py`

**Current Configuration**:
```python
SPEECH_THREAD_POOL_SIZE = 20  # For Azure Speech API
AUDIO_THREAD_POOL_SIZE = 10   # For audio conversion
```

**Analysis**:
- Thread pools exist for Azure Speech and audio conversion
- **GCS upload does NOT use thread pool** (blocking sync call)
- Speech thread pool sized for concurrency=20 (Cloud Run setting)

**Gap**: No dedicated thread pool for GCS I/O operations

#### 5. Cloud Run vs VM Deployment Differences

**Cloud Run (Staging)**:
```yaml
CPU: 500m (0.5 core)
Memory: 256Mi
Concurrency: 1 (CPU < 1 requires concurrency=1)
Min Instances: 0 (scale-to-zero)
Max Instances: 1
```

**VM (Production)**:
```nginx
# Nginx reverse proxy
upstream backend {
    server 127.0.0.1:8080;
}
```

**Key Differences**:
| Aspect | Cloud Run (Staging) | VM (Production) |
|--------|---------------------|-----------------|
| CPU | 0.5 core | Unknown (likely 1-2 cores) |
| Memory | 256MB | Unknown |
| Concurrency | 1 request/instance | Depends on Uvicorn workers |
| Auto-scaling | Yes (0-1 instances) | No |
| Nginx | No | Yes (reverse proxy) |
| Connection pooling | Per container | Shared across workers |

**Implications**:
- Cloud Run's concurrency=1 means it can only handle 1 request at a time
- High concurrency will trigger auto-scaling (cold start latency)
- VM environment may have better throughput if multi-worker configured

#### 6. Rate Limiting
**File**: `/backend/main.py`

**Current Configuration**:
```python
@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    allowed, info = await global_rate_limiter.check_rate_limit(
        request,
        max_requests=500,  # Very loose
        window_seconds=60,
    )
```

**Analysis**:
- Global limit: 500 requests/minute per IP
- **Upload-specific limit**: None
- No per-endpoint backpressure

**Risk**: Users can overwhelm system with concurrent uploads before rate limit triggers

#### 7. Nginx Configuration (VM Only)
**File**: `/deployment/vm/nginx.conf`

**Current Configuration**:
```nginx
events {
    worker_connections 1024;
}

location /api/ {
    proxy_pass http://backend/api/;
    # No explicit timeout configured
    # No request body size limit
}
```

**Missing Configurations**:
- `client_max_body_size` (default 1MB, but audio files are up to 2MB)
- `proxy_read_timeout` (default 60s, may timeout during high load)
- `proxy_buffer_size` (affects upload throughput)

**Recommendation**: Add explicit limits and timeouts

---

## Potential Failure Scenarios

### Scenario 1: Database Pool Exhaustion
**Trigger**: 20+ concurrent uploads holding DB connections during GCS upload

**Status**: **FIXED in upload_student_recording()**
```python
# PHASE 1: Quick DB query
db_query()

# PHASE 2: Release DB before GCS upload
db.close()
audio_url = await upload_audio()  # 2-5 seconds, no DB connection held

# PHASE 3: Reopen DB for update
db_new = SessionLocal()
db_new.commit()
db_new.close()
```

**Load Test Goal**: Verify fix works under 50+ concurrent uploads

### Scenario 2: GCS Upload Backlog
**Trigger**: 50+ users upload simultaneously, sync I/O creates queue

**Expected Behavior**:
- First 20 uploads start immediately (assuming 20 workers/threads)
- Remaining 30 uploads wait in queue
- Average wait time: (30 / 6.7 uploads/sec) ≈ 4.5 seconds
- Client timeouts may occur if frontend timeout < queue time

**Mitigation Needed**: Add async wrapper or increase workers

### Scenario 3: Cloud Run Cold Start Cascade
**Trigger**: Sudden spike from 0 to 50 concurrent uploads (staging)

**Expected Behavior**:
- Cloud Run scale-to-zero means first request triggers instance start
- Cold start latency: 2-5 seconds
- With concurrency=1, each new request may trigger new instance
- Max instances=1 means requests queue after first instance

**Result**: Extreme latency during spikes in staging environment

### Scenario 4: Memory Exhaustion
**Trigger**: Many large audio files (2MB each) uploaded concurrently

**Calculation**:
- 50 concurrent uploads × 2MB = 100MB memory just for file buffers
- Cloud Run staging has only 256MB total
- Python FastAPI overhead: ~100MB
- **Risk**: OOM kills in Cloud Run environment

---

## Load Testing Priorities

### Phase 1: Validate DB Pool Fix (Priority: HIGH)
**Goal**: Confirm DB connection release prevents pool exhaustion

**Test**:
- 30 concurrent users uploading continuously for 2 minutes
- Monitor: `pg_stat_activity` connection count
- Success criteria: Connections never exceed 20

### Phase 2: Find GCS Upload Threshold (Priority: HIGH)
**Goal**: Identify maximum concurrent uploads before latency degrades

**Test**:
- Ramp from 10 → 50 → 100 users over 5 minutes
- Monitor: Response time p95, p99
- Failure threshold: p95 > 10 seconds or error rate > 5%

### Phase 3: Spike Test (Priority: MEDIUM)
**Goal**: Test sudden traffic burst (realistic user behavior)

**Test**:
- 0 → 50 users in 10 seconds
- Hold for 1 minute
- Monitor: Error rate, cold start count (Cloud Run)

### Phase 4: Endurance Test (Priority: MEDIUM)
**Goal**: Validate stability over time

**Test**:
- 20 concurrent users for 30 minutes
- Monitor: Memory leaks, connection pool leaks, error rate

### Phase 5: Stress Test (Priority: LOW)
**Goal**: Find absolute breaking point

**Test**:
- Ramp to 200+ users
- Continue until system fails
- Document failure mode

---

## Monitoring Metrics

### Application Metrics
- Response time: p50, p95, p99
- Error rate: HTTP 500, 503, 429
- Request throughput: requests/second
- Active connections: DB pool usage

### Infrastructure Metrics
- CPU usage: Backend container
- Memory usage: Backend container
- Network: GCS upload bandwidth
- Database: Connection count, query latency

### GCS Metrics
- Upload latency: Time to complete upload
- Throughput: Bytes/second
- Error rate: Failed uploads

---

## Environment-Specific Considerations

### PROD (VM) Environment
**Expected Strengths**:
- More resources (CPU/memory)
- No scale-to-zero latency
- Nginx reverse proxy (connection pooling)

**Testing Focus**:
- Multi-worker configuration testing
- Nginx tuning validation
- Absolute capacity limits

**Access**:
- SSH required for direct VM testing
- Production database (be careful!)
- Real user impact risk

### Staging (Cloud Run) Environment
**Expected Weaknesses**:
- Low resources (0.5 CPU, 256MB RAM)
- Concurrency=1 (serial processing)
- Scale-to-zero cold starts

**Testing Focus**:
- Cold start impact
- Memory limits
- Auto-scaling behavior

**Advantages**:
- Safe to test (isolated environment)
- Same architecture as preview environments
- No real user impact

---

## Recommendations for Optimization

### Immediate (Before Load Testing)
1. **Add explicit client_max_body_size to Nginx** (VM)
   ```nginx
   location /api/ {
       client_max_body_size 3M;  # 2MB audio + overhead
       proxy_read_timeout 30s;   # Prevent hanging requests
   }
   ```

2. **Add upload-specific rate limiting**
   ```python
   @limiter.limit("10/minute")  # Max 10 uploads per minute per user
   async def upload_student_recording(...):
   ```

3. **Monitor DB connection pool in health check**
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "database": {
               "pool_size": engine.pool.size(),
               "checked_out": engine.pool.checkedout(),
           }
       }
   ```

### After Load Testing (Based on Results)
1. **If GCS upload is bottleneck**: Wrap in thread pool
   ```python
   loop = asyncio.get_event_loop()
   await loop.run_in_executor(None, sync_gcs_upload, content)
   ```

2. **If VM needs more workers**: Update startup command
   ```bash
   uvicorn main:app --workers=4 --host=0.0.0.0 --port=8080
   ```

3. **If Cloud Run hits memory limits**: Increase memory allocation
   ```yaml
   memory: 512Mi  # Double current limit
   ```

4. **If DB pool still exhausts**: Increase pool size cautiously
   ```python
   pool_size = 15  # Up from 10
   max_overflow = 15  # Up from 10
   ```

---

## Testing Constraints & Warnings

### Production Testing Risks
- Real user traffic may be impacted
- Database writes affect production data
- GCS uploads create real storage costs
- Rate limiting may block legitimate users

**Mitigation**:
- Test during low-traffic hours (late night)
- Use test teacher/student accounts
- Monitor real user error rates
- Have rollback plan ready

### Staging Testing Limitations
- Performance will be worse than production (by design)
- Results may not reflect production behavior
- Cold start latency dominates small tests
- Single instance limit may not show scalability issues

**Mitigation**:
- Test staging first to validate methodology
- Interpret results with architectural differences in mind
- Focus on relative metrics (trends) not absolute numbers

---

## Next Steps

1. ✅ **Code Analysis Complete** (this document)
2. **Create Load Testing Framework**
   - Implement Locust test scenarios
   - Add environment configuration
   - Generate test audio samples
3. **Execute Staging Tests** (Safe environment)
   - Validate test framework
   - Identify obvious bottlenecks
4. **Execute Production Tests** (Careful!)
   - Low-traffic hours only
   - Incremental load increase
   - Real-time monitoring
5. **Analyze Results & Optimize**
   - Compare staging vs production
   - Implement recommendations
   - Re-test to validate improvements

---

## Conclusion

The audio upload system has been partially optimized (DB connection release fix), but several potential bottlenecks remain:

**High Risk**:
- GCS upload synchronous I/O (2-5s blocking)
- Cloud Run concurrency=1 (staging)
- Missing backpressure mechanisms

**Medium Risk**:
- Single Uvicorn worker (no multi-processing)
- Cloud Run cold starts (scale-to-zero)
- Nginx timeout configurations (VM)

**Low Risk**:
- Database connection pool (already fixed)
- Rate limiting (very loose)

**Critical Testing Goal**: Find exact concurrent user threshold where failures begin, then optimize the limiting factor.
