/**
 * Add Classroom Flow — state machine logic (teacher personal backend)
 *
 * Steps:
 * 1. choose_mode    — single or batch
 * 2. collect_single — collect name + level for one classroom
 * 3. collect_batch  — collect multiple classrooms (free text)
 * 4. confirm        — show table, allow modifications
 * 5. execute        — create classrooms via API
 * 6. complete       — summary
 */

import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import type { ChatMessage, QuickButton, TableColumn } from "../chat/types";

// ─── Types ───

export type FlowStep =
  | "choose_mode"
  | "collect_single_name"
  | "collect_single_level"
  | "collect_batch"
  | "confirm"
  | "execute"
  | "complete";

export interface ParsedClassroom {
  name: string;
  level: string;
  valid: boolean;
  error: string | null;
}

export interface FlowState {
  step: FlowStep;
  classrooms: ParsedClassroom[];
  inputDisabled: boolean;
}

// ─── Constants ───

const VALID_LEVELS = ["PREA", "A1", "A2", "B1", "B2", "C1", "C2"];

const LEVEL_BUTTONS: QuickButton[] = VALID_LEVELS.map((l) => ({
  label: l,
  value: `select_level:${l}`,
}));

const TABLE_COLUMNS: TableColumn[] = [
  { key: "index", label: "#" },
  { key: "name", label: "班級名稱" },
  { key: "level", label: "語言等級" },
  { key: "status", label: "狀態" },
];

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
  if (!res.ok) throw new Error("AI 解析失敗");
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
  if (!res.ok) throw new Error("AI 處理失敗");
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
    throw new Error(err?.detail || "建立班級失敗");
  }
  return res.json();
}

// ─── Flow class ───

export class AddClassroomFlow {
  state: FlowState;
  messages: ChatMessage[];

  private pushMsg: (msgs: ChatMessage[]) => void;
  private updateState: (partial: Partial<FlowState>) => void;

  constructor(
    pushMsg: (msgs: ChatMessage[]) => void,
    updateState: (partial: Partial<FlowState>) => void,
  ) {
    this.pushMsg = pushMsg;
    this.updateState = updateState;
    this.messages = [];
    this.state = {
      step: "choose_mode",
      classrooms: [],
      inputDisabled: true,
    };

    // Start flow
    this.showModeChoice();
  }

  // ─── Step: choose_mode ───

  private showModeChoice() {
    this.emit([
      assistantMsg("請問您要怎麼新增班級？", {
        buttons: [
          {
            label: "一個一個新增",
            value: "mode:single",
            variant: "default",
          },
          {
            label: "批次新增",
            value: "mode:batch",
          },
        ],
      }),
    ]);
  }

  // ─── Step: collect_single ───

  private collectSingleName() {
    this.emit([assistantMsg("請輸入班級名稱：")]);
    this.set({ step: "collect_single_name", inputDisabled: false });
  }

  private collectSingleLevel(name: string) {
    this.state.classrooms = [{ name, level: "", valid: true, error: null }];
    this.emit([
      assistantMsg(`班級名稱：**${name}**\n\n請選擇語言等級：`, {
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
      assistantMsg(
        "請輸入班級資料，每行一個班級。\n格式：**班級名稱 等級**（等級不填預設 A1）\n\n例如：\n```\n高級英文班 B1\n初級英文班 A1\n兒童班 PREA\n```",
      ),
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
        label: "確認建立",
        value: "confirm_execute",
        variant: "default",
      });
    } else {
      buttons.push({
        label: "⚠️ 請修正錯誤後才能確認",
        value: "_disabled",
        variant: "secondary",
      });
    }
    buttons.push({ label: "我要修改", value: "edit_table" });

    const header =
      classrooms.length === 1
        ? "即將建立以下班級："
        : `即將建立 ${classrooms.length} 個班級：`;

    this.emit([
      assistantMsg(header, {
        table: {
          columns: TABLE_COLUMNS,
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

    this.emit([assistantMsg("正在建立班級...", { loading: true })]);

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
    let summary = "建立完成！\n\n";

    if (successes.length > 0) {
      summary += `✅ 成功：${successes.length} 個班級\n`;
      for (const s of successes) {
        summary += `  - ${s.name} (${s.level})\n`;
      }
    }

    if (failures.length > 0) {
      summary += `\n⚠️ 失敗：${failures.length} 個班級\n`;
      for (const f of failures) {
        summary += `  - ${f.name} → ${f.error}\n`;
      }
    }

    summary += "\n接下來可以到班級中新增學生。";

    this.emit([
      assistantMsg(summary, {
        buttons: [
          { label: "繼續新增班級", value: "restart_flow", variant: "default" },
          {
            label: "前往我的班級 →",
            value: "navigate:/teacher/classrooms",
          },
          { label: "結束", value: "close_panel" },
        ],
      }),
    ]);
    this.set({ step: "complete", inputDisabled: true });
  }

  // ─── Public: handle user input ───

  async handleUserInput(text: string) {
    const { step } = this.state;

    if (step === "collect_single_name") {
      const name = text.trim();
      if (!name) {
        this.emit([
          userMsg(text),
          assistantMsg("班級名稱不能為空，請重新輸入："),
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
            assistantMsg(first.error || "班級名稱不適當，請重新輸入："),
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
            `「${text}」不是有效的等級。請選擇：${VALID_LEVELS.join("、")}`,
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
  }

  // ─── Public: handle button click ───

  async handleButtonSelect(_messageId: string, value: string) {
    if (value === "_disabled") return;
    if (value.startsWith("navigate:")) return; // Handled by parent component

    if (value === "mode:single") {
      this.emit([userMsg("一個一個新增")]);
      this.collectSingleName();
      return;
    }

    if (value === "mode:batch") {
      this.emit([userMsg("批次新增")]);
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
      this.emit([userMsg("確認建立")]);
      await this.executeCreate();
      return;
    }

    if (value.startsWith("remove:")) {
      const idx = parseInt(value.replace("remove:", ""), 10);
      if (idx >= 0 && idx < this.state.classrooms.length) {
        this.emit([userMsg(`移除 ${this.state.classrooms[idx].name}`)]);
        this.removeClassroom(idx);
      }
      return;
    }

    if (value === "edit_table") {
      this.emit([
        userMsg("我要修改"),
        assistantMsg(
          "請告訴我要怎麼修改，例如：\n- 「高級英文班改成 B2」\n- 「把兒童班移除」\n- 「再加一個 中級班 A2」",
        ),
      ]);
      this.set({ inputDisabled: false });
      return;
    }

    if (value === "restart_flow") {
      this.emit([userMsg("繼續新增班級")]);
      this.state.classrooms = [];
      this.showModeChoice();
      return;
    }

    if (value === "close_panel") {
      this.emit([
        userMsg("結束"),
        assistantMsg("感謝使用！如需再新增班級，隨時點選 AI 助手。"),
      ]);
      return;
    }
  }

  // ─── AI-powered batch parsing ───

  private async parseBatchWithAI(text: string) {
    this.emit([assistantMsg("正在解析班級資料...", { loading: true })]);
    this.set({ inputDisabled: true });

    try {
      const result = await callParseClassrooms(text);
      if (result.classrooms.length === 0) {
        this.emit([
          assistantMsg(result.message || "未偵測到班級資料，請重新輸入。"),
        ]);
        this.set({ inputDisabled: false });
        return;
      }
      this.state.classrooms = result.classrooms;
      this.showConfirmTable();
    } catch {
      this.emit([assistantMsg("AI 解析失敗，請重新輸入班級資料。")]);
      this.set({ inputDisabled: false });
    }
  }

  // ─── Modification handling (AI-powered) ───

  private async handleModification(text: string) {
    const classrooms = this.state.classrooms;
    const trimmed = text.trim();

    // ── Bare commands without target — handle locally ──
    if (/^(?:我要|我想|請)?(?:移除|刪除|去掉)$/.test(trimmed)) {
      const buttons: QuickButton[] = classrooms.map((c, i) => ({
        label: `移除 ${c.name}`,
        value: `remove:${i}`,
      }));
      this.emit([assistantMsg("請選擇要移除的班級：", { buttons })]);
      return;
    }

    if (/^(?:我要|我想|請)?修改$/.test(trimmed)) {
      this.emit([
        assistantMsg(
          "請告訴我要怎麼修改，例如：\n- 「高級英文班改成 B2」\n- 「把兒童班移除」\n- 「再加一個 中級班 A2」",
        ),
      ]);
      return;
    }

    // ── All other modifications → delegate to AI ──
    this.emit([assistantMsg("正在處理修改...", { loading: true })]);
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
        this.emit([assistantMsg("已移除所有班級。請重新輸入班級資料。")]);
        this.set({ step: "collect_batch", inputDisabled: false });
        return;
      }

      this.showConfirmTable();
    } catch {
      this.emit([
        assistantMsg(
          "AI 處理失敗。請用以下格式：\n- 「高級英文班改成 B2」\n- 「把兒童班移除」\n- 「再加一個 中級班 A2」",
        ),
      ]);
      this.set({ inputDisabled: false });
    }
  }

  private removeClassroom(idx: number) {
    const classrooms = this.state.classrooms;
    const removed = classrooms.splice(idx, 1)[0];
    if (classrooms.length === 0) {
      this.emit([assistantMsg("已移除所有班級。請重新輸入班級資料。")]);
      this.set({ step: "collect_batch", inputDisabled: false });
      return;
    }
    this.emit([assistantMsg(`已移除「${removed.name}」`)]);
    this.showConfirmTable();
  }

  // ─── Internal helpers ───

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
