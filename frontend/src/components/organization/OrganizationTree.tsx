import { useEffect, useCallback } from "react";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Building2, School as SchoolIcon, Users } from "lucide-react";
import { cn } from "@/lib/utils";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface SchoolData {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface OrganizationTreeProps {
  onNodeSelect?: (
    type: "organization" | "school",
    data: Organization | SchoolData,
  ) => void;
  className?: string;
}

/**
 * OrganizationTree - Hierarchical tree view of organizations and schools
 * Used in the organization portal dashboard
 */
export function OrganizationTree({
  onNodeSelect,
  className,
}: OrganizationTreeProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const user = useTeacherAuthStore((state) => state.user);
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

  // Check if user is school-level only (cannot click organization nodes)
  const isSchoolLevelUser =
    user?.role === "school_admin" || user?.role === "school_director";

  const fetchSchools = useCallback(
    async (orgId: string) => {
      try {
        const response = await fetch(
          `${API_URL}/api/schools?organization_id=${orgId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
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

  // Auto-fetch schools when organization is expanded
  useEffect(() => {
    expandedOrgs.forEach((orgId) => {
      if (!schools[orgId]) {
        fetchSchools(orgId);
      }
    });
  }, [expandedOrgs, schools, fetchSchools]);

  const handleNodeClick = (
    type: "organization" | "school",
    data: Organization | SchoolData,
  ) => {
    // School-level users cannot click organization nodes
    if (type === "organization" && isSchoolLevelUser) {
      return;
    }

    setSelectedNode({ type, id: data.id, data });
    onNodeSelect?.(type, data);
  };

  if (isFetchingOrgs) {
    return (
      <div className={cn("p-8 text-center", className)}>
        <div className="text-gray-500">載入組織架構中...</div>
      </div>
    );
  }

  if (organizations.length === 0) {
    return (
      <div className={cn("p-8 text-center", className)}>
        <Building2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p className="text-gray-500 mb-2">尚無組織資料</p>
        <p className="text-sm text-gray-400">請聯繫系統管理員建立組織</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      <Accordion
        type="multiple"
        value={expandedOrgs}
        onValueChange={setExpandedOrgs}
        className="space-y-2"
      >
        {organizations.map((org) => (
          <AccordionItem
            key={org.id}
            value={org.id}
            className="border rounded-lg bg-white shadow-sm"
          >
            <AccordionTrigger
              className={cn(
                "hover:no-underline rounded-t-lg px-4 py-3 transition-colors",
                isSchoolLevelUser
                  ? "cursor-default opacity-60"
                  : "hover:bg-blue-50 cursor-pointer",
                !isSchoolLevelUser &&
                  selectedNode?.type === "organization" &&
                  selectedNode.id === org.id &&
                  "bg-blue-100 text-blue-900",
              )}
              onClick={() => handleNodeClick("organization", org)}
            >
              <div className="flex items-center gap-3 flex-1">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Building2 className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-semibold text-base">
                    {org.display_name || org.name}
                  </div>
                  {org.description && (
                    <div className="text-sm text-gray-500 mt-1">
                      {org.description}
                    </div>
                  )}
                </div>
              </div>
            </AccordionTrigger>

            <AccordionContent className="px-4 pb-3">
              <div className="space-y-1 mt-2">
                {schools[org.id]?.map((school) => (
                  <button
                    key={school.id}
                    onClick={() => handleNodeClick("school", school)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-green-50 text-left transition-colors border border-transparent",
                      selectedNode?.type === "school" &&
                        selectedNode.id === school.id &&
                        "bg-green-100 border-green-300 text-green-900",
                    )}
                  >
                    <div className="p-1.5 bg-green-100 rounded">
                      <SchoolIcon className="w-4 h-4 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-sm">
                        {school.display_name || school.name}
                      </div>
                      {school.description && (
                        <div className="text-xs text-gray-500 mt-0.5">
                          {school.description}
                        </div>
                      )}
                    </div>
                    <Users className="w-4 h-4 text-gray-400" />
                  </button>
                ))}

                {schools[org.id]?.length === 0 && (
                  <div className="text-sm text-gray-400 px-3 py-4 text-center bg-gray-50 rounded-lg">
                    此組織尚無學校
                  </div>
                )}

                {!schools[org.id] && (
                  <div className="text-sm text-gray-400 px-3 py-4 text-center">
                    載入學校資料中...
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
