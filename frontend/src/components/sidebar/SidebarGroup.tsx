/**
 * Sidebar 分組組件
 */

import { SidebarGroup as SidebarGroupType } from "@/types/sidebar";
import { SidebarItem } from "./SidebarItem";

interface SidebarGroupProps {
  group: SidebarGroupType;
  isCollapsed: boolean;
  isActive: (path: string) => boolean;
  readOnlyItemIds?: string[];
  onNavigate?: () => void;
}

export const SidebarGroup = ({
  group,
  isCollapsed,
  isActive,
  readOnlyItemIds = [],
  onNavigate,
}: SidebarGroupProps) => {
  return (
    <li>
      {/* Group Items - No header, direct display */}
      <ul className="space-y-1">
        {group.items.map((item) => (
          <li key={item.id}>
            <SidebarItem
              item={item}
              isActive={isActive(item.path)}
              isCollapsed={isCollapsed}
              isReadOnly={readOnlyItemIds.includes(item.id)}
              onNavigate={onNavigate}
            />
          </li>
        ))}
      </ul>
    </li>
  );
};
