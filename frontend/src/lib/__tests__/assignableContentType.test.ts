/**
 * 可派發型別的白名單（Issue #1030）。
 *
 * 這張單的起因是「情境對話尚未開放派發，卻在派發流程裡點得下去，而且會被當成
 * 單字集」。所以測試盯的是白名單本身：認得的兩種可派，**其餘一律不可派**。
 */
import { describe, it, expect } from "vitest";
import {
  explainNotSelectable,
  isAssignableContentType,
  isExampleSentencesType,
  isScenarioDialogueType,
  isVocabularySetType,
  reasonNothingSelectable,
} from "../assignableContentType";
import {
  DATASET_LABEL_KEY,
  PRACTICE_MODE_REGISTRY,
  type PracticeMode,
} from "../practiceMode";

describe("例句集 / 單字集判定（含 legacy 名稱）", () => {
  it.each(["EXAMPLE_SENTENCES", "READING_ASSESSMENT", "example_sentences"])(
    "%s 是例句集",
    (type) => {
      expect(isExampleSentencesType(type)).toBe(true);
      expect(isVocabularySetType(type)).toBe(false);
    },
  );

  it.each(["VOCABULARY_SET", "SENTENCE_MAKING", "vocabulary_set"])(
    "%s 是單字集",
    (type) => {
      expect(isVocabularySetType(type)).toBe(true);
      expect(isExampleSentencesType(type)).toBe(false);
    },
  );
});

describe("可派發白名單", () => {
  it.each([
    "EXAMPLE_SENTENCES",
    "READING_ASSESSMENT",
    "VOCABULARY_SET",
    "SENTENCE_MAKING",
  ])("%s 可以派發", (type) => {
    expect(isAssignableContentType(type)).toBe(true);
  });

  it("情境對話可以派發（#1031 起：學生端作答與批改頁都做好了）", () => {
    expect(isAssignableContentType("SCENARIO_DIALOGUE")).toBe(true);
    expect(isAssignableContentType("scenario_dialogue")).toBe(true);
  });

  it.each(["MULTIPLE_CHOICE", "SOMETHING_NEW", "", null, undefined])(
    "未知型別 %s 預設不可派發（白名單仍在，開放題型必須明確加進來）",
    (type) => {
      expect(isAssignableContentType(type)).toBe(false);
    },
  );
});

// 「停用的卡片要不要保持可點」的規則已於 #1033 統一（全部都要），
// 判定不再需要一個函式 —— 行為改由 ContentSelectCard 的測試守著
// （見 components/assignment/__tests__/ContentSelectCard.test.tsx）。

describe("整課都不能選時，原因要分得出來（PR #1032 review round 2）", () => {
  // 用仍不可派發的型別當例子（情境對話已於 #1031 開放）——
  // 這裡驗的是規則，不是某個特定題型
  it("整課都是還不能派發的題型 → 叫老師換模式沒有用", () => {
    expect(reasonNothingSelectable(["MULTIPLE_CHOICE"])).toBe("not_assignable");
    expect(reasonNothingSelectable(["MULTIPLE_CHOICE", "SOMETHING_NEW"])).toBe(
      "not_assignable",
    );
  });

  it("課裡有可派發的內容 → 是模式／型別不合，換個模式就可以", () => {
    expect(
      reasonNothingSelectable(["MULTIPLE_CHOICE", "EXAMPLE_SENTENCES"]),
    ).toBe("mode_mismatch");
    expect(reasonNothingSelectable(["VOCABULARY_SET"])).toBe("mode_mismatch");
    // #1031 起情境對話也算可派發
    expect(reasonNothingSelectable(["SCENARIO_DIALOGUE"])).toBe(
      "mode_mismatch",
    );
  });

  it("空的一課視為「還不能派發」，不會誤導成換模式", () => {
    expect(reasonNothingSelectable([])).toBe("not_assignable");
  });
});

describe("情境對話自成一個資料集（#1031）", () => {
  it("只認 SCENARIO_DIALOGUE（大小寫皆可）", () => {
    expect(isScenarioDialogueType("SCENARIO_DIALOGUE")).toBe(true);
    expect(isScenarioDialogueType("scenario_dialogue")).toBe(true);
    expect(isScenarioDialogueType("VOCABULARY_SET")).toBe(false);
    expect(isScenarioDialogueType(null)).toBe(false);
  });
});

describe("點了灰掉的卡片要給哪一句提示（Issue #1033）", () => {
  it("題型還不能派 → 叫老師換模式沒有用", () => {
    expect(explainNotSelectable("MULTIPLE_CHOICE", "reading")).toEqual({
      kind: "not_assignable",
    });
  });

  it("未選模式時，可派發的型別本來就選得到 —— 沒有要解釋的事", () => {
    expect(explainNotSelectable("EXAMPLE_SENTENCES", "")).toBeNull();
    expect(explainNotSelectable("SCENARIO_DIALOGUE", "")).toBeNull();
  });

  it("選得到的組合回 null，不會憑空跳提示", () => {
    expect(explainNotSelectable("VOCABULARY_SET", "word_reading")).toBeNull();
    expect(explainNotSelectable("EXAMPLE_SENTENCES", "reading")).toBeNull();
    expect(
      explainNotSelectable("SCENARIO_DIALOGUE", "scenario_dialogue"),
    ).toBeNull();
  });

  describe("模式與型別不合時，要說對「現在能選什麼」", () => {
    /**
     * 這句提示原本寫死「只能選擇單字集」。在它還是死碼時看不出問題（原生 disabled
     * 吃掉了 click），#1033 讓它真的出得來，內容就必須是對的 —— 指錯方向比沒有提示
     * 更糟。名單取自 registry，不是二分法猜的（#1034 的教訓）。
     */
    it("單字模式下點例句集 → 說單字集", () => {
      expect(explainNotSelectable("EXAMPLE_SENTENCES", "word_reading")).toEqual(
        {
          kind: "mode_mismatch",
          allowedDatasetKeys: [DATASET_LABEL_KEY.vocabulary_set],
        },
      );
    });

    it("情境對話模式下點例句集 → 說情境對話，不是單字集", () => {
      expect(
        explainNotSelectable("EXAMPLE_SENTENCES", "scenario_dialogue"),
      ).toEqual({
        kind: "mode_mismatch",
        allowedDatasetKeys: [DATASET_LABEL_KEY.scenario_dialogue],
      });
    });

    it("朗讀模式下點情境對話 → 說例句集與單字集，不是單字集而已", () => {
      expect(explainNotSelectable("SCENARIO_DIALOGUE", "reading")).toEqual({
        kind: "mode_mismatch",
        allowedDatasetKeys: [
          DATASET_LABEL_KEY.example_sentences,
          DATASET_LABEL_KEY.vocabulary_set,
        ],
      });
    });

    it("重組模式下點情境對話 → 同樣是例句集與單字集", () => {
      expect(
        explainNotSelectable("SCENARIO_DIALOGUE", "rearrangement"),
      ).toEqual({
        kind: "mode_mismatch",
        allowedDatasetKeys: [
          DATASET_LABEL_KEY.example_sentences,
          DATASET_LABEL_KEY.vocabulary_set,
        ],
      });
    });

    it("任何 mode_mismatch 都給得出非空的名單", () => {
      // 空名單會讓提示變成「目前只能選擇，請先清除…」這種殘句
      for (const mode of Object.keys(
        PRACTICE_MODE_REGISTRY,
      ) as PracticeMode[]) {
        for (const type of [
          "EXAMPLE_SENTENCES",
          "VOCABULARY_SET",
          "SCENARIO_DIALOGUE",
        ]) {
          const result = explainNotSelectable(type, mode);
          if (result?.kind === "mode_mismatch") {
            expect(result.allowedDatasetKeys.length).toBeGreaterThan(0);
          }
        }
      }
    });
  });
});
