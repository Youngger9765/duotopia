variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "duotopia-469413"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-east1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-east1-a"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_user" {
  description = "Database username"
  type        = string
  default     = "duotopia"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT Secret Key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth Client ID"
  type        = string
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "sendgrid_api_key" {
  description = "SendGrid API Key"
  type        = string
  sensitive   = true
}