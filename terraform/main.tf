terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# First, just create a storage bucket
resource "google_storage_bucket" "test" {
  name          = "${var.project_id}-test-bucket"
  location      = var.region
  force_destroy = true
}