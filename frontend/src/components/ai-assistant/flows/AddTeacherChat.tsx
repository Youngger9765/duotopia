import { useState, useEffect, useRef, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChatContainer } from "../chat/ChatContainer";
import { useAiAssistant } from "../useAiAssistant";
import { AddTeacherFlow, type FlowState } from "./add-teacher-flow";
import { useOrganization } from "@/contexts/OrganizationContext";
import type { ChatMessage } from "../chat/types";

export function AddTeacherChat() {
  const { exitFlow } = useAiAssistant();
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedNode } = useOrganization();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [flowState, setFlowState] = useState<Partial<FlowState>>({
    inputDisabled: true,
  });
  const flowRef = useRef<AddTeacherFlow | null>(null);

  // Detect orgId: first from URL params, then from OrganizationContext
  const detectedOrgId = (() => {
    // URL: /organization/:orgId/...
    const match = location.pathname.match(/^\/organization\/([a-f0-9-]+)/);
    if (match) return match[1];
    // Context: selected org node
    if (selectedNode?.type === "organization") return selectedNode.id;
    return undefined;
  })();

  const pushMsg = useCallback((msgs: ChatMessage[]) => {
    setMessages([...msgs]);
  }, []);

  const updateState = useCallback((partial: Partial<FlowState>) => {
    setFlowState((prev) => ({ ...prev, ...partial }));
  }, []);

  // Initialize flow once
  useEffect(() => {
    if (!flowRef.current) {
      flowRef.current = new AddTeacherFlow(pushMsg, updateState, detectedOrgId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSend = useCallback((text: string) => {
    flowRef.current?.handleUserInput(text);
  }, []);

  const handleButtonSelect = useCallback(
    (messageId: string, value: string) => {
      if (value === "_disabled") return;
      // Handle navigation buttons with React Router (no full page reload)
      if (value.startsWith("navigate:")) {
        const path = value.replace("navigate:", "");
        navigate(path);
        return;
      }
      flowRef.current?.handleButtonSelect(messageId, value);
    },
    [navigate],
  );

  return (
    <ChatContainer
      title="新增機構教師"
      messages={messages}
      onSend={handleSend}
      onButtonSelect={handleButtonSelect}
      onBack={exitFlow}
      inputDisabled={flowState.inputDisabled ?? true}
      inputPlaceholder="輸入教師資料或修改指令..."
    />
  );
}
