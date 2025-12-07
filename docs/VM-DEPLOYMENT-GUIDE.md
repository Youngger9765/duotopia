# VM Deployment Guide - duotopia-prod-vm

Quick reference guide for deploying Duotopia backend to GCP e2-small VM.

## 📋 VM Information

- **VM Name**: `duotopia-prod-vm`
- **Zone**: `asia-east1-b`
- **Machine Type**: `e2-small` (2 vCPU, 2GB RAM)
- **Static IP**: `34.81.38.211`
- **OS**: Container-Optimized OS (or Debian with Docker)
- **Cost**: ~$13/month (fixed)

## 🚀 Quick Deploy

### Method 1: GitHub Actions (Recommended)

1. Go to: https://github.com/young/duotopia/actions/workflows/deploy-vm-prod.yml
2. Click "Run workflow"
3. Enter confirmation: `deploy-to-vm`
4. Click "Run workflow"
5. Wait for deployment to complete (~5-10 minutes)

### Method 2: Manual Deploy (Emergency)

```bash
# 1. Build Docker image locally
cd backend
docker build -t gcr.io/duotopia-472708/duotopia-backend-vm:manual .

# 2. Push to GCR
gcloud auth configure-docker gcr.io
docker push gcr.io/duotopia-472708/duotopia-backend-vm:manual

# 3. SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# 4. On VM: Pull and deploy
gcloud auth configure-docker gcr.io
docker pull gcr.io/duotopia-472708/duotopia-backend-vm:manual
docker stop duotopia-backend 2>/dev/null || true
docker rm duotopia-backend 2>/dev/null || true
docker run -d \
  --name duotopia-backend \
  --restart unless-stopped \
  -p 80:8080 \
  --env-file /tmp/backend.env \
  gcr.io/duotopia-472708/duotopia-backend-vm:manual
```

## 🔍 Monitoring & Troubleshooting

### Check VM Status

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Check container status
docker ps -a --filter name=duotopia-backend

# Expected output:
# CONTAINER ID   IMAGE         STATUS        PORTS                  NAMES
# abc123def456   gcr.io/...    Up 2 hours    0.0.0.0:80->8080/tcp   duotopia-backend
```

### View Logs

```bash
# SSH to VM first
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# View real-time logs
docker logs -f duotopia-backend

# View last 100 lines
docker logs --tail=100 duotopia-backend

# View logs with timestamps
docker logs -f --timestamps duotopia-backend
```

### Health Check

```bash
# From anywhere
curl http://34.81.38.211/api/health

# Expected response:
# {
#   "status": "healthy",
#   "environment": "production-vm",
#   "version": "1.0.0",
#   ...
# }
```

### Resource Usage

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Check CPU and memory
top

# Check disk usage
df -h

# Check memory details
free -h

# Check Docker stats
docker stats duotopia-backend --no-stream
```

## 🛠️ Common Operations

### Restart Container

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Restart container
docker restart duotopia-backend

# Wait 10 seconds and verify
sleep 10
curl http://localhost/api/health
```

### Stop Container

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Stop container
docker stop duotopia-backend

# Verify stopped
docker ps -a --filter name=duotopia-backend
```

### Update Environment Variables

```bash
# 1. Update environment file on VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# 2. Edit environment file (on VM)
nano /tmp/backend.env

# 3. Restart container to apply changes
docker restart duotopia-backend

# 4. Verify new settings
docker logs --tail=20 duotopia-backend
```

### Clean Up Old Images

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# List all images
docker images | grep duotopia-backend-vm

# Remove unused images (keeps running container)
docker image prune -f

# Remove specific old image
docker rmi gcr.io/duotopia-472708/duotopia-backend-vm:<OLD_SHA>
```

## 🔄 Rollback to Previous Version

### Step 1: Find Previous Version

```bash
# List all available image tags
gcloud container images list-tags gcr.io/duotopia-472708/duotopia-backend-vm

# Example output:
# DIGEST        TAGS         TIMESTAMP
# sha256:abc123 abc1234567   2025-12-07T10:30:00
# sha256:def456 def4567890   2025-12-06T15:20:00  <- Previous version
```

### Step 2: Deploy Previous Version

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Stop current container
docker stop duotopia-backend
docker rm duotopia-backend

# Deploy previous version (replace <OLD_SHA> with actual commit SHA)
docker run -d \
  --name duotopia-backend \
  --restart unless-stopped \
  -p 80:8080 \
  --env-file /tmp/backend.env \
  gcr.io/duotopia-472708/duotopia-backend-vm:<OLD_SHA>

# Verify rollback
curl http://localhost/api/health
docker logs --tail=50 duotopia-backend
```

## 🚨 Emergency Procedures

### Service Not Responding

```bash
# 1. Check if VM is running
gcloud compute instances describe duotopia-prod-vm --zone=asia-east1-b

# 2. Check if container is running
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker ps -a --filter name=duotopia-backend"

# 3. Check container logs for errors
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker logs --tail=100 duotopia-backend"

# 4. Restart container if needed
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker restart duotopia-backend"
```

### VM Not Accessible

```bash
# 1. Check VM status
gcloud compute instances describe duotopia-prod-vm \
  --zone=asia-east1-b \
  --format='value(status)'

# 2. Start VM if stopped
gcloud compute instances start duotopia-prod-vm --zone=asia-east1-b

# 3. Check firewall rules
gcloud compute firewall-rules list --filter="name~duotopia"

# 4. Verify static IP
gcloud compute addresses describe duotopia-prod-vm-ip \
  --region=asia-east1 \
  --format='value(address)'
```

### Database Connection Issues

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# Check if environment variables are set correctly
docker exec duotopia-backend env | grep DATABASE_URL

# Test database connection from container
docker exec -it duotopia-backend python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
print('✅ Database connection successful')
conn.close()
"
```

## 📊 Performance Monitoring

### Set Up Monitoring Script

```bash
# Create monitoring script on VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# On VM: Create monitor.sh
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
  echo "=== $(date) ==="
  echo "Container Status:"
  docker ps --filter name=duotopia-backend --format "table {{.Status}}\t{{.Ports}}"
  echo ""
  echo "Resource Usage:"
  docker stats duotopia-backend --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}"
  echo ""
  echo "Recent Logs:"
  docker logs --tail=5 duotopia-backend
  echo "========================================"
  sleep 60
done
EOF

chmod +x monitor.sh

# Run in background
nohup ./monitor.sh > monitor.log 2>&1 &
```

### Check Monitoring Logs

```bash
# SSH to VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# View monitoring logs
tail -f monitor.log
```

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` files or expose secrets in logs
2. **SSH Access**: Use `gcloud compute ssh` (automatic key management)
3. **Firewall**: Only port 80 (HTTP) and 22 (SSH) should be open
4. **Updates**: Regularly update VM OS and Docker
5. **Backups**: Database backups handled by Supabase

## 📚 Additional Resources

- **GitHub Actions Workflow**: `.github/workflows/deploy-vm-prod.yml`
- **CICD Documentation**: `CICD.md` (VM Deployment section)
- **Docker Documentation**: https://docs.docker.com/
- **GCP VM Documentation**: https://cloud.google.com/compute/docs

## 💡 Tips & Tricks

### Alias for Quick SSH

Add to your local `~/.bashrc` or `~/.zshrc`:

```bash
alias vm-ssh='gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b'
alias vm-logs='gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b --command="docker logs -f duotopia-backend"'
alias vm-status='gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b --command="docker ps -a --filter name=duotopia-backend"'
```

Then you can simply run:

```bash
vm-ssh        # SSH to VM
vm-logs       # View logs
vm-status     # Check status
```

### Quick Health Check Script

```bash
#!/bin/bash
# save as check-vm-health.sh

VM_IP="34.81.38.211"
HEALTH_ENDPOINT="http://${VM_IP}/api/health"

echo "Checking VM health..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT")

if [ "$RESPONSE" -eq 200 ]; then
    echo "✅ VM is healthy (HTTP $RESPONSE)"
    curl -s "$HEALTH_ENDPOINT" | jq '.'
else
    echo "❌ VM is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

## 🆚 When to Use VM vs Cloud Run

**Use VM when**:
- Testing cost optimization
- Need consistent performance (no cold starts)
- Want full control over container lifecycle
- Experimenting with different configurations

**Use Cloud Run when**:
- Production traffic with variable load
- Need automatic scaling
- Want zero maintenance
- Prefer pay-per-use pricing

---

**Last Updated**: 2025-12-07
**Maintained By**: Duotopia DevOps Team
