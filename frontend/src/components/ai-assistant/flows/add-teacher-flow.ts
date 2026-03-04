/**
 * Add Teacher Flow — state machine logic
 *
 * Steps:
 * 1. confirm_org   — detect / select organization
 * 2. check_quota   — check teacher limit
 * 3. collect_data  — prompt user to input teacher info
 * 4. parse_input   — call Gemini to parse free text
 * 5. confirm_table — show table, allow modifications
 * 6. execute       — invite each teacher + ask school assignment
 * 7. complete      — summary
 */

import { apiClient } from "@/lib/api";
import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import i18n from "@/i18n/config";
import type { ChatMessage, QuickButton, TableColumn } from "../chat/types";

// ─── Types ───

export type FlowStep =
  | "confirm_org"
  | "check_quota"
  | "collect_data"
  | "parse_input"
  | "confirm_table"
  | "execute"
  | "complete";

export interface ParsedTeacher {
  name: string;
  email: string;
  role: string;
  valid: boolean;
  error: string | null;
}

interface OrgInfo {
  id: string;
  name: string;
  display_name?: string;
  teacher_limit: number | null;
}

interface SchoolInfo {
  id: string;
  name: string;
}

interface ExecutionResult {
  teacher: ParsedTeacher;
  success: boolean;
  error?: string;
  teacher_id?: number;
  school?: string;
}

export interface FlowState {
  step: FlowStep;
  orgs: OrgInfo[];
  selectedOrg: OrgInfo | null;
  schools: SchoolInfo[];
  currentTeacherCount: number;
  teachers: ParsedTeacher[];
  executionResults: ExecutionResult[];
  /** Index of teacher currently being executed (for sequential invite+school) */
  executingIndex: number;
  /** Whether we're waiting for school assignment for current teacher */
  awaitingSchoolAssignment: boolean;
  inputDisabled: boolean;
}

// ─── Helpers ───

let _msgId = 0;
function msgId() {
  return `msg-${++_msgId}`;
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

function orgDisplayName(org: OrgInfo) {
  return org.display_name || org.name;
}

// ─── Navigation helpers ───

/** Map of page keywords to path templates. orgId/schoolId are filled at runtime. */
function getPageNavMap(): Record<
  string,
  { label: string; pathTemplate: string }
> {
  return {
    [i18n.t("aiAssistant.teacher.nav.teacherList.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.teacherList.button"),
      pathTemplate: "/organization/{orgId}/teachers",
    },
    [i18n.t("aiAssistant.teacher.nav.schoolList.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.schoolList.button"),
      pathTemplate: "/organization/{orgId}/schools",
    },
    [i18n.t("aiAssistant.teacher.nav.materials.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.materials.button"),
      pathTemplate: "/organization/{orgId}/materials",
    },
    [i18n.t("aiAssistant.teacher.nav.myClassrooms.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.myClassrooms.button"),
      pathTemplate: "/teacher/classrooms",
    },
    [i18n.t("aiAssistant.teacher.nav.allStudents.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.allStudents.button"),
      pathTemplate: "/teacher/students",
    },
    [i18n.t("aiAssistant.teacher.nav.myMaterials.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.myMaterials.button"),
      pathTemplate: "/teacher/programs",
    },
    [i18n.t("aiAssistant.teacher.nav.profile.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.profile.button"),
      pathTemplate: "/teacher/profile",
    },
    [i18n.t("aiAssistant.teacher.nav.subscription.label")]: {
      label: i18n.t("aiAssistant.teacher.nav.subscription.button"),
      pathTemplate: "/teacher/subscription",
    },
  };
}

function buildNavButtons(message: string, orgId?: string): QuickButton[] {
  const buttons: QuickButton[] = [];
  const pageNavMap = getPageNavMap();
  for (const [keyword, nav] of Object.entries(pageNavMap)) {
    if (message.includes(keyword)) {
      const path = orgId
        ? nav.pathTemplate.replace("{orgId}", orgId)
        : nav.pathTemplate;
      buttons.push({ label: nav.label, value: `navigate:${path}` });
    }
  }
  return buttons;
}

// ─── Table helpers ───

function getTeacherTableColumns(): TableColumn[] {
  return [
    { key: "index", label: "#" },
    { key: "name", label: i18n.t("aiAssistant.teacher.table.name") },
    { key: "email", label: i18n.t("aiAssistant.teacher.table.email") },
    { key: "role", label: i18n.t("aiAssistant.teacher.table.role") },
    { key: "status", label: i18n.t("aiAssistant.teacher.table.status") },
  ];
}

function roleLabel(role: string) {
  return role === "org_admin"
    ? i18n.t("aiAssistant.teacher.roles.orgAdmin")
    : i18n.t("aiAssistant.teacher.roles.teacher");
}

function teacherTableRows(teachers: ParsedTeacher[]) {
  return teachers.map((t, i) => ({
    index: String(i + 1),
    name: t.name,
    email: t.email,
    role: roleLabel(t.role),
    status: t.valid ? "✓" : `⚠️ ${t.error}`,
  }));
}

// ─── API calls ───

async function fetchOrganizations(): Promise<OrgInfo[]> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/organizations`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(i18n.t("aiAssistant.teacher.fetchOrgsFailed"));
  const data = await res.json();
  return data.map((o: Record<string, unknown>) => ({
    id: String(o.id),
    name: o.name as string,
    display_name: o.display_name as string | undefined,
    teacher_limit: o.teacher_limit as number | null,
  }));
}

async function fetchOrgTeacherCount(orgId: string): Promise<number> {
  const teachers = await apiClient.getOrganizationTeachers(orgId);
  return teachers.filter((t) => t.is_active).length;
}

async function fetchSchools(orgId: string): Promise<SchoolInfo[]> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/schools?organization_id=${orgId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.map((s: Record<string, unknown>) => ({
    id: String(s.id),
    name: (s.display_name || s.name) as string,
  }));
}

async function callParseTeachers(
  userInput: string,
): Promise<{ teachers: ParsedTeacher[]; message: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/ai/assistant/parse-teachers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ user_input: userInput }),
  });
  if (!res.ok) throw new Error(i18n.t("aiAssistant.teacher.parseFailed"));
  return res.json();
}

async function callProcessModification(
  userInput: string,
  currentTeachers: ParsedTeacher[],
): Promise<{ teachers: ParsedTeacher[]; message: string; action: string }> {
  const token = useTeacherAuthStore.getState().token;
  const res = await fetch(`${API_URL}/api/ai/assistant/process-modification`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      user_input: userInput,
      current_teachers: currentTeachers,
    }),
  });
  if (!res.ok)
    throw new Error(i18n.t("aiAssistant.teacher.modifyProcessFailed"));
  return res.json();
}

// ─── Flow class ───

export class AddTeacherFlow {
  state: FlowState;
  messages: ChatMessage[];

  private pushMsg: (msgs: ChatMessage[]) => void;
  private updateState: (partial: Partial<FlowState>) => void;

  constructor(
    pushMsg: (msgs: ChatMessage[]) => void,
    updateState: (partial: Partial<FlowState>) => void,
    /** Pre-detected orgId from URL (e.g., from /organization/:orgId/...) */
    detectedOrgId?: string,
  ) {
    this.pushMsg = pushMsg;
    this.updateState = updateState;
    this.messages = [];
    this.state = {
      step: "confirm_org",
      orgs: [],
      selectedOrg: null,
      schools: [],
      currentTeacherCount: 0,
      teachers: [],
      executionResults: [],
      executingIndex: 0,
      awaitingSchoolAssignment: false,
      inputDisabled: true,
    };

    // Start flow
    this.initConfirmOrg(detectedOrgId);
  }

  // ─── Step: confirm_org ───

  private async initConfirmOrg(detectedOrgId?: string) {
    try {
      const orgs = await fetchOrganizations();
      this.state.orgs = orgs;

      if (orgs.length === 0) {
        this.emit([assistantMsg(i18n.t("aiAssistant.teacher.noOrgs"))]);
        return;
      }

      if (orgs.length === 1) {
        // Auto-select the only org
        this.selectOrg(orgs[0]);
        return;
      }

      // If we detected an org from URL, auto-select it
      if (detectedOrgId) {
        const found = orgs.find((o) => o.id === detectedOrgId);
        if (found) {
          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.teacher.confirmOrg", {
                orgName: orgDisplayName(found),
              }),
              {
                buttons: [
                  {
                    label: i18n.t("aiAssistant.common.yes"),
                    value: `select_org:${found.id}`,
                  },
                  {
                    label: i18n.t("aiAssistant.common.selectOtherOrg"),
                    value: "pick_org",
                  },
                ],
              },
            ),
          ]);
          this.set({ step: "confirm_org" });
          return;
        }
      }

      // Multiple orgs, no detection — list for user to pick
      const buttons: QuickButton[] = orgs.map((o) => ({
        label: orgDisplayName(o),
        value: `select_org:${o.id}`,
      }));
      this.emit([
        assistantMsg(i18n.t("aiAssistant.teacher.selectOrg"), { buttons }),
      ]);
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.teacher.fetchOrgDataFailed", {
            error: (e as Error).message,
          }),
        ),
      ]);
    }
  }

  private async selectOrg(org: OrgInfo) {
    this.state.selectedOrg = org;
    this.emit([
      assistantMsg(
        i18n.t("aiAssistant.teacher.orgSelected", {
          orgName: orgDisplayName(org),
        }),
        { loading: true },
      ),
    ]);
    this.set({ step: "check_quota", selectedOrg: org });
    await this.checkQuota();
  }

  // ─── Step: check_quota ───

  private async checkQuota() {
    const org = this.state.selectedOrg!;
    try {
      // Re-fetch org data to get latest teacher_limit
      const freshOrgs = await fetchOrganizations();
      const freshOrg = freshOrgs.find((o) => o.id === org.id);
      if (freshOrg) {
        Object.assign(org, freshOrg);
        this.state.selectedOrg = org;
      }

      const count = await fetchOrgTeacherCount(org.id);
      this.state.currentTeacherCount = count;
      const schools = await fetchSchools(org.id);
      this.state.schools = schools;

      if (org.teacher_limit !== null && count >= org.teacher_limit) {
        this.emit([
          assistantMsg(
            i18n.t("aiAssistant.teacher.quotaFull", {
              orgName: orgDisplayName(org),
              count,
              limit: org.teacher_limit,
            }),
          ),
        ]);
        return;
      }

      const quotaInfo =
        org.teacher_limit !== null
          ? i18n.t("aiAssistant.teacher.quotaInfo", {
              count,
              limit: org.teacher_limit,
              remaining: org.teacher_limit - count,
            })
          : "";

      this.emit([
        assistantMsg(
          quotaInfo + i18n.t("aiAssistant.teacher.collectInstructions"),
        ),
      ]);
      this.set({ step: "collect_data", inputDisabled: false });
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.teacher.fetchQuotaFailed", {
            error: (e as Error).message,
          }),
        ),
      ]);
    }
  }

  // ─── Step: parse_input ───

  private async parseInput(text: string) {
    this.set({ step: "parse_input", inputDisabled: true });
    this.emit([
      userMsg(text),
      assistantMsg(i18n.t("aiAssistant.teacher.parsing"), { loading: true }),
    ]);

    try {
      const result = await callParseTeachers(text);
      if (result.teachers.length === 0) {
        // AI understood but found no teacher data — show message with nav buttons if applicable
        const navButtons = buildNavButtons(
          result.message,
          this.state.selectedOrg?.id,
        );
        this.emit([
          assistantMsg(
            result.message,
            navButtons.length > 0 ? { buttons: navButtons } : undefined,
          ),
        ]);
        this.set({ step: "collect_data", inputDisabled: false });
      } else {
        this.state.teachers = result.teachers;
        this.showConfirmTable(result.message);
      }
    } catch (e) {
      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.teacher.parseFailedRetry", {
            error: (e as Error).message,
          }),
        ),
      ]);
      this.set({ step: "collect_data", inputDisabled: false });
    }
  }

  // ─── Step: confirm_table ───

  private showConfirmTable(aiMessage?: string) {
    const org = this.state.selectedOrg!;
    const teachers = this.state.teachers;
    const allValid = teachers.every((t) => t.valid);

    // Check quota
    const validCount = teachers.filter((t) => t.valid).length;
    let quotaWarning = "";
    if (org.teacher_limit !== null) {
      const remaining = org.teacher_limit - this.state.currentTeacherCount;
      if (validCount > remaining) {
        quotaWarning = i18n.t("aiAssistant.teacher.quotaWarning", {
          count: this.state.currentTeacherCount,
          limit: org.teacher_limit,
          remaining,
          validCount,
        });
      }
    }

    const canConfirm = allValid && !quotaWarning;

    const header = i18n.t("aiAssistant.teacher.confirmHeader", {
      orgName: orgDisplayName(org),
    });
    const footer = aiMessage ? `\n${aiMessage}` : "";

    // Role toggle buttons — for each valid teacher, offer to switch role
    const roleButtons: QuickButton[] = [];
    const validTeachers = teachers.filter((t) => t.valid);
    for (let i = 0; i < validTeachers.length; i++) {
      const t = validTeachers[i];
      const idx = teachers.indexOf(t);
      if (t.role === "teacher") {
        const label =
          validTeachers.length === 1
            ? i18n.t("aiAssistant.teacher.changeToAdmin")
            : i18n.t("aiAssistant.teacher.changeToAdminNamed", {
                name: t.name,
              });
        roleButtons.push({ label, value: `toggle_role:${idx}:org_admin` });
      } else {
        const label =
          validTeachers.length === 1
            ? i18n.t("aiAssistant.teacher.changeToTeacher")
            : i18n.t("aiAssistant.teacher.changeToTeacherNamed", {
                name: t.name,
              });
        roleButtons.push({ label, value: `toggle_role:${idx}:teacher` });
      }
    }

    const buttons: QuickButton[] = [];

    if (canConfirm) {
      buttons.push({
        label: i18n.t("aiAssistant.common.confirm"),
        value: "confirm_execute",
        variant: "default",
      });
    } else if (!quotaWarning) {
      buttons.push({
        label: i18n.t("aiAssistant.common.fixErrors"),
        value: "_disabled",
        variant: "secondary",
      });
    }

    buttons.push(...roleButtons);
    buttons.push({
      label: i18n.t("aiAssistant.common.modify"),
      value: "edit_table",
    });

    this.emit([
      assistantMsg(`${header}${footer}${quotaWarning}`, {
        table: {
          columns: getTeacherTableColumns(),
          rows: teacherTableRows(teachers),
        },
        buttons,
      }),
    ]);
    this.set({
      step: "confirm_table",
      teachers,
      inputDisabled: false,
    });
  }

  // ─── Step: execute ───

  private async executeInvites() {
    this.set({ step: "execute", inputDisabled: true, executingIndex: 0 });
    const teachers = this.state.teachers.filter((t) => t.valid);
    const org = this.state.selectedOrg!;
    const results: ExecutionResult[] = [];

    for (let i = 0; i < teachers.length; i++) {
      const t = teachers[i];
      this.state.executingIndex = i;

      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.teacher.inviting", {
            current: i + 1,
            total: teachers.length,
          }),
          { loading: true },
        ),
      ]);

      try {
        const resp = await apiClient.inviteTeacherToOrganization(org.id, {
          email: t.email,
          name: t.name,
          role: t.role,
        });

        const teacherId = (resp as { teacher_id?: number }).teacher_id ?? 0;

        // Ask about school assignment
        if (this.state.schools.length > 0) {
          const schoolButtons: QuickButton[] = this.state.schools.map((s) => ({
            label: s.name,
            value: `assign_school:${i}:${s.id}`,
          }));
          schoolButtons.push({
            label: i18n.t("aiAssistant.common.skip"),
            value: `assign_school:${i}:skip`,
          });

          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.teacher.inviteSuccessWithSchool", {
                name: t.name,
                email: t.email,
                role: roleLabel(t.role),
              }),
              { buttons: schoolButtons },
            ),
          ]);

          // Wait for school assignment response
          results.push({
            teacher: t,
            success: true,
            teacher_id: teacherId,
          });
          this.state.executionResults = results;
          this.state.awaitingSchoolAssignment = true;
          this.set({ awaitingSchoolAssignment: true });
          return; // Will continue from handleSchoolAssignment
        } else {
          results.push({ teacher: t, success: true, teacher_id: teacherId });
          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.teacher.inviteSuccess", {
                name: t.name,
                email: t.email,
                role: roleLabel(t.role),
              }),
            ),
          ]);
        }
      } catch (e) {
        const errMsg = (e as Error).message;
        results.push({
          teacher: t,
          success: false,
          error: errMsg,
        });
        this.emit([
          assistantMsg(
            i18n.t("aiAssistant.teacher.inviteFailed", {
              name: t.name,
              email: t.email,
              error: errMsg,
            }),
          ),
        ]);
      }
    }

    this.state.executionResults = results;
    this.showSummary();
  }

  /** Continue execution after a school assignment response */
  private async continueExecution(fromIndex: number) {
    this.state.awaitingSchoolAssignment = false;
    const teachers = this.state.teachers.filter((t) => t.valid);
    const org = this.state.selectedOrg!;
    const results = this.state.executionResults;

    for (let i = fromIndex + 1; i < teachers.length; i++) {
      const t = teachers[i];
      this.state.executingIndex = i;

      this.emit([
        assistantMsg(
          i18n.t("aiAssistant.teacher.inviting", {
            current: i + 1,
            total: teachers.length,
          }),
          { loading: true },
        ),
      ]);

      try {
        const resp = await apiClient.inviteTeacherToOrganization(org.id, {
          email: t.email,
          name: t.name,
          role: t.role,
        });

        const teacherId = (resp as { teacher_id?: number }).teacher_id ?? 0;

        if (this.state.schools.length > 0) {
          const schoolButtons: QuickButton[] = this.state.schools.map((s) => ({
            label: s.name,
            value: `assign_school:${i}:${s.id}`,
          }));
          schoolButtons.push({
            label: i18n.t("aiAssistant.common.skip"),
            value: `assign_school:${i}:skip`,
          });

          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.teacher.inviteSuccessWithSchool", {
                name: t.name,
                email: t.email,
                role: roleLabel(t.role),
              }),
              { buttons: schoolButtons },
            ),
          ]);

          results.push({
            teacher: t,
            success: true,
            teacher_id: teacherId,
          });
          this.state.executionResults = results;
          this.state.awaitingSchoolAssignment = true;
          this.set({ awaitingSchoolAssignment: true });
          return;
        } else {
          results.push({
            teacher: t,
            success: true,
            teacher_id: teacherId,
          });
          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.teacher.inviteSuccess", {
                name: t.name,
                email: t.email,
                role: roleLabel(t.role),
              }),
            ),
          ]);
        }
      } catch (e) {
        const errMsg = (e as Error).message;
        results.push({
          teacher: t,
          success: false,
          error: errMsg,
        });
        this.emit([
          assistantMsg(
            i18n.t("aiAssistant.teacher.inviteFailed", {
              name: t.name,
              email: t.email,
              error: errMsg,
            }),
          ),
        ]);
      }
    }

    this.state.executionResults = results;
    this.showSummary();
  }

  // ─── Step: complete ───

  private showSummary() {
    const results = this.state.executionResults;
    const successes = results.filter((r) => r.success);
    const failures = results.filter((r) => !r.success);

    let summary = i18n.t("aiAssistant.teacher.complete") + "\n\n";

    if (successes.length > 0) {
      summary +=
        i18n.t("aiAssistant.teacher.successCount", {
          count: successes.length,
        }) + "\n";
      for (const r of successes) {
        const schoolInfo = r.school ? ` → ${r.school}` : "";
        summary += `  - ${r.teacher.name} (${r.teacher.email}) → ${roleLabel(r.teacher.role)}${schoolInfo}\n`;
      }
    }

    if (failures.length > 0) {
      summary +=
        "\n" +
        i18n.t("aiAssistant.teacher.failureCount", {
          count: failures.length,
        }) +
        "\n";
      for (const r of failures) {
        summary += `  - ${r.teacher.name} (${r.teacher.email}) → ${r.error}\n`;
      }
    }

    summary += "\n" + i18n.t("aiAssistant.teacher.emailNotice");

    this.emit([
      assistantMsg(summary, {
        buttons: [
          {
            label: i18n.t("aiAssistant.common.continueAdd"),
            value: "restart_flow",
            variant: "default",
          },
          { label: i18n.t("aiAssistant.common.end"), value: "close_panel" },
        ],
      }),
    ]);
    this.set({ step: "complete", inputDisabled: true });
  }

  // ─── Public: handle user input ───

  async handleUserInput(text: string) {
    const { step } = this.state;

    if (step === "collect_data") {
      await this.parseInput(text);
      return;
    }

    if (step === "confirm_table") {
      // Quick fix: if there's exactly one teacher missing a name, and user
      // provides something that looks like a name (no @), fill it in directly
      const missingName = this.state.teachers.filter(
        (t) => !t.name && t.error === i18n.t("aiAssistant.teacher.missingName"),
      );
      if (
        missingName.length === 1 &&
        !text.includes("@") &&
        text.trim().length < 30
      ) {
        this.emit([userMsg(text)]);
        missingName[0].name = text.trim();
        missingName[0].valid = true;
        missingName[0].error = null;
        this.showConfirmTable(
          i18n.t("aiAssistant.teacher.nameFilled", { name: text.trim() }),
        );
        return;
      }

      // User is providing modification instructions
      this.emit([
        userMsg(text),
        assistantMsg(i18n.t("aiAssistant.teacher.modifying"), {
          loading: true,
        }),
      ]);
      this.set({ inputDisabled: true });

      try {
        const result = await callProcessModification(text, this.state.teachers);
        if (result.action === "unclear") {
          this.emit([assistantMsg(result.message)]);
          this.set({ inputDisabled: false });
        } else {
          this.state.teachers = result.teachers;
          this.showConfirmTable(result.message);
        }
      } catch {
        // Modification failed — fallback: re-parse input as fresh teacher data
        try {
          const parsed = await callParseTeachers(text);
          this.state.teachers = parsed.teachers;
          this.showConfirmTable(parsed.message);
        } catch (e2) {
          this.emit([
            assistantMsg(
              i18n.t("aiAssistant.teacher.modifyFailed", {
                error: (e2 as Error).message,
              }),
            ),
          ]);
          this.set({ inputDisabled: false });
        }
      }
      return;
    }
  }

  // ─── Public: handle button click ───

  async handleButtonSelect(_messageId: string, value: string) {
    // Navigate buttons are handled by AddTeacherChat (React Router)
    // so they won't reach here, but guard just in case
    if (value.startsWith("navigate:")) return;

    // Restart flow — continue adding more teachers
    if (value === "restart_flow") {
      this.emit([userMsg(i18n.t("aiAssistant.common.continueAdd"))]);
      // Reset state for a new round, keep the same org
      this.state.teachers = [];
      this.state.executionResults = [];
      this.state.executingIndex = 0;
      this.state.awaitingSchoolAssignment = false;
      // Re-check quota then go to collect_data
      this.emit([
        assistantMsg(i18n.t("aiAssistant.teacher.quotaChecking"), {
          loading: true,
        }),
      ]);
      await this.checkQuota();
      return;
    }

    // Close panel
    if (value === "close_panel") {
      this.emit([userMsg(i18n.t("aiAssistant.common.end"))]);
      this.emit([assistantMsg(i18n.t("aiAssistant.teacher.thankYou"))]);
      return;
    }

    // Org selection
    if (value.startsWith("select_org:")) {
      const orgId = value.replace("select_org:", "");
      const org = this.state.orgs.find((o) => o.id === orgId);
      if (org) {
        this.emit([userMsg(orgDisplayName(org))]);
        await this.selectOrg(org);
      }
      return;
    }

    if (value === "pick_org") {
      const buttons: QuickButton[] = this.state.orgs.map((o) => ({
        label: orgDisplayName(o),
        value: `select_org:${o.id}`,
      }));
      this.emit([
        userMsg(i18n.t("aiAssistant.common.selectOtherOrg")),
        assistantMsg(i18n.t("aiAssistant.teacher.selectOrgs"), { buttons }),
      ]);
      return;
    }

    // Confirm execute
    if (value === "confirm_execute") {
      this.emit([userMsg(i18n.t("aiAssistant.common.confirm"))]);
      await this.executeInvites();
      return;
    }

    // Role toggle
    if (value.startsWith("toggle_role:")) {
      const parts = value.split(":");
      const idx = parseInt(parts[1], 10);
      const newRole = parts[2];
      const t = this.state.teachers[idx];
      if (t) {
        t.role = newRole;
        this.emit([
          userMsg(
            i18n.t("aiAssistant.teacher.roleChangeEcho", {
              name: t.name,
              role: roleLabel(newRole),
            }),
          ),
        ]);
        this.showConfirmTable(
          i18n.t("aiAssistant.teacher.roleChanged", {
            name: t.name,
            role: roleLabel(newRole),
          }),
        );
      }
      return;
    }

    // Edit table — just enable input
    if (value === "edit_table") {
      this.emit([
        userMsg(i18n.t("aiAssistant.common.modify")),
        assistantMsg(i18n.t("aiAssistant.teacher.modifyInstructions")),
      ]);
      this.set({ inputDisabled: false });
      return;
    }

    // School assignment
    if (value.startsWith("assign_school:")) {
      const parts = value.split(":");
      const teacherIndex = parseInt(parts[1], 10);
      const schoolId = parts[2];
      const results = this.state.executionResults;
      const resultEntry = results[results.length - 1]; // Most recent

      if (schoolId === "skip") {
        this.emit([userMsg(i18n.t("aiAssistant.common.skip"))]);
      } else {
        const school = this.state.schools.find((s) => s.id === schoolId);
        const schoolName = school?.name ?? schoolId;
        this.emit([userMsg(schoolName)]);

        // Call API to assign to school
        if (resultEntry?.teacher_id) {
          try {
            await apiClient.addTeacherToSchool(schoolId, {
              teacher_id: resultEntry.teacher_id,
              roles: [
                resultEntry.teacher.role === "org_admin"
                  ? "school_admin"
                  : "teacher",
              ],
            });
            resultEntry.school = schoolName;
            this.emit([
              assistantMsg(
                i18n.t("aiAssistant.teacher.assignedToSchool", {
                  school: schoolName,
                }),
              ),
            ]);
          } catch (e) {
            this.emit([
              assistantMsg(
                i18n.t("aiAssistant.teacher.assignFailed", {
                  school: schoolName,
                  error: (e as Error).message,
                }),
              ),
            ]);
          }
        }
      }

      // Continue with next teacher
      await this.continueExecution(teacherIndex);
      return;
    }
  }

  // ─── Internal helpers ───

  private emit(msgs: ChatMessage[]) {
    // Filter out previous loading messages
    this.messages = this.messages.filter((m) => !m.loading);
    this.messages.push(...msgs);
    this.pushMsg([...this.messages]);
  }

  private set(partial: Partial<FlowState>) {
    Object.assign(this.state, partial);
    this.updateState(partial);
  }
}
