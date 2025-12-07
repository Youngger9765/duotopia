# VM Deployment Pre-Flight Checklist

Use this checklist before running the VM deployment workflow for the first time.

## Prerequisites

### 1. VM Configuration

- [ ] VM `duotopia-prod-vm` is created in zone `asia-east1-b`
  ```bash
  gcloud compute instances describe duotopia-prod-vm --zone=asia-east1-b
  ```

- [ ] VM has static IP `34.81.38.211` assigned
  ```bash
  gcloud compute instances describe duotopia-prod-vm \
    --zone=asia-east1-b \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
  ```

- [ ] SSH access is working
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b
  ```

### 2. Docker on VM

- [ ] Docker is installed on VM
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="docker --version"
  ```

- [ ] Docker runs without sudo (user in docker group)
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="docker ps"
  ```

- [ ] Docker can authenticate to GCR
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="gcloud auth configure-docker gcr.io --quiet && echo 'Auth configured'"
  ```

If Docker is not installed, run:
```bash
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# On VM:
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Exit and reconnect
exit
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Verify
docker ps
```

### 3. Firewall Rules

- [ ] Port 80 (HTTP) is open for incoming traffic
  ```bash
  gcloud compute firewall-rules list --filter="name~duotopia" --format="table(name,allowed[].map().firewall_rule().list())"
  ```

- [ ] Port 22 (SSH) is open for administration
  ```bash
  gcloud compute firewall-rules list --filter="targetTags:duotopia AND allowed.ports:22"
  ```

If firewall rules are missing:
```bash
# Allow HTTP traffic
gcloud compute firewall-rules create duotopia-vm-http \
  --allow tcp:80 \
  --target-tags=duotopia-prod \
  --source-ranges=0.0.0.0/0 \
  --description="Allow HTTP traffic to Duotopia VM"

# Ensure VM has the tag
gcloud compute instances add-tags duotopia-prod-vm \
  --zone=asia-east1-b \
  --tags=duotopia-prod
```

### 4. GitHub Secrets

All the following secrets must be set in GitHub repository settings:

**Required Secrets:**
- [ ] `GCP_SA_KEY` - GCP Service Account JSON key
- [ ] `PRODUCTION_DATABASE_URL` - Supabase production database URL
- [ ] `PRODUCTION_DATABASE_POOLER_URL` - Supabase pooler URL
- [ ] `PRODUCTION_SUPABASE_URL` - Supabase API URL
- [ ] `PRODUCTION_SUPABASE_ANON_KEY` - Supabase anon key
- [ ] `PRODUCTION_JWT_SECRET` - JWT secret for authentication
- [ ] `PRODUCTION_FRONTEND_URL` - Frontend URL
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `AZURE_SPEECH_KEY` - Azure Speech API key
- [ ] `AZURE_SPEECH_REGION` - Azure Speech region
- [ ] `AZURE_SPEECH_ENDPOINT` - Azure Speech endpoint
- [ ] `SMTP_HOST` - SMTP server host
- [ ] `SMTP_PORT` - SMTP server port
- [ ] `SMTP_USER` - SMTP username
- [ ] `SMTP_PASSWORD` - SMTP password
- [ ] `FROM_EMAIL` - Sender email address
- [ ] `FROM_NAME` - Sender name
- [ ] `TAPPAY_PRODUCTION_APP_ID` - TapPay production app ID
- [ ] `TAPPAY_PRODUCTION_APP_KEY` - TapPay production app key
- [ ] `TAPPAY_PRODUCTION_PARTNER_KEY` - TapPay production partner key
- [ ] `TAPPAY_PRODUCTION_MERCHANT_ID` - TapPay production merchant ID
- [ ] `TAPPAY_SANDBOX_APP_ID` - TapPay sandbox app ID
- [ ] `TAPPAY_SANDBOX_APP_KEY` - TapPay sandbox app key
- [ ] `TAPPAY_SANDBOX_PARTNER_KEY` - TapPay sandbox partner key
- [ ] `TAPPAY_SANDBOX_MERCHANT_ID` - TapPay sandbox merchant ID
- [ ] `PRODUCTION_CRON_SECRET` - Cron job authentication secret
- [ ] `PRODUCTION_ENABLE_PAYMENT` - Payment feature flag (true/false)

Verify secrets are set:
```bash
gh secret list | grep -E "PRODUCTION_|OPENAI_|AZURE_|SMTP_|TAPPAY_|GCP_SA_KEY"
```

### 5. GCP Permissions

- [ ] GCP Service Account has required permissions
  - Compute Instance Admin (for SSH and deployment)
  - Storage Admin (for GCR access)
  - Service Account User

Verify service account:
```bash
# Extract service account email from key
gcloud iam service-accounts list --filter="email:github-actions@*"
```

### 6. Local Environment

- [ ] `gcloud` CLI is installed and configured
  ```bash
  gcloud --version
  gcloud config get-value project
  # Should output: duotopia-472708
  ```

- [ ] `gh` CLI is installed (optional, for workflow monitoring)
  ```bash
  gh --version
  ```

## Pre-Deployment Tests

### 1. Verify Backend Code Quality

- [ ] All tests pass locally
  ```bash
  cd backend
  pytest tests/unit/ -v
  ```

- [ ] Code is properly formatted
  ```bash
  cd backend
  black --check .
  flake8 . --max-line-length=120 --ignore=E203,W503
  ```

- [ ] Backend imports successfully
  ```bash
  cd backend
  python -c "import main; print('✅ Import successful')"
  ```

### 2. Test Docker Build Locally

- [ ] Docker image builds successfully
  ```bash
  cd backend
  docker build -t duotopia-backend-vm-test .
  ```

- [ ] Container starts with sample env
  ```bash
  docker run -d \
    --name test-backend \
    -p 8080:8080 \
    -e DATABASE_URL=sqlite:///test.db \
    -e JWT_SECRET=test-secret \
    -e ENVIRONMENT=test \
    duotopia-backend-vm-test

  # Wait a few seconds
  sleep 5

  # Test health endpoint
  curl http://localhost:8080/health

  # Cleanup
  docker stop test-backend
  docker rm test-backend
  ```

### 3. Verify GitHub Workflow Syntax

- [ ] Workflow file is valid YAML
  ```bash
  # View workflow file
  cat .github/workflows/deploy-vm-prod.yml

  # Check for syntax errors (if yamllint is installed)
  yamllint .github/workflows/deploy-vm-prod.yml
  ```

- [ ] Workflow appears in GitHub Actions UI
  - Go to: https://github.com/your-username/duotopia/actions
  - Look for "Deploy to VM (Production)" workflow

## First Deployment

### Step 1: Trigger Deployment

1. [ ] Go to GitHub Actions: https://github.com/your-username/duotopia/actions/workflows/deploy-vm-prod.yml
2. [ ] Click "Run workflow" dropdown button
3. [ ] Select branch: `main` (or feature branch for testing)
4. [ ] Enter confirmation text: `deploy-to-vm`
5. [ ] Click green "Run workflow" button

### Step 2: Monitor Deployment

- [ ] Watch workflow progress
  ```bash
  gh run watch
  # Or monitor on GitHub Actions UI
  ```

- [ ] Check each job completes successfully:
  - [ ] Verify Deployment Confirmation
  - [ ] Test Backend
  - [ ] Build & Push Docker Image
  - [ ] Deploy to VM
  - [ ] Cleanup Old Images

### Step 3: Verify Deployment

- [ ] Health check responds
  ```bash
  curl http://34.81.38.211/api/health
  ```

  Expected response:
  ```json
  {
    "status": "healthy",
    "environment": "production-vm",
    ...
  }
  ```

- [ ] API docs are accessible
  ```bash
  # Open in browser
  http://34.81.38.211/api/docs
  ```

- [ ] Container is running on VM
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="docker ps --filter name=duotopia-backend"
  ```

  Expected output:
  ```
  CONTAINER ID   IMAGE                                     STATUS      PORTS
  abc123def      gcr.io/.../duotopia-backend-vm:sha...   Up X mins   0.0.0.0:80->8080/tcp
  ```

- [ ] Container logs show no errors
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="docker logs --tail=50 duotopia-backend"
  ```

### Step 4: Test API Functionality

- [ ] Test authentication endpoint
  ```bash
  curl -X POST http://34.81.38.211/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test_user","password":"test_pass"}'
  ```

- [ ] Test other critical endpoints
  ```bash
  # Add your critical endpoint tests here
  ```

## Post-Deployment Monitoring

### First 24 Hours

- [ ] Check container status every hour
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="docker stats duotopia-backend --no-stream"
  ```

- [ ] Monitor VM resources
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="top -b -n 1 | head -20"
  ```

- [ ] Review container logs for errors
  ```bash
  gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
    --command="docker logs --since=1h duotopia-backend | grep -i error"
  ```

### Ongoing Monitoring

- [ ] Set up monitoring dashboard (GCP Console)
  - CPU utilization
  - Memory usage
  - Network traffic
  - Disk I/O

- [ ] Configure alerts for:
  - High CPU usage (>80%)
  - High memory usage (>80%)
  - Container restart
  - VM stopped

## Troubleshooting

If deployment fails, check:

1. **Workflow logs** - View in GitHub Actions UI
2. **Container logs** - `gcloud compute ssh ... --command="docker logs duotopia-backend"`
3. **VM system logs** - `gcloud compute ssh ... --command="sudo journalctl -xe"`
4. **Environment variables** - Ensure all secrets are set correctly
5. **Firewall rules** - Verify ports 22 and 80 are open
6. **Docker status** - `gcloud compute ssh ... --command="systemctl status docker"`

## Rollback Plan

If deployment has critical issues:

```bash
# 1. SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# 2. List available images
gcloud container images list-tags gcr.io/duotopia-472708/duotopia-backend-vm

# 3. Stop current container
docker stop duotopia-backend && docker rm duotopia-backend

# 4. Deploy previous version
docker run -d \
  --name duotopia-backend \
  --restart unless-stopped \
  -p 80:8080 \
  --env-file /tmp/backend.env \
  gcr.io/duotopia-472708/duotopia-backend-vm:<PREVIOUS_SHA>

# 5. Verify rollback
curl http://localhost/api/health
```

## Success Criteria

Deployment is considered successful when:

- [x] All workflow jobs complete without errors
- [x] Health endpoint returns 200 status
- [x] Container is running and stable (no restarts)
- [x] API endpoints respond correctly
- [x] No errors in container logs
- [x] VM resources are within acceptable limits
- [x] All critical features work as expected

## Notes

- VM deployment is **independent** from Cloud Run deployment
- Both can run simultaneously for A/B testing
- VM deployment is **manual trigger only** (no auto-deploy)
- Container restart policy is `unless-stopped` (survives VM reboots)
- Old images are automatically cleaned up (keeps last 3)

## References

- Workflow: `.github/workflows/deploy-vm-prod.yml`
- Guide: `docs/VM-DEPLOYMENT-GUIDE.md`
- CICD: `CICD.md` (VM Deployment section)

---

**Last Updated**: 2025-12-07
