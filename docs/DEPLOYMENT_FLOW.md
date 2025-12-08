# Deployment Flow - New Strategy

## Overview

This document describes the new deployment strategy implemented for the Duotopia project.

## Strategy Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT STRATEGY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Push to main branch      →  Deploy to VM (Production)          │
│  Push to staging branch   →  Deploy to Cloud Run (Staging)      │
│  Pull requests            →  Deploy to Cloud Run (Per-Issue)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Workflows

### 1. Production Deployment (VM)

**Workflow:** `deploy-vm-prod.yml`

**Trigger:**
- Automatic on push to `main` branch
- Manual trigger available for emergencies

**Target:** GCP e2-small VM (duotopia-prod-vm)

**Features:**
- ✅ Runs tests before deployment
- ✅ Builds and pushes Docker images to Artifact Registry
- ✅ Deploys both frontend and backend containers
- ✅ Sets up Nginx reverse proxy
- ✅ Health checks after deployment
- ✅ Automatic image cleanup

**Cost:** ~$16/month (93% savings vs Cloud Run)

**Changes Made:**
- ❌ Removed manual confirmation requirement
- ✅ Added automatic trigger on main branch push
- ✅ Kept manual trigger option for partial deployments
- ✅ All conditional logic now uses `determine-component` job output

---

### 2. Staging Deployment (Cloud Run)

**Workflows:**
- `deploy-backend.yml` - Backend to Cloud Run
- `deploy-frontend.yml` - Frontend to Cloud Run

**Trigger:**
- Automatic on push to `staging` branch
- **Excludes** main branch (safety check added)
- Manual trigger available

**Target:** Cloud Run services (staging environment)

**Features:**
- ✅ Runs tests before deployment
- ✅ Uses staging database and secrets
- ✅ Scale-to-zero for cost optimization
- ✅ Minimal resource allocation (256Mi, 0.5 CPU)
- ✅ Automatic database migrations
- ✅ RLS verification

**Changes Made:**
- ✅ Added `branches-ignore: [main]` to prevent main branch deployments
- ✅ Added safety check that fails if triggered on main branch
- ✅ Simplified environment logic (removed production conditionals)
- ✅ Removed production-specific configurations

---

### 3. Per-Issue Deployment (Cloud Run)

**Workflow:** `deploy-per-issue.yml`

**Trigger:**
- Automatic on push to branches matching:
  - `fix/issue-*`
  - `feature/issue-*`
  - `claude/issue-*`

**Target:** Cloud Run services (per-issue preview environments)

**Features:**
- ✅ Dedicated backend and frontend per issue
- ✅ Automatic comment on GitHub issue with URLs
- ✅ Uses staging database
- ✅ Automatic cleanup when issue closes
- ✅ Minimal cost (scale-to-zero)

**Changes Made:**
- ✅ No changes needed (already isolated from main branch)

---

### 4. Shared Configuration (Optional)

**Workflow:** `deploy-shared.yml`

**Purpose:** Trigger backend/frontend deployments when shared config changes

**Changes Made:**
- ✅ No changes needed (triggers other workflows)

---

## Deployment Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CODE PUSH EVENT                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Which branch?  │
                    └────────┬───────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │   main   │  │ staging  │  │ PR/issue │
         └────┬─────┘  └────┬─────┘  └────┬─────┘
              │             │             │
              ▼             ▼             ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ deploy-vm-prod  │  │ deploy-backend  │  │deploy-per-issue │
    │     .yml        │  │ deploy-frontend │  │      .yml       │
    │                 │  │      .yml       │  │                 │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  🧪 Run Tests   │  │  🧪 Run Tests   │  │  🐳 Build       │
    │  ✅ Pass Tests  │  │  ✅ Pass Tests  │  │  🚀 Deploy      │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  🐳 Build       │  │  🐳 Build       │  │  Cloud Run      │
    │  Docker Images  │  │  Docker Images  │  │  (Preview)      │
    └────────┬────────┘  └────────┬────────┘  │                 │
             │                    │            │ issue-123-be    │
             ▼                    ▼            │ issue-123-fe    │
    ┌─────────────────┐  ┌─────────────────┐  └─────────────────┘
    │  📤 Upload to   │  │  🚀 Deploy to   │
    │     VM via SSH  │  │   Cloud Run     │
    │                 │  │   (Staging)     │
    │ • Backend       │  │                 │
    │ • Frontend      │  │ duotopia-       │
    │ • Nginx         │  │ staging-backend │
    └────────┬────────┘  │ duotopia-       │
             │           │ staging-frontend│
             ▼           └─────────────────┘
    ┌─────────────────┐
    │  🩺 Health      │
    │     Check       │
    │                 │
    │ • Backend API   │
    │ • Frontend Page │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  ✅ Production  │
    │    VM Ready     │
    │                 │
    │ http://         │
    │ 34.81.38.211    │
    └─────────────────┘
```

## Testing Strategy

### Before Deployment

All workflows run tests before deploying:

**Backend (VM & Cloud Run):**
1. Black formatting check
2. Flake8 linting
3. pytest (unit tests for VM, full suite for staging)

**Frontend (VM & Cloud Run):**
1. Prettier formatting check
2. TypeScript type check
3. ESLint check
4. API testing framework
5. Build test

### After Deployment

**VM Deployment:**
1. Health check on backend API (`/api/health`)
2. Health check on frontend (`/`)
3. Retry logic (up to 10 attempts with 10s delay)

**Cloud Run Deployment:**
1. Health check on backend API
2. Health check on frontend
3. Deployment verification (check revision, timestamp)

## Cost Comparison

| Environment | Infrastructure | Monthly Cost | Notes |
|-------------|---------------|--------------|-------|
| Production  | VM (e2-small) | ~$16 | 93% savings vs Cloud Run |
| Staging     | Cloud Run | ~$20 | Scale-to-zero, minimal resources |
| Per-Issue   | Cloud Run | ~$0-5 | Scale-to-zero, auto-cleanup |

## Security Features

### VM Deployment
- ✅ Backend environment variables (secrets) created on-the-fly
- ✅ Environment files never committed to repository
- ✅ Files uploaded via secure gcloud SCP
- ✅ Firewall rules configured (ports 80, 443, 8080)

### Cloud Run Deployment
- ✅ RLS (Row Level Security) verification
- ✅ Alembic migration checks
- ✅ Environment-specific secrets
- ✅ Automatic image cleanup

## Manual Override

All workflows support manual triggering via `workflow_dispatch`:

### VM Deployment
```bash
# GitHub Actions UI → deploy-vm-prod.yml → Run workflow
# Select component: frontend, backend, or both
```

### Cloud Run Deployment
```bash
# GitHub Actions UI → deploy-backend.yml → Run workflow
# GitHub Actions UI → deploy-frontend.yml → Run workflow
```

## Rollback Strategy

### VM Production
1. Use manual trigger to deploy previous working version
2. Or SSH into VM and manually switch containers

### Cloud Run Staging
1. Use GCP Console to switch to previous revision
2. Or use manual trigger to deploy previous commit

## Migration Steps (Already Completed)

✅ 1. Updated `deploy-vm-prod.yml`:
   - Changed trigger from `workflow_dispatch` to `push` on main
   - Removed confirmation requirement
   - Added `determine-component` job
   - Updated all job dependencies

✅ 2. Updated `deploy-backend.yml`:
   - Added `branches-ignore: [main]`
   - Added safety check for main branch
   - Simplified to staging-only logic
   - Removed all production conditionals

✅ 3. Updated `deploy-frontend.yml`:
   - Added `branches-ignore: [main]`
   - Added safety check for main branch
   - Simplified to staging-only logic
   - Removed production-specific cache clearing

✅ 4. No changes to `deploy-per-issue.yml` (already isolated)

✅ 5. No changes to `deploy-shared.yml` (already correct)

## Verification Checklist

Before pushing to main:

- [ ] All workflow YAML files are valid
- [ ] Branch filters are correct
- [ ] Environment variable references are correct
- [ ] Job dependencies are properly set
- [ ] Health checks are configured
- [ ] Security secrets are referenced correctly

After first main branch push:

- [ ] VM deployment triggers automatically
- [ ] Tests pass before deployment
- [ ] Docker images build successfully
- [ ] Containers deploy to VM
- [ ] Health checks pass
- [ ] Frontend is accessible at http://34.81.38.211
- [ ] Backend API is accessible at http://34.81.38.211/api

After staging branch push:

- [ ] Cloud Run deployment triggers
- [ ] Tests pass before deployment
- [ ] Services deploy to Cloud Run
- [ ] Health checks pass
- [ ] Staging URLs are accessible

## Monitoring

### VM Production
- Check deployment logs in GitHub Actions
- SSH into VM to check container status: `docker ps -a`
- View container logs: `docker logs -f duotopia-backend`

### Cloud Run Staging
- Check deployment logs in GitHub Actions
- View logs in GCP Console (Cloud Run)
- Monitor costs in GCP Billing

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review this documentation
3. Consult `.github/workflows/*.yml` files
4. Check `CLAUDE.md` for project-specific rules
