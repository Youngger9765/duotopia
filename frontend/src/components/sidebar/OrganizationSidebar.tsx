import { useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { useNavigate } from "react-router-dom";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Building2, School as SchoolIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface OrganizationSidebarProps {
  isCollapsed: boolean;
  onNavigate?: () => void;
}

export function OrganizationSidebar({
  isCollapsed,
  onNavigate,
}: OrganizationSidebarProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);
  const {
    selectedNode,
    setSelectedNode,
    organizations,
    schools,
    setSchools,
    expandedOrgs,
    setExpandedOrgs,
    isFetchingOrgs,
  } = useOrganization();

  // OrganizationSidebar 不再负责抓取 organizations数据，只负责显示
  // organizations 由 OrganizationHub 页面统一抓取并放入 Context

  const fetchSchools = useCallback(
    async (orgId: string) => {
      try {
        const response = await fetch(`/api/schools?organization_id=${orgId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setSchools((prev) => ({ ...prev, [orgId]: data }));
        }
      } catch (error) {
        console.error("Failed to fetch schools:", error);
      }
    },
    [token, setSchools],
  );

  // 监听 expandedOrgs 变化，自动 fetch schools
  useEffect(() => {
    expandedOrgs.forEach((orgId) => {
      if (!schools[orgId]) {
        fetchSchools(orgId);
      }
    });
  }, [expandedOrgs, schools, fetchSchools]);

  const handleNodeClick = (type: "organization" | "school", data: any) => {
    console.log("🔵 Sidebar: Clicking node", {
      type,
      id: data.id,
      name: data.name,
    });
    setSelectedNode({ type, id: data.id, data });
    console.log("🔵 Sidebar: selectedNode set, navigating...");
    // 導航到 OrganizationHub 頁面
    navigate("/teacher/organizations-hub");
    onNavigate?.();
  };

  if (isCollapsed) {
    return null;
  }

  if (isFetchingOrgs) {
    return (
      <div className="p-4 text-center text-sm text-gray-500">
        {t("common.loading")}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <Accordion
        type="multiple"
        value={expandedOrgs}
        onValueChange={setExpandedOrgs}
        className="space-y-1"
      >
        {organizations.map((org) => (
          <AccordionItem key={org.id} value={org.id} className="border-none">
            <AccordionTrigger
              className={cn(
                "hover:no-underline hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md px-2 py-2",
                selectedNode?.type === "organization" &&
                  selectedNode.id === org.id &&
                  "bg-blue-100 dark:bg-blue-900/40 text-blue-900 dark:text-blue-100",
              )}
            >
              <div
                className="flex items-center gap-2 flex-1"
                onClick={(e) => {
                  e.stopPropagation(); // 防止触发 accordion toggle
                  handleNodeClick("organization", org);
                }}
              >
                <Building2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium truncate">
                  {org.display_name || org.name}
                </span>
              </div>
            </AccordionTrigger>

            <AccordionContent className="pb-0 pt-1">
              <div className="pl-6 space-y-1">
                {schools[org.id]?.map((school) => (
                  <button
                    key={school.id}
                    onClick={() => handleNodeClick("school", school)}
                    className={cn(
                      "w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-left",
                      selectedNode?.type === "school" &&
                        selectedNode.id === school.id &&
                        "bg-green-100 dark:bg-green-900/40 text-green-900 dark:text-green-100",
                    )}
                  >
                    <SchoolIcon className="w-4 h-4 text-green-600 dark:text-green-400" />
                    <span className="text-sm truncate">
                      {school.display_name || school.name}
                    </span>
                  </button>
                ))}

                {schools[org.id]?.length === 0 && (
                  <div className="text-xs text-gray-400 px-2 py-1">
                    {t("organizationHub.noSchools")}
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      {organizations.length === 0 && (
        <div className="p-4 text-center text-sm text-gray-500">
          {t("organizationHub.noOrganizations")}
        </div>
      )}
    </div>
  );
}
