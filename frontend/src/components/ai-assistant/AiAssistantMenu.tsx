import { useLocation } from "react-router-dom";
import { HelpCircle, School, UserPlus } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAiAssistant } from "./useAiAssistant";

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
  const isOrgBackend = location.pathname.startsWith("/organization");

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500 mb-4">
        選擇您想要執行的功能，AI 助手將引導您完成操作。
      </p>

      <MenuItem
        icon={<School className="h-5 w-5 text-blue-600" />}
        title="新增班級和班級學生"
        description="即將推出"
        disabled
      />

      {isOrgBackend && (
        <MenuItem
          icon={<UserPlus className="h-5 w-5 text-blue-600" />}
          title="新增機構教師"
          description="透過對話方式快速新增教師到機構中"
          onClick={() => {
            startFlow("add-teacher");
          }}
        />
      )}

      <MenuItem
        icon={<HelpCircle className="h-5 w-5 text-blue-600" />}
        title="找功能"
        description="告訴我您想做什麼，我幫您找到對應的頁面"
        onClick={() => {
          startFlow("find-feature");
        }}
      />
    </div>
  );
}
