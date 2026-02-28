import { Wand2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAiAssistant } from "./useAiAssistant";
import { AiAssistantMenu } from "./AiAssistantMenu";
import { AddTeacherChat } from "./flows/AddTeacherChat";
import { FindFeatureChat } from "./flows/FindFeatureChat";
import { cn } from "@/lib/utils";

export function AiAssistantPanel() {
  const { isOpen, activeFlow, close } = useAiAssistant();

  return (
    <div
      className={cn(
        "shrink-0 border-l bg-white transition-all duration-300 overflow-hidden",
        isOpen ? "w-[380px]" : "w-0 border-l-0",
      )}
    >
      {isOpen && (
        <div className="flex h-full w-[380px] flex-col">
          {/* Header */}
          <div className="flex h-14 items-center justify-between border-b px-4">
            <div className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-blue-600" />
              <span className="font-semibold">AI 助手</span>
            </div>
            <Button variant="ghost" size="icon" onClick={close}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Content — switches between menu and active flow */}
          {activeFlow === "add-teacher" ? (
            <AddTeacherChat />
          ) : activeFlow === "find-feature" ? (
            <FindFeatureChat />
          ) : (
            <div className="flex-1 overflow-y-auto p-4">
              <AiAssistantMenu />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
