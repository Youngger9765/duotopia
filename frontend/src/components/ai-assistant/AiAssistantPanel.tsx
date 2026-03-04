import { useRef, useContext } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import { Wand2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAiAssistant, type FlowId } from "./useAiAssistant";
import { AiAssistantMenu } from "./AiAssistantMenu";
import { HubChat } from "./flows/HubChat";
import { AddTeacherChat } from "./flows/AddTeacherChat";
import { AddClassroomChat } from "./flows/AddClassroomChat";
import { AddStudentsChat } from "./flows/AddStudentsChat";
import { FindFeatureChat } from "./flows/FindFeatureChat";
import { QuickStartChat } from "./flows/QuickStartChat";
import { WorkspaceContext } from "@/contexts/WorkspaceContext";
import { cn } from "@/lib/utils";

const FLOW_COMPONENTS: Record<FlowId, React.FC> = {
  "quick-start": QuickStartChat,
  "add-teacher": AddTeacherChat,
  "add-classroom": AddClassroomChat,
  "add-students": AddStudentsChat,
  "find-feature": FindFeatureChat,
};

export function AiAssistantPanel() {
  const { t } = useTranslation();
  const location = useLocation();
  const workspace = useContext(WorkspaceContext);
  const { isOpen, activeFlow, close } = useAiAssistant();
  // Track which flows have been opened at least once, so they stay mounted
  const mountedFlows = useRef(new Set<FlowId>());
  // Track whether HubChat has been mounted
  const hubMounted = useRef(false);

  if (activeFlow) {
    mountedFlows.current.add(activeFlow);
  }

  // Detect context — same logic as AiAssistantMenu
  const isOrgBackend = location.pathname.startsWith("/organization");
  const isTeacherOrgView = !isOrgBackend && workspace?.mode === "organization";
  const isTeacherPersonal = !isOrgBackend && !isTeacherOrgView;

  // Keep HubChat mounted once shown (preserves conversation history)
  if (isTeacherPersonal && activeFlow === null) {
    hubMounted.current = true;
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
            <span className="font-semibold">
              {t("aiAssistant.panel.title")}
            </span>
            <span className="rounded-full bg-blue-600 px-2 py-0.5 text-[10px] font-bold leading-none text-white">
              Beta
            </span>
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

        {/* HubChat — teacher personal only, stays mounted to preserve history */}
        {isTeacherPersonal && hubMounted.current && (
          <div
            className={cn(
              "flex-1 overflow-hidden",
              activeFlow !== null && "hidden",
            )}
          >
            <HubChat />
          </div>
        )}

        {/* Menu — shown for org backend and teacher org-view only */}
        {!isTeacherPersonal && activeFlow === null && (
          <div className="flex-1 overflow-y-auto p-4">
            <AiAssistantMenu />
          </div>
        )}
      </div>
    </div>
  );
}
