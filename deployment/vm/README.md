# VM Full-Stack Deployment Guide

## Overview

This deployment configuration allows you to run the complete Duotopia product (frontend + backend) on a single GCP e2-small VM, providing 93% cost savings compared to Cloud Run.

## Architecture

```
Internet (port 80)
    ↓
[Nginx Reverse Proxy Container] --network=host
    ↓
    ├─→ / → localhost:3000 → [Frontend Container] --network=host
    └─→ /api → localhost:8080 → [Backend Container] --network=host
```

**Network Mode**: All containers use `--network=host` to share the VM's network stack. This allows containers to communicate via `localhost` without Docker bridge networking overhead.

### Components

1. **Nginx Container** (listens on port 80)
   - Acts as reverse proxy
   - Routes `/` to frontend (localhost:3000)
   - Routes `/api` to backend (localhost:8080)
   - Handles CORS and security headers
   - Uses `--network=host` for direct host network access

2. **Frontend Container** (listens on port 3000)
   - Built with Vite/React
   - Pre-configured with `VITE_API_URL=/api`
   - Static files served by Nginx (via localhost)
   - Uses `--network=host` to bind directly to VM port 3000

3. **Backend Container** (listens on port 8080)
   - FastAPI application
   - Connected to Supabase database
   - All environment variables via `.env` file
   - Uses `--network=host` to bind directly to VM port 8080

### Why --network=host?

Docker containers are isolated by default, each with their own network namespace. Using `127.0.0.1` or `localhost` in the default bridge network mode would fail because:
- Each container sees `127.0.0.1` as its own loopback, not the host's
- Containers cannot communicate via `127.0.0.1` in bridge mode

The `--network=host` mode:
- ✅ Removes network isolation - containers share the VM's network stack
- ✅ Containers can bind directly to host ports (3000, 8080, 80)
- ✅ Communication via `localhost` works as expected
- ✅ No port mapping needed (`-p` flag not required)
- ✅ Better performance (no NAT overhead)
- ⚠️ Less isolation (acceptable for single-tenant VM deployment)

## Deployment

### Prerequisites

1. VM must be running and accessible
2. VM must have Docker and docker-credential-gcr installed
3. Firewall rule must allow port 80 ingress
4. GitHub Actions secrets must be configured

### Manual Deployment

Trigger the workflow from GitHub Actions:

1. Go to **Actions** → **Deploy Full Stack to VM (Production)**
2. Click **Run workflow**
3. Enter confirmation: `deploy-fullstack-vm`
4. Select component:
   - `both` - Deploy both frontend and backend (recommended for first deploy)
   - `frontend` - Only update frontend
   - `backend` - Only update backend
5. Click **Run workflow**

### What the Workflow Does

1. **Tests** - Runs backend and frontend tests
2. **Builds** - Creates Docker images for selected components
3. **Pushes** - Uploads images to Artifact Registry
4. **Deploys** - SSH to VM and runs containers
5. **Health Check** - Verifies deployment success

### Deployment Time

- Frontend only: ~3-5 minutes
- Backend only: ~4-6 minutes
- Both: ~6-8 minutes

## Access URLs

After successful deployment:

- **Frontend**: http://34.81.38.211/
- **Backend API Docs**: http://34.81.38.211/api/docs
- **Backend Health**: http://34.81.38.211/api/health

## Configuration Files

### Nginx Configuration
- **File**: `deployment/vm/nginx.conf`
- **Purpose**: Routes traffic between frontend and backend
- **Mounted**: `/tmp/nginx.conf` on VM → `/etc/nginx/nginx.conf` in container

### Backend Environment
- **Generated**: During workflow execution
- **Contains**: All secrets from GitHub Actions
- **Uploaded**: `/tmp/backend.env` on VM
- **Security**: Only accessible by VM user

## Container Management

### View Running Containers

```bash
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker ps -a --filter name=duotopia'
```

### View Logs

```bash
# Backend logs
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs -f duotopia-backend'

# Frontend logs
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs -f duotopia-frontend'

# Nginx logs
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs -f duotopia-nginx'
```

### Restart Container

```bash
# Restart backend
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker restart duotopia-backend'

# Restart frontend
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker restart duotopia-frontend'

# Restart nginx
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker restart duotopia-nginx'
```

### Stop All Containers

```bash
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker stop duotopia-nginx duotopia-frontend duotopia-backend'
```

## Troubleshooting

### Frontend Shows 502 Bad Gateway

**Possible causes:**
1. Frontend container not running
2. Frontend container crashed
3. Nginx cannot reach frontend on port 3000

**Solution:**
```bash
# Check frontend container status
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker ps -a --filter name=duotopia-frontend'

# Check frontend logs
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs --tail=50 duotopia-frontend'

# Restart frontend
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker restart duotopia-frontend'
```

### API Calls Return 502

**Possible causes:**
1. Backend container not running
2. Backend crashed due to missing env vars
3. Database connection issues

**Solution:**
```bash
# Check backend container status
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker ps -a --filter name=duotopia-backend'

# Check backend logs
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs --tail=100 duotopia-backend'

# Test database connectivity
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker exec duotopia-backend python -c "from database import engine; print(engine)"'
```

### CORS Errors in Browser

**Possible causes:**
1. Nginx CORS headers not configured correctly
2. Backend CORS settings incorrect

**Solution:**
1. Check nginx configuration includes CORS headers
2. Verify frontend uses relative paths `/api/*`
3. Check browser console for exact CORS error

### Port Already in Use

**Symptoms:** Container fails to start with "address already in use"

**Cause:** When using `--network=host`, containers bind directly to VM ports. If a port is already in use (by another container or process), the new container will fail to start.

**Solution:**
```bash
# Find what's using the port
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='sudo netstat -tlnp | grep ":80\|:3000\|:8080"'

# Stop conflicting container
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker stop <container-name>'
```

### Nginx Shows "Connection Refused" to Backend/Frontend

**Symptoms:** Nginx logs show `connect() failed (111: Connection refused) while connecting to upstream`

**Cause:** Backend or Frontend container is not running or not listening on expected port.

**Solution:**
```bash
# Check if all containers are running
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker ps -a --filter name=duotopia'

# Verify ports are listening on the VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='sudo netstat -tlnp | grep ":3000\|:8080"'

# Check backend logs for startup errors
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs --tail=100 duotopia-backend'

# Check frontend logs for startup errors
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker logs --tail=100 duotopia-frontend'
```

## Firewall Configuration

### Check Current Rules

```bash
gcloud compute firewall-rules list --filter="name~duotopia"
```

### Required Rule

```yaml
Name: allow-http-duotopia-vm
Direction: INGRESS
Priority: 1000
Network: default
Target tags: duotopia-vm
Source IP ranges: 0.0.0.0/0
Protocols/Ports: tcp:80
Action: ALLOW
```

### Create Rule (if missing)

```bash
gcloud compute firewall-rules create allow-http-duotopia-vm \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=duotopia-vm
```

## Cost Analysis

### VM Costs (e2-small, us-east1)
- VM instance: ~$13/month
- Static IP: ~$3/month
- Egress: ~$0-5/month (depends on traffic)
- **Total**: ~$16-21/month

### Cloud Run Costs (comparison)
- Frontend: ~$120/month
- Backend: ~$120/month
- **Total**: ~$240/month

### Savings
- **Monthly**: $220 saved (93% reduction)
- **Annual**: $2,640 saved

## Maintenance

### Image Cleanup

Old Docker images are automatically cleaned up during deployment. Manual cleanup:

```bash
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker image prune -f'
```

### Artifact Registry Cleanup

The workflow automatically keeps only the 3 most recent images. Manual cleanup:

```bash
# List images
gcloud artifacts docker images list \
  asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-frontend-vm

# Delete specific version
gcloud artifacts docker images delete \
  asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-frontend-vm@sha256:xxxxx
```

### Update Environment Variables

1. Update GitHub Actions secrets
2. Re-run deployment workflow with `backend` option
3. New container will use updated environment variables

## Rollback

To rollback to a previous version:

1. Find the previous image SHA from workflow logs
2. SSH to VM
3. Stop current container
4. Start container with previous image

```bash
# Example rollback
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='
    docker stop duotopia-backend
    docker rm duotopia-backend
    docker run -d \
      --name duotopia-backend \
      --restart unless-stopped \
      --network=host \
      --env-file /tmp/backend.env \
      asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-backend-vm:PREVIOUS_SHA
  '
```

## Monitoring

### Health Checks

```bash
# Quick health check
curl http://34.81.38.211/health
curl http://34.81.38.211/api/health

# Detailed backend health
curl http://34.81.38.211/api/health | jq '.'
```

### Resource Usage

```bash
# CPU, Memory, Network usage
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='docker stats --no-stream'
```

### Disk Usage

```bash
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command='df -h && docker system df'
```

## Security Considerations

1. **No Public Secrets**: All secrets are in GitHub Actions, never committed
2. **Environment Isolation**: VM deployment isolated from Cloud Run
3. **Firewall**: Only port 80 is exposed
4. **HTTPS**: Consider adding SSL certificate (Let's Encrypt) for production
5. **SSH Access**: Restricted to authorized gcloud users

## Future Improvements

1. **SSL/HTTPS**: Add Let's Encrypt certificate with certbot
2. **Domain Name**: Point custom domain to VM IP
3. **CDN**: Add Cloud CDN for static assets
4. **Backup**: Automated container state backups
5. **Monitoring**: Add Prometheus/Grafana for metrics
6. **Auto-scaling**: Consider horizontal scaling if traffic grows

## FAQ

### Q: Will this affect Cloud Run deployments?
**A**: No, this is completely separate. Cloud Run continues to use different workflows and configurations.

### Q: Can I run both VM and Cloud Run simultaneously?
**A**: Yes, they are independent. VM uses `34.81.38.211`, Cloud Run uses its own URLs.

### Q: What happens if the VM restarts?
**A**: All containers have `--restart unless-stopped`, so they'll auto-start after VM reboot.

### Q: How do I update only the frontend?
**A**: Run the workflow with `deploy_component: frontend` option.

### Q: Can I SSH to the VM directly?
**A**: Yes, use `gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b`

### Q: How do I view real-time logs?
**A**: Use `docker logs -f <container-name>` (see Container Management section above)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Check container logs on VM
4. Verify firewall rules and network connectivity
