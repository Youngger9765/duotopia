import { useRef } from "react";
import { Wand2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAiAssistant, type FlowId } from "./useAiAssistant";
import { AiAssistantMenu } from "./AiAssistantMenu";
import { AddTeacherChat } from "./flows/AddTeacherChat";
import { AddClassroomChat } from "./flows/AddClassroomChat";
import { AddStudentsChat } from "./flows/AddStudentsChat";
import { FindFeatureChat } from "./flows/FindFeatureChat";
import { QuickStartChat } from "./flows/QuickStartChat";
import { cn } from "@/lib/utils";

const FLOW_COMPONENTS: Record<FlowId, React.FC> = {
  "quick-start": QuickStartChat,
  "add-teacher": AddTeacherChat,
  "add-classroom": AddClassroomChat,
  "add-students": AddStudentsChat,
  "find-feature": FindFeatureChat,
};

export function AiAssistantPanel() {
  const { isOpen, activeFlow, close } = useAiAssistant();
  // Track which flows have been opened at least once, so they stay mounted
  const mountedFlows = useRef(new Set<FlowId>());

  if (activeFlow) {
    mountedFlows.current.add(activeFlow);
  }

  return (
    <div
      className={cn(
        "shrink-0 border-l bg-white transition-all duration-300 overflow-hidden h-full",
        isOpen ? "w-full md:w-[380px]" : "w-0 border-l-0",
      )}
    >
      <div
        className={cn(
          "flex h-full w-full md:w-[380px] flex-col",
          !isOpen && "invisible",
        )}
      >
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

        {/* Content — flow components stay mounted once activated,
            so conversation state persists across panel open/close. */}
        {(Object.entries(FLOW_COMPONENTS) as [FlowId, React.FC][]).map(
          ([flowId, Component]) =>
            mountedFlows.current.has(flowId) && (
              <div
                key={flowId}
                className={cn(
                  "flex-1 overflow-hidden",
                  activeFlow !== flowId && "hidden",
                )}
              >
                <Component />
              </div>
            ),
        )}

        {/* Menu — shown when no flow is active */}
        {activeFlow === null && (
          <div className="flex-1 overflow-y-auto p-4">
            <AiAssistantMenu />
          </div>
        )}
      </div>
    </div>
  );
}
