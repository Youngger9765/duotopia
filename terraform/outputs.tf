# Infrastructure outputs for use by application deployment

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "database_ip" {
  description = "Cloud SQL instance IP address"
  value       = google_sql_database_instance.main.public_ip_address
}

output "uploads_bucket" {
  description = "GCS bucket for uploads"
  value       = google_storage_bucket.uploads.name
}

output "static_bucket" {
  description = "GCS bucket for static assets"
  value       = google_storage_bucket.static.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/duotopia"
}

output "backend_service_account" {
  description = "Service account email for backend services"
  value       = google_service_account.backend.email
}

# output "github_actions_service_account" {
#   description = "Service account email for GitHub Actions"
#   value       = google_service_account.github_actions.email
# }

# Secret Manager secret names for application reference
output "secret_db_connection" {
  description = "Secret Manager secret name for database connection"
  value       = google_secret_manager_secret.db_connection.secret_id
}

output "secret_jwt" {
  description = "Secret Manager secret name for JWT secret"
  value       = google_secret_manager_secret.jwt_secret.secret_id
}

output "secret_google_oauth" {
  description = "Secret Manager secret name for Google OAuth client secret"
  value       = google_secret_manager_secret.google_client_secret.secret_id
}

output "secret_openai" {
  description = "Secret Manager secret name for OpenAI API key"
  value       = google_secret_manager_secret.openai_api_key.secret_id
}

output "secret_sendgrid" {
  description = "Secret Manager secret name for SendGrid API key"
  value       = google_secret_manager_secret.sendgrid_api_key.secret_id
}