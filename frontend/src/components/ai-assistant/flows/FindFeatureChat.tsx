import { useState, useCallback, useRef, useContext, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import { ChatContainer } from "../chat/ChatContainer";
import { useAiAssistant, type FlowId } from "../useAiAssistant";
import { OrganizationContext } from "@/contexts/OrganizationContext";
import { WorkspaceContext } from "@/contexts/WorkspaceContext";
import { useHubCooldown } from "../useHubCooldown";
import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import type { ChatMessage, QuickButton } from "../chat/types";

const INTENT_TO_FLOW: Record<string, FlowId> = {
  classroom_management: "add-classroom",
  student_management: "add-students",
  find_feature: "find-feature",
  quick_start: "quick-start",
};

let _msgId = 0;
function msgId() {
  return `ff-msg-${++_msgId}`;
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

export function FindFeatureChat() {
  const { t } = useTranslation();
  const { isCoolingDown, recordUnclear, resetCount } = useHubCooldown();
  const {
    exitFlow,
    startFlow,
    startFlowWithData,
    initialFlowData,
    clearInitialData,
  } = useAiAssistant();
  const autoSentRef = useRef(false);
  const location = useLocation();
  // Safe access: OrganizationContext only exists in OrganizationLayout, not TeacherLayout
  const orgCtx = useContext(OrganizationContext);
  const selectedNode = orgCtx?.selectedNode ?? null;
  // Safe access: WorkspaceContext only exists in TeacherLayout, not OrganizationLayout
  const workspace = useContext(WorkspaceContext);
  const [messages, setMessages] = useState<ChatMessage[]>([
    assistantMsg(t("aiAssistant.findFeature.initialPrompt")),
  ]);
  const [inputDisabled, setInputDisabled] = useState(false);
  const messagesRef = useRef<ChatMessage[]>([
    assistantMsg(t("aiAssistant.findFeature.initialPrompt")),
  ]);

  // Resolve orgId from URL or context
  const resolveOrgId = useCallback((): string | undefined => {
    const match = location.pathname.match(/^\/organization\/([a-f0-9-]+)/);
    if (match) return match[1];
    if (selectedNode?.type === "organization") return selectedNode.id;
    return undefined;
  }, [location.pathname, selectedNode]);

  const emit = useCallback((msgs: ChatMessage[]) => {
    // Remove loading messages
    const current = messagesRef.current.filter((m) => !m.loading);
    current.push(...msgs);
    messagesRef.current = current;
    setMessages([...current]);
  }, []);

  /** Call the find-feature API (the actual feature search) */
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
            context: location.pathname.startsWith("/organization")
              ? "organization"
              : "teacher",
            user_roles: useTeacherAuthStore.getState().userRoles ?? [],
            current_path: location.pathname,
            workspace_mode: workspace?.mode ?? "",
            workspace_org: workspace?.selectedOrganization?.name ?? "",
            workspace_school: workspace?.selectedSchool?.name ?? "",
          }),
        });

        if (!res.ok) throw new Error("find-feature failed");
        const data = await res.json();

        const orgId = resolveOrgId();
        const buttons: QuickButton[] = (data.navigation || [])
          .map((nav: { label: string; path: string }) => {
            let path = nav.path;
            if (orgId) path = path.replace("{orgId}", orgId);
            if (path.includes("{schoolId}") && orgId) {
              return {
                label: t("aiAssistant.findFeature.goToSchoolList"),
                value: `navigate:/organization/${orgId}/schools`,
              };
            }
            return { label: `${nav.label} →`, value: `navigate:${path}` };
          })
          .filter((b: QuickButton) => !b.value.includes("{"));

        // Deduplicate buttons
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
        emit([assistantMsg(t("aiAssistant.findFeature.error"))]);
      }
    },
    [emit, resolveOrgId, t, location.pathname, workspace],
  );

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

      setInputDisabled(true);
      emit([
        userMsg(text),
        assistantMsg(t("aiAssistant.hub.thinking"), { loading: true }),
      ]);

      try {
        // First: detect intent to route properly
        const token = useTeacherAuthStore.getState().token;
        const res = await fetch(`${API_URL}/api/ai/assistant/detect-intent`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            user_input: text,
            context: "teacher",
            current_path: location.pathname,
            workspace_mode: workspace?.mode ?? "personal",
          }),
        });

        if (!res.ok) throw new Error("detect-intent failed");
        const data = await res.json();
        const intent = data.intent as string;

        // ── find_feature → use the dedicated find-feature API ──
        if (intent === "find_feature") {
          resetCount();
          await callFindFeature(text);
          setInputDisabled(false);
          return;
        }

        // ── Different actionable flow → switch ──
        const targetFlow = INTENT_TO_FLOW[intent];
        if (targetFlow && targetFlow !== "find-feature") {
          resetCount();
          startFlowWithData(targetFlow, {
            parsedData: data.parsed_data ?? undefined,
            subIntent: data.sub_intent ?? undefined,
          });
          return;
        }
        if (intent === "quick_start") {
          resetCount();
          startFlow("quick-start");
          return;
        }

        // ── Delete request → show message + nav buttons inline ──
        if (intent === "delete_request") {
          resetCount();
          const navButtons: QuickButton[] = (data.navigation ?? []).map(
            (nav: { label: string; path: string }) => ({
              label: `${nav.label} →`,
              value: `navigate:${nav.path}`,
            }),
          );
          emit([
            assistantMsg(data.message ?? "", {
              buttons: navButtons.length > 0 ? navButtons : undefined,
            }),
          ]);
          setInputDisabled(false);
          return;
        }

        // ── greeting → show message, reset count ──
        if (intent === "greeting") {
          resetCount();
          emit([assistantMsg(data.message ?? "")]);
          setInputDisabled(false);
          return;
        }

        // ── off_topic / unclear → show AI message, track abuse ──
        const triggered = recordUnclear();
        if (triggered) {
          emit([assistantMsg(t("aiAssistant.hub.cooldownTriggered"))]);
        } else {
          emit([assistantMsg(data.message ?? t("aiAssistant.hub.error"))]);
        }
      } catch {
        // detect-intent failed → fallback: try find-feature directly
        await callFindFeature(text);
      }

      setInputDisabled(false);
    },
    [
      emit,
      t,
      location.pathname,
      workspace,
      callFindFeature,
      startFlow,
      startFlowWithData,
      isCoolingDown,
      recordUnclear,
      resetCount,
    ],
  );

  // Auto-send query from HubChat intent detection
  useEffect(() => {
    if (initialFlowData?.parsedData?.query && !autoSentRef.current) {
      autoSentRef.current = true;
      const query = initialFlowData.parsedData.query as string;
      clearInitialData();
      // Skip detect-intent for auto-send (already detected as find_feature)
      setInputDisabled(true);
      emit([
        userMsg(query),
        assistantMsg(t("aiAssistant.findFeature.searching"), { loading: true }),
      ]);
      callFindFeature(query).then(() => setInputDisabled(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialFlowData]);

  const handleButtonSelect = useCallback(
    (_messageId: string, value: string) => {
      if (value.startsWith("navigate:")) {
        const path = value.replace("navigate:", "");
        window.open(path, "_blank");
        return;
      }
    },
    [],
  );

  return (
    <ChatContainer
      title={t("aiAssistant.findFeature.title")}
      messages={messages}
      onSend={handleSend}
      onButtonSelect={handleButtonSelect}
      onBack={exitFlow}
      inputDisabled={inputDisabled}
      inputPlaceholder={t("aiAssistant.findFeature.inputPlaceholder")}
    />
  );
}
