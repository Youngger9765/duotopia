import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { ChatContainer } from "../chat/ChatContainer";
import { useAiAssistant } from "../useAiAssistant";
import { ManageStudentsFlow, type FlowState } from "./add-students-flow";
import type { ChatMessage } from "../chat/types";

export function AddStudentsChat() {
  const { t } = useTranslation();
  const { exitFlow, initialFlowData, clearInitialData } = useAiAssistant();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [, setFlowState] = useState<Partial<FlowState>>({});
  const flowRef = useRef<ManageStudentsFlow | null>(null);

  const pushMsg = useCallback((msgs: ChatMessage[]) => {
    setMessages([...msgs]);
  }, []);

  const updateState = useCallback((partial: Partial<FlowState>) => {
    setFlowState((prev) => ({ ...prev, ...partial }));
  }, []);

  // Initialize flow — pass initialData if coming from HubChat intent detection
  useEffect(() => {
    const initData = initialFlowData
      ? { subIntent: initialFlowData.subIntent }
      : undefined;

    if (!flowRef.current) {
      flowRef.current = new ManageStudentsFlow(pushMsg, updateState, initData);
    } else if (initData) {
      flowRef.current = new ManageStudentsFlow(pushMsg, updateState, initData);
    }

    if (initialFlowData) clearInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialFlowData]);

  const handleSend = useCallback((text: string) => {
    const flow = flowRef.current;
    if (!flow) return;

    // Pass all text input to the flow for processing
    flow.handleUserInput(text);
  }, []);

  const handleButtonSelect = useCallback(
    async (_messageId: string, value: string) => {
      if (value === "_disabled") return;

      if (value.startsWith("navigate:")) {
        const path = value.replace("navigate:", "");
        window.open(path, "_blank");
        return;
      }
      flowRef.current?.handleButtonSelect(_messageId, value);
    },
    [],
  );

  return (
    <ChatContainer
      title={t("aiAssistant.students.chatTitle")}
      messages={messages}
      onSend={handleSend}
      onButtonSelect={handleButtonSelect}
      onBack={exitFlow}
      inputDisabled={false}
      inputPlaceholder={t("aiAssistant.students.inputPlaceholder")}
    />
  );
}
