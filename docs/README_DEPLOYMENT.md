# Duotopia Deployment Guide

## 🚀 Quick Start (Day 1 Deployment)

### Prerequisites
1. Google Cloud Platform account with billing enabled
2. Tools installed:
   - Node.js 18+
   - Python 3.11+
   - Docker
   - Terraform
   - Google Cloud SDK (`gcloud`)

### Initial Setup

1. **Clone and setup project**
```bash
git clone <your-repo>
cd duotopia
./scripts/setup.sh
```

2. **Configure GCP**
```bash
# Login to GCP
gcloud auth login
gcloud config set project duotopia-469413

# Enable billing for the project
# Visit: https://console.cloud.google.com/billing
```

3. **Set up secrets**
Edit `terraform/terraform.tfvars`:
```hcl
db_password          = "secure-password-here"
jwt_secret           = "secure-jwt-secret-here"
google_client_id     = "your-oauth-client-id"
google_client_secret = "your-oauth-client-secret"
openai_api_key       = "your-openai-api-key"
sendgrid_api_key     = "your-sendgrid-api-key"
```

### Deploy to Production

```bash
# Deploy everything with one command
./scripts/deploy.sh
```

This will:
1. Enable required GCP APIs
2. Create infrastructure with Terraform
3. Build and deploy Docker images
4. Set up Cloud SQL database
5. Configure networking and security

### GitHub Actions Setup

1. **Create Service Account for CI/CD**
```bash
# Create service account
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding duotopia-469413 \
    --member="serviceAccount:github-actions@duotopia-469413.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"
```

2. **Set up Workload Identity Federation**
```bash
# Follow Google's guide to set up Workload Identity Federation
# This allows GitHub Actions to authenticate without service account keys
```

3. **Add GitHub Secrets**
- `WIF_PROVIDER`: Workload Identity Federation provider
- `DB_PASSWORD`: Database password
- `JWT_SECRET`: JWT secret key
- `GOOGLE_CLIENT_ID`: OAuth client ID
- `GOOGLE_CLIENT_SECRET`: OAuth client secret
- `OPENAI_API_KEY`: OpenAI API key
- `SENDGRID_API_KEY`: SendGrid API key

### Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Cloud SQL  │
│ (Cloud Run) │     │ (Cloud Run) │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │     GCS     │
                    │  (Storage)  │
                    └─────────────┘
```

### Monitoring & Operations

1. **View logs**
```bash
gcloud run logs read --service=duotopia-backend
gcloud run logs read --service=duotopia-frontend
```

2. **Database access**
```bash
gcloud sql connect duotopia-db-production --user=duotopia
```

3. **Update deployment**
```bash
# Push to main branch triggers automatic deployment
git push origin main
```

### Cost Optimization

- Cloud Run scales to zero when not in use
- Cloud SQL uses smallest tier for development
- Automatic backup retention is minimized
- All resources are in the same region

### Troubleshooting

1. **API not enabled error**
```bash
gcloud services enable <service-name>.googleapis.com
```

2. **Permission denied**
```bash
# Check current authentication
gcloud auth list

# Re-authenticate if needed
gcloud auth login
```

3. **Terraform state issues**
```bash
# Reinitialize Terraform
cd terraform
terraform init -reconfigure
```

### Security Notes

- All secrets are stored in Secret Manager
- Database uses private IP within VPC
- HTTPS is enforced on all endpoints
- Service accounts follow least privilege principle

### Next Steps

1. Set up custom domain
2. Configure monitoring alerts
3. Set up backup automation
4. Implement staging environment

### Support

For issues or questions:
1. Check Cloud Run logs
2. Review Terraform output
3. Verify all secrets are set correctly