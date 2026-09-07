/**
 * 內容型別 → 能不能派發（Issue #1030）。
 *
 * 這幾個判定原本寫在 `AssignmentDialog.tsx` 裡（3000 行的元件，沒有測試檔），
 * 抽出來是為了讓「哪些型別可以派發」這件事**驗得到** —— 這張單的重點正是它先前
 * 判斷錯了。
 *
 * ## 為什麼需要「可派發」這個概念
 *
 * `AssignmentDialog` 原本只有「是不是例句集」「是不是單字集」兩個判定，其餘型別沒有
 * 任何處理，於是：
 *
 * * Step 1 的 dataset 是二分法（`=== "example_sentences" ? ... : "vocabulary_set"`），
 *   情境對話會被**當成單字集**，顯示單字朗讀／拼寫／克漏字一整排錯的模式；
 * * `isContentSelectable` 在未選模式時一律回 `true`，情境對話在清單裡看起來可以勾。
 *
 * 結果是老師可以派出一份「用單字集模式跑的情境對話作業」，學生端再落到不認得的
 * practice_mode。所以這裡把判定從「是不是這兩種」補上「**其餘一律不可派發**」。
 *
 * ## 情境對話什麼時候會變成可派發
 *
 * 等 #1031（學生端作答 + 批改頁 + 派發流程）做完。那時是把 `SCENARIO_DIALOGUE`
 * 從這裡的排除名單移到支援名單，而不是把整個防呆拿掉。
 */

/** 例句集（含 legacy 名稱 READING_ASSESSMENT） */
export function isExampleSentencesType(type?: string | null): boolean {
  const normalized = (type ?? "").toUpperCase();
  return ["READING_ASSESSMENT", "EXAMPLE_SENTENCES"].includes(normalized);
}

/** 單字集（含 legacy 名稱 SENTENCE_MAKING） */
export function isVocabularySetType(type?: string | null): boolean {
  const normalized = (type ?? "").toUpperCase();
  return ["SENTENCE_MAKING", "VOCABULARY_SET"].includes(normalized);
}

/**
 * 這個型別現在能不能派發作業。
 *
 * 白名單而不是黑名單 —— 未來新增題型時，預設是「不能派」而不是「悄悄落到單字集
 * 分支」。要開放時必須明確加進來，那一步自然會逼人去想學生端與批改頁做了沒有。
 */
export function isAssignableContentType(type?: string | null): boolean {
  return isExampleSentencesType(type) || isVocabularySetType(type);
}

/**
 * 這張卡片要不要用「原生 `disabled` 屬性」。
 *
 * **原生 disabled 的按鈕不會派發 click 事件** —— 於是 `onClick` 裡那句「為什麼不能選」
 * 的提示永遠出不來，老師點灰掉的卡片完全沒有回饋（PR #1032 review 抓到；這個 PR 一開始
 * 就踩了，說明文件還寫著「點下去會提示」）。
 *
 * 所以「這個題型還不能派發」這種**需要解釋**的情況要保持可點，由 `toggleContent` 的
 * 守衛擋住並跳提示；其餘情況（模式與型別不合、單字集達上限）維持原生 disabled。
 *
 * > 註：`mixedContentType`（模式與型別不合）那句提示其實也因為同樣原因構不到，
 * > 但那是本 PR 之前就存在的行為，不在這張單的範圍內，另外回報。
 */
export function usesNativeDisabled(options: {
  /** 卡片在畫面上是否呈現為停用 */
  disabled: boolean;
  /** 停用的原因是不是「這個題型還不能派發」 */
  notAssignable: boolean;
}): boolean {
  return options.disabled && !options.notAssignable;
}

/** 「整課都不能選」的原因。決定要給老師哪一句提示。 */
export type NothingSelectableReason = "not_assignable" | "mode_mismatch";

/**
 * 一課裡所有內容都不能選時，原因是哪一種。
 *
 * 兩者對老師的意思完全不同：
 *
 * * ``not_assignable`` —— 整課都是還不能派發的題型（例如整課只有情境對話）。
 *   叫他去換練習模式沒有用，**換哪個模式都不會變**。
 * * ``mode_mismatch`` —— 課裡有可派發的內容，只是與目前選的模式／購物車型別不合，
 *   換個模式就可以。
 *
 * 「全選」原本一律跳 mode_mismatch，於是整課只有情境對話時老師會被指去換模式，
 * 換完發現還是不能選（PR #1032 review round 2）。
 */
export function reasonNothingSelectable(
  contentTypes: Array<string | null | undefined>,
): NothingSelectableReason {
  const hasAssignable = contentTypes.some((type) =>
    isAssignableContentType(type),
  );
  return hasAssignable ? "mode_mismatch" : "not_assignable";
}
