/**
 * WorkspaceSwitcher - Modal-based workspace selector
 *
 * Provides a button that shows current workspace and opens a modal dialog to:
 * - Switch between Personal mode and Organization mode
 * - Select organization and school from a list
 */

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Building2,
  GraduationCap,
  User,
  ChevronDown,
  Check,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  useWorkspace,
  Organization,
  School,
} from "@/contexts/WorkspaceContext";
import { cn } from "@/lib/utils";

export const WorkspaceSwitcher: React.FC = () => {
  const { t } = useTranslation();
  const {
    mode,
    organizations,
    selectedOrganization,
    selectedSchool,
    setMode,
    selectSchool,
    loading,
  } = useWorkspace();

  const [open, setOpen] = useState(false);
  const [expandedOrgId, setExpandedOrgId] = useState<string | null>(null);

  // Determine current workspace display text
  const getCurrentWorkspaceLabel = () => {
    if (mode === "personal") {
      return t("workspace.personalMode");
    }

    if (selectedSchool && selectedOrganization) {
      return `${selectedOrganization.name} - ${selectedSchool.name}`;
    }

    return t("workspace.selectOrganization");
  };

  // Handle selection
  const handleSelectPersonal = () => {
    setMode("personal");
    setOpen(false);
  };

  const handleSelectSchool = (school: School, org: Organization) => {
    selectSchool(school, org);
    setOpen(false);
  };

  const toggleOrganization = (orgId: string) => {
    setExpandedOrgId(expandedOrgId === orgId ? null : orgId);
  };

  // Icon for current mode
  const CurrentIcon =
    mode === "personal" ? User : selectedSchool ? GraduationCap : Building2;

  return (
    <>
      {/* Trigger Button - Shows current workspace */}
      <Button
        variant="outline"
        onClick={() => setOpen(true)}
        className="w-full justify-between h-auto py-3 px-4 mb-4 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
      >
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <CurrentIcon className="h-5 w-5 flex-shrink-0 text-slate-600 dark:text-slate-400" />
          <div className="flex flex-col items-start min-w-0 flex-1">
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {t("workspace.currentWorkspace")}
            </span>
            <span className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate w-full text-left">
              {getCurrentWorkspaceLabel()}
            </span>
          </div>
        </div>
        <ChevronDown className="h-4 w-4 flex-shrink-0 text-slate-400" />
      </Button>

      {/* Modal Dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[80vh] flex flex-col p-0">
          <DialogHeader className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
            <DialogTitle>{t("workspace.selectWorkspace")}</DialogTitle>
          </DialogHeader>

          <div className="max-h-[60vh] overflow-y-auto px-6 py-4">
            <div className="space-y-3">
              {/* Personal Mode Option */}
              <WorkspaceOption
                icon={User}
                label={t("workspace.personalMode")}
                description={t("workspace.personal.description")}
                isSelected={mode === "personal"}
                onClick={handleSelectPersonal}
              />

              {/* Organizations Section */}
              {loading ? (
                <div className="space-y-2 py-4">
                  {[1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-16 bg-slate-100 dark:bg-slate-800 rounded-lg animate-pulse"
                    />
                  ))}
                </div>
              ) : organizations.length > 0 ? (
                <div className="space-y-2">
                  {organizations.map((org) => (
                    <OrganizationSection
                      key={org.id}
                      organization={org}
                      isExpanded={expandedOrgId === org.id}
                      selectedSchoolId={
                        mode === "organization" &&
                        selectedOrganization?.id === org.id
                          ? selectedSchool?.id
                          : null
                      }
                      onToggle={() => toggleOrganization(org.id)}
                      onSelectSchool={(school) =>
                        handleSelectSchool(school, org)
                      }
                    />
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {t("workspace.organization.noOrganizations")}
                  </p>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

// ============================================
// Workspace Option Component (Personal Mode)
// ============================================

interface WorkspaceOptionProps {
  icon: React.ElementType;
  label: string;
  description: string;
  isSelected: boolean;
  onClick: () => void;
}

const WorkspaceOption: React.FC<WorkspaceOptionProps> = ({
  icon: Icon,
  label,
  description,
  isSelected,
  onClick,
}) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full p-4 rounded-lg border-2 transition-all duration-150 text-left",
        "hover:border-blue-300 dark:hover:border-blue-700",
        isSelected
          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-600"
          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800",
      )}
    >
      <div className="flex items-start gap-3">
        <Icon
          className={cn(
            "h-5 w-5 flex-shrink-0 mt-0.5",
            isSelected
              ? "text-blue-600 dark:text-blue-400"
              : "text-slate-500 dark:text-slate-400",
          )}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {label}
            </h3>
            {isSelected && (
              <Check className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {description}
          </p>
        </div>
      </div>
    </button>
  );
};

// ============================================
// Organization Section Component
// ============================================

interface OrganizationSectionProps {
  organization: Organization;
  isExpanded: boolean;
  selectedSchoolId: string | null | undefined;
  onToggle: () => void;
  onSelectSchool: (school: School) => void;
}

const OrganizationSection: React.FC<OrganizationSectionProps> = ({
  organization,
  isExpanded,
  selectedSchoolId,
  onToggle,
  onSelectSchool,
}) => {
  const { t } = useTranslation();
  const hasSchools = organization.schools && organization.schools.length > 0;

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Organization Header */}
      <button
        onClick={onToggle}
        className={cn(
          "w-full p-4 flex items-center gap-3 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors",
          isExpanded &&
            hasSchools &&
            "border-b border-slate-200 dark:border-slate-700",
        )}
      >
        <Building2 className="h-5 w-5 text-slate-600 dark:text-slate-400 flex-shrink-0" />
        <div className="flex-1 text-left min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
            {organization.name}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {hasSchools
              ? `${organization.schools.length} ${organization.schools.length === 1 ? "school" : "schools"}`
              : t("workspace.noSchoolsInOrg")}
          </p>
        </div>
        {hasSchools && (
          <ChevronDown
            className={cn(
              "h-4 w-4 text-slate-400 transition-transform duration-200 flex-shrink-0",
              isExpanded && "rotate-180",
            )}
          />
        )}
      </button>

      {/* Schools List */}
      {isExpanded && hasSchools && (
        <div className="bg-white dark:bg-slate-900">
          {organization.schools.map((school, index) => (
            <button
              key={school.id}
              onClick={() => onSelectSchool(school)}
              className={cn(
                "w-full px-4 py-3 flex items-center gap-3 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors",
                index !== organization.schools.length - 1 &&
                  "border-b border-slate-100 dark:border-slate-800",
                selectedSchoolId === school.id &&
                  "bg-blue-50 dark:bg-blue-900/20",
              )}
            >
              <GraduationCap
                className={cn(
                  "h-4 w-4 flex-shrink-0",
                  selectedSchoolId === school.id
                    ? "text-blue-600 dark:text-blue-400"
                    : "text-slate-500 dark:text-slate-400",
                )}
              />
              <span
                className={cn(
                  "text-sm flex-1 text-left truncate",
                  selectedSchoolId === school.id
                    ? "font-semibold text-blue-900 dark:text-blue-100"
                    : "text-slate-700 dark:text-slate-300",
                )}
              >
                {school.name}
              </span>
              {selectedSchoolId === school.id && (
                <Check className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorkspaceSwitcher;
