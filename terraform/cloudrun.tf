# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "duotopia"
  format        = "DOCKER"
  
  description = "Docker repository for Duotopia images"
}

# Cloud Run Service - Backend API
resource "google_cloud_run_service" "backend" {
  name     = "duotopia-backend"
  location = var.region
  
  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/duotopia/backend:latest"
        
        ports {
          container_port = 8000
        }
        
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_connection.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.uploads.name
        }
        
        env {
          name = "JWT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "GOOGLE_CLIENT_ID"
          value = var.google_client_id
        }
        
        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_secret.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openai_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "SENDGRID_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.sendgrid_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = "2"
            memory = "1Gi"
          }
        }
      }
      
      service_account_name = google_service_account.backend.email
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"        = "100"
        "autoscaling.knative.dev/minScale"        = var.environment == "production" ? "1" : "0"
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.name
        "run.googleapis.com/vpc-access-egress"    = "private-ranges-only"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# Cloud Run Service - Frontend
resource "google_cloud_run_service" "frontend" {
  name     = "duotopia-frontend"
  location = var.region
  
  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/duotopia/frontend:latest"
        
        ports {
          container_port = 80
        }
        
        env {
          name  = "VITE_API_URL"
          value = google_cloud_run_service.backend.status[0].url
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "autoscaling.knative.dev/minScale" = var.environment == "production" ? "1" : "0"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# IAM - Allow public access to frontend
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM - Allow public access to backend API
resource "google_cloud_run_service_iam_member" "backend_public" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}