/**
 * ScenarioDialogueGradingPanel — 批改頁中間欄：情境對話（Issue #1031）
 *
 * 對應 `practice_mode = "scenario_dialogue"`（學生看情境與題目後開口錄音回答）。
 *
 * ## 與朗讀批改的關鍵差別：沒有 AI 分數
 *
 * 朗讀類有 Azure 發音評測的 accuracy / fluency / pronunciation 分數可看，因為題目
 * 本身就是「該唸出來的那句話」。情境對話是**開放式回答** —— 學生講什麼因人而異，
 * 沒有可比對的正解，所以這裡是**純人工批改**：老師聽錄音、對照參考答案與必用字詞，
 * 自己判定通過與否並寫評語。
 *
 * （情境對話的 AI 評分要另做：錄音轉逐字稿 → 依語言特徵評分。既有那套硬套上來會把
 * 「講得跟範例不同」判成錯，見 `utils/scenario_dialogue.py` 的模組說明。）
 *
 * ## 參考答案是「示範」不是「正解」
 *
 * `reference_answer` 只出現在老師端（學生端的 `public_item_view` 會濾掉）。它的用途
 * 是讓老師快速抓到**語言特徵**該長什麼樣（時態、句型、用字水準、資訊完整度），
 * **不是拿來逐字比對** —— 同一題每個學生講的內容本來就不同（#864 規格 3-3）。
 * 所以畫面上它被標示為「參考」而不是「答案」，並與必用字詞、本題說明放在一起。
 *
 * 詳見 docs/design/grading-page-architecture.md
 */

import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle, X, ChevronDown, ChevronUp, Mic } from "lucide-react";
import type {
  StudentSubmission,
  ItemFeedback,
  SubmissionItem,
} from "@/pages/teacher/GradingPage";

interface ScenarioDialogueGradingPanelProps {
  submission: StudentSubmission;
  selectedGroupIndex: number;
  expandedRows: Set<number>;
  activeTab: "students" | "content" | "grading";
  itemFeedbacks: ItemFeedback;
  onSelectGroup: (idx: number) => void;
  onToggleRow: (globalIndex: number) => void;
  onTogglePassed: (globalIndex: number, passed: boolean) => Promise<void>;
  onItemFeedbackChange: (globalIndex: number, feedback: string) => void;
  onAutoSave: () => Promise<void>;
}

/** 時態／語態的穩定代碼 → 顯示字串。空值代表老師沒指定，就不顯示這個 chip。 */
function useCodeLabels() {
  const { t } = useTranslation();
  return {
    tense: (tense?: { time: string; aspect: string }) => {
      if (!tense?.time || !tense?.aspect) return "";
      return t("scenarioDialogue.tenseCombo", {
        time: t(`scenarioDialogue.tenseTimes.${tense.time}`),
        aspect: t(`scenarioDialogue.tenseAspects.${tense.aspect}`),
      });
    },
    voice: (voice?: string) =>
      voice ? t(`scenarioDialogue.voices.${voice}`) : "",
  };
}

export function ScenarioDialogueGradingPanel({
  submission,
  selectedGroupIndex,
  expandedRows,
  activeTab,
  itemFeedbacks,
  onToggleRow,
  onTogglePassed,
  onItemFeedbackChange,
  onAutoSave,
}: ScenarioDialogueGradingPanelProps) {
  const { t } = useTranslation();
  const labels = useCodeLabels();

  // 分組與 globalIndex 的算法與 SentenceRearrangementPanel 一致：content_groups 各自
  // 帶著自己的 submissions，globalIndex 是前面各組長度的累加（itemFeedbacks 以它為 key）
  const currentGroup = submission.content_groups
    ? submission.content_groups[selectedGroupIndex]
    : null;

  let startIndex = 0;
  if (submission.content_groups) {
    for (let i = 0; i < selectedGroupIndex; i++) {
      startIndex += submission.content_groups[i].submissions.length;
    }
  }

  const items: SubmissionItem[] = currentGroup
    ? currentGroup.submissions
    : submission.submissions;

  return (
    <div
      className={`col-span-12 lg:col-span-6 ${
        activeTab === "content" ? "block" : "hidden lg:block"
      }`}
    >
      <Card className="p-4 space-y-3">
        {items.length === 0 && (
          <p className="text-sm text-gray-500">
            {t("gradingPage.messages.noItems")}
          </p>
        )}

        {items.map((item, localIndex) => {
          const globalIndex = startIndex + localIndex;
          const itemFeedback = itemFeedbacks[globalIndex];
          const expanded = expandedRows.has(globalIndex);
          const scenario = item.scenario_dialogue;
          const tenseLabel = labels.tense(scenario?.tense);
          const voiceLabel = labels.voice(scenario?.voice);

          return (
            <div
              key={globalIndex}
              className="border rounded-lg p-3 space-y-2 bg-white"
            >
              <div className="flex items-start gap-3">
                {/* 通過 / 不通過 —— 情境對話沒有 AI 分數，全靠老師判定 */}
                <div
                  className="flex flex-col gap-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Button
                    size="sm"
                    variant={
                      itemFeedback?.passed === true ? "default" : "outline"
                    }
                    className={`p-1 h-7 w-7 ${
                      itemFeedback?.passed === true
                        ? "bg-green-600 hover:bg-green-700"
                        : ""
                    }`}
                    onClick={() => onTogglePassed(globalIndex, true)}
                    disabled={submission?.status === "GRADED"}
                    aria-label={t("gradingPage.labels.pass")}
                  >
                    <CheckCircle className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant={
                      itemFeedback?.passed === false ? "default" : "outline"
                    }
                    className={`p-1 h-7 w-7 ${
                      itemFeedback?.passed === false
                        ? "bg-red-600 hover:bg-red-700"
                        : ""
                    }`}
                    onClick={() => onTogglePassed(globalIndex, false)}
                    disabled={submission?.status === "GRADED"}
                    aria-label={t("gradingPage.labels.fail")}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-semibold text-gray-500 mt-1">
                      {localIndex + 1}.
                    </span>
                    <div className="flex-1">
                      <p className="font-medium text-sm">
                        {item.question_text}
                      </p>
                      {item.question_translation && (
                        <p className="text-xs text-gray-500 mt-1">
                          {item.question_translation}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* 學生錄音 —— 這是批改情境對話唯一的作答內容 */}
                  <div className="mt-2">
                    {item.audio_url ? (
                      <audio
                        controls
                        preload="none"
                        src={item.audio_url}
                        className="w-full h-8"
                      />
                    ) : (
                      <p className="text-xs text-gray-400 flex items-center gap-1">
                        <Mic className="h-3 w-3" />
                        {t("gradingPage.scenarioDialogue.noRecording")}
                      </p>
                    )}
                  </div>

                  {/* 出題設定：老師批改時的判斷依據 */}
                  {(scenario?.keywords?.length || tenseLabel || voiceLabel) && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {tenseLabel && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                          {tenseLabel}
                        </span>
                      )}
                      {voiceLabel && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                          {voiceLabel}
                        </span>
                      )}
                      {scenario?.keywords?.map((word) => (
                        <span
                          key={word}
                          className="text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700"
                        >
                          {word}
                        </span>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => onToggleRow(globalIndex)}
                    className="mt-2 text-xs text-blue-600 flex items-center gap-1"
                  >
                    {expanded ? (
                      <ChevronUp className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                    {t("gradingPage.scenarioDialogue.toggleDetail")}
                  </button>
                </div>
              </div>

              {expanded && (
                <div className="pl-10 space-y-2">
                  {scenario?.rubric_note && (
                    <p className="text-xs text-gray-600">
                      <span className="font-semibold">
                        {t("gradingPage.scenarioDialogue.rubricNote")}：
                      </span>
                      {scenario.rubric_note}
                    </p>
                  )}

                  {scenario?.reference_answer && (
                    <div className="text-xs bg-gray-50 rounded p-2">
                      <p className="font-semibold text-gray-600">
                        {t("gradingPage.scenarioDialogue.referenceAnswer")}
                      </p>
                      <p className="text-gray-700 mt-1">
                        {scenario.reference_answer}
                      </p>
                      {/* 這一行不是裝飾 —— 沒有它，老師很容易把參考答案當成標準答案
                          去逐字比對，而口說同一題每個學生講的內容本來就不同 */}
                      <p className="text-[11px] text-gray-400 mt-1">
                        {t("gradingPage.scenarioDialogue.referenceHint")}
                      </p>
                    </div>
                  )}

                  <textarea
                    value={itemFeedback?.feedback ?? ""}
                    onChange={(e) =>
                      onItemFeedbackChange(globalIndex, e.target.value)
                    }
                    onBlur={() => void onAutoSave()}
                    disabled={submission?.status === "GRADED"}
                    placeholder={t(
                      "gradingPage.scenarioDialogue.feedbackPlaceholder",
                    )}
                    className="w-full text-xs border rounded p-2 min-h-[60px]"
                  />
                </div>
              )}
            </div>
          );
        })}
      </Card>
    </div>
  );
}

export default ScenarioDialogueGradingPanel;
