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
