import { useState, useCallback, useRef, useContext, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import { ChatMessages } from "../chat/ChatMessages";
import { ChatInput } from "../chat/ChatInput";
import { useAiAssistant } from "../useAiAssistant";
import { useHubCooldown } from "../useHubCooldown";
import { WorkspaceContext } from "@/contexts/WorkspaceContext";
import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import {
  ManageClassroomFlow,
  type FlowState as ClassroomFlowState,
  type ParsedClassroom,
} from "./add-classroom-flow";
import {
  ManageStudentsFlow,
  type FlowState as StudentFlowState,
} from "./add-students-flow";
import type { ChatMessage, QuickButton } from "../chat/types";

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

let _msgId = 0;
function msgId() {
  return `hub-msg-${++_msgId}`;
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

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type EmbeddedFlowType = "classroom" | "students";
type AnyFlow = ManageClassroomFlow | ManageStudentsFlow;

interface ChatResponseData {
  action: string;
  message?: string;
  selected_action?: string;
  workflow_type?: string;
  sub_intent?: string;
  parsed_data?: Record<string, unknown>;
  navigation?: { label: string; path: string }[];
  respond_type?: string; // "greeting" | "off_topic" | "unclear"
}

/* ------------------------------------------------------------------ */
/*  getVisibleButtonLabels — extract label=value pairs from flow       */
/* ------------------------------------------------------------------ */

function getVisibleButtonLabels(flow: AnyFlow): string[] {
  for (let i = flow.messages.length - 1; i >= 0; i--) {
    const msg = flow.messages[i];
    if (msg.role === "assistant" && msg.buttons?.length) {
      return msg.buttons.map((b) => {
        const label = b.label.replace(/ →$/, "");
        return `${label}=${b.value}`;
      });
    }
  }
  return [];
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function HubChat() {
  const { t } = useTranslation();
  const location = useLocation();
  const workspace = useContext(WorkspaceContext);
  const { startFlow } = useAiAssistant();
  const { isCoolingDown, recordUnclear, resetCount } = useHubCooldown();

  const welcomeButtons: QuickButton[] = useMemo(
    () => [
      {
        label: t("aiAssistant.hub.manageClassrooms"),
        value: "inline:classroom",
      },
      {
        label: t("aiAssistant.hub.manageStudents"),
        value: "inline:students",
      },
      { label: t("aiAssistant.hub.findFeature"), value: "inline:find-feature" },
    ],
    [t],
  );

  const [messages, setMessages] = useState<ChatMessage[]>([
    assistantMsg(t("aiAssistant.hub.welcome"), { buttons: welcomeButtons }),
  ]);
  const [inputDisabled, setInputDisabled] = useState(false);
  const messagesRef = useRef<ChatMessage[]>([
    assistantMsg(t("aiAssistant.hub.welcome"), { buttons: welcomeButtons }),
  ]);
  const abortRef = useRef<AbortController | null>(null);

  // ── Embedded flow state ──
  const embeddedFlowRef = useRef<AnyFlow | null>(null);
  const flowTypeRef = useRef<EmbeddedFlowType | null>(null);
  const hubPrefixRef = useRef<ChatMessage[]>([]);

  /* ---------------------------------------------------------------- */
  /*  Hub-level emit (appends to messagesRef, filters loading)         */
  /* ---------------------------------------------------------------- */

  const emit = useCallback((msgs: ChatMessage[]) => {
    const current = messagesRef.current.filter((m) => !m.loading);
    current.push(...msgs);
    messagesRef.current = current;
    setMessages([...current]);
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Embedded flow lifecycle                                          */
  /* ---------------------------------------------------------------- */

  const startEmbeddedFlow = useCallback(
    (
      type: EmbeddedFlowType,
      initData?: {
        subIntent?: string;
        parsedData?: Record<string, unknown>;
      },
    ) => {
      // Save hub messages as prefix (clean loading first)
      hubPrefixRef.current = messagesRef.current.filter((m) => !m.loading);

      // pushMsg callback: merge hub prefix + flow messages
      const flowPushMsg = (flowMsgs: ChatMessage[]) => {
        const merged = [...hubPrefixRef.current, ...flowMsgs];
        messagesRef.current = merged;
        setMessages([...merged]);
      };

      // updateState callback (just for tracking)
      const flowUpdateState = () => {
        // We read state directly from flow.state when needed
      };

      if (type === "classroom") {
        const flow = new ManageClassroomFlow(
          flowPushMsg,
          flowUpdateState as (p: Partial<ClassroomFlowState>) => void,
          {
            classrooms: initData?.parsedData?.classrooms as
              | ParsedClassroom[]
              | undefined,
            subIntent: initData?.subIntent,
          },
        );
        embeddedFlowRef.current = flow;
      } else {
        const flow = new ManageStudentsFlow(
          flowPushMsg,
          flowUpdateState as (p: Partial<StudentFlowState>) => void,
          { subIntent: initData?.subIntent },
        );
        embeddedFlowRef.current = flow;
      }

      flowTypeRef.current = type;
    },
    [],
  );

  const clearEmbeddedFlow = useCallback(() => {
    embeddedFlowRef.current = null;
    flowTypeRef.current = null;
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Find-feature inline (no flow class needed)                       */
  /* ---------------------------------------------------------------- */

  const callFindFeature = useCallback(
    async (text: string) => {
      try {
        const token = useTeacherAuthStore.getState().token;
        const res = await fetch(`${API_URL}/api/ai/assistant/find-feature`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            user_input: text,
            context: "teacher",
            user_roles: useTeacherAuthStore.getState().userRoles ?? [],
            current_path: location.pathname,
            workspace_mode: workspace?.mode ?? "",
            workspace_org: "",
            workspace_school: "",
          }),
        });

        if (!res.ok) throw new Error("find-feature failed");
        const data = await res.json();

        const buttons: QuickButton[] = (data.navigation || [])
          .map((nav: { label: string; path: string }) => ({
            label: `${nav.label} →`,
            value: `navigate:${nav.path}`,
          }))
          .filter((b: QuickButton) => !b.value.includes("{"));

        // Deduplicate
        const seen = new Set<string>();
        const uniqueButtons = buttons.filter((b) => {
          if (seen.has(b.value)) return false;
          seen.add(b.value);
          return true;
        });

        emit([
          assistantMsg(
            data.message,
            uniqueButtons.length > 0 ? { buttons: uniqueButtons } : undefined,
          ),
        ]);
      } catch {
        emit([assistantMsg(t("aiAssistant.hub.error"))]);
      }
    },
    [emit, t, location.pathname, workspace?.mode],
  );

  /* ---------------------------------------------------------------- */
  /*  AI Chat — the core AI-first routing                              */
  /* ---------------------------------------------------------------- */

  const callAiChat = useCallback(
    async (text: string) => {
      const flow = embeddedFlowRef.current;

      // 1. Collect conversation history (last 20 non-loading messages)
      const conversationHistory = messagesRef.current
        .filter((m) => !m.loading)
        .slice(-20)
        .map((m) => ({ role: m.role, content: m.content }));

      // 2. Collect flow state if active (including current_data for parse steps)
      let flowState = null;
      if (flow) {
        const base = {
          type: flowTypeRef.current!,
          step: flow.state.step,
          available_actions: getVisibleButtonLabels(flow),
          current_data: undefined as Record<string, unknown> | undefined,
        };

        // Inject current_data for modification/parse steps
        const step = flow.state.step;
        const type = flowTypeRef.current!;

        if (step === "confirm" && type === "students") {
          const sf = flow.state as StudentFlowState;
          if (sf.students?.length) {
            base.current_data = {
              students: sf.students.map((s) => ({
                name: s.name,
                birthdate: s.birthdate,
              })),
            };
          }
        } else if (step === "confirm" && type === "classroom") {
          const cf = flow.state as ClassroomFlowState;
          if (cf.classrooms?.length) {
            base.current_data = {
              classrooms: cf.classrooms.map((c) => ({
                name: c.name,
                level: c.level,
              })),
            };
          }
        } else if (step === "batch_edit_collect" && type === "students") {
          const sf = flow.state as StudentFlowState;
          if (sf.existingStudents?.length) {
            base.current_data = {
              students: sf.existingStudents.map((s) => ({
                id: s.id,
                name: s.name,
                birthdate: s.birthdate,
                email: s.email,
                student_number: s.student_number,
                phone: s.phone,
              })),
            };
          }
        }

        flowState = base;
      }

      // 3. Call AI
      const token = useTeacherAuthStore.getState().token;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const res = await fetch(`${API_URL}/api/ai/assistant/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_input: text,
          conversation_history: conversationHistory,
          flow_state: flowState,
          context: "teacher",
          current_path: location.pathname,
          workspace_mode: workspace?.mode ?? "personal",
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error("chat failed");
      return (await res.json()) as ChatResponseData;
    },
    [location.pathname, workspace?.mode],
  );

  /* ---------------------------------------------------------------- */
  /*  Handle AI response — execute the action                          */
  /* ---------------------------------------------------------------- */

  const handleAiResponse = useCallback(
    (data: ChatResponseData, originalText: string) => {
      const flow = embeddedFlowRef.current;

      switch (data.action) {
        case "select_action": {
          // AI matched a button — simulate click
          if (flow && data.selected_action) {
            const lastMsgId = flow.messages[flow.messages.length - 1]?.id ?? "";
            flow.handleButtonSelect(lastMsgId, data.selected_action);
          }
          break;
        }

        case "provide_data": {
          // AI says user is providing data for current step
          if (flow) {
            // If AI returned parsed_data, inject it directly (unified AI brain)
            if (data.parsed_data && Object.keys(data.parsed_data).length > 0) {
              flow.injectParsedData(originalText, data.parsed_data);
            } else {
              // Fallback: let flow call its own parse endpoint
              flow.handleUserInput(originalText);
            }
          }
          break;
        }

        case "respond": {
          // AI reply — show inline (in flow or hub)
          const navButtons: QuickButton[] | undefined = data.navigation?.map(
            (nav) => ({
              label: `${nav.label} →`,
              value: `navigate:${nav.path}`,
            }),
          );
          if (flow) {
            flow.injectMessage(originalText, data.message ?? "", {
              buttons:
                navButtons && navButtons.length > 0 ? navButtons : undefined,
            });
          } else {
            emit([
              assistantMsg(data.message ?? "", {
                buttons:
                  navButtons && navButtons.length > 0 ? navButtons : undefined,
              }),
            ]);
          }
          break;
        }

        case "start_workflow": {
          // Start a new embedded flow
          resetCount();
          if (data.workflow_type === "classroom") {
            startEmbeddedFlow("classroom", {
              subIntent: data.sub_intent ?? undefined,
              parsedData: data.parsed_data ?? undefined,
            });
          } else if (data.workflow_type === "students") {
            startEmbeddedFlow("students", {
              subIntent: data.sub_intent ?? undefined,
              parsedData: data.parsed_data ?? undefined,
            });
          }
          break;
        }

        case "switch_workflow": {
          // Clear current flow and start a new one
          resetCount();
          clearEmbeddedFlow();
          if (data.workflow_type === "classroom") {
            startEmbeddedFlow("classroom", {
              subIntent: data.sub_intent ?? undefined,
              parsedData: data.parsed_data ?? undefined,
            });
          } else if (data.workflow_type === "students") {
            startEmbeddedFlow("students", {
              subIntent: data.sub_intent ?? undefined,
              parsedData: data.parsed_data ?? undefined,
            });
          }
          break;
        }

        case "find_feature": {
          // Clear flow if in one, then search
          if (flow) clearEmbeddedFlow();
          emit([
            assistantMsg(t("aiAssistant.hub.thinking"), { loading: true }),
          ]);
          callFindFeature(originalText);
          break;
        }

        default:
          emit([assistantMsg(data.message ?? t("aiAssistant.hub.error"))]);
      }
    },
    [
      emit,
      resetCount,
      clearEmbeddedFlow,
      startEmbeddedFlow,
      callFindFeature,
      t,
    ],
  );

  /* ---------------------------------------------------------------- */
  /*  handleSend — AI-first: ALL text goes through AI                  */
  /* ---------------------------------------------------------------- */

  const handleSend = useCallback(
    async (text: string) => {
      // Check cooldown
      if (isCoolingDown()) {
        emit([
          userMsg(text),
          assistantMsg(t("aiAssistant.hub.cooldownMessage")),
        ]);
        return;
      }

      const flow = embeddedFlowRef.current;

      // Show user message + loading
      if (flow) {
        flow.injectMessage(text, t("aiAssistant.hub.thinking"), {
          loading: true,
        });
      } else {
        emit([
          userMsg(text),
          assistantMsg(t("aiAssistant.hub.thinking"), { loading: true }),
        ]);
      }

      setInputDisabled(true);

      try {
        const data = await callAiChat(text);

        // Clean up loading messages before handling response
        if (flow) {
          flow.messages = flow.messages.filter((m) => !m.loading);
          if (flow.messages[flow.messages.length - 1]?.role === "user") {
            flow.messages.pop();
          }
        }
        const preCleaned = messagesRef.current.filter((m) => !m.loading);
        if (preCleaned.length !== messagesRef.current.length) {
          messagesRef.current = preCleaned;
          setMessages([...preCleaned]);
        }

        // Track unclear for cooldown (greetings don't count)
        if (
          data.action === "respond" &&
          (data.respond_type === "off_topic" || data.respond_type === "unclear")
        ) {
          const triggered = recordUnclear();
          if (triggered) {
            if (flow) {
              flow.injectMessage(text, t("aiAssistant.hub.cooldownTriggered"));
            } else {
              emit([assistantMsg(t("aiAssistant.hub.cooldownTriggered"))]);
            }
            setInputDisabled(false);
            return;
          }
        } else if (data.action !== "respond") {
          // Non-respond actions reset the counter
          resetCount();
        }

        handleAiResponse(data, text);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;

        // Clean up loading
        if (flow) {
          flow.messages = flow.messages.filter((m) => !m.loading);
          if (flow.messages[flow.messages.length - 1]?.role === "user") {
            flow.messages.pop();
          }
          flow.injectMessage(text, t("aiAssistant.hub.error"));
        } else {
          const cleaned = messagesRef.current.filter((m) => !m.loading);
          messagesRef.current = cleaned;
          setMessages([...cleaned]);
          emit([assistantMsg(t("aiAssistant.hub.error"))]);
        }
      }

      setInputDisabled(false);
    },
    [
      isCoolingDown,
      emit,
      t,
      callAiChat,
      handleAiResponse,
      recordUnclear,
      resetCount,
    ],
  );

  /* ---------------------------------------------------------------- */
  /*  handleButtonSelect — instant, no AI                              */
  /* ---------------------------------------------------------------- */

  const handleButtonSelect = useCallback(
    (_messageId: string, value: string) => {
      // ── Embedded flow buttons ──
      if (embeddedFlowRef.current) {
        // Special intercepts
        if (value === "close_panel") {
          clearEmbeddedFlow();
          emit([
            assistantMsg(t("aiAssistant.hub.welcome"), {
              buttons: welcomeButtons,
            }),
          ]);
          return;
        }
        if (value.startsWith("navigate:")) {
          const path = value.replace("navigate:", "");
          window.open(path, "_blank");
          return;
        }
        // All other button values → delegate to flow
        embeddedFlowRef.current.handleButtonSelect(_messageId, value);
        return;
      }

      // ── Hub-level buttons ──
      if (value === "inline:classroom") {
        const buttons: QuickButton[] = [
          {
            label: t("aiAssistant.classroom.actionAdd") + " →",
            value: "embed:classroom:add",
          },
          {
            label: t("aiAssistant.classroom.actionEdit") + " →",
            value: "embed:classroom:edit",
          },
        ];
        emit([
          assistantMsg(t("aiAssistant.classroom.actionChoice"), { buttons }),
        ]);
        return;
      }
      if (value === "inline:students") {
        const buttons: QuickButton[] = [
          {
            label: t("aiAssistant.students.actionAdd") + " →",
            value: "embed:students:add",
          },
          {
            label: t("aiAssistant.students.actionEdit") + " →",
            value: "embed:students:edit",
          },
        ];
        emit([
          assistantMsg(t("aiAssistant.students.actionChoice"), { buttons }),
        ]);
        return;
      }
      if (value === "inline:find-feature") {
        emit([assistantMsg(t("aiAssistant.findFeature.initialPrompt"))]);
        return;
      }
      if (value.startsWith("embed:")) {
        const [, type, subIntent] = value.split(":");
        startEmbeddedFlow(type as EmbeddedFlowType, { subIntent });
        return;
      }
      if (value.startsWith("flow:")) {
        const flowId = value.replace("flow:", "");
        startFlow(flowId as Parameters<typeof startFlow>[0]);
        return;
      }
      if (value.startsWith("navigate:")) {
        const path = value.replace("navigate:", "");
        window.open(path, "_blank");
        return;
      }
    },
    [clearEmbeddedFlow, startEmbeddedFlow, startFlow, emit, t, welcomeButtons],
  );

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */

  return (
    <div className="flex h-full flex-col">
      <ChatMessages messages={messages} onButtonSelect={handleButtonSelect} />
      <ChatInput
        onSend={handleSend}
        disabled={inputDisabled}
        placeholder={t("aiAssistant.hub.inputPlaceholder")}
      />
    </div>
  );
}
