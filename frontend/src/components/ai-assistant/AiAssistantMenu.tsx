import { useContext } from "react";
import { useLocation } from "react-router-dom";
import { HelpCircle, Rocket, School, UserPlus, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAiAssistant } from "./useAiAssistant";
import { WorkspaceContext } from "@/contexts/WorkspaceContext";

interface MenuItemProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  disabled?: boolean;
  onClick?: () => void;
}

function MenuItem({
  icon,
  title,
  description,
  disabled = false,
  onClick,
}: MenuItemProps) {
  return (
    <button
      className={cn(
        "w-full text-left border rounded-lg p-4 transition-colors",
        disabled
          ? "opacity-50 cursor-not-allowed bg-gray-50"
          : "hover:bg-blue-50 cursor-pointer",
      )}
      disabled={disabled}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">{icon}</div>
        <div>
          <div className="font-medium">{title}</div>
          <div className="mt-1 text-sm text-gray-500">{description}</div>
        </div>
      </div>
    </button>
  );
}

export function AiAssistantMenu() {
  const location = useLocation();
  const { startFlow } = useAiAssistant();
  const workspace = useContext(WorkspaceContext);

  const isOrgBackend = location.pathname.startsWith("/organization");
  const isTeacherOrgView = !isOrgBackend && workspace?.mode === "organization";

  // Icon color per context
  // Org backend: blue | Teacher personal: green | Teacher org view: purple
  const iconColor = isOrgBackend
    ? "text-blue-600"
    : isTeacherOrgView
      ? "text-purple-600"
      : "text-green-600";

  // ─── Org backend menu ───
  if (isOrgBackend) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-gray-500 mb-4">
          選擇您想要執行的功能，AI 助手將引導您完成操作。
        </p>

        <MenuItem
          icon={<School className={cn("h-5 w-5", iconColor)} />}
          title="新增機構班級"
          description="在分校下建立新班級"
          disabled
        />

        <MenuItem
          icon={<Users className={cn("h-5 w-5", iconColor)} />}
          title="新增班級學生"
          description="將學生加入班級"
          disabled
        />

        <MenuItem
          icon={<UserPlus className={cn("h-5 w-5", iconColor)} />}
          title="新增機構教師"
          description="透過對話方式快速新增教師到機構中"
          onClick={() => startFlow("add-teacher")}
        />

        <MenuItem
          icon={<HelpCircle className={cn("h-5 w-5", iconColor)} />}
          title="找功能"
          description="告訴我您想做什麼，我幫您找到對應的頁面"
          onClick={() => startFlow("find-feature")}
        />
      </div>
    );
  }

  // ─── Teacher org view menu ───
  if (isTeacherOrgView) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-gray-500 mb-4">
          選擇您想要執行的功能，AI 助手將引導您完成操作。
        </p>

        <MenuItem
          icon={<HelpCircle className={cn("h-5 w-5", iconColor)} />}
          title="找功能"
          description="告訴我您想做什麼，我幫您找到對應的頁面"
          onClick={() => startFlow("find-feature")}
        />
      </div>
    );
  }

  // ─── Teacher personal view menu ───
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500 mb-4">
        選擇您想要執行的功能，AI 助手將引導您完成操作。
      </p>

      <MenuItem
        icon={<Rocket className={cn("h-5 w-5", iconColor)} />}
        title="新手快速指引"
        description="第一次使用？按照步驟快速上手"
        onClick={() => startFlow("quick-start")}
      />

      <MenuItem
        icon={<School className={cn("h-5 w-5", iconColor)} />}
        title="新增班級"
        description="建立新的班級"
        onClick={() => startFlow("add-classroom")}
      />

      <MenuItem
        icon={<Users className={cn("h-5 w-5", iconColor)} />}
        title="新增班級學生"
        description="將學生加入現有班級"
        onClick={() => startFlow("add-students")}
      />

      <MenuItem
        icon={<HelpCircle className={cn("h-5 w-5", iconColor)} />}
        title="找功能"
        description="告訴我您想做什麼，我幫您找到對應的頁面"
        onClick={() => startFlow("find-feature")}
      />
    </div>
  );
}
