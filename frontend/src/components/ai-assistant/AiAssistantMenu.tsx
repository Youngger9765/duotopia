import { useContext } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
          {t("aiAssistant.menu.prompt")}
        </p>

        <MenuItem
          icon={<School className={cn("h-5 w-5", iconColor)} />}
          title={t("aiAssistant.menu.addOrgClassroom.title")}
          description={t("aiAssistant.menu.addOrgClassroom.description")}
          disabled
        />

        <MenuItem
          icon={<Users className={cn("h-5 w-5", iconColor)} />}
          title={t("aiAssistant.menu.addOrgStudents.title")}
          description={t("aiAssistant.menu.addOrgStudents.description")}
          disabled
        />

        <MenuItem
          icon={<UserPlus className={cn("h-5 w-5", iconColor)} />}
          title={t("aiAssistant.menu.addTeacher.title")}
          description={t("aiAssistant.menu.addTeacher.description")}
          onClick={() => startFlow("add-teacher")}
        />

        <MenuItem
          icon={<HelpCircle className={cn("h-5 w-5", iconColor)} />}
          title={t("aiAssistant.menu.findFeature.title")}
          description={t("aiAssistant.menu.findFeature.description")}
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
          {t("aiAssistant.menu.prompt")}
        </p>

        <MenuItem
          icon={<HelpCircle className={cn("h-5 w-5", iconColor)} />}
          title={t("aiAssistant.menu.findFeature.title")}
          description={t("aiAssistant.menu.findFeature.description")}
          onClick={() => startFlow("find-feature")}
        />
      </div>
    );
  }

  // ─── Teacher personal view menu ───
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500 mb-4">
        {t("aiAssistant.menu.prompt")}
      </p>

      <MenuItem
        icon={<Rocket className={cn("h-5 w-5", iconColor)} />}
        title={t("aiAssistant.menu.quickStart.title")}
        description={t("aiAssistant.menu.quickStart.description")}
        onClick={() => startFlow("quick-start")}
      />

      <MenuItem
        icon={<School className={cn("h-5 w-5", iconColor)} />}
        title={t("aiAssistant.menu.addClassroom.title")}
        description={t("aiAssistant.menu.addClassroom.description")}
        onClick={() => startFlow("add-classroom")}
      />

      <MenuItem
        icon={<Users className={cn("h-5 w-5", iconColor)} />}
        title={t("aiAssistant.menu.addStudents.title")}
        description={t("aiAssistant.menu.addStudents.description")}
        onClick={() => startFlow("add-students")}
      />

      <MenuItem
        icon={<HelpCircle className={cn("h-5 w-5", iconColor)} />}
        title={t("aiAssistant.menu.findFeature.title")}
        description={t("aiAssistant.menu.findFeature.description")}
        onClick={() => startFlow("find-feature")}
      />
    </div>
  );
}
