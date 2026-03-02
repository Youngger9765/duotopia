"""
訂閱方案常數 - 所有方案相關的數值統一在此定義

修改此檔案即可全域更新方案名稱、價格與配額。
"""

# === 方案名稱 ===
PLAN_FREE_TRIAL = "Free Trial"
PLAN_TUTOR = "Tutor Teachers"
PLAN_SCHOOL = "School Teachers"
PLAN_DEMO_UNLIMITED = "Demo Unlimited Plan"
PLAN_VIP = "VIP"

# === 試用方案 ===
TRIAL_QUOTA = 2000
TRIAL_DAYS = 365

# === 訂閱價格 (TWD/月) ===
PLAN_PRICES = {
    PLAN_TUTOR: 299,
    PLAN_SCHOOL: 599,
}
DEFAULT_PRICE = 299

# === 每月點數配額 ===
PLAN_QUOTAS = {
    PLAN_FREE_TRIAL: 2000,
    PLAN_TUTOR: 2000,
    PLAN_SCHOOL: 6000,
    PLAN_DEMO_UNLIMITED: 999999,
    PLAN_VIP: 0,  # VIP 由 Admin 自訂
}
