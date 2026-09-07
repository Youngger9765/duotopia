/**
 * useScenarioDialogueEditor — 情境對話面板的開啟／存檔接線（Issue #1014）。
 *
 * `ContentTypeDialog` 目前有四個接線點（我的教材／機構教材／學校教材／班級教材，
 * 加上共用的 `ProgramTreeView`）。其他題型的面板**自己存檔**，情境對話面板則是把資料
 * 交給呼叫端存（#1013 這樣設計，因為面板不該認得 lesson / program / content id）——
 * 所以每個接線點都得有一份「三條建立路徑 + rollback + 編輯載入」的邏輯。複製四份等於
 * 埋四顆同樣的雷，因此收在這裡，由 `<ScenarioDialogueEditorSheet>` 搭配使用。
 *
 * 刻意**只**收情境對話自己的接線，不動 reading / vocabulary 的既有寫法：那些面板在
 * 各頁的 props 介面本來就不一致（有的沒傳 programId、有的自帶 handleSaveContent、
 * ProgramTreeView 還有未解的 TODO），一起抽的風險遠高於這張單的價值。
 */
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { apiClient } from "@/lib/api";
import {
  fromScenarioContentDetail,
  toScenarioSavePayload,
  type ScenarioContentDetail,
  type ScenarioDialogueInitialState,
  type ScenarioSaveInput,
} from "@/lib/scenarioDialogue";

/** 開啟面板時要指定存到哪裡。lessonId 與 programId 二擇一（#587 的教材沒有 lesson） */
export interface ScenarioDialogueTarget {
  lessonId?: number | null;
  /** program-direct 教材（lesson_id 為 null）才需要 */
  programId?: number | null;
  /** 教材難度預設值，沿用課程 level */
  programLevel?: string;
}

export interface ScenarioDialogueEditorState {
  isOpen: boolean;
  isSaving: boolean;
  /** 編輯模式的既有資料；null = 新增模式 */
  initialData: ScenarioDialogueInitialState | null;
  /** 有值 = 編輯既有內容 */
  contentId: number | null;
  programLevel: string | undefined;
  openForCreate: (target: ScenarioDialogueTarget) => void;
  openForEdit: (
    contentId: number,
    target: ScenarioDialogueTarget,
  ) => Promise<void>;
  close: () => void;
  save: (data: ScenarioSaveInput) => Promise<void>;
}

export interface UseScenarioDialogueEditorOptions {
  /**
   * 存檔成功後的列表刷新。**只在成功後呼叫**，而且它丟出的錯誤不會被當成存檔失敗
   * （老師的東西已經存好了，這時再說一句「儲存失敗」只會讓人白白重做一次）。
   */
  onSaved?: () => void | Promise<void>;
}

export function useScenarioDialogueEditor(
  options: UseScenarioDialogueEditorOptions = {},
): ScenarioDialogueEditorState {
  const { t } = useTranslation();
  const { onSaved } = options;

  const [isOpen, setIsOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lessonId, setLessonId] = useState<number | null>(null);
  const [programId, setProgramId] = useState<number | null>(null);
  const [contentId, setContentId] = useState<number | null>(null);
  const [initialData, setInitialData] =
    useState<ScenarioDialogueInitialState | null>(null);
  const [programLevel, setProgramLevel] = useState<string | undefined>(
    undefined,
  );

  /**
   * 關閉並清掉所有 state。
   *
   * contentId / initialData 一定要一起清 —— 留著的話下次「新增」會沿用上一次的
   * 內容 id，等於把新內容存進舊教材。
   */
  const close = useCallback(() => {
    setIsOpen(false);
    setLessonId(null);
    setProgramId(null);
    setContentId(null);
    setInitialData(null);
    setProgramLevel(undefined);
  }, []);

  const openForCreate = useCallback((target: ScenarioDialogueTarget) => {
    setLessonId(target.lessonId ?? null);
    setProgramId(target.programId ?? null);
    setContentId(null);
    setInitialData(null);
    setProgramLevel(target.programLevel);
    setIsOpen(true);
  }, []);

  /**
   * 讀取既有內容再開面板。
   *
   * 順序不能反：先開面板再讀，老師會先看到一張空白卡、資料回來才突然被換掉，中間
   * 打的字也會不見。讀取失敗就不開 —— 開了也只是空白卡，改完存回去等於把原本的
   * 題目全部洗掉。
   */
  const openForEdit = useCallback(
    async (id: number, target: ScenarioDialogueTarget) => {
      try {
        const detail = (await apiClient.getContentDetail(
          id,
        )) as ScenarioContentDetail;

        setLessonId(target.lessonId ?? null);
        setProgramId(target.programId ?? null);
        setContentId(id);
        setInitialData(fromScenarioContentDetail(detail));
        setProgramLevel(target.programLevel);
        setIsOpen(true);
      } catch (error) {
        console.error("Failed to load scenario dialogue content:", error);
        toast.error(t("contentEditor.messages.loadingContentFailed"));
      }
    },
    [t],
  );

  /**
   * 存檔。三條路徑：
   *   1. 編輯既有內容 → PUT /contents/{id}
   *   2. lesson 底下新增 → POST /lessons/{id}/contents（一次帶齊）
   *   3. program-direct 新增（#587）→ 該端點只吃 type + title，items 與整份設定要
   *      再打一次 PUT；第二步失敗就把第一步建出來的空殼刪掉，否則老師重試會在教材
   *      列表留下一堆 0 題的內容。
   *
   * 失敗時**不關面板**也不清 state，並把例外往上拋讓面板知道沒存成功 —— 老師剛填的
   * 十題不能因為一次網路錯誤就消失。
   */
  const save = useCallback(
    async (data: ScenarioSaveInput) => {
      const { scenario_settings, items } = toScenarioSavePayload(data);
      setIsSaving(true);
      try {
        if (contentId) {
          await apiClient.updateContent(contentId, {
            title: data.title,
            items,
            scenario_settings,
          });
        } else if (lessonId) {
          await apiClient.createContent(lessonId, {
            type: "SCENARIO_DIALOGUE",
            title: data.title,
            items,
            scenario_settings,
          });
        } else if (programId) {
          const created = (await apiClient.createProgramContent(programId, {
            type: "SCENARIO_DIALOGUE",
            title: data.title,
          })) as { id: number };
          try {
            await apiClient.updateContent(created.id, {
              title: data.title,
              items,
              scenario_settings,
            });
          } catch (updateError) {
            try {
              await apiClient.deleteContent(created.id);
            } catch (rollbackError) {
              console.error(
                "Failed to roll back orphaned scenario content:",
                rollbackError,
              );
            }
            throw updateError;
          }
        } else {
          throw new Error(
            "scenario dialogue: no lesson/program/content target",
          );
        }
      } catch (error) {
        console.error("Failed to save scenario dialogue content:", error);
        toast.error(t("contentEditor.messages.savingFailed"));
        throw error;
      } finally {
        setIsSaving(false);
      }

      // 存檔已經成功 —— 以下任何失敗都不可以再回報成「存檔失敗」，否則老師會在
      // 資料其實已經存好、面板也關掉之後看到「儲存失敗」，而且無從重試（#1016 review）
      toast.success(t("contentEditor.messages.savingSuccess"));
      close();
      await onSaved?.();
    },
    [close, contentId, lessonId, onSaved, programId, t],
  );

  return {
    isOpen,
    isSaving,
    initialData,
    contentId,
    programLevel,
    openForCreate,
    openForEdit,
    close,
    save,
  };
}
