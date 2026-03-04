import { create } from "zustand";

const AI_ASSISTANT_SEEN_KEY = "ai-assistant-seen";

export type FlowId =
  | "add-teacher"
  | "add-classroom"
  | "add-students"
  | "find-feature"
  | "quick-start";

export interface InitialFlowData {
  parsedData?: Record<string, unknown>;
  subIntent?: string;
}

interface AiAssistantState {
  isOpen: boolean;
  activeFlow: FlowId | null;
  initialFlowData: InitialFlowData | null;
  open: () => void;
  close: () => void;
  toggle: () => void;
  startFlow: (flowId: FlowId) => void;
  startFlowWithData: (flowId: FlowId, data: InitialFlowData) => void;
  exitFlow: () => void;
  clearInitialData: () => void;
}

export const useAiAssistant = create<AiAssistantState>((set) => {
  const hasSeen = localStorage.getItem(AI_ASSISTANT_SEEN_KEY) === "true";
  const initialOpen = !hasSeen;

  if (!hasSeen) {
    localStorage.setItem(AI_ASSISTANT_SEEN_KEY, "true");
  }

  return {
    isOpen: initialOpen,
    activeFlow: null,
    initialFlowData: null,
    open: () => set({ isOpen: true }),
    close: () => set({ isOpen: false }),
    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
    startFlow: (flowId: FlowId) => set({ activeFlow: flowId }),
    startFlowWithData: (flowId: FlowId, data: InitialFlowData) =>
      set({ activeFlow: flowId, initialFlowData: data }),
    exitFlow: () => set({ activeFlow: null, initialFlowData: null }),
    clearInitialData: () => set({ initialFlowData: null }),
  };
});
