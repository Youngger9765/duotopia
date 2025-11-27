/**
 * Sidebar 配置 - 定義所有選單分組和項目
 */

import {
  Home,
  Building2,
  School,
  GraduationCap,
  Users,
  BookOpen,
} from "lucide-react";
import { SidebarGroup } from "@/types/sidebar";

export const getSidebarGroups = (t: (key: string) => string): SidebarGroup[] => [
  // 🏢 機構管理 (org_owner, org_admin)
  {
    id: "organization-management",
    label: "機構管理",
    icon: Building2,
    requiredRoles: ["org_owner", "org_admin"],
    items: [
      {
        id: "organizations",
        label: "機構列表",
        icon: Building2,
        path: "/teacher/organizations",
      },
    ],
  },
  // 🏫 學校管理 (org_owner, org_admin, school_admin)
  {
    id: "school-management",
    label: "學校管理",
    icon: School,
    requiredRoles: ["org_owner", "org_admin", "school_admin"],
    items: [
      {
        id: "schools",
        label: "學校資訊",
        icon: School,
        path: "/teacher/schools",
      },
    ],
  },
  // 👥 班生課管理 (所有教師) - 包含儀表板
  {
    id: "class-management",
    label: "班生課管理",
    icon: GraduationCap,
    items: [
      {
        id: "dashboard",
        label: t("teacherLayout.nav.dashboard"),
        icon: Home,
        path: "/teacher/dashboard",
      },
      {
        id: "classrooms",
        label: t("teacherLayout.nav.myClassrooms"),
        icon: GraduationCap,
        path: "/teacher/classrooms",
      },
      {
        id: "students",
        label: t("teacherLayout.nav.allStudents"),
        icon: Users,
        path: "/teacher/students",
      },
      {
        id: "programs",
        label: t("teacherLayout.nav.publicPrograms"),
        icon: BookOpen,
        path: "/teacher/programs",
      },
    ],
  },
];
