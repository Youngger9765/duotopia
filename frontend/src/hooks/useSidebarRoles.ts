/**
 * Sidebar 角色管理 Hook
 * 負責獲取用戶角色並過濾可見的 sidebar 分組
 */

import { useState, useEffect } from "react";
import { SidebarGroup } from "@/types/sidebar";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

interface SystemConfig {
  enablePayment: boolean;
  environment: string;
}

interface TeacherProfile {
  is_admin?: boolean;
}

export const useSidebarRoles = (
  sidebarGroups: SidebarGroup[],
  config: SystemConfig | null,
  teacherProfile: TeacherProfile | null
) => {
  const [userRoles, setUserRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const token = useTeacherAuthStore((state) => state.token);

  useEffect(() => {
    fetchUserRoles();
  }, [token]);

  const fetchUserRoles = async () => {
    try {
      // 如果沒有 token，直接返回（可能是未登入或已登出）
      if (!token) {
        console.log("⚠️ [useSidebarRoles] No token found, skipping roles fetch");
        setLoading(false);
        return;
      }

      console.log("🔍 [useSidebarRoles] Fetching roles...");
      const response = await fetch("/api/teachers/me/roles", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        console.log("✅ [useSidebarRoles] Roles received:", data);
        console.log("✅ [useSidebarRoles] all_roles:", data.all_roles);
        setUserRoles(data.all_roles || []);
      } else {
        console.error("❌ [useSidebarRoles] API response not OK:", response.status);
      }
    } catch (err) {
      console.error("❌ [useSidebarRoles] Failed to fetch user roles:", err);
    } finally {
      setLoading(false);
    }
  };

  // 根據用戶角色和系統配置過濾分組
  const visibleGroups = sidebarGroups
    .map((group) => {
      // 過濾組內的項目
      const visibleItems = group.items.filter((item) => {
        // 訂閱選單特殊處理
        if (item.id === "subscription") {
          return config?.enablePayment === true;
        }
        // Admin 選單特殊處理
        if (item.adminOnly) {
          return teacherProfile?.is_admin === true;
        }
        // 檢查是否有角色要求
        if (item.requiredRoles && item.requiredRoles.length > 0) {
          return item.requiredRoles.some((role) => userRoles.includes(role));
        }
        return true;
      });

      return {
        ...group,
        items: visibleItems,
      };
    })
    .filter((group) => {
      // 過濾掉沒有項目的組
      if (group.items.length === 0) {
        return false;
      }
      // 檢查組本身是否有角色要求
      if (group.requiredRoles && group.requiredRoles.length > 0) {
        const hasPermission = group.requiredRoles.some((role) => userRoles.includes(role));
        console.log(
          `🔐 [useSidebarRoles] Group "${group.label}": requiredRoles=${group.requiredRoles}, userRoles=${JSON.stringify(userRoles)}, hasPermission=${hasPermission}`
        );
        return hasPermission;
      }
      return true;
    });

  console.log(`📋 [useSidebarRoles] Total groups: ${sidebarGroups.length}, Visible groups: ${visibleGroups.length}`);
  console.log(`📋 [useSidebarRoles] Visible group labels:`, visibleGroups.map(g => g.label));

  return { visibleGroups, userRoles, loading };
};
