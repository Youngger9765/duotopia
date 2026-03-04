/**
 * Manage Students Flow — state machine logic (teacher personal backend)
 *
 * Entry:
 *   choose_action → [新增學生] or [修改學生] (also accepts free text)
 *
 * Add path:
 *   choose_mode → select_classroom → collect_single_name → collect_single_birthday
 *     → collect_optional_fields → confirm → execute → complete
 *   choose_mode → select_classroom → collect_batch → confirm → execute → complete
 *
 * Edit path (batch, natural language):
 *   edit_select_classroom → batch_edit_collect (show students + text input)
 *     → AI processes → batch_edit_confirm (show changes) → batch_edit_execute → edit_complete
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
  | "select_classroom"
  | "collect_single_name"
  | "collect_single_birthday"
  | "collect_optional_fields"
  | "collect_optional_value"
  | "collect_batch"
  | "confirm"
  | "execute"
  | "complete"
  // Edit path (batch, natural language)
  | "edit_select_classroom"
  | "batch_edit_collect"
  | "batch_edit_confirm"
  | "batch_edit_execute"
  | "edit_complete";

export interface ParsedStudent {
  name: string;
  birthdate: string;
  email?: string;
  student_number?: string;
  phone?: string;
  valid: boolean;
  error: string | null;
}

interface ClassroomInfo {
  id: number;
  name: string;
  level: string;
}

interface ExistingStudent {
  id: number;
  name: string;
  birthdate: string | null;
  email: string | null;
  student_number: string | null;
  phone: string | null;
}

interface StudentEditChange {
  id: number;
  name: string;
  changes: {
    field: string;
    label: string;
    oldValue: string;
    newValue: string;
  }[];
}

export interface FlowState {
  step: FlowStep;
  mode: "single" | "batch" | null;
  classrooms: ClassroomInfo[];
  selectedClassroom: ClassroomInfo | null;
  students: ParsedStudent[];
  pendingBatchStudents: ParsedStudent[] | null;
  inputDisabled: boolean;
  // Optional field collection (add single)
  currentOptionalField: "email" | "student_number" | "phone" | null;
  // Edit path (batch)
  existingStudents: ExistingStudent[];
  editChanges: StudentEditChange[];
  editedStudents: ExistingStudent[];
}

// ─── Constants ───

const EDIT_INTENT_RE = /(?:修改|改|編輯|更新|rename|edit|update|change)/i;

function getTableColumns(students: ParsedStudent[]): TableColumn[] {
  const cols: TableColumn[] = [
    { key: "index", label: "#" },
    { key: "name", label: i18n.t("aiAssistant.students.table.name") },
    { key: "birthdate", label: i18n.t("aiAssistant.students.table.birthdate") },
  ];

  if (students.some((s) => s.email)) {
    cols.push({
      key: "email",
      label: i18n.t("aiAssistant.students.table.email"),
    });
  }
  if (students.some((s) => s.student_number)) {
    cols.push({
      key: "student_number",
      label: i18n.t("aiAssistant.students.table.studentNumber"),
    });
  }
  if (students.some((s) => s.phone)) {
    cols.push({
      key: "phone",
      label: i18n.t("aiAssistant.students.table.phone"),
    });
  }

  cols.push({
    key: "status",
    label: i18n.t("aiAssistant.students.table.status"),
  });
  return cols;
}

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
    email: s.email || "",
    student_number: s.student_number || "",
    phone: s.phone || "",
    status: s.valid ? "✓" : `⚠️ ${s.error}`,
  }));
}

// ─── API calls ───

async function fetchTeacherClassrooms(): Promise<ClassroomInfo[]> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/classrooms?mode=personal`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok)
    throw new Error(i18n.t("aiAssistant.students.fetchClassroomsFailed"));
  const data = await res.json();
  return data.map((c: Record<string, unknown>) => ({
    id: c.id as number,
    name: c.name as string,
    level: (c.level || c.program_level || "A1") as string,
  }));
}

async function fetchClassroomStudents(
  classroomId: number,
): Promise<ExistingStudent[]> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(
    `${API_URL}/api/teachers/classrooms/${classroomId}/students`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!res.ok)
    throw new Error(i18n.t("aiAssistant.students.fetchStudentsFailed"));
  const data = await res.json();
  return data.map((s: Record<string, unknown>) => ({
    id: s.id as number,
    name: s.name as string,
    birthdate: (s.birthdate as string | null) || null,
    email: (s.email as string | null) || null,
    student_number: (s.student_number as string | null) || null,
    phone: (s.phone as string | null) || null,
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
  if (!res.ok) throw new Error(i18n.t("aiAssistant.students.parseFailed"));
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
  if (!res.ok)
    throw new Error(i18n.t("aiAssistant.students.modifyProcessFailed"));
  return res.json();
}

async function createStudent(data: {
  name: string;
  birthdate: string;
  classroom_id: number;
  email?: string;
  student_number?: string;
  phone?: string;
}): Promise<{ id: number; name: string; default_password: string }> {
  const token = useTeacherAuthStore.getState().token;
  const body: Record<string, unknown> = {
    name: data.name,
    birthdate: data.birthdate,
    classroom_id: data.classroom_id,
  };
  if (data.email) body.email = data.email;
  if (data.student_number) body.student_number = data.student_number;
  if (data.phone) body.phone = data.phone;

  const res = await fetch(`${API_URL}/api/teachers/students`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || i18n.t("aiAssistant.students.createFailed"));
  }
  return res.json();
}

async function updateStudentApi(
  studentId: number,
  data: {
    name?: string;
    email?: string;
    student_number?: string;
    birthdate?: string;
    phone?: string;
  },
): Promise<Record<string, unknown>> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/teachers/students/${studentId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || i18n.t("aiAssistant.students.editFailed"));
  }
  return res.json();
}

async function callBatchStudentEdit(
  userInput: string,
  currentStudents: ExistingStudent[],
): Promise<{ students: ExistingStudent[]; message: string; action: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(
    `${API_URL}/api/ai/assistant/process-batch-student-edit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        user_input: userInput,
        current_students: currentStudents.map((s) => ({
          id: s.id,
          name: s.name,
          birthdate: s.birthdate || "",
          email: s.email || "",
          student_number: s.student_number || "",
          phone: s.phone || "",
        })),
      }),
    },
  );
  if (!res.ok) throw new Error(i18n.t("aiAssistant.students.batchEditFailed"));
  return res.json();
}

// ─── Flow class ───

export class ManageStudentsFlow {
  state: FlowState;
  messages: ChatMessage[];

  private pushMsg: (msgs: ChatMessage[]) => void;
  private updateState: (partial: Partial<FlowState>) => void;

  constructor(
    pushMsg: (msgs: ChatMessage[]) => void,
    updateState: (partial: Partial<FlowState>) => void,
    initialData?: { subIntent?: string },
  ) {
    this.pushMsg = pushMsg;
    this.updateState = updateState;
    this.messages = [];
    this.state = {
      step: "choose_action",
      mode: null,
      classrooms: [],
      selectedClassroom: null,
      students: [],
      pendingBatchStudents: null,
      inputDisabled: true,
      currentOptionalField: null,
      existingStudents: [],
      editChanges: [],
      editedStudents: [],
    };

    // Route based on initialData from intent detection
    if (initialData?.subIntent === "edit") {
      this.loadAndShowClassroomsForEdit();
    } else if (initialData?.subIntent === "add") {
      this.showModeChoice();
    } else {
      this.showActionChoice();
    }
  }

  // ═══════════════════════════════════════════════
  // Entry: choose_action
  // ═══════════════════════════════════════════════

  private showActionChoice() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.actionChoice"), {
        buttons: [
          {
            label: i18n.t("aiAssistant.students.actionAdd"),
            value: "action:add",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.students.actionEdit"),
            value: "action:edit",
          },
        ],
      }),
    ]);
    this.set({ step: "choose_action", inputDisabled: false });
  }

  // ═══════════════════════════════════════════════
  // ADD PATH
  // ═══════════════════════════════════════════════

  // ─── Step: choose_mode ───

  private showModeChoice() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.modeChoice"), {
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

  // ─── Step: select_classroom ───

  private async selectClassroom() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.loadingClassrooms"), {
        loading: true,
      }),
    ]);

    try {
      const classrooms = await fetchTeacherClassrooms();
      this.state.classrooms = classrooms;

      if (classrooms.length === 0) {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.students.noClassrooms"), {
            buttons: [
              {
                label: i18n.t("aiAssistant.common.goToClassrooms"),
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

      this.emit([
        assistantMsg(i18n.t("aiAssistant.students.selectClassroom"), {
          buttons,
        }),
      ]);
      this.set({ step: "select_classroom" });
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.students.loadClassroomsFailed", {
            error: (e as Error).message,
          }),
        ),
      ]);
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
        i18n.t("aiAssistant.students.classroomLabel", {
          name: classroom.name,
          level: classroom.level,
        }) + i18n.t("aiAssistant.students.enterName"),
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
      assistantMsg(i18n.t("aiAssistant.students.enterBirthday", { name }), {
        buttons: [
          {
            label: i18n.t("aiAssistant.students.unknownBirthday"),
            value: "unknown_birthday",
          },
        ],
      }),
    ]);
    this.set({ step: "collect_single_birthday", inputDisabled: false });
  }

  private confirmSingleStudent(birthdate: string) {
    this.state.students[0].birthdate = birthdate;
    // Route through optional fields before confirming
    this.showOptionalFieldPrompt();
  }

  // ─── Step: collect_optional_fields ───

  private showOptionalFieldPrompt() {
    const student = this.state.students[0];
    const remaining: QuickButton[] = [];

    if (!student.email) {
      remaining.push({ label: "Email", value: "optional_field:email" });
    }
    if (!student.student_number) {
      remaining.push({
        label: i18n.t("aiAssistant.students.fieldStudentNumber"),
        value: "optional_field:student_number",
      });
    }
    if (!student.phone) {
      remaining.push({
        label: i18n.t("aiAssistant.students.fieldPhone"),
        value: "optional_field:phone",
      });
    }

    if (remaining.length === 0) {
      this.showConfirmTable();
      return;
    }

    remaining.push({
      label: i18n.t("aiAssistant.students.skipOptional"),
      value: "skip_optional",
      variant: "secondary",
    });

    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.optionalFieldPrompt"), {
        buttons: remaining,
      }),
    ]);
    this.set({ step: "collect_optional_fields", inputDisabled: true });
  }

  private collectOptionalValue(field: "email" | "student_number" | "phone") {
    this.state.currentOptionalField = field;

    const promptKey =
      field === "email"
        ? "aiAssistant.students.enterEmail"
        : field === "student_number"
          ? "aiAssistant.students.enterStudentNumber"
          : "aiAssistant.students.enterPhone";

    this.emit([assistantMsg(i18n.t(promptKey))]);
    this.set({ step: "collect_optional_value", inputDisabled: false });
  }

  // ─── Step: collect_batch ───

  private collectBatch() {
    const classroom = this.state.selectedClassroom!;
    this.emit([
      assistantMsg(
        i18n.t("aiAssistant.students.classroomLabel", {
          name: classroom.name,
          level: classroom.level,
        }) + i18n.t("aiAssistant.students.batchInstructions"),
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
        label: i18n.t("aiAssistant.common.confirm"),
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

    const header = i18n.t("aiAssistant.students.confirmHeader", {
      classroom: classroom.name,
    });

    this.emit([
      assistantMsg(header, {
        table: {
          columns: getTableColumns(students),
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

    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.creating"), { loading: true }),
    ]);

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
          ...(s.email && { email: s.email }),
          ...(s.student_number && { student_number: s.student_number }),
          ...(s.phone && { phone: s.phone }),
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
    let summary = i18n.t("aiAssistant.students.complete") + "\n\n";

    if (successes.length > 0) {
      summary +=
        i18n.t("aiAssistant.students.successCount", {
          count: successes.length,
        }) + "\n";
      for (const s of successes) {
        summary += `  - ${s.name} (${s.birthdate})\n`;
      }
      summary += "\n" + i18n.t("aiAssistant.students.loginInfo") + "\n";
    }

    if (failures.length > 0) {
      summary +=
        "\n" +
        i18n.t("aiAssistant.students.failureCount", {
          count: failures.length,
        }) +
        "\n";
      for (const f of failures) {
        summary += `  - ${f.name} → ${f.error}\n`;
      }
    }

    this.emit([
      assistantMsg(summary, {
        buttons: [
          {
            label: i18n.t("aiAssistant.students.continueAddTo", {
              classroom: classroom.name,
            }),
            value: "restart_same_classroom",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.students.switchToEdit"),
            value: "switch_to_edit",
          },
          {
            label: i18n.t("aiAssistant.common.selectOtherClassroom"),
            value: "restart_flow",
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

  // ─── Prompt: switch to batch ───

  private promptSwitchToBatch() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.switchToBatchPrompt"), {
        buttons: [
          {
            label: i18n.t("aiAssistant.common.switchToBatch"),
            value: "confirm_switch_batch",
          },
          {
            label: i18n.t("aiAssistant.common.continueSingle"),
            value: "cancel_switch_batch",
          },
        ],
      }),
    ]);
    this.set({ inputDisabled: true });
  }

  // ═══════════════════════════════════════════════
  // EDIT PATH
  // ═══════════════════════════════════════════════

  // ─── Step: edit_select_classroom ───

  private async loadAndShowClassroomsForEdit() {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.loadingClassrooms"), {
        loading: true,
      }),
    ]);
    this.set({ step: "edit_select_classroom", inputDisabled: true });

    try {
      const classrooms = await fetchTeacherClassrooms();
      this.state.classrooms = classrooms;

      if (classrooms.length === 0) {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.students.noClassrooms"), {
            buttons: [
              {
                label: i18n.t("aiAssistant.students.actionAdd"),
                value: "action:add",
                variant: "default",
              },
              { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
            ],
          }),
        ]);
        return;
      }

      const buttons: QuickButton[] = classrooms.map((c) => ({
        label: `${c.name} (${c.level})`,
        value: `select_edit_classroom:${c.id}`,
      }));

      this.emit([
        assistantMsg(i18n.t("aiAssistant.students.selectClassroom"), {
          buttons,
        }),
      ]);
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.students.loadClassroomsFailed", {
            error: (e as Error).message,
          }),
          {
            buttons: [
              {
                label: i18n.t("aiAssistant.students.actionAdd"),
                value: "action:add",
              },
              { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
            ],
          },
        ),
      ]);
    }
  }

  // ─── Step: batch_edit_collect ───

  private async loadStudentsAndShowBatchEdit(classroomId: number) {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.loadingStudents"), {
        loading: true,
      }),
    ]);
    this.set({ inputDisabled: true });

    try {
      const students = await fetchClassroomStudents(classroomId);
      this.state.existingStudents = students;

      if (students.length === 0) {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.students.noStudentsForEdit"), {
            buttons: [
              {
                label: i18n.t("aiAssistant.students.actionAdd"),
                value: "action:add",
                variant: "default",
              },
              {
                label: i18n.t("aiAssistant.students.editOtherClassroomStudent"),
                value: "edit_other_classroom_student",
              },
              { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
            ],
          }),
        ]);
        return;
      }

      this.showBatchEditCollect();
    } catch (_e) {
      this.emit([
        assistantMsg(i18n.t("aiAssistant.students.fetchStudentsFailed"), {
          buttons: [
            {
              label: i18n.t("aiAssistant.students.editOtherClassroomStudent"),
              value: "edit_other_classroom_student",
            },
            { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
          ],
        }),
      ]);
    }
  }

  private showBatchEditCollect() {
    const classroom = this.state.selectedClassroom!;
    const students = this.state.existingStudents;

    const list = students
      .map((s) => `- ${s.name}${s.birthdate ? ` (${s.birthdate})` : ""}`)
      .join("\n");

    this.emit([
      assistantMsg(
        i18n.t("aiAssistant.students.batchEditSummary", {
          classroom: classroom.name,
          count: students.length,
          list,
        }),
      ),
    ]);
    this.set({ step: "batch_edit_collect", inputDisabled: false });
  }

  // ─── Step: batch_edit_confirm ───

  private async processBatchEdit(text: string) {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.batchEditProcessing"), {
        loading: true,
      }),
    ]);
    this.set({ inputDisabled: true });

    try {
      const result = await callBatchStudentEdit(
        text,
        this.state.existingStudents,
      );

      if (result.action === "unclear") {
        this.emit([
          assistantMsg(
            i18n.t("aiAssistant.students.batchEditUnclear", {
              message: result.message,
            }),
          ),
        ]);
        this.set({ inputDisabled: false });
        return;
      }

      // Compute diff
      const changes = this.computeEditChanges(
        this.state.existingStudents,
        result.students,
      );

      if (changes.length === 0) {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.students.batchEditNoChanges")),
        ]);
        this.set({ inputDisabled: false });
        return;
      }

      this.state.editChanges = changes;
      this.state.editedStudents = result.students;
      this.showBatchEditConfirm();
    } catch (_e) {
      this.emit([assistantMsg(i18n.t("aiAssistant.students.batchEditFailed"))]);
      this.set({ inputDisabled: false });
    }
  }

  private computeEditChanges(
    original: ExistingStudent[],
    modified: ExistingStudent[],
  ): StudentEditChange[] {
    const fieldLabels: Record<string, string> = {
      name: i18n.t("aiAssistant.students.table.name"),
      birthdate: i18n.t("aiAssistant.students.table.birthdate"),
      email: "Email",
      student_number: i18n.t("aiAssistant.students.table.studentNumber"),
      phone: i18n.t("aiAssistant.students.table.phone"),
    };

    const changes: StudentEditChange[] = [];
    const modifiedMap = new Map(modified.map((s) => [s.id, s]));
    const fields = [
      "name",
      "birthdate",
      "email",
      "student_number",
      "phone",
    ] as const;

    for (const orig of original) {
      const mod = modifiedMap.get(orig.id);
      if (!mod) continue;

      const studentChanges: StudentEditChange["changes"] = [];
      for (const f of fields) {
        const oldVal = (orig[f] || "") as string;
        const newVal = (mod[f] || "") as string;
        if (oldVal !== newVal) {
          studentChanges.push({
            field: f,
            label: fieldLabels[f],
            oldValue: oldVal || i18n.t("aiAssistant.students.notSet"),
            newValue: newVal || i18n.t("aiAssistant.students.notSet"),
          });
        }
      }

      if (studentChanges.length > 0) {
        changes.push({ id: orig.id, name: orig.name, changes: studentChanges });
      }
    }

    return changes;
  }

  private showBatchEditConfirm() {
    const changes = this.state.editChanges;

    let totalChanges = 0;
    let msg =
      i18n.t("aiAssistant.students.batchEditConfirmHeader", {
        count: changes.length,
      }) + "\n\n";

    for (const c of changes) {
      for (const ch of c.changes) {
        msg += `- **${c.name}**：${ch.label} ${ch.oldValue} → ${ch.newValue}\n`;
        totalChanges++;
      }
    }

    // suppress unused
    void totalChanges;

    this.emit([
      assistantMsg(msg, {
        buttons: [
          {
            label: i18n.t("aiAssistant.students.batchEditConfirm"),
            value: "confirm_batch_edit",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.students.batchEditContinue"),
            value: "continue_batch_edit",
          },
          {
            label: i18n.t("aiAssistant.students.batchEditCancel"),
            value: "cancel_batch_edit",
          },
        ],
      }),
    ]);
    this.set({ step: "batch_edit_confirm", inputDisabled: true });
  }

  // ─── Step: batch_edit_execute ───

  private async executeBatchEdit() {
    this.set({ step: "batch_edit_execute", inputDisabled: true });
    const changes = this.state.editChanges;
    const editedMap = new Map(this.state.editedStudents.map((s) => [s.id, s]));

    let success = 0;
    let fail = 0;

    this.emit([
      assistantMsg(
        i18n.t("aiAssistant.students.batchEditExecuting", {
          current: 0,
          total: changes.length,
        }),
        { loading: true },
      ),
    ]);

    for (const c of changes) {
      const edited = editedMap.get(c.id);
      if (!edited) continue;

      const payload: Record<string, string> = {};
      for (const ch of c.changes) {
        payload[ch.field] =
          ch.newValue === i18n.t("aiAssistant.students.notSet")
            ? ""
            : ch.newValue;
      }

      try {
        await updateStudentApi(c.id, payload);
        success++;
      } catch {
        fail++;
      }
    }

    // Update local existingStudents with the edited values
    this.state.existingStudents = this.state.editedStudents;

    this.showEditComplete(success, fail);
  }

  // ─── Step: edit_complete ───

  private showEditComplete(success: number, fail: number) {
    const summaryKey =
      fail > 0
        ? "aiAssistant.students.batchEditPartialFail"
        : "aiAssistant.students.batchEditComplete";

    this.emit([
      assistantMsg(i18n.t(summaryKey, { success, fail }), {
        buttons: [
          {
            label: i18n.t("aiAssistant.students.batchEditContinueSame"),
            value: "continue_batch_edit_same",
            variant: "default",
          },
          {
            label: i18n.t("aiAssistant.students.editOtherClassroomStudent"),
            value: "edit_other_classroom_student",
          },
          {
            label: i18n.t("aiAssistant.students.switchToAdd"),
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

    // ── collect_batch: AI parsed students from natural language ──
    if (step === "collect_batch" && Array.isArray(parsedData.students)) {
      const students = parsedData.students as ParsedStudent[];
      if (students.length === 0) {
        // AI couldn't parse — show message or fallback
        this.emit([
          assistantMsg(
            (parsedData.message as string) ||
              i18n.t("aiAssistant.students.noDataDetected"),
          ),
        ]);
        return;
      }

      // Deduplicate by name + birthdate (same logic as parseBatchWithAI)
      const seen = new Set<string>();
      const deduped: ParsedStudent[] = [];
      const dupes: string[] = [];
      for (const s of students) {
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
          assistantMsg(
            i18n.t("aiAssistant.students.dedupeNotice", {
              names: dupes.join("、"),
            }),
          ),
        ]);
      }

      this.state.students = deduped;
      this.showConfirmTable();
      return;
    }

    // ── confirm: AI modified the student list ──
    if (step === "confirm" && parsedData.modification_action) {
      const action = parsedData.modification_action as string;

      if (action === "unclear") {
        this.emit([
          assistantMsg(
            (parsedData.message as string) ||
              i18n.t("aiAssistant.students.modifyInstructions"),
          ),
        ]);
        return;
      }

      if (Array.isArray(parsedData.students)) {
        const students = parsedData.students as ParsedStudent[];
        this.state.students = students;

        if (students.length === 0) {
          this.emit([assistantMsg(i18n.t("aiAssistant.students.allRemoved"))]);
          this.set({ step: "collect_batch", inputDisabled: false });
          return;
        }

        this.showConfirmTable();
        return;
      }
    }

    // ── batch_edit_collect: AI modified existing students (with IDs) ──
    if (step === "batch_edit_collect" && parsedData.modification_action) {
      const action = parsedData.modification_action as string;

      if (action === "unclear") {
        this.emit([
          assistantMsg(
            i18n.t("aiAssistant.students.batchEditUnclear", {
              message: (parsedData.message as string) || "不確定您要修改什麼。",
            }),
          ),
        ]);
        return;
      }

      if (Array.isArray(parsedData.students)) {
        const modified = parsedData.students as ExistingStudent[];

        // Compute diff
        const changes = this.computeEditChanges(
          this.state.existingStudents,
          modified,
        );

        if (changes.length === 0) {
          this.emit([
            assistantMsg(i18n.t("aiAssistant.students.batchEditNoChanges")),
          ]);
          return;
        }

        this.state.editChanges = changes;
        this.state.editedStudents = modified;
        this.showBatchEditConfirm();
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
        await this.loadAndShowClassroomsForEdit();
      } else {
        this.showModeChoice();
      }
      return;
    }

    // ── collect_optional_value ──
    if (step === "collect_optional_value") {
      this.emit([userMsg(text)]);
      const field = this.state.currentOptionalField!;
      const value = text.trim();
      if (!value) {
        this.emit([assistantMsg(i18n.t("aiAssistant.students.emptyValue"))]);
        return;
      }
      this.state.students[0][field] = value;
      this.state.currentOptionalField = null;
      this.showOptionalFieldPrompt();
      return;
    }

    // ── batch_edit_collect: natural language edit instruction ──
    if (step === "batch_edit_collect") {
      this.emit([userMsg(text)]);
      await this.processBatchEdit(text);
      return;
    }

    // ── Add path (existing) ──

    if (step === "collect_single_name") {
      const name = text.trim();
      if (!name) {
        this.emit([
          userMsg(text),
          assistantMsg(i18n.t("aiAssistant.students.emptyName")),
        ]);
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
          this.emit([
            assistantMsg(
              first.error || i18n.t("aiAssistant.students.inappropriateName"),
            ),
          ]);
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
              first?.error ||
                i18n.t("aiAssistant.students.birthdayUnrecognized"),
            ),
          ]);
          this.set({ inputDisabled: false });
        }
      } catch {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.students.birthdayUnrecognized")),
        ]);
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

  // ═══════════════════════════════════════════════
  // Public: handle button click
  // ═══════════════════════════════════════════════

  async handleButtonSelect(_messageId: string, value: string) {
    if (value === "_disabled") return;
    if (value.startsWith("navigate:")) return; // Handled by parent component

    // ── Entry ──

    if (value === "action:add") {
      this.emit([userMsg(i18n.t("aiAssistant.students.actionAdd"))]);
      this.showModeChoice();
      return;
    }

    if (value === "action:edit") {
      this.emit([userMsg(i18n.t("aiAssistant.students.actionEdit"))]);
      await this.loadAndShowClassroomsForEdit();
      return;
    }

    // ── Add path ──

    if (value === "confirm_switch_batch") {
      this.emit([userMsg(i18n.t("aiAssistant.common.switchToBatch"))]);
      this.state.mode = "batch";
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
      this.emit([userMsg(i18n.t("aiAssistant.common.continueSingle"))]);
      if (this.state.step === "collect_single_birthday") {
        this.emit([
          assistantMsg(i18n.t("aiAssistant.students.continueBirthday")),
        ]);
      } else {
        this.emit([assistantMsg(i18n.t("aiAssistant.students.continueName"))]);
      }
      this.set({ inputDisabled: false });
      return;
    }

    if (value === "unknown_birthday") {
      this.emit([
        userMsg(i18n.t("aiAssistant.students.unknownBirthday")),
        assistantMsg(i18n.t("aiAssistant.students.unknownBirthdayExplain")),
      ]);
      this.confirmSingleStudent("2012-01-01");
      return;
    }

    if (value === "mode:single") {
      this.emit([userMsg(i18n.t("aiAssistant.common.addSingle"))]);
      this.state.mode = "single";
      await this.selectClassroom();
      return;
    }

    if (value === "mode:batch") {
      this.emit([userMsg(i18n.t("aiAssistant.common.addBatch"))]);
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
      this.emit([userMsg(i18n.t("aiAssistant.common.confirm"))]);
      await this.executeCreate();
      return;
    }

    if (value.startsWith("remove:")) {
      const idx = parseInt(value.replace("remove:", ""), 10);
      if (idx >= 0 && idx < this.state.students.length) {
        this.emit([
          userMsg(
            i18n.t("aiAssistant.common.remove", {
              name: this.state.students[idx].name,
            }),
          ),
        ]);
        this.removeStudent(idx);
      }
      return;
    }

    if (value === "edit_table") {
      this.emit([
        userMsg(i18n.t("aiAssistant.common.modify")),
        assistantMsg(i18n.t("aiAssistant.students.modifyInstructions")),
      ]);
      this.set({ inputDisabled: false });
      return;
    }

    if (value === "restart_same_classroom") {
      this.emit([userMsg(i18n.t("aiAssistant.common.continueAdd"))]);
      this.state.students = [];
      if (this.state.mode === "single") {
        this.collectSingleName();
      } else {
        this.collectBatch();
      }
      return;
    }

    if (value === "restart_flow") {
      this.emit([userMsg(i18n.t("aiAssistant.common.selectOtherClassroom"))]);
      this.state.students = [];
      this.state.selectedClassroom = null;
      await this.selectClassroom();
      return;
    }

    if (value === "close_panel") {
      this.emit([
        userMsg(i18n.t("aiAssistant.common.end")),
        assistantMsg(i18n.t("aiAssistant.students.thankYou")),
      ]);
      return;
    }

    // ── Optional fields (add single) ──

    if (value.startsWith("optional_field:")) {
      const field = value.replace("optional_field:", "") as
        | "email"
        | "student_number"
        | "phone";
      const fieldLabel =
        field === "email"
          ? "Email"
          : field === "student_number"
            ? i18n.t("aiAssistant.students.fieldStudentNumber")
            : i18n.t("aiAssistant.students.fieldPhone");
      this.emit([userMsg(fieldLabel)]);
      this.collectOptionalValue(field);
      return;
    }

    if (value === "skip_optional") {
      this.emit([userMsg(i18n.t("aiAssistant.students.skipOptional"))]);
      this.showConfirmTable();
      return;
    }

    // ── Edit path ──

    if (value.startsWith("select_edit_classroom:")) {
      const id = parseInt(value.replace("select_edit_classroom:", ""), 10);
      const classroom = this.state.classrooms.find((c) => c.id === id);
      if (classroom) {
        this.emit([userMsg(`${classroom.name} (${classroom.level})`)]);
        this.state.selectedClassroom = classroom;
        await this.loadStudentsAndShowBatchEdit(id);
      }
      return;
    }

    if (value === "confirm_batch_edit") {
      this.emit([userMsg(i18n.t("aiAssistant.students.batchEditConfirm"))]);
      await this.executeBatchEdit();
      return;
    }

    if (value === "continue_batch_edit") {
      this.emit([userMsg(i18n.t("aiAssistant.students.batchEditContinue"))]);
      this.showBatchEditCollect();
      return;
    }

    if (value === "cancel_batch_edit") {
      this.emit([userMsg(i18n.t("aiAssistant.students.batchEditCancel"))]);
      this.showBatchEditCollect();
      return;
    }

    if (value === "continue_batch_edit_same") {
      this.emit([
        userMsg(i18n.t("aiAssistant.students.batchEditContinueSame")),
      ]);
      this.showBatchEditCollect();
      return;
    }

    if (value === "edit_other_classroom_student") {
      this.emit([
        userMsg(i18n.t("aiAssistant.students.editOtherClassroomStudent")),
      ]);
      await this.loadAndShowClassroomsForEdit();
      return;
    }

    if (value === "switch_to_add") {
      this.emit([userMsg(i18n.t("aiAssistant.students.switchToAdd"))]);
      this.state.students = [];
      this.showModeChoice();
      return;
    }

    if (value === "switch_to_edit") {
      this.emit([userMsg(i18n.t("aiAssistant.students.switchToEdit"))]);
      await this.loadAndShowClassroomsForEdit();
      return;
    }
  }

  // ═══════════════════════════════════════════════
  // AI-powered batch parsing
  // ═══════════════════════════════════════════════

  private async parseBatchWithAI(text: string) {
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.parsing"), { loading: true }),
    ]);
    this.set({ inputDisabled: true });

    try {
      const result = await callParseStudents(text);
      if (result.students.length === 0) {
        this.emit([
          assistantMsg(
            result.message || i18n.t("aiAssistant.students.noDataDetected"),
          ),
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
          assistantMsg(
            i18n.t("aiAssistant.students.dedupeNotice", {
              names: dupes.join("、"),
            }),
          ),
        ]);
      }

      this.state.students = deduped;
      this.showConfirmTable();
    } catch {
      this.emit([
        assistantMsg(i18n.t("aiAssistant.students.parseFailedRetry")),
      ]);
      this.set({ inputDisabled: false });
    }
  }

  // ═══════════════════════════════════════════════
  // Modification handling (AI-powered, for add confirm step)
  // ═══════════════════════════════════════════════

  private async handleModification(text: string) {
    const students = this.state.students;
    const trimmed = text.trim();

    // ── Bare commands without target — handle locally ──
    if (/^(?:我要|我想|請)?(?:移除|刪除|去掉)$/.test(trimmed)) {
      const buttons: QuickButton[] = students.map((s, i) => ({
        label: i18n.t("aiAssistant.common.remove", { name: s.name }),
        value: `remove:${i}`,
      }));
      this.emit([
        assistantMsg(i18n.t("aiAssistant.students.selectRemove"), { buttons }),
      ]);
      return;
    }

    if (/^(?:我要|我想|請)?修改$/.test(trimmed)) {
      this.emit([
        assistantMsg(i18n.t("aiAssistant.students.modifyInstructions")),
      ]);
      return;
    }

    // ── All other modifications → delegate to AI ──
    this.emit([
      assistantMsg(i18n.t("aiAssistant.students.modifying"), { loading: true }),
    ]);
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
        this.emit([assistantMsg(i18n.t("aiAssistant.students.allRemoved"))]);
        this.set({ step: "collect_batch", inputDisabled: false });
        return;
      }

      this.showConfirmTable();
    } catch {
      this.emit([assistantMsg(i18n.t("aiAssistant.students.modifyFailed"))]);
      this.set({ inputDisabled: false });
    }
  }

  private removeStudent(idx: number) {
    const students = this.state.students;
    const removed = students.splice(idx, 1)[0];
    if (students.length === 0) {
      this.emit([assistantMsg(i18n.t("aiAssistant.students.allRemoved"))]);
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
      await this.loadAndShowClassroomsForEdit();
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
