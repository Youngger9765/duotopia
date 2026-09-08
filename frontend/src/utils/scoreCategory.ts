export type ScoreCategory = "speaking" | "listening" | "reading" | "writing";

/**
 * 前端版成績類別解析，鏡射後端 `backend/utils/score_category.py` 的 `resolve_score_category`
 * （唯一真相仍在後端，前端只在派發 UI 預覽用）。規則化的等價實作見
 * `lib/practiceMode.ts` 的 `resolveScoreCategoryFE`，兩者由 `practiceMode.test.ts` 斷言等價。
 *
 * 注意（皆於 #878 調整，無回填——既有作業保留原值，僅新建/更新者套新規則）：
 * - `rearrangement` / `word_selection` / `word_selection_quiz` 無音檔→ reading（理解/選擇）、有音檔→ listening。
 * - `word_cloze` / `word_cloze_quiz` 改走通則（打字填空＝產出文字 → 無音檔 writing、有音檔 listening），
 *   不再恆 reading。
 */
export function getScoreCategory(
  practiceMode: string | undefined | null,
  playAudio: boolean | undefined | null,
): ScoreCategory {
  const mode = (practiceMode ?? "").trim().toLowerCase();
  const audioOn = Boolean(playAudio);

  // #1013 / #1031: 情境對話與朗讀同屬「開口作答」，題目音檔只是提示素材，
  // 不該因為 play_audio 就翻成聽力。唯一判定在後端 utils/score_category.py。
  if (
    mode === "reading" ||
    mode === "word_reading" ||
    mode === "scenario_dialogue"
  )
    return "speaking";
  if (
    (mode === "rearrangement" ||
      mode === "word_selection" ||
      mode === "word_selection_quiz") &&
    !audioOn
  )
    return "reading";
  return audioOn ? "listening" : "writing";
}
