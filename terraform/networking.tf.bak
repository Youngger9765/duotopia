# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "duotopia-vpc"
  auto_create_subnetworks = false
}

# Subnet for Cloud Run
resource "google_compute_subnetwork" "cloudrun" {
  name          = "duotopia-cloudrun-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  private_ip_google_access = true
}

# Subnet for Cloud SQL
resource "google_compute_subnetwork" "sql" {
  name          = "duotopia-sql-subnet"
  ip_cidr_range = "10.0.2.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  private_ip_google_access = true
}

# VPC Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "duotopia-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.0.3.0/28"
  
  min_instances = 2
  max_instances = 10
}

# Reserve IP range for VPC peering
resource "google_compute_global_address" "private_ip_address" {
  name          = "duotopia-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# Create VPC peering
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}