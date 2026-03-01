import { create } from "zustand";

const AI_ASSISTANT_SEEN_KEY = "ai-assistant-seen";

export type FlowId =
  | "add-teacher"
  | "add-classroom"
  | "add-students"
  | "find-feature"
  | "quick-start";

interface AiAssistantState {
  isOpen: boolean;
  activeFlow: FlowId | null;
  open: () => void;
  close: () => void;
  toggle: () => void;
  startFlow: (flowId: FlowId) => void;
  exitFlow: () => void;
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
    open: () => set({ isOpen: true }),
    close: () => set({ isOpen: false }),
    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
    startFlow: (flowId: FlowId) => set({ activeFlow: flowId }),
    exitFlow: () => set({ activeFlow: null }),
  };
});
