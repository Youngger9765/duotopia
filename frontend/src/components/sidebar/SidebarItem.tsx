/**
 * Sidebar 單個項目組件
 */

import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { SidebarItem as SidebarItemType } from "@/types/sidebar";

interface SidebarItemProps {
  item: SidebarItemType;
  isActive: boolean;
  isCollapsed: boolean;
  onNavigate?: () => void;
}

export const SidebarItem = ({
  item,
  isActive,
  isCollapsed,
  onNavigate,
}: SidebarItemProps) => {
  const Icon = item.icon;

  return (
    <Link to={item.path} className="block" onClick={onNavigate}>
      <Button
        variant={isActive ? "default" : "ghost"}
        className={`w-full justify-start h-10 min-h-10 ${isCollapsed ? "px-3" : "px-4"}`}
      >
        <Icon className="h-4 w-4" />
        {!isCollapsed && <span className="ml-2 text-sm">{item.label}</span>}
      </Button>
    </Link>
  );
};
