import { useState, useCallback, useRef, useContext } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChatContainer } from "../chat/ChatContainer";
import { useAiAssistant } from "../useAiAssistant";
import { useOrganization } from "@/contexts/OrganizationContext";
import { WorkspaceContext } from "@/contexts/WorkspaceContext";
import { API_URL } from "@/config/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import type { ChatMessage, QuickButton } from "../chat/types";

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
  const { exitFlow } = useAiAssistant();
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedNode } = useOrganization();
  // Safe access: WorkspaceContext only exists in TeacherLayout, not OrganizationLayout
  const workspace = useContext(WorkspaceContext);
  const [messages, setMessages] = useState<ChatMessage[]>([
    assistantMsg(
      "請問您想找什麼功能？\n例如：「我想看班級學生名單」、「怎麼管理教材」",
    ),
  ]);
  const [inputDisabled, setInputDisabled] = useState(false);
  const messagesRef = useRef<ChatMessage[]>([
    assistantMsg(
      "請問您想找什麼功能？\n例如：「我想看班級學生名單」、「怎麼管理教材」",
    ),
  ]);

  // Resolve orgId from URL or context
  const resolveOrgId = useCallback((): string | undefined => {
    const match = location.pathname.match(/^\/organization\/([a-f0-9-]+)/);
    if (match) return match[1];
    if (selectedNode?.type === "organization") return selectedNode.id;
    return undefined;
  }, [location.pathname, selectedNode]);

  const emit = useCallback(
    (msgs: ChatMessage[]) => {
      // Remove loading messages
      const current = messagesRef.current.filter((m) => !m.loading);
      current.push(...msgs);
      messagesRef.current = current;
      setMessages([...current]);
    },
    [],
  );

  const handleSend = useCallback(
    async (text: string) => {
      setInputDisabled(true);
      emit([
        userMsg(text),
        assistantMsg("正在搜尋...", { loading: true }),
      ]);

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
            user_roles: useTeacherAuthStore.getState().userRoles,
            current_path: location.pathname,
            workspace_mode: workspace?.mode ?? "",
            workspace_org: workspace?.selectedOrganization?.name ?? "",
            workspace_school: workspace?.selectedSchool?.name ?? "",
          }),
        });

        if (!res.ok) throw new Error("AI 處理失敗");
        const data = await res.json();

        const orgId = resolveOrgId();
        const buttons: QuickButton[] = (data.navigation || [])
          .map((nav: { label: string; path: string }) => {
            let path = nav.path;
            if (orgId) path = path.replace("{orgId}", orgId);
            // If schoolId is unresolved, fall back to the schools list
            if (path.includes("{schoolId}") && orgId) {
              return {
                label: "前往分校清單（請先選擇分校） →",
                value: `navigate:/organization/${orgId}/schools`,
              };
            }
            return { label: `${nav.label} →`, value: `navigate:${path}` };
          })
          .filter((b: QuickButton) => !b.value.includes("{"));  // Skip remaining unresolved

        // Deduplicate buttons (e.g., multiple school pages → single schools link)
        const seen = new Set<string>();
        const uniqueButtons = buttons.filter((b) => {
          if (seen.has(b.value)) return false;
          seen.add(b.value);
          return true;
        });

        emit([
          assistantMsg(data.message, uniqueButtons.length > 0 ? { buttons: uniqueButtons } : undefined),
        ]);
      } catch {
        emit([
          assistantMsg("抱歉，目前無法處理您的問題。請試著用不同方式描述。"),
        ]);
      }

      setInputDisabled(false);
    },
    [emit, resolveOrgId],
  );

  const handleButtonSelect = useCallback(
    (_messageId: string, value: string) => {
      if (value.startsWith("navigate:")) {
        const path = value.replace("navigate:", "");
        navigate(path);
        return;
      }
    },
    [navigate],
  );

  return (
    <ChatContainer
      title="找功能"
      messages={messages}
      onSend={handleSend}
      onButtonSelect={handleButtonSelect}
      onBack={exitFlow}
      inputDisabled={inputDisabled}
      inputPlaceholder="描述您想找的功能..."
    />
  );
}
