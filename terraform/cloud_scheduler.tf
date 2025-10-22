# Cloud Scheduler for Monthly Renewal
# 每月 1 號凌晨 2:00 執行自動續訂

resource "google_cloud_scheduler_job" "monthly_renewal" {
  name        = "monthly-renewal-job"
  description = "每月 1 號執行自動續訂"
  schedule    = "0 2 1 * *"  # 每月 1 號凌晨 2:00 (Cron: 分 時 日 月 星期)
  time_zone   = "Asia/Taipei"
  region      = var.region

  http_target {
    uri         = "${var.backend_url}/api/cron/monthly-renewal"
    http_method = "POST"

    headers = {
      "X-Cron-Secret" = var.cron_secret
      "Content-Type"  = "application/json"
    }

    # 重試設定
    retry_config {
      retry_count = 3
    }
  }
}

# Cloud Scheduler for Renewal Reminder
# 每天凌晨 3:00 檢查即將到期的用戶並發送提醒

resource "google_cloud_scheduler_job" "renewal_reminder" {
  name        = "renewal-reminder-job"
  description = "每天檢查即將到期的訂閱並發送提醒"
  schedule    = "0 3 * * *"  # 每天凌晨 3:00
  time_zone   = "Asia/Taipei"
  region      = var.region

  http_target {
    uri         = "${var.backend_url}/api/cron/renewal-reminder"
    http_method = "POST"

    headers = {
      "X-Cron-Secret" = var.cron_secret
      "Content-Type"  = "application/json"
    }

    # 重試設定
    retry_config {
      retry_count = 2
    }
  }
}

# 變數定義（在 variables.tf 中）
variable "cron_secret" {
  description = "Cron Job Secret Key"
  type        = string
  sensitive   = true
}

variable "backend_url" {
  description = "Backend API URL"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-east1"
}
