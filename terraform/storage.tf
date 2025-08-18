# Bucket for uploaded files (audio recordings, etc.)
resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-uploads"
  location      = var.region
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = var.environment == "production" ? ["https://duotopia.com"] : ["*"]
    method          = ["GET", "POST", "PUT", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  versioning {
    enabled = true
  }
}

# Bucket for static assets (if needed)
resource "google_storage_bucket" "static" {
  name          = "${var.project_id}-static"
  location      = var.region
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }
}

# Bucket for Terraform state (created separately)
resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }
}