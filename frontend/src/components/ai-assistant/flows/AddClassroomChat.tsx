import { useState, useEffect, useRef, useCallback } from "react";
import { ChatContainer } from "../chat/ChatContainer";
import { useAiAssistant } from "../useAiAssistant";
import { AddClassroomFlow, type FlowState } from "./add-classroom-flow";
import type { ChatMessage } from "../chat/types";

export function AddClassroomChat() {
  const { exitFlow } = useAiAssistant();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [flowState, setFlowState] = useState<Partial<FlowState>>({
    inputDisabled: true,
  });
  const flowRef = useRef<AddClassroomFlow | null>(null);

  const pushMsg = useCallback((msgs: ChatMessage[]) => {
    setMessages([...msgs]);
  }, []);

  const updateState = useCallback((partial: Partial<FlowState>) => {
    setFlowState((prev) => ({ ...prev, ...partial }));
  }, []);

  // Initialize flow once
  useEffect(() => {
    if (!flowRef.current) {
      flowRef.current = new AddClassroomFlow(pushMsg, updateState);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSend = useCallback((text: string) => {
    flowRef.current?.handleUserInput(text);
  }, []);

  const handleButtonSelect = useCallback(
    (_messageId: string, value: string) => {
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
      title="新增班級"
      messages={messages}
      onSend={handleSend}
      onButtonSelect={handleButtonSelect}
      onBack={exitFlow}
      inputDisabled={flowState.inputDisabled ?? true}
      inputPlaceholder="輸入班級資料..."
    />
  );
}
