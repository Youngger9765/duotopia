/**
 * Sidebar 分組組件
 */

import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";
import { SidebarGroup as SidebarGroupType } from "@/types/sidebar";
import { SidebarItem } from "./SidebarItem";

interface SidebarGroupProps {
  group: SidebarGroupType;
  isExpanded: boolean;
  isCollapsed: boolean;
  isActive: (path: string) => boolean;
  onToggle: () => void;
  onNavigate?: () => void;
}

export const SidebarGroup = ({
  group,
  isExpanded,
  isCollapsed,
  isActive,
  onToggle,
  onNavigate,
}: SidebarGroupProps) => {
  const GroupIcon = group.icon;
  const hasMultipleItems = group.items.length > 1;

  return (
    <li>
      {/* Group Header */}
      {hasMultipleItems ? (
        <Button
          variant="ghost"
          className={`w-full justify-start h-10 min-h-10 ${isCollapsed ? "px-3" : "px-4"} text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100`}
          onClick={onToggle}
        >
          <GroupIcon className="h-4 w-4" />
          {!isCollapsed && (
            <>
              <span className="ml-2 flex-1 text-left text-sm font-medium">
                {group.label}
              </span>
              {isExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </>
          )}
        </Button>
      ) : null}

      {/* Group Items */}
      {((hasMultipleItems && isExpanded) || !hasMultipleItems) && (
        <ul className={`${hasMultipleItems ? "ml-2 mt-1 space-y-1" : ""}`}>
          {group.items.map((item) => (
            <li key={item.id}>
              <SidebarItem
                item={item}
                isActive={isActive(item.path)}
                isCollapsed={isCollapsed}
                onNavigate={onNavigate}
              />
            </li>
          ))}
        </ul>
      )}
    </li>
  );
};
