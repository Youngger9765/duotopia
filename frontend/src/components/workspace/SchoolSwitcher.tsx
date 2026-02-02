/**
 * SchoolSwitcher - Dropdown to switch between schools (Phase 2)
 *
 * Appears after a school is selected. Allows quick switching
 * between schools without going back to the list.
 */

import React from "react";
import { Check, ChevronsUpDown, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { cn } from "@/lib/utils";

export const SchoolSwitcher: React.FC = () => {
  const { selectedOrganization, selectedSchool, selectSchool } = useWorkspace();

  if (!selectedOrganization || !selectedSchool) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          className="w-full h-14 px-3 py-2 justify-between border-2 border-blue-200 dark:border-blue-700 rounded-lg hover:border-blue-400 dark:hover:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <div className="flex items-center gap-3 flex-1 text-left">
            <Building2 className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <div className="flex flex-col min-w-0">
              {/* Organization Name */}
              <span className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {selectedOrganization.name}
              </span>
              {/* School Name */}
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                {selectedSchool.name}
              </span>
            </div>
          </div>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        className="w-[calc(100%-2rem)] max-h-[300px] overflow-y-auto"
        align="start"
      >
        {selectedOrganization.schools.map((school) => (
          <DropdownMenuItem
            key={school.id}
            onClick={() => selectSchool(school, selectedOrganization)}
            className={cn(
              "py-2.5 px-3 cursor-pointer",
              school.id === selectedSchool.id
                ? "bg-blue-100 dark:bg-blue-900/40"
                : "hover:bg-blue-50 dark:hover:bg-blue-900/20",
            )}
          >
            <div className="flex items-center justify-between w-full">
              <span className="text-sm">{school.name}</span>
              {school.id === selectedSchool.id && (
                <Check className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              )}
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default SchoolSwitcher;
