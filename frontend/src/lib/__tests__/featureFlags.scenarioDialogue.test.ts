/**
 * 情境對話的前端開關 — Issue #1039。
 *
 * 這個開關存在的理由不是「功能沒做完」，而是「**還沒被人驗過就已經在 prod 上**」
 * （PR #1038 把 staging 發到 main 並成功部署）。與其 revert 一整條發版線，改成把
 * 前端入口關掉：不動歷史、不動資料庫，日後打開只是翻一個布林值。
 *
 * 兩種狀態都要測 —— 只測關閉會讓「打開之後其實壞掉」在下一次發版才爆出來，
 * 那正是這張單想避免的情況。
 *
 * 用 `vi.resetModules()` + 動態 import 而不是靜態 import：開關是模組層級常數，
 * 必須在每次 import 前換掉 mock 才驗得到兩種狀態。
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

async function loadWith(enabled: boolean) {
  vi.resetModules();
  vi.doMock("../featureFlags", () => ({
    SCENARIO_DIALOGUE_ENABLED: enabled,
  }));
  return await import("../assignableContentType");
}

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock("../featureFlags");
});

describe("開關關閉時，情境對話不可派發", () => {
  it("isAssignableContentType 對情境對話回 false", async () => {
    const { isAssignableContentType } = await loadWith(false);
    expect(isAssignableContentType("SCENARIO_DIALOGUE")).toBe(false);
  });

  it("點下去給的是「還不能派發」，不是「模式與型別不合」", async () => {
    // 兩句話對老師的意思完全不同：前者是「別等了，先用別的」，後者是
    // 「換個模式就可以」。關閉期間換哪個模式都沒用，必須是前者。
    const { explainNotSelectable } = await loadWith(false);
    expect(
      explainNotSelectable("SCENARIO_DIALOGUE", "scenario_dialogue"),
    ).toEqual({ kind: "not_assignable" });
  });

  it("整課都是情境對話時，不會叫老師去換模式", async () => {
    const { reasonNothingSelectable } = await loadWith(false);
    expect(reasonNothingSelectable(["SCENARIO_DIALOGUE"])).toBe(
      "not_assignable",
    );
  });

  it("例句集與單字集完全不受影響", async () => {
    const { isAssignableContentType } = await loadWith(false);
    expect(isAssignableContentType("EXAMPLE_SENTENCES")).toBe(true);
    expect(isAssignableContentType("VOCABULARY_SET")).toBe(true);
    expect(isAssignableContentType("READING_ASSESSMENT")).toBe(true);
    expect(isAssignableContentType("SENTENCE_MAKING")).toBe(true);
  });
});

describe("開關打開時，行為回到 #1031 交付的樣子", () => {
  it("isAssignableContentType 對情境對話回 true", async () => {
    const { isAssignableContentType } = await loadWith(true);
    expect(isAssignableContentType("SCENARIO_DIALOGUE")).toBe(true);
  });

  it("情境對話模式下選情境對話是選得到的", async () => {
    const { explainNotSelectable } = await loadWith(true);
    expect(
      explainNotSelectable("SCENARIO_DIALOGUE", "scenario_dialogue"),
    ).toBeNull();
  });

  it("整課都是情境對話時，回的是「模式不合」而不是「不能派發」", async () => {
    const { reasonNothingSelectable } = await loadWith(true);
    expect(reasonNothingSelectable(["SCENARIO_DIALOGUE"])).toBe(
      "mode_mismatch",
    );
  });
});

describe("開關本身", () => {
  it("預設是關閉的 —— 打開必須是一個明確的、走發版流程的動作", async () => {
    vi.resetModules();
    vi.doUnmock("../featureFlags");
    const { SCENARIO_DIALOGUE_ENABLED } = await import("../featureFlags");
    expect(SCENARIO_DIALOGUE_ENABLED).toBe(false);
  });

  it("型別是 boolean 而不是字面值 false —— 兩個分支都要編得過", async () => {
    const flags = await import("../featureFlags");
    expect(typeof flags.SCENARIO_DIALOGUE_ENABLED).toBe("boolean");
  });
});
