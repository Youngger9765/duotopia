import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { PermissionManager, TeacherPermissions } from "@/lib/permissions";
import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PermissionCheckboxProps {
  permission: keyof TeacherPermissions;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  showDescription?: boolean;
}

/**
 * Permission toggle component with label and description
 */
export function PermissionCheckbox({
  permission,
  checked,
  onCheckedChange,
  disabled = false,
  showDescription = true,
}: PermissionCheckboxProps) {
  const description = PermissionManager.getPermissionDescription(permission);

  // Format permission name for display
  const formatPermissionName = (perm: string): string => {
    return perm
      .replace(/_/g, " ")
      .replace(/^can /, "")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const displayName = formatPermissionName(permission);

  return (
    <div className="flex items-center space-x-2">
      <Checkbox
        id={permission}
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
      />
      <div className="flex-1">
        <Label
          htmlFor={permission}
          className={`text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 ${disabled ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
        >
          {displayName}
        </Label>
      </div>
      {showDescription && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-4 w-4 text-gray-400 cursor-help" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-sm">{description}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
}
