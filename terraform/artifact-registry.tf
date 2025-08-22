# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "duotopia"
  format        = "DOCKER"
  
  description = "Docker repository for Duotopia images"
}

# Note: Cloud Run services are now managed by GitHub Actions
# This follows the principle of separating infrastructure (Terraform) 
# from application deployment (CI/CD)