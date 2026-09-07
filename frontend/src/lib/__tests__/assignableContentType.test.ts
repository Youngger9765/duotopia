/**
 * 可派發型別的白名單（Issue #1030）。
 *
 * 這張單的起因是「情境對話尚未開放派發，卻在派發流程裡點得下去，而且會被當成
 * 單字集」。所以測試盯的是白名單本身：認得的兩種可派，**其餘一律不可派**。
 */
import { describe, it, expect } from "vitest";
import {
  isAssignableContentType,
  isExampleSentencesType,
  isVocabularySetType,
} from "../assignableContentType";

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

  it("情境對話不可派發 —— 學生端作答與批改頁都還沒做（#1031）", () => {
    expect(isAssignableContentType("SCENARIO_DIALOGUE")).toBe(false);
    expect(isAssignableContentType("scenario_dialogue")).toBe(false);
  });

  it.each(["MULTIPLE_CHOICE", "SOMETHING_NEW", "", null, undefined])(
    "未知型別 %s 預設不可派發（白名單，不是黑名單）",
    (type) => {
      expect(isAssignableContentType(type)).toBe(false);
    },
  );
});
