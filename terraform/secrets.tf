# JWT Secret
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret
}

# Google OAuth Client Secret
resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "google-client-secret"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "google_client_secret" {
  secret      = google_secret_manager_secret.google_client_secret.id
  secret_data = var.google_client_secret
}

# OpenAI API Key
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# SendGrid API Key
resource "google_secret_manager_secret" "sendgrid_api_key" {
  secret_id = "sendgrid-api-key"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "sendgrid_api_key" {
  secret      = google_secret_manager_secret.sendgrid_api_key.id
  secret_data = var.sendgrid_api_key
}