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

# === 點數包定義 ===
CREDIT_PACKAGES = {
    "pkg-1000": {"points": 1000, "bonus": 0, "price": 180},
    "pkg-2000": {"points": 2000, "bonus": 0, "price": 320},
    "pkg-5000": {"points": 5000, "bonus": 200, "price": 700},
    "pkg-10000": {"points": 10000, "bonus": 500, "price": 1200},
    "pkg-20000": {"points": 20000, "bonus": 800, "price": 2000},
}

# 機構可購買的點數包
ORG_ALLOWED_PACKAGES = ["pkg-20000"]

# 點數包效期（天）
CREDIT_PACKAGE_VALIDITY_DAYS = 365
