/**
 * 訂閱方案常數 - 所有方案相關的數值統一在此定義
 *
 * 修改此檔案即可全域更新方案名稱、價格與配額。
 */

// === 方案名稱 ===
export const PLAN_NAMES = {
  FREE_TRIAL: "Free Trial",
  TUTOR: "Tutor Teachers",
  SCHOOL: "School Teachers",
} as const;

// === 試用方案 ===
export const TRIAL_QUOTA = 2000;
export const TRIAL_DAYS = 365;

// === 訂閱價格 (TWD/月) ===
export const PLAN_PRICES = {
  [PLAN_NAMES.TUTOR]: 299,
  [PLAN_NAMES.SCHOOL]: 599,
} as const;

// === 每月點數配額 ===
export const PLAN_QUOTAS = {
  [PLAN_NAMES.FREE_TRIAL]: 2000,
  [PLAN_NAMES.TUTOR]: 2000,
  [PLAN_NAMES.SCHOOL]: 6000,
} as const;

// === 點數包定義 ===
export const CREDIT_PACKAGES = {
  "pkg-1000": { points: 1000, bonus: 0, price: 180 },
  "pkg-2000": { points: 2000, bonus: 0, price: 320 },
  "pkg-5000": { points: 5000, bonus: 200, price: 700 },
  "pkg-10000": { points: 10000, bonus: 500, price: 1200 },
  "pkg-20000": { points: 20000, bonus: 800, price: 2000 },
} as const;

export type CreditPackageId = keyof typeof CREDIT_PACKAGES;

// 點數包效期（天）
export const CREDIT_PACKAGE_VALIDITY_DAYS = 365;
