/**
 * Sidebar 角色管理 Hook
 * 負責獲取用戶角色並過濾可見的 sidebar 分組
 */

import { useEffect, useMemo, useRef } from "react";
import { useShallow } from "zustand/react/shallow";
import { SidebarGroup } from "@/types/sidebar";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";

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
  teacherProfile: TeacherProfile | null,
) => {
  // ✅ 使用 shallow compare 優化 - 只在這些欄位變化時才 re-render
  const { token, userRoles, loading, setUserRoles, setRolesLoading } =
    useTeacherAuthStore(
      useShallow((state) => ({
        token: state.token,
        userRoles: state.userRoles,
        loading: state.rolesLoading,
        setUserRoles: state.setUserRoles,
        setRolesLoading: state.setRolesLoading,
      })),
    );

  // 使用 ref 防止 React 18 Strict Mode 重复执行
  const hasFetchedRef = useRef(false);

  // 只在 token 存在且 userRoles 为空时才抓取（全局只抓取一次）
  useEffect(() => {
    const fetchUserRoles = async () => {
      // 如果没有 token 或已经有 roles 或正在加载或已经抓取过，就跳过
      if (!token || userRoles.length > 0 || loading || hasFetchedRef.current) {
        return;
      }

      // 立即标记，防止并发执行
      hasFetchedRef.current = true;

      try {
        setRolesLoading(true);
        console.log("🔍 [useSidebarRoles] Fetching roles from:", `${API_URL}/api/teachers/me/roles`);
        const response = await fetch(`${API_URL}/api/teachers/me/roles`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          console.log("✅ [useSidebarRoles] Roles received:", data);
          console.log("✅ [useSidebarRoles] all_roles:", data.all_roles);
          setUserRoles(data.all_roles || []);
        } else {
          console.error(
            "❌ [useSidebarRoles] API response not OK:",
            response.status,
          );
          hasFetchedRef.current = false; // 失败时允许重试
        }
      } catch (err) {
        console.error("❌ [useSidebarRoles] Failed to fetch user roles:", err);
        hasFetchedRef.current = false; // 失败时允许重试
      } finally {
        setRolesLoading(false);
      }
    };

    fetchUserRoles();
  }, [token, userRoles.length, loading, setUserRoles, setRolesLoading]);

  // 使用 useMemo 缓存过滤结果，只在依赖变化时重新计算
  const visibleGroups = useMemo(() => {
    const filtered = sidebarGroups
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
          const hasPermission = group.requiredRoles.some((role) =>
            userRoles.includes(role),
          );
          console.log(
            `🔐 [useSidebarRoles] Group "${group.label}": requiredRoles=${group.requiredRoles}, userRoles=${JSON.stringify(userRoles)}, hasPermission=${hasPermission}`,
          );
          return hasPermission;
        }
        return true;
      });

    console.log(
      `📋 [useSidebarRoles] Total groups: ${sidebarGroups.length}, Visible groups: ${filtered.length}`,
    );
    console.log(
      `📋 [useSidebarRoles] Visible group labels:`,
      filtered.map((g) => g.label),
    );

    return filtered;
  }, [sidebarGroups, userRoles, config, teacherProfile]); // 只在这些依赖变化时重新计算

  return { visibleGroups, userRoles, loading };
};
