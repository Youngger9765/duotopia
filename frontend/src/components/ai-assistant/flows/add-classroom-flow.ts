/**
 * Manage Classroom Flow — state machine logic (teacher personal backend)
 *
 * Entry:
 *   choose_action → [新增班級] or [修改班級]
 *
 * Add path (unchanged):
 *   choose_mode → collect_single_name → collect_single_level → confirm → execute → complete
 *   choose_mode → collect_batch → confirm → execute → complete
 *
 * Edit path (new):
 *   select_classroom → choose_edit_field → collect_edit_value → confirm_edit → execute_edit → edit_complete
 */

import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import i18n from "@/i18n/config";
import type { ChatMessage, QuickButton, TableColumn } from "../chat/types";

// ─── Types ───

export type FlowStep =
  // Entry
  | "choose_action"
  // Add path
  | "choose_mode"
  | "collect_single_name"
  | "collect_single_level"
  | "collect_batch"
  | "confirm"
  | "execute"
  | "complete"
  // Edit path
  | "select_classroom"
  | "choose_edit_field"
  | "collect_edit_value"
  | "confirm_edit"
  | "execute_edit"
  | "edit_complete";

export interface ParsedClassroom {
  name: string;
  level: string;
  valid: boolean;
  error: string | null;
}

interface ExistingClassroom {
  id: number;
  name: string;
  level: string;
  description: string | null;
  student_count: number;
}

export interface FlowState {
  step: FlowStep;
  classrooms: ParsedClassroom[];
  inputDisabled: boolean;
  // Edit-related state
  existingClassrooms: ExistingClassroom[];
  selectedClassroom: ExistingClassroom | null;
  editField: "name" | "level" | "description" | null;
  editValue: string | null;
}

// ─── Constants ───

const VALID_LEVELS = ["PREA", "A1", "A2", "B1", "B2", "C1", "C2"];

const LEVEL_BUTTONS: QuickButton[] = VALID_LEVELS.map((l) => ({
  label: l,
  value: `select_level:${l}`,
}));

function getTableColumns(): TableColumn[] {
  return [
    { key: "index", label: "#" },
    { key: "name", label: i18n.t("aiAssistant.classroom.table.name") },
    { key: "level", label: i18n.t("aiAssistant.classroom.table.level") },
    { key: "status", label: i18n.t("aiAssistant.classroom.table.status") },
  ];
}

const EDIT_INTENT_RE = /(?:修改|改|編輯|更新|rename|edit|update|change)/i;

// ─── Helpers ───

let _msgId = 0;
function msgId() {
  return `acr-${++_msgId}`;
}

function assistantMsg(
  content: string,
  extra?: Partial<ChatMessage>,
): ChatMessage {
  return { id: msgId(), role: "assistant", content, ...extra };
}

function userMsg(content: string): ChatMessage {
  return { id: msgId(), role: "user", content };
}

function normalizeLevel(input: string): string | null {
  const upper = input.trim().toUpperCase();
  // Handle with/without hyphen: "pre-a" → "PREA"
  const normalized = upper.replace(/[-\s]/g, "");
  if (VALID_LEVELS.includes(normalized)) return normalized;
  // Try matching "PRE A" → "PREA"
  if (normalized === "PREA1" || normalized === "PRE") return "PREA";
  return null;
}

function classroomTableRows(classrooms: ParsedClassroom[]) {
  return classrooms.map((c, i) => ({
    index: String(i + 1),
    name: c.name,
    level: c.level,
    status: c.valid ? "✓" : `⚠️ ${c.error}`,
  }));
}

// ─── API calls ───

async function callParseClassrooms(
  userInput: string,
): Promise<{ classrooms: ParsedClassroom[]; message: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/ai/assistant/parse-classrooms`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ user_input: userInput }),
  });
  if (!res.ok) throw new Error(i18n.t("aiAssistant.classroom.parseFailed"));
  return res.json();
}

async function callProcessClassroomModification(
  userInput: string,
  currentClassrooms: ParsedClassroom[],
): Promise<{ classrooms: ParsedClassroom[]; message: string; action: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(
    `${API_URL}/api/ai/assistant/process-classroom-modification`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        user_input: userInput,
        current_classrooms: currentClassrooms,
      }),
    },
  );
  if (!res.ok)
    throw new Error(i18n.t("aiAssistant.classroom.modifyProcessFailed"));
  return res.json();
}

async function createClassroom(data: {
  name: string;
  level: string;
}): Promise<{ id: number; name: string; level: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/classrooms`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name: data.name, level: data.level }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(
      err?.detail || i18n.t("aiAssistant.classroom.createFailed"),
    );
  }
  return res.json();
}

async function fetchTeacherClassrooms(): Promise<ExistingClassroom[]> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/classrooms?mode=personal`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok)
    throw new Error(i18n.t("aiAssistant.classroom.loadClassroomsFailed"));
  const data = await res.json();
  return data.map((c: Record<string, unknown>) => ({
    id: c.id as number,
    name: c.name as string,
    level: (c.level || "A1") as string,
    description: (c.description ?? null) as string | null,
    student_count: (c.student_count || 0) as number,
  }));
}

async function updateClassroomApi(
  classroomId: number,
  data: { name?: string; level?: string; description?: string | null },
): Promise<{
  id: number;
  name: string;
  level: string;
  description: string | null;
}> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/classrooms/${classroomId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || i18n.t("aiAssistant.classroom.editFailed"));
  }
  return res.json();
}

// ─── Flow class ───

export class ManageClassroomFlow {
  state: FlowState;
  messages: ChatMessage[];

  private pushMsg: (msgs: ChatMessage[]) => void;
  private updateState: (partial: Partial<FlowState>) => void;

  constructor(
    pushMsg: (msgs: ChatMessage[]) => void,
    updateState: (partial: Partial<FlowState>) => void,
    initialData?: { classrooms?: ParsedClassroom[]; subIntent?: string },
  ) {
    this.pushMsg = pushMsg;
    this.updateState = updateState;
    this.messages = [];
    this.state = {
      step: "choose_action",
      classrooms: [],
      inputDisabled: true,
      existingClassrooms: [],
      selectedClassroom: null,
      editField: null,
      editValue: null,
    };

    // Route based on initialData from intent detection
    if (initialData?.subIntent === "edit") {
      this.loadAndShowClassrooms();
    } else if (initialData?.classrooms?.length) {
      this.state.classrooms = initialData.classrooms;
      this.showConfirmTable();
    } else {
      this.showActionChoice();
    }
  }

  // ═══════════════════════════════════════════════
  // Entry: choose_action
  // ═══════════════════════════════════════════════

  private showActionChoice() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.actionChoice"), {
        buttons: [
          {
            label: i18n.t("aiAssistant.classroom.actionAdd"),
            value: "action:add",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.classroom.actionEdit"),
            value: "action:edit",
          },
        ],
      }),
    ]);
    this.set({ step: "choose_action", inputDisabled: false });
  }

  // ═══════════════════════════════════════════════
  // ADD PATH (preserved from original)
  // ═══════════════════════════════════════════════

  // ─── Step: choose_mode ───

  private showModeChoice() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.modeChoice"), {
        buttons: [
          {
            label: i18n.t("aiAssistant.common.addSingle"),
            value: "mode:single",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.common.addBatch"),
            value: "mode:batch",
          },
        ],
      }),
    ]);
    this.set({ step: "choose_mode", inputDisabled: true });
  }

  // ─── Step: collect_single ───

  private collectSingleName() {
    this.emit([assistantMsg(i18n.t("aiAssistant.classroom.enterName"))]);
    this.set({ step: "collect_single_name", inputDisabled: false });
  }

  private collectSingleLevel(name: string) {
    this.state.classrooms = [{ name, level: "", valid: true, error: null }];
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.selectLevel", { name }), {
        buttons: LEVEL_BUTTONS,
      }),
    ]);
    this.set({ step: "collect_single_level", inputDisabled: true });
  }

  private confirmSingle(level: string) {
    this.state.classrooms[0].level = level;
    this.showConfirmTable();
  }

  // ─── Step: collect_batch ───

  private collectBatch() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.batchInstructions")),
    ]);
    this.set({ step: "collect_batch", inputDisabled: false });
  }

  // ─── Step: confirm ───

  private showConfirmTable() {
    const classrooms = this.state.classrooms;
    const allValid = classrooms.every((c) => c.valid);

    const buttons: QuickButton[] = [];

    if (allValid) {
      buttons.push({
        label: i18n.t("aiAssistant.common.confirmCreate"),
        value: "confirm_execute",
        variant: "default",
      });
    } else {
      buttons.push({
        label: i18n.t("aiAssistant.common.fixErrors"),
        value: "_disabled",
        variant: "secondary",
      });
    }
    buttons.push({
      label: i18n.t("aiAssistant.common.modify"),
      value: "edit_table",
    });

    const header =
      classrooms.length === 1
        ? i18n.t("aiAssistant.classroom.confirmHeader")
        : i18n.t("aiAssistant.classroom.confirmHeaderBatch", {
            count: classrooms.length,
          });

    this.emit([
      assistantMsg(header, {
        table: {
          columns: getTableColumns(),
          rows: classroomTableRows(classrooms),
        },
        buttons,
      }),
    ]);
    this.set({ step: "confirm", inputDisabled: false });
  }

  // ─── Step: execute ───

  private async executeCreate() {
    this.set({ step: "execute", inputDisabled: true });
    const classrooms = this.state.classrooms.filter((c) => c.valid);

    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.creating"), { loading: true }),
    ]);

    const successes: { name: string; level: string; id: number }[] = [];
    const failures: { name: string; error: string }[] = [];

    for (const c of classrooms) {
      try {
        const result = await createClassroom({
          name: c.name,
          level: c.level,
        });
        successes.push({ name: c.name, level: c.level, id: result.id });
      } catch (e) {
        failures.push({ name: c.name, error: (e as Error).message });
      }
    }

    this.showSummary(successes, failures);
  }

  // ─── Step: complete ───

  private showSummary(
    successes: { name: string; level: string; id: number }[],
    failures: { name: string; error: string }[],
  ) {
    let summary = i18n.t("aiAssistant.classroom.complete") + "\n\n";

    if (successes.length > 0) {
      summary +=
        i18n.t("aiAssistant.classroom.successCount", {
          count: successes.length,
        }) + "\n";
      for (const s of successes) {
        summary += `  - ${s.name} (${s.level})\n`;
      }
    }

    if (failures.length > 0) {
      summary +=
        "\n" +
        i18n.t("aiAssistant.classroom.failureCount", {
          count: failures.length,
        }) +
        "\n";
      for (const f of failures) {
        summary += `  - ${f.name} → ${f.error}\n`;
      }
    }

    summary += "\n" + i18n.t("aiAssistant.classroom.nextStep");

    this.emit([
      assistantMsg(summary, {
        buttons: [
          {
            label: i18n.t("aiAssistant.classroom.continueAdd"),
            value: "restart_flow",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.classroom.switchToEdit"),
            value: "switch_to_edit",
          },
          {
            label: i18n.t("aiAssistant.common.goToClassrooms"),
            value: "navigate:/teacher/classrooms",
          },
          { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
        ],
      }),
    ]);
    this.set({ step: "complete", inputDisabled: true });
  }

  // ═══════════════════════════════════════════════
  // EDIT PATH (new)
  // ═══════════════════════════════════════════════

  // ─── Step: select_classroom ───

  private async loadAndShowClassrooms() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.loadingClassrooms"), {
        loading: true,
      }),
    ]);
    this.set({ step: "select_classroom", inputDisabled: true });

    try {
      const classrooms = await fetchTeacherClassrooms();
      this.state.existingClassrooms = classrooms;

      if (classrooms.length === 0) {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.classroom.noClassroomsForEdit"), {
            buttons: [
              {
                label: i18n.t("aiAssistant.classroom.actionAdd"),
                value: "action:add",
                variant: "default",
              },
              { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
            ],
          }),
        ]);
        return;
      }

      const buttons: QuickButton[] = classrooms.map((c) => {
        const studentInfo =
          c.student_count > 0
            ? ` - ${i18n.t("aiAssistant.classroom.studentCountLabel", { count: c.student_count })}`
            : "";
        return {
          label: `${c.name} (${c.level})${studentInfo}`,
          value: `select_edit_classroom:${c.id}`,
        };
      });

      this.emit([
        assistantMsg(i18n.t("aiAssistant.classroom.selectEditClassroom"), {
          buttons,
        }),
      ]);
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.classroom.loadClassroomsFailed", {
            error: (e as Error).message,
          }),
          {
            buttons: [
              {
                label: i18n.t("aiAssistant.classroom.actionAdd"),
                value: "action:add",
              },
              { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
            ],
          },
        ),
      ]);
    }
  }

  // ─── Step: choose_edit_field ───

  private showEditFieldChoice() {
    const c = this.state.selectedClassroom!;
    const descLine = c.description
      ? c.description
      : i18n.t("aiAssistant.classroom.noDescription");

    const info = i18n.t("aiAssistant.classroom.classroomInfo", {
      name: c.name,
      level: c.level,
      description: descLine,
    });

    this.emit([
      assistantMsg(info, {
        buttons: [
          {
            label: i18n.t("aiAssistant.classroom.editFieldName"),
            value: "edit_field:name",
          },
          {
            label: i18n.t("aiAssistant.classroom.editFieldLevel"),
            value: "edit_field:level",
          },
          {
            label: i18n.t("aiAssistant.classroom.editFieldDescription"),
            value: "edit_field:description",
          },
        ],
      }),
    ]);
    this.set({ step: "choose_edit_field", inputDisabled: true });
  }

  // ─── Step: collect_edit_value ───

  private collectEditValue(field: "name" | "level" | "description") {
    this.state.editField = field;
    this.set({ step: "collect_edit_value" });

    if (field === "level") {
      const editLevelButtons: QuickButton[] = VALID_LEVELS.map((l) => ({
        label: l,
        value: `select_edit_level:${l}`,
      }));
      this.emit([
        assistantMsg(i18n.t("aiAssistant.classroom.selectNewLevel"), {
          buttons: editLevelButtons,
        }),
      ]);
      this.set({ inputDisabled: true });
    } else if (field === "name") {
      this.emit([assistantMsg(i18n.t("aiAssistant.classroom.enterNewName"))]);
      this.set({ inputDisabled: false });
    } else {
      this.emit([
        assistantMsg(i18n.t("aiAssistant.classroom.enterNewDescription")),
      ]);
      this.set({ inputDisabled: false });
    }
  }

  // ─── Step: confirm_edit ───

  private showEditConfirmation() {
    const c = this.state.selectedClassroom!;
    const field = this.state.editField!;
    const newValue = this.state.editValue!;

    const fieldLabel =
      field === "name"
        ? i18n.t("aiAssistant.classroom.editFieldName")
        : field === "level"
          ? i18n.t("aiAssistant.classroom.editFieldLevel")
          : i18n.t("aiAssistant.classroom.editFieldDescription");

    const oldValue =
      field === "name"
        ? c.name
        : field === "level"
          ? c.level
          : c.description || i18n.t("aiAssistant.classroom.noDescription");

    const displayNewValue =
      newValue === ""
        ? i18n.t("aiAssistant.classroom.descriptionCleared")
        : newValue;

    const msg =
      i18n.t("aiAssistant.classroom.confirmEditHeader", { name: c.name }) +
      "\n\n" +
      i18n.t("aiAssistant.classroom.confirmEditField", {
        field: fieldLabel,
        oldValue,
        newValue: displayNewValue,
      });

    this.emit([
      assistantMsg(msg, {
        buttons: [
          {
            label: i18n.t("aiAssistant.classroom.confirmEdit"),
            value: "confirm_edit_execute",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.classroom.cancelEdit"),
            value: "cancel_edit",
          },
        ],
      }),
    ]);
    this.set({ step: "confirm_edit", inputDisabled: true });
  }

  // ─── Step: execute_edit ───

  private async executeEdit() {
    this.set({ step: "execute_edit", inputDisabled: true });
    const c = this.state.selectedClassroom!;
    const field = this.state.editField!;
    const newValue = this.state.editValue!;

    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.editExecuting"), {
        loading: true,
      }),
    ]);

    try {
      const payload: Record<string, string | null> = {};
      if (field === "description" && newValue === "") {
        payload[field] = null;
      } else {
        payload[field] = newValue;
      }

      const updated = await updateClassroomApi(c.id, payload);

      // Update local state so subsequent edits reflect the change
      this.state.selectedClassroom = {
        ...c,
        name: updated.name,
        level: updated.level,
        description: updated.description,
      };

      this.showEditComplete(updated.name);
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.classroom.editFailed", {
            error: (e as Error).message,
          }),
          {
            buttons: [
              {
                label: i18n.t("aiAssistant.classroom.continueEditSame"),
                value: "continue_edit_same",
              },
              { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
            ],
          },
        ),
      ]);
      this.set({ step: "edit_complete", inputDisabled: true });
    }
  }

  // ─── Step: edit_complete ───

  private showEditComplete(name: string) {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.editSuccess", { name }), {
        buttons: [
          {
            label: i18n.t("aiAssistant.classroom.continueEditSame"),
            value: "continue_edit_same",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.classroom.editOtherClassroom"),
            value: "edit_other_classroom",
          },
          {
            label: i18n.t("aiAssistant.classroom.switchToAdd"),
            value: "switch_to_add",
          },
          { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
        ],
      }),
    ]);
    this.set({ step: "edit_complete", inputDisabled: true });
  }

  // ═══════════════════════════════════════════════
  // Public: inject pre-parsed data from unified AI
  // ═══════════════════════════════════════════════

  /**
   * Called by HubChat when the unified AI (/chat) returns action=provide_data
   * with parsed_data. Skips the flow's internal parse API calls.
   * Falls back to handleUserInput if the step/data don't match.
   */
  injectParsedData(text: string, parsedData: Record<string, unknown>) {
    const { step } = this.state;

    // ── collect_batch: AI parsed classrooms from natural language ──
    if (step === "collect_batch" && Array.isArray(parsedData.classrooms)) {
      const classrooms = parsedData.classrooms as ParsedClassroom[];
      if (classrooms.length === 0) {
        this.emit([
          assistantMsg(
            (parsedData.message as string) ||
              i18n.t("aiAssistant.classroom.noDataDetected"),
          ),
        ]);
        return;
      }

      this.state.classrooms = classrooms;
      this.showConfirmTable();
      return;
    }

    // ── confirm: AI modified the classroom list ──
    if (step === "confirm" && parsedData.modification_action) {
      const action = parsedData.modification_action as string;

      if (action === "unclear") {
        this.emit([
          assistantMsg(
            (parsedData.message as string) ||
              i18n.t("aiAssistant.classroom.modifyInstructions"),
          ),
        ]);
        return;
      }

      if (Array.isArray(parsedData.classrooms)) {
        const classrooms = parsedData.classrooms as ParsedClassroom[];
        this.state.classrooms = classrooms;

        if (classrooms.length === 0) {
          this.emit([assistantMsg(i18n.t("aiAssistant.classroom.allRemoved"))]);
          this.set({ step: "collect_batch", inputDisabled: false });
          return;
        }

        this.showConfirmTable();
        return;
      }
    }

    // ── Fallback: let handleUserInput process it ──
    this.handleUserInput(text);
  }

  // ═══════════════════════════════════════════════
  // Public: handle user input
  // ═══════════════════════════════════════════════

  async handleUserInput(text: string) {
    const { step } = this.state;

    // ── choose_action: detect intent from free text ──
    if (step === "choose_action") {
      this.emit([userMsg(text)]);
      if (EDIT_INTENT_RE.test(text)) {
        await this.loadAndShowClassrooms();
      } else {
        this.showModeChoice();
      }
      return;
    }

    // ── Add path ──

    if (step === "collect_single_name") {
      const name = text.trim();
      if (!name) {
        this.emit([
          userMsg(text),
          assistantMsg(i18n.t("aiAssistant.classroom.emptyName")),
        ]);
        return;
      }
      this.emit([userMsg(text), assistantMsg("", { loading: true })]);
      // Validate name through AI (profanity check)
      this.set({ inputDisabled: true });
      try {
        const result = await callParseClassrooms(`${name} A1`);
        const first = result.classrooms[0];
        if (first && !first.valid) {
          this.emit([
            assistantMsg(
              first.error || i18n.t("aiAssistant.classroom.inappropriateName"),
            ),
          ]);
          this.set({ inputDisabled: false });
          return;
        }
        this.collectSingleLevel(first ? first.name : name);
      } catch {
        // API failure — allow through, backend will catch on create
        this.collectSingleLevel(name);
      }
      return;
    }

    if (step === "collect_single_level") {
      // User typed a level instead of clicking button
      const level = normalizeLevel(text);
      if (level) {
        this.emit([userMsg(text)]);
        this.confirmSingle(level);
      } else {
        this.emit([
          userMsg(text),
          assistantMsg(
            i18n.t("aiAssistant.classroom.invalidLevel", {
              input: text,
              levels: VALID_LEVELS.join("、"),
            }),
            { buttons: LEVEL_BUTTONS },
          ),
        ]);
      }
      return;
    }

    if (step === "collect_batch") {
      this.emit([userMsg(text)]);
      await this.parseBatchWithAI(text);
      return;
    }

    if (step === "confirm") {
      // User is providing modification instructions (free text)
      this.emit([userMsg(text)]);
      await this.handleModification(text);
      return;
    }

    // ── Edit path ──

    if (step === "collect_edit_value") {
      this.emit([userMsg(text)]);
      const field = this.state.editField!;

      if (field === "name") {
        const name = text.trim();
        if (!name) {
          this.emit([assistantMsg(i18n.t("aiAssistant.classroom.emptyName"))]);
          return;
        }
        this.state.editValue = name;
        this.showEditConfirmation();
      } else if (field === "level") {
        const level = normalizeLevel(text);
        if (level) {
          this.state.editValue = level;
          this.showEditConfirmation();
        } else {
          const editLevelButtons: QuickButton[] = VALID_LEVELS.map((l) => ({
            label: l,
            value: `select_edit_level:${l}`,
          }));
          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.classroom.invalidLevel", {
                input: text,
                levels: VALID_LEVELS.join("、"),
              }),
              { buttons: editLevelButtons },
            ),
          ]);
        }
      } else {
        // description — allow empty (clear description)
        const trimmed = text.trim();
        const clearRe = /^(?:清除|清空|刪除|移除|clear|remove|delete|none)$/i;
        this.state.editValue = clearRe.test(trimmed) ? "" : trimmed;
        this.showEditConfirmation();
      }
      return;
    }
  }

  // ═══════════════════════════════════════════════
  // Public: handle button click
  // ═══════════════════════════════════════════════

  async handleButtonSelect(_messageId: string, value: string) {
    if (value === "_disabled") return;
    if (value.startsWith("navigate:")) return; // Handled by parent component

    // ── Entry ──

    if (value === "action:add") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.actionAdd"))]);
      this.showModeChoice();
      return;
    }

    if (value === "action:edit") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.actionEdit"))]);
      await this.loadAndShowClassrooms();
      return;
    }

    // ── Add path ──

    if (value === "mode:single") {
      this.emit([userMsg(i18n.t("aiAssistant.common.addSingle"))]);
      this.collectSingleName();
      return;
    }

    if (value === "mode:batch") {
      this.emit([userMsg(i18n.t("aiAssistant.common.addBatch"))]);
      this.collectBatch();
      return;
    }

    if (value.startsWith("select_level:")) {
      const level = value.replace("select_level:", "");
      this.emit([userMsg(level)]);
      this.confirmSingle(level);
      return;
    }

    if (value === "confirm_execute") {
      this.emit([userMsg(i18n.t("aiAssistant.common.confirmCreate"))]);
      await this.executeCreate();
      return;
    }

    if (value.startsWith("remove:")) {
      const idx = parseInt(value.replace("remove:", ""), 10);
      if (idx >= 0 && idx < this.state.classrooms.length) {
        this.emit([
          userMsg(
            i18n.t("aiAssistant.common.remove", {
              name: this.state.classrooms[idx].name,
            }),
          ),
        ]);
        this.removeClassroom(idx);
      }
      return;
    }

    if (value === "edit_table") {
      this.emit([
        userMsg(i18n.t("aiAssistant.common.modify")),
        assistantMsg(i18n.t("aiAssistant.classroom.modifyInstructions")),
      ]);
      this.set({ inputDisabled: false });
      return;
    }

    if (value === "restart_flow") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.continueAdd"))]);
      this.state.classrooms = [];
      this.showModeChoice();
      return;
    }

    if (value === "close_panel") {
      this.emit([
        userMsg(i18n.t("aiAssistant.common.end")),
        assistantMsg(i18n.t("aiAssistant.classroom.thankYou")),
      ]);
      return;
    }

    // ── Edit path ──

    if (value.startsWith("select_edit_classroom:")) {
      const id = parseInt(value.replace("select_edit_classroom:", ""), 10);
      const classroom = this.state.existingClassrooms.find((c) => c.id === id);
      if (!classroom) return;
      this.emit([userMsg(classroom.name)]);
      this.state.selectedClassroom = classroom;
      this.showEditFieldChoice();
      return;
    }

    if (value.startsWith("edit_field:")) {
      const field = value.replace("edit_field:", "") as
        | "name"
        | "level"
        | "description";
      const fieldLabel =
        field === "name"
          ? i18n.t("aiAssistant.classroom.editFieldName")
          : field === "level"
            ? i18n.t("aiAssistant.classroom.editFieldLevel")
            : i18n.t("aiAssistant.classroom.editFieldDescription");
      this.emit([userMsg(fieldLabel)]);
      this.collectEditValue(field);
      return;
    }

    if (value.startsWith("select_edit_level:")) {
      const level = value.replace("select_edit_level:", "");
      this.emit([userMsg(level)]);
      this.state.editValue = level;
      this.showEditConfirmation();
      return;
    }

    if (value === "confirm_edit_execute") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.confirmEdit"))]);
      await this.executeEdit();
      return;
    }

    if (value === "cancel_edit") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.cancelEdit"))]);
      this.showEditFieldChoice();
      return;
    }

    if (value === "continue_edit_same") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.continueEditSame"))]);
      this.showEditFieldChoice();
      return;
    }

    if (value === "edit_other_classroom") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.editOtherClassroom"))]);
      await this.loadAndShowClassrooms();
      return;
    }

    if (value === "switch_to_add") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.switchToAdd"))]);
      this.state.classrooms = [];
      this.showModeChoice();
      return;
    }

    if (value === "switch_to_edit") {
      this.emit([userMsg(i18n.t("aiAssistant.classroom.switchToEdit"))]);
      await this.loadAndShowClassrooms();
      return;
    }
  }

  // ═══════════════════════════════════════════════
  // AI-powered batch parsing
  // ═══════════════════════════════════════════════

  private async parseBatchWithAI(text: string) {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.parsing"), { loading: true }),
    ]);
    this.set({ inputDisabled: true });

    try {
      const result = await callParseClassrooms(text);
      if (result.classrooms.length === 0) {
        this.emit([
          assistantMsg(
            result.message || i18n.t("aiAssistant.classroom.noDataDetected"),
          ),
        ]);
        this.set({ inputDisabled: false });
        return;
      }
      this.state.classrooms = result.classrooms;
      this.showConfirmTable();
    } catch {
      this.emit([
        assistantMsg(i18n.t("aiAssistant.classroom.parseFailedRetry")),
      ]);
      this.set({ inputDisabled: false });
    }
  }

  // ═══════════════════════════════════════════════
  // Modification handling (AI-powered, for add confirm step)
  // ═══════════════════════════════════════════════

  private async handleModification(text: string) {
    const classrooms = this.state.classrooms;
    const trimmed = text.trim();

    // ── Bare commands without target — handle locally ──
    if (/^(?:我要|我想|請)?(?:移除|刪除|去掉)$/.test(trimmed)) {
      const buttons: QuickButton[] = classrooms.map((c, i) => ({
        label: i18n.t("aiAssistant.common.remove", { name: c.name }),
        value: `remove:${i}`,
      }));
      this.emit([
        assistantMsg(i18n.t("aiAssistant.classroom.selectRemove"), { buttons }),
      ]);
      return;
    }

    if (/^(?:我要|我想|請)?修改$/.test(trimmed)) {
      this.emit([
        assistantMsg(i18n.t("aiAssistant.classroom.modifyInstructions")),
      ]);
      return;
    }

    // ── All other modifications → delegate to AI ──
    this.emit([
      assistantMsg(i18n.t("aiAssistant.classroom.modifying"), {
        loading: true,
      }),
    ]);
    this.set({ inputDisabled: true });

    try {
      const result = await callProcessClassroomModification(
        trimmed,
        classrooms,
      );

      if (result.action === "unclear") {
        this.emit([assistantMsg(result.message)]);
        this.set({ inputDisabled: false });
        return;
      }

      this.state.classrooms = result.classrooms;

      // If all classrooms were removed, go back to input mode
      if (result.classrooms.length === 0) {
        this.emit([assistantMsg(i18n.t("aiAssistant.classroom.allRemoved"))]);
        this.set({ step: "collect_batch", inputDisabled: false });
        return;
      }

      this.showConfirmTable();
    } catch {
      this.emit([assistantMsg(i18n.t("aiAssistant.classroom.modifyFailed"))]);
      this.set({ inputDisabled: false });
    }
  }

  private removeClassroom(idx: number) {
    const classrooms = this.state.classrooms;
    const removed = classrooms.splice(idx, 1)[0];
    if (classrooms.length === 0) {
      this.emit([assistantMsg(i18n.t("aiAssistant.classroom.allRemoved"))]);
      this.set({ step: "collect_batch", inputDisabled: false });
      return;
    }
    this.emit([
      assistantMsg(
        i18n.t("aiAssistant.common.removed", { name: removed.name }),
      ),
    ]);
    this.showConfirmTable();
  }

  // ═══════════════════════════════════════════════
  // Internal helpers
  // ═══════════════════════════════════════════════

  /** Inject external messages (e.g. AI inline responses) into the flow's message history */
  injectMessage(
    userText: string,
    botContent: string,
    botExtra?: Partial<ChatMessage>,
  ) {
    this.messages.push(userMsg(userText));
    this.messages.push(assistantMsg(botContent, botExtra));
    this.pushMsg([...this.messages]);
  }

  /** Re-route the flow to a different sub-intent (add/edit) mid-conversation */
  async rerouteToSubIntent(subIntent?: string) {
    if (subIntent === "edit") {
      await this.loadAndShowClassrooms();
    } else {
      this.showModeChoice();
    }
  }

  private emit(msgs: ChatMessage[]) {
    this.messages = this.messages.filter((m) => !m.loading);
    this.messages.push(...msgs);
    this.pushMsg([...this.messages]);
  }

  private set(partial: Partial<FlowState>) {
    Object.assign(this.state, partial);
    this.updateState(partial);
  }
}
