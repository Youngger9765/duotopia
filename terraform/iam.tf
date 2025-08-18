# Service Account for Backend
resource "google_service_account" "backend" {
  account_id   = "duotopia-backend"
  display_name = "Duotopia Backend Service Account"
}

# Service Account for Cloud Build
resource "google_service_account" "cloudbuild" {
  account_id   = "duotopia-cloudbuild"
  display_name = "Duotopia Cloud Build Service Account"
}

# Backend permissions
resource "google_project_iam_member" "backend_permissions" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Cloud Build permissions
resource "google_project_iam_member" "cloudbuild_permissions" {
  for_each = toset([
    "roles/cloudbuild.builds.builder",
    "roles/run.developer",
    "roles/artifactregistry.writer",
    "roles/logging.logWriter",
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# Allow Cloud Build to act as backend service account
resource "google_service_account_iam_member" "cloudbuild_actas_backend" {
  service_account_id = google_service_account.backend.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloudbuild.email}"
}