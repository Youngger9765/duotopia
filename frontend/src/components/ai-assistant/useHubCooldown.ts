const STORAGE_KEY_COUNT = "ai-hub-unclear-count";
const STORAGE_KEY_COOLDOWN = "ai-hub-cooldown-until";
const MAX_UNCLEAR = 3;
const COOLDOWN_MS = 12 * 60 * 60 * 1000; // 12 hours

export function useHubCooldown() {
  const getCount = () =>
    parseInt(localStorage.getItem(STORAGE_KEY_COUNT) || "0", 10);

  const getCooldownUntil = () =>
    parseInt(localStorage.getItem(STORAGE_KEY_COOLDOWN) || "0", 10);

  const isCoolingDown = () => Date.now() < getCooldownUntil();

  /**
   * Record an "unclear" input. Returns true if cooldown was triggered.
   */
  const recordUnclear = (): boolean => {
    const count = getCount() + 1;
    localStorage.setItem(STORAGE_KEY_COUNT, String(count));
    if (count >= MAX_UNCLEAR) {
      localStorage.setItem(
        STORAGE_KEY_COOLDOWN,
        String(Date.now() + COOLDOWN_MS),
      );
      localStorage.setItem(STORAGE_KEY_COUNT, "0");
      return true;
    }
    return false;
  };

  const resetCount = () => localStorage.setItem(STORAGE_KEY_COUNT, "0");

  return { isCoolingDown, recordUnclear, resetCount, getCooldownUntil };
}
