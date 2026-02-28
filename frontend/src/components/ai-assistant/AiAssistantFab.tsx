import { Wand2 } from "lucide-react";
import { useAiAssistant } from "./useAiAssistant";
import { cn } from "@/lib/utils";

export function AiAssistantFab() {
  const { isOpen, open } = useAiAssistant();

  if (isOpen) return null;

  return (
    <button
      onClick={open}
      className={cn(
        "fixed bottom-6 right-6 z-50",
        "h-14 w-14 rounded-full",
        "bg-blue-600 hover:bg-blue-700 text-white",
        "shadow-lg hover:shadow-xl",
        "flex items-center justify-center",
        "transition-all duration-200 hover:scale-110",
      )}
      aria-label="AI 助手"
    >
      <Wand2 className="h-6 w-6" />
    </button>
  );
}
