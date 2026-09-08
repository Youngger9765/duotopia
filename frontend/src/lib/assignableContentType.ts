import {
  DATASET_LABEL_KEY,
  PRACTICE_MODE_REGISTRY,
  contentTypeToDataset,
  type PracticeMode,
} from "./practiceMode";

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
 * ## 情境對話（#1031 起可派發）
 *
 * #1030 先把它擋下（當時學生端作答與批改頁都還沒做），#1031 做完後移到支援名單。
 * **防呆本身保留** —— 未來新增的題型仍然預設不可派發，要開放必須明確加進來。
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
/** 情境對話（#1031 起可派發） */
export function isScenarioDialogueType(type?: string | null): boolean {
  return (type ?? "").toUpperCase() === "SCENARIO_DIALOGUE";
}

export function isAssignableContentType(type?: string | null): boolean {
  return (
    isExampleSentencesType(type) ||
    isVocabularySetType(type) ||
    // Issue #1031: 學生端作答與批改頁都做好了，從 #1030 的擋板移到支援名單。
    // 白名單的意義就在這裡 —— 開放一個題型是「明確加進來」的動作，而不是
    // 悄悄從某個 fallback 漏過去。
    isScenarioDialogueType(type)
  );
}

/**
 * ## 停用的卡片為什麼不用原生 `disabled`
 *
 * 這裡曾經有一個 `usesNativeDisabled()`，用來區分「哪些停用原因要保持可點」。
 * #1033 把它移除了 —— 答案是**全部都要**，一個只會回同一個答案的函式只是多一層。
 *
 * 原因：**原生 `disabled` 的按鈕不會派發 click 事件**。卡片灰掉的每一種原因
 * （題型還不能派、模式與型別不合、單字集達上限），`AssignmentDialog.toggleContent()`
 * 裡都寫了一句對應的提示要告訴老師。只要用了原生 disabled，那句提示就是死碼，
 * 老師點下去完全沒有回饋。
 *
 * #1030 只把「題型還不能派」那一種挑出來修，另外兩種留在原生 disabled 上（#1033）。
 * 現在規則統一了：**停用一律是視覺與語意上的（`aria-disabled`），事件照常派發**，
 * 由守衛負責擋下並說明。實作見 `components/assignment/ContentSelectCard.tsx`。
 */

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

/** 點了灰掉的卡片時，要告訴老師哪一件事。`null` = 這張其實選得到。 */
export type NotSelectableExplanation =
  | { kind: "not_assignable" }
  | { kind: "mode_mismatch"; allowedDatasetKeys: string[] };

/**
 * 這個型別在目前的練習模式下為什麼不能選（Issue #1033）。
 *
 * 抽出來的理由與這個檔案本身一樣：**要驗得到**。
 * `AssignmentDialog.toggleContent()` 裡那句「目前只能選擇 X」原本寫死 X = 單字集。
 * 在它還是死碼時（原生 disabled 吃掉 click）沒人發現，一旦讓它真的出得來，寫死就會
 * 說謊 —— 選了情境對話模式時該說情境對話，選了朗讀模式去點情境對話時該說例句集與
 * 單字集。**指錯方向比沒有提示更糟**，所以這個判定必須有測試。
 *
 * 「這個模式吃得下哪些資料集」直接查 registry 的 `supportedDatasets`，不自己列模式
 * 清單 —— 三個資料集之後，任何二分法的猜測都會在某個組合上講錯（#1034 的教訓）。
 */
export function explainNotSelectable(
  contentType: string | null | undefined,
  mode: PracticeMode | "",
): NotSelectableExplanation | null {
  if (!isAssignableContentType(contentType)) {
    // 換哪個模式都不會變 —— 叫老師去換模式是錯的建議
    return { kind: "not_assignable" };
  }
  // 還沒選模式時，可派發的型別本來就都選得到
  if (!mode) return null;

  const dataset = contentTypeToDataset(contentType);
  const supported = PRACTICE_MODE_REGISTRY[mode].supportedDatasets;
  if (dataset && supported.includes(dataset)) return null;

  return {
    kind: "mode_mismatch",
    allowedDatasetKeys: supported.map((d) => DATASET_LABEL_KEY[d]),
  };
}
