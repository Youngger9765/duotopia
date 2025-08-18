output "frontend_url" {
  description = "URL of the frontend Cloud Run service"
  value       = google_cloud_run_service.frontend.status[0].url
}

output "backend_url" {
  description = "URL of the backend API Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "uploads_bucket" {
  description = "GCS bucket for uploads"
  value       = google_storage_bucket.uploads.name
}

output "artifact_registry" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/duotopia"
}