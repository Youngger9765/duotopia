import { useOrganization } from "@/contexts/OrganizationContext";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Building2, Plus, Settings } from "lucide-react";

interface OrganizationHeaderProps {
  onCreateOrganization?: () => void;
  onCreateSchool?: () => void;
  onSettings?: () => void;
}

/**
 * OrganizationHeader - Header component with organization selector and quick actions
 * Used at the top of organization management pages
 */
export function OrganizationHeader({
  onCreateOrganization,
  onCreateSchool,
  onSettings,
}: OrganizationHeaderProps) {
  const { organizations, selectedNode, setSelectedNode } = useOrganization();

  const handleOrganizationChange = (orgId: string) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) {
      setSelectedNode({ type: "organization", id: org.id, data: org });
    }
  };

  const selectedOrgId =
    selectedNode?.type === "organization" ? selectedNode.id : undefined;

  return (
    <div className="flex items-center justify-between bg-white border-b px-6 py-4">
      {/* Organization Selector */}
      <div className="flex items-center gap-4">
        <Building2 className="h-6 w-6 text-blue-600" />
        <div className="min-w-[250px]">
          {organizations.length > 0 ? (
            <Select
              value={selectedOrgId}
              onValueChange={handleOrganizationChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="選擇組織" />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>
                    {org.display_name || org.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <div className="text-gray-500 text-sm">尚無組織</div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-2">
        {onCreateSchool && selectedOrgId && (
          <Button
            variant="outline"
            size="sm"
            onClick={onCreateSchool}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            新增學校
          </Button>
        )}

        {onCreateOrganization && (
          <Button
            variant="default"
            size="sm"
            onClick={onCreateOrganization}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            新增組織
          </Button>
        )}

        {onSettings && (
          <Button variant="ghost" size="sm" onClick={onSettings}>
            <Settings className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
