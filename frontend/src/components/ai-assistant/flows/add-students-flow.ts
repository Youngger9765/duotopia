/**
 * Add Students Flow — state machine logic (teacher personal backend)
 *
 * Steps:
 * 1. choose_mode       — single or batch
 * 2. select_classroom   — pick from teacher's classrooms
 * 3. collect_single     — collect one student at a time
 * 4. collect_batch      — collect multiple students (free text)
 * 5. confirm            — show table, allow modifications
 * 6. execute            — create students via API
 * 7. complete           — summary
 */

import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import type { ChatMessage, QuickButton, TableColumn } from "../chat/types";

// ─── Types ───

export type FlowStep =
  | "choose_mode"
  | "select_classroom"
  | "collect_single_name"
  | "collect_single_birthday"
  | "collect_batch"
  | "confirm"
  | "execute"
  | "complete";

export interface ParsedStudent {
  name: string;
  birthdate: string;
  valid: boolean;
  error: string | null;
}

interface ClassroomInfo {
  id: number;
  name: string;
  level: string;
}

export interface FlowState {
  step: FlowStep;
  mode: "single" | "batch" | null;
  classrooms: ClassroomInfo[];
  selectedClassroom: ClassroomInfo | null;
  students: ParsedStudent[];
  pendingBatchStudents: ParsedStudent[] | null;
  inputDisabled: boolean;
}

// ─── Constants ───

const TABLE_COLUMNS: TableColumn[] = [
  { key: "index", label: "#" },
  { key: "name", label: "姓名" },
  { key: "birthdate", label: "生日" },
  { key: "status", label: "狀態" },
];

// ─── Helpers ───

let _msgId = 0;
function msgId() {
  return `ast-${++_msgId}`;
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

/**
 * Parse a date string into YYYY-MM-DD format (used for single birthday input).
 * Supports: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD, MM/DD/YYYY
 */
function parseBirthdate(input: string): string | null {
  const s = input.trim();

  // YYYY-MM-DD or YYYY/MM/DD
  const isoMatch = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
  if (isoMatch) {
    const [, y, m, d] = isoMatch;
    return formatDate(y, m, d);
  }

  // YYYYMMDD
  const compactMatch = s.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (compactMatch) {
    const [, y, m, d] = compactMatch;
    return formatDate(y, m, d);
  }

  // MM/DD/YYYY
  const usMatch = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (usMatch) {
    const [, m, d, y] = usMatch;
    return formatDate(y, m, d);
  }

  return null;
}

function formatDate(y: string, m: string, d: string): string | null {
  const year = parseInt(y, 10);
  const month = parseInt(m, 10);
  const day = parseInt(d, 10);

  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  if (year < 1900 || year > 2030) return null;

  return `${y}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function studentTableRows(students: ParsedStudent[]) {
  return students.map((s, i) => ({
    index: String(i + 1),
    name: s.name,
    birthdate: s.birthdate,
    status: s.valid ? "✓" : `⚠️ ${s.error}`,
  }));
}

// ─── API calls ───

async function fetchTeacherClassrooms(): Promise<ClassroomInfo[]> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/classrooms?mode=personal`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("無法取得班級列表");
  const data = await res.json();
  return data.map((c: Record<string, unknown>) => ({
    id: c.id as number,
    name: c.name as string,
    level: (c.level || c.program_level || "A1") as string,
  }));
}

async function callParseStudents(
  userInput: string,
): Promise<{ students: ParsedStudent[]; message: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/ai/assistant/parse-students`, {
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

async function callProcessStudentModification(
  userInput: string,
  currentStudents: ParsedStudent[],
): Promise<{ students: ParsedStudent[]; message: string; action: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(
    `${API_URL}/api/ai/assistant/process-student-modification`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        user_input: userInput,
        current_students: currentStudents,
      }),
    },
  );
  if (!res.ok) throw new Error("AI 處理失敗");
  return res.json();
}

async function createStudent(data: {
  name: string;
  birthdate: string;
  classroom_id: number;
}): Promise<{ id: number; name: string; default_password: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/students`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      name: data.name,
      birthdate: data.birthdate,
      classroom_id: data.classroom_id,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || "新增學生失敗");
  }
  return res.json();
}

// ─── Flow class ───

export class AddStudentsFlow {
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
      mode: null,
      classrooms: [],
      selectedClassroom: null,
      students: [],
      pendingBatchStudents: null,
      inputDisabled: true,
    };

    this.showModeChoice();
  }

  // ─── Step: choose_mode ───

  private showModeChoice() {
    this.emit([
      assistantMsg("請問您要怎麼新增學生？", {
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

  // ─── Step: select_classroom ───

  private async selectClassroom() {
    this.emit([assistantMsg("正在載入班級列表...", { loading: true })]);

    try {
      const classrooms = await fetchTeacherClassrooms();
      this.state.classrooms = classrooms;

      if (classrooms.length === 0) {
        this.emit([
          assistantMsg("您目前沒有班級。請先建立班級再新增學生。", {
            buttons: [
              {
                label: "前往我的班級 →",
                value: "navigate:/teacher/classrooms",
              },
            ],
          }),
        ]);
        return;
      }

      const buttons: QuickButton[] = classrooms.map((c) => ({
        label: `${c.name} (${c.level})`,
        value: `select_classroom:${c.id}`,
      }));

      this.emit([assistantMsg("請選擇要新增學生的班級：", { buttons })]);
      this.set({ step: "select_classroom" });
    } catch (e) {
      this.emit([assistantMsg(`載入班級失敗：${(e as Error).message}`)]);
    }
  }

  private onClassroomSelected(classroomId: number) {
    const classroom = this.state.classrooms.find((c) => c.id === classroomId);
    if (!classroom) return;

    this.state.selectedClassroom = classroom;

    if (this.state.mode === "single") {
      this.collectSingleName();
    } else {
      this.collectBatch();
    }
  }

  // ─── Step: collect_single ───

  private collectSingleName() {
    const classroom = this.state.selectedClassroom!;
    this.emit([
      assistantMsg(
        `班級：**${classroom.name} (${classroom.level})**\n\n請輸入學生姓名：`,
      ),
    ]);
    this.set({ step: "collect_single_name", inputDisabled: false });
  }

  private collectSingleBirthday(name: string) {
    this.state.students = [
      {
        name,
        birthdate: "",
        valid: true,
        error: null,
      },
    ];
    this.emit([
      assistantMsg(
        `學生姓名：**${name}**\n\n請輸入生日（西元年）：\n\n💡 生日將作為學生的預設登入密碼（YYYYMMDD 格式）`,
        {
          buttons: [
            {
              label: "不知道生日",
              value: "unknown_birthday",
            },
          ],
        },
      ),
    ]);
    this.set({ step: "collect_single_birthday", inputDisabled: false });
  }

  private confirmSingleStudent(birthdate: string) {
    this.state.students[0].birthdate = birthdate;
    this.showConfirmTable();
  }

  // ─── Step: collect_batch ───

  private collectBatch() {
    const classroom = this.state.selectedClassroom!;
    this.emit([
      assistantMsg(
        `班級：**${classroom.name} (${classroom.level})**\n\n請提供學生的**姓名**和**生日**。\n可一次提供多位，例如：\n\`\`\`\n林小明 2015-03-21\n張美玲 2014-08-15\n王大偉 2015-01-10\n\`\`\`\n也可以用自然語言描述，例如：\n「小明、小華、小美，生日都是 2015-01-01」\n\n💡 生日將作為學生的預設登入密碼（YYYYMMDD 格式）\n不知道生日可以說「不知道生日」，系統會使用預設值。`,
      ),
    ]);
    this.set({ step: "collect_batch", inputDisabled: false });
  }

  // ─── Step: confirm ───

  private showConfirmTable() {
    const students = this.state.students;
    const classroom = this.state.selectedClassroom!;
    const allValid = students.every((s) => s.valid);

    const buttons: QuickButton[] = [];

    if (allValid) {
      buttons.push({
        label: "確認新增",
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

    const header = `即將在【${classroom.name}】新增以下學生：`;

    this.emit([
      assistantMsg(header, {
        table: {
          columns: TABLE_COLUMNS,
          rows: studentTableRows(students),
        },
        buttons,
      }),
    ]);
    this.set({ step: "confirm", inputDisabled: false });
  }

  // ─── Step: execute ───

  private async executeCreate() {
    this.set({ step: "execute", inputDisabled: true });
    const students = this.state.students.filter((s) => s.valid);
    const classroom = this.state.selectedClassroom!;

    this.emit([assistantMsg("正在新增學生...", { loading: true })]);

    const successes: {
      name: string;
      birthdate: string;
      default_password: string;
    }[] = [];
    const failures: { name: string; error: string }[] = [];

    for (const s of students) {
      try {
        const result = await createStudent({
          name: s.name,
          birthdate: s.birthdate,
          classroom_id: classroom.id,
        });
        successes.push({
          name: s.name,
          birthdate: s.birthdate,
          default_password: result.default_password,
        });
      } catch (e) {
        failures.push({ name: s.name, error: (e as Error).message });
      }
    }

    this.showSummary(successes, failures);
  }

  // ─── Step: complete ───

  private showSummary(
    successes: {
      name: string;
      birthdate: string;
      default_password: string;
    }[],
    failures: { name: string; error: string }[],
  ) {
    const classroom = this.state.selectedClassroom!;
    let summary = "新增完成！\n\n";

    if (successes.length > 0) {
      summary += `✅ 成功：${successes.length} 位\n`;
      for (const s of successes) {
        summary += `  - ${s.name} (${s.birthdate})\n`;
      }
      summary += `\n學生登入資訊：\n  帳號：使用 Email 或教師提供的登入連結\n  預設密碼：學生的生日（YYYYMMDD 格式）\n`;
    }

    if (failures.length > 0) {
      summary += `\n⚠️ 失敗：${failures.length} 位\n`;
      for (const f of failures) {
        summary += `  - ${f.name} → ${f.error}\n`;
      }
    }

    this.emit([
      assistantMsg(summary, {
        buttons: [
          {
            label: `繼續新增到${classroom.name}`,
            value: "restart_same_classroom",
            variant: "default",
          },
          {
            label: "選擇其他班級",
            value: "restart_flow",
          },
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

  // ─── Prompt: switch to batch ───

  private promptSwitchToBatch() {
    this.emit([
      assistantMsg("看起來您想一次新增多位學生，要切換到**批次新增**嗎？", {
        buttons: [
          { label: "切換到批次新增", value: "confirm_switch_batch" },
          { label: "繼續單筆新增", value: "cancel_switch_batch" },
        ],
      }),
    ]);
    this.set({ inputDisabled: true });
  }

  // ─── Public: handle user input ───

  async handleUserInput(text: string) {
    const { step } = this.state;

    if (step === "collect_single_name") {
      const name = text.trim();
      if (!name) {
        this.emit([userMsg(text), assistantMsg("姓名不能為空，請重新輸入：")]);
        return;
      }
      this.emit([userMsg(text), assistantMsg("", { loading: true })]);
      this.set({ inputDisabled: true });
      try {
        // Send raw text to AI — let AI decide if it's one name or multiple students
        const result = await callParseStudents(text);
        // AI returned multiple students → user likely wants batch mode
        if (result.students.length > 1) {
          this.state.pendingBatchStudents = result.students;
          this.promptSwitchToBatch();
          return;
        }
        const first = result.students[0];
        if (first && !first.valid && first.error?.includes("不適當")) {
          this.emit([assistantMsg(first.error || "姓名不適當，請重新輸入：")]);
          this.set({ inputDisabled: false });
          return;
        }
        this.collectSingleBirthday(first ? first.name : name);
      } catch {
        // API failure — allow through, backend will catch on create
        this.collectSingleBirthday(name);
      }
      return;
    }

    if (step === "collect_single_birthday") {
      // Try local parsing first (instant), fallback to AI for unusual formats
      const birthdate = parseBirthdate(text.trim());
      if (birthdate) {
        this.emit([userMsg(text)]);
        this.confirmSingleStudent(birthdate);
        return;
      }
      // AI fallback for natural language dates
      this.emit([userMsg(text), assistantMsg("", { loading: true })]);
      this.set({ inputDisabled: true });
      try {
        const studentName = this.state.students[0]?.name || "學生";
        const result = await callParseStudents(`${studentName} ${text.trim()}`);
        // AI returned multiple students → batch intent
        if (result.students.length > 1) {
          this.state.pendingBatchStudents = result.students;
          this.promptSwitchToBatch();
          return;
        }
        const first = result.students[0];
        if (first?.valid && first.birthdate) {
          this.confirmSingleStudent(first.birthdate);
        } else {
          this.emit([
            assistantMsg(
              first?.error || "無法辨識生日，請使用西元年重新輸入：",
            ),
          ]);
          this.set({ inputDisabled: false });
        }
      } catch {
        this.emit([assistantMsg("無法辨識生日，請使用西元年重新輸入：")]);
        this.set({ inputDisabled: false });
      }
      return;
    }

    if (step === "collect_batch") {
      this.emit([userMsg(text)]);
      await this.parseBatchWithAI(text);
      return;
    }

    if (step === "confirm") {
      this.emit([userMsg(text)]);
      await this.handleModification(text);
      return;
    }
  }

  // ─── Public: handle button click ───

  async handleButtonSelect(_messageId: string, value: string) {
    if (value === "_disabled") return;
    if (value.startsWith("navigate:")) return; // Handled by parent component

    if (value === "confirm_switch_batch") {
      this.emit([userMsg("切換到批次新增")]);
      this.state.mode = "batch";
      // If AI already parsed students, go straight to confirm table
      if (
        this.state.pendingBatchStudents &&
        this.state.pendingBatchStudents.length > 0
      ) {
        this.state.students = this.state.pendingBatchStudents;
        this.state.pendingBatchStudents = null;
        this.showConfirmTable();
      } else {
        this.state.students = [];
        this.collectBatch();
      }
      return;
    }

    if (value === "cancel_switch_batch") {
      this.emit([userMsg("繼續單筆新增")]);
      // Resume where we were
      if (this.state.step === "collect_single_birthday") {
        this.emit([assistantMsg("好的，請繼續輸入生日（西元年）：")]);
      } else {
        this.emit([assistantMsg("好的，請繼續輸入學生姓名：")]);
      }
      this.set({ inputDisabled: false });
      return;
    }

    if (value === "unknown_birthday") {
      this.emit([
        userMsg("不知道生日"),
        assistantMsg(
          "好的，我先幫您使用預設生日 **2012-01-01**，預設密碼為 **20120101**。\n\n請提醒學生第一次登入後自行修改密碼。",
        ),
      ]);
      this.confirmSingleStudent("2012-01-01");
      return;
    }

    if (value === "mode:single") {
      this.emit([userMsg("一個一個新增")]);
      this.state.mode = "single";
      await this.selectClassroom();
      return;
    }

    if (value === "mode:batch") {
      this.emit([userMsg("批次新增")]);
      this.state.mode = "batch";
      await this.selectClassroom();
      return;
    }

    if (value.startsWith("select_classroom:")) {
      const id = parseInt(value.replace("select_classroom:", ""), 10);
      const classroom = this.state.classrooms.find((c) => c.id === id);
      if (classroom) {
        this.emit([userMsg(`${classroom.name} (${classroom.level})`)]);
        this.onClassroomSelected(id);
      }
      return;
    }

    if (value === "confirm_execute") {
      this.emit([userMsg("確認新增")]);
      await this.executeCreate();
      return;
    }

    if (value.startsWith("remove:")) {
      const idx = parseInt(value.replace("remove:", ""), 10);
      if (idx >= 0 && idx < this.state.students.length) {
        this.emit([userMsg(`移除 ${this.state.students[idx].name}`)]);
        this.removeStudent(idx);
      }
      return;
    }

    if (value === "edit_table") {
      this.emit([
        userMsg("我要修改"),
        assistantMsg(
          "請告訴我要怎麼修改，例如：\n- 「林小明的生日改成 2015-04-21」\n- 「把王大偉移除」\n- 「再加一個 趙小華 2015-06-01」",
        ),
      ]);
      this.set({ inputDisabled: false });
      return;
    }

    if (value === "restart_same_classroom") {
      this.emit([userMsg("繼續新增")]);
      this.state.students = [];
      if (this.state.mode === "single") {
        this.collectSingleName();
      } else {
        this.collectBatch();
      }
      return;
    }

    if (value === "restart_flow") {
      this.emit([userMsg("選擇其他班級")]);
      this.state.students = [];
      this.state.selectedClassroom = null;
      await this.selectClassroom();
      return;
    }

    if (value === "close_panel") {
      this.emit([
        userMsg("結束"),
        assistantMsg("感謝使用！如需再新增學生，隨時點選 AI 助手。"),
      ]);
      return;
    }
  }

  // ─── AI-powered batch parsing ───

  private async parseBatchWithAI(text: string) {
    this.emit([assistantMsg("正在解析學生資料...", { loading: true })]);
    this.set({ inputDisabled: true });

    try {
      const result = await callParseStudents(text);
      if (result.students.length === 0) {
        this.emit([
          assistantMsg(result.message || "未偵測到學生資料，請重新輸入。"),
        ]);
        this.set({ inputDisabled: false });
        return;
      }

      // Deduplicate by name + birthdate
      const seen = new Set<string>();
      const deduped: ParsedStudent[] = [];
      const dupes: string[] = [];
      for (const s of result.students) {
        const key = `${s.name}|${s.birthdate}`;
        if (seen.has(key)) {
          dupes.push(s.name);
        } else {
          seen.add(key);
          deduped.push(s);
        }
      }

      if (dupes.length > 0) {
        this.emit([
          assistantMsg(`提醒：已去除重複的學生：${dupes.join("、")}`),
        ]);
      }

      this.state.students = deduped;
      this.showConfirmTable();
    } catch {
      this.emit([assistantMsg("AI 解析失敗，請重新輸入學生資料。")]);
      this.set({ inputDisabled: false });
    }
  }

  // ─── Modification handling (AI-powered) ───

  private async handleModification(text: string) {
    const students = this.state.students;
    const trimmed = text.trim();

    // ── Bare commands without target — handle locally ──
    if (/^(?:我要|我想|請)?(?:移除|刪除|去掉)$/.test(trimmed)) {
      const buttons: QuickButton[] = students.map((s, i) => ({
        label: `移除 ${s.name}`,
        value: `remove:${i}`,
      }));
      this.emit([assistantMsg("請選擇要移除的學生：", { buttons })]);
      return;
    }

    if (/^(?:我要|我想|請)?修改$/.test(trimmed)) {
      this.emit([
        assistantMsg(
          "請告訴我要怎麼修改，例如：\n- 「林小明的生日改成 2015-04-21」\n- 「把王大偉移除」\n- 「再加一個 趙小華 2015-06-01」",
        ),
      ]);
      return;
    }

    // ── All other modifications → delegate to AI ──
    this.emit([assistantMsg("正在處理修改...", { loading: true })]);
    this.set({ inputDisabled: true });

    try {
      const result = await callProcessStudentModification(trimmed, students);

      if (result.action === "unclear") {
        this.emit([assistantMsg(result.message)]);
        this.set({ inputDisabled: false });
        return;
      }

      this.state.students = result.students;

      // If all students were removed, go back to input mode
      if (result.students.length === 0) {
        this.emit([assistantMsg("已移除所有學生。請重新輸入學生資料。")]);
        this.set({ step: "collect_batch", inputDisabled: false });
        return;
      }

      this.showConfirmTable();
    } catch {
      this.emit([
        assistantMsg(
          "AI 處理失敗。請用以下格式：\n- 「林小明的生日改成 2015-04-21」\n- 「把王大偉移除」\n- 「再加一個 趙小華 2015-06-01」",
        ),
      ]);
      this.set({ inputDisabled: false });
    }
  }

  private removeStudent(idx: number) {
    const students = this.state.students;
    const removed = students.splice(idx, 1)[0];
    if (students.length === 0) {
      this.emit([assistantMsg("已移除所有學生。請重新輸入學生資料。")]);
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
