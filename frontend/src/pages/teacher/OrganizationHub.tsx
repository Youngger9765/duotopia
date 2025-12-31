/**
 * 組織管理中心 - 內容區域
 * 配合 TeacherLayout sidebar 使用
 */

import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Building2, School, Settings, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import TeacherLayout from "@/components/TeacherLayout";

interface Teacher {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

interface Classroom {
  id: string;
  name: string;
  program_level: string;
  is_active: boolean;
  created_at: string;
  teacher_name?: string;
  teacher_email?: string;
  student_count: number;
  assignment_count: number;
}

interface SchoolWithAdmin {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
  admin_name?: string;
  admin_email?: string;
  classroom_count: number;
  teacher_count: number;
  student_count: number;
}

function OrganizationHubContent() {
  const { t } = useTranslation();
  const token = useTeacherAuthStore((state) => state.token);
  const userRoles = useTeacherAuthStore((state) => state.userRoles);
  const {
    selectedNode,
    setSelectedNode,
    organizations,
    setOrganizations,
    isFetchingOrgs,
    setIsFetchingOrgs,
    setExpandedOrgs,
  } = useOrganization();

  const [statsLoading, setStatsLoading] = useState(false);
  const [orgSchools, setOrgSchools] = useState<SchoolWithAdmin[]>([]);
  const [schoolTeachers, setSchoolTeachers] = useState<Teacher[]>([]);
  const [schoolClassrooms, setSchoolClassrooms] = useState<Classroom[]>([]);
  const [isLoadingSchoolDetails, setIsLoadingSchoolDetails] = useState(false);

  // 编辑机构 Dialog 状态
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    display_name: "",
    description: "",
    contact_email: "",
  });
  const [isSaving, setIsSaving] = useState(false);

  // 检查是否有管理权限（org_owner 或 org_admin）
  const hasManagementPermission =
    userRoles.includes("org_owner") || userRoles.includes("org_admin");

  // 使用 ref 防止 React 18 Strict Mode 的重复执行
  const hasFetchedRef = useRef(false);

  // 页面加载时统一抓取 organizations
  useEffect(() => {
    const fetchOrganizations = async () => {
      // 检查 token 是否存在
      if (!token) {
        console.log("🔴 OrganizationHub: No token available yet");
        return;
      }

      // 立即检查 ref，防止 race condition
      if (hasFetchedRef.current || isFetchingOrgs || organizations.length > 0) {
        console.log(
          "🔴 OrganizationHub: Skipping fetch (already have data or fetching)",
        );
        return;
      }

      // 立即标记，防止其他并发的 useEffect
      hasFetchedRef.current = true;

      try {
        setIsFetchingOrgs(true);
        console.log("🔴 OrganizationHub: Fetching organizations...");
        const response = await fetch(`${API_URL}/api/organizations`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          console.log(
            "🔴 OrganizationHub: Fetched organizations:",
            data.length,
            data,
          );
          setOrganizations(data);
          // 自动展开第一个机构
          if (data.length > 0) {
            setExpandedOrgs([data[0].id]);
          }
        } else {
          console.error(
            "🔴 OrganizationHub: Failed to fetch organizations, status:",
            response.status,
          );
          hasFetchedRef.current = false; // 失败时允许重试
        }
      } catch (error) {
        console.error("Failed to fetch organizations:", error);
        hasFetchedRef.current = false; // 失败时允许重试
      } finally {
        setIsFetchingOrgs(false);
      }
    };

    fetchOrganizations();
  }, [token, organizations.length, isFetchingOrgs]); // 当 token 可用时执行

  // 自动选中第一个组织
  useEffect(() => {
    console.log("🟡 OrganizationHub: organizations changed", {
      count: organizations.length,
      hasSelectedNode: !!selectedNode,
    });
    if (!selectedNode && organizations.length > 0) {
      console.log(
        "🟢 OrganizationHub: Auto-selecting first organization:",
        organizations[0],
      );
      setSelectedNode({
        type: "organization",
        id: organizations[0].id,
        data: organizations[0],
      });
    }
  }, [organizations]);

  useEffect(() => {
    console.log("🟣 OrganizationHub: selectedNode changed", selectedNode);
    if (selectedNode) {
      fetchNodeStats(selectedNode.type, selectedNode.id);
      if (selectedNode.type === "school") {
        fetchSchoolDetails(selectedNode.id);
        setOrgSchools([]);
      } else {
        setSchoolTeachers([]);
        setSchoolClassrooms([]);
      }
    }
  }, [selectedNode]);

  const fetchNodeStats = async (
    type: "organization" | "school",
    id: string,
  ) => {
    try {
      setStatsLoading(true);

      if (type === "organization") {
        const schoolsRes = await fetch(`${API_URL}/api/schools?organization_id=${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (schoolsRes.ok) {
          const schoolsData = await schoolsRes.json();
          setOrgSchools(schoolsData);
        }
      }
    } catch (error) {
      console.error("Failed to fetch node stats:", error);
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchSchoolDetails = async (schoolId: string) => {
    try {
      setIsLoadingSchoolDetails(true);
      const [teachersRes, classroomsRes] = await Promise.all([
        fetch(`${API_URL}/api/schools/${schoolId}/teachers`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/schools/${schoolId}/classrooms`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (teachersRes.ok) {
        const teachersData = await teachersRes.json();
        setSchoolTeachers(teachersData);
      }

      if (classroomsRes.ok) {
        const classroomsData = await classroomsRes.json();
        setSchoolClassrooms(classroomsData);
      }
    } catch (error) {
      console.error("Failed to fetch school details:", error);
    } finally {
      setIsLoadingSchoolDetails(false);
    }
  };

  const handleSchoolClick = (school: SchoolWithAdmin) => {
    setSelectedNode({
      type: "school",
      id: school.id,
      data: school,
    });
  };

  const handleEditClick = () => {
    if (!selectedNode) return;

    // 初始化表單資料
    setEditFormData({
      display_name: selectedNode.data.display_name || "",
      description: selectedNode.data.description || "",
      contact_email: selectedNode.data.contact_email || "",
    });
    setIsEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedNode) return;

    try {
      setIsSaving(true);

      // 呼叫 API 更新機構
      await apiClient.put(
        `/api/organizations/${selectedNode.id}`,
        editFormData,
      );

      // 更新 Context 中的資料
      setOrganizations((prev) =>
        prev.map((org) =>
          org.id === selectedNode.id ? { ...org, ...editFormData } : org,
        ),
      );

      // 更新 selectedNode
      setSelectedNode({
        ...selectedNode,
        data: { ...selectedNode.data, ...editFormData },
      });

      toast.success(t("organizationHub.editSuccess"));
      setIsEditDialogOpen(false);
    } catch (error) {
      console.error("Failed to update organization:", error);
      toast.error(t("organizationHub.editError"));
    } finally {
      setIsSaving(false);
    }
  };

  return selectedNode ? (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div className="flex items-start gap-3 flex-1">
          {selectedNode.type === "organization" ? (
            <Building2 className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
          ) : (
            <School className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
          )}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold truncate">
                {selectedNode.data.display_name || selectedNode.data.name}
              </h1>
              <span
                className={cn(
                  "px-2 py-1 rounded-md text-xs font-medium whitespace-nowrap flex-shrink-0",
                  selectedNode.type === "organization"
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                    : "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
                )}
              >
                {selectedNode.type === "organization"
                  ? t("organizationHub.organization")
                  : t("organizationHub.school")}
              </span>
            </div>
            {selectedNode.data.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {selectedNode.data.description}
              </p>
            )}
          </div>
        </div>
        {hasManagementPermission ? (
          <Button
            variant="outline"
            size="sm"
            className="flex-shrink-0"
            onClick={handleEditClick}
          >
            <Settings className="w-4 h-4 sm:mr-2" />
            <span className="hidden sm:inline">
              {t("organizationHub.edit")}
            </span>
          </Button>
        ) : null}
      </div>

      {/* 基本資訊 - 可收合 */}
      <Accordion type="single" collapsible className="mb-6">
        <AccordionItem
          value="info"
          className="border rounded-lg px-4 bg-white dark:bg-gray-800"
        >
          <AccordionTrigger className="hover:no-underline">
            <h3 className="text-lg font-semibold">
              {t("organizationHub.info.title")}
            </h3>
          </AccordionTrigger>
          <AccordionContent className="pt-4 pb-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {t("organizationHub.info.name")}
                </label>
                <p className="mt-1">{selectedNode.data.name}</p>
              </div>

              {selectedNode.data.display_name && (
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {t("organizationHub.info.displayName")}
                  </label>
                  <p className="mt-1">{selectedNode.data.display_name}</p>
                </div>
              )}

              {selectedNode.data.contact_email && (
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {t("organizationHub.info.contactEmail")}
                  </label>
                  <p className="mt-1">{selectedNode.data.contact_email}</p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {t("organizationHub.info.createdAt")}
                </label>
                <p className="mt-1">
                  {new Date(selectedNode.data.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* 學校列表 (機構) / 班級教師管理 Tabs (學校) */}
      {selectedNode.type === "organization" ? (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{t("organizationHub.schools")}</CardTitle>
              {hasManagementPermission && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button size="sm" disabled>
                        <Plus className="w-4 h-4 mr-2" />
                        {t("organizationHub.addSchool")}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{t("common.comingSoon")}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="text-center py-8 text-gray-500">
                {t("common.loading")}
              </div>
            ) : orgSchools.length > 0 ? (
              <div className="overflow-x-auto -mx-6 sm:mx-0">
                <div className="inline-block min-w-full align-middle">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="whitespace-nowrap">
                          {t("organizationHub.table.schoolName")}
                        </TableHead>
                        <TableHead className="whitespace-nowrap">
                          {t("organizationHub.table.admin")}
                        </TableHead>
                        <TableHead className="hidden md:table-cell whitespace-nowrap">
                          {t("organizationHub.table.contactEmail")}
                        </TableHead>
                        <TableHead className="text-center whitespace-nowrap">
                          {t("organizationHub.table.classroomCount")}
                        </TableHead>
                        <TableHead className="text-center whitespace-nowrap">
                          {t("organizationHub.table.teacherCount")}
                        </TableHead>
                        <TableHead className="text-center whitespace-nowrap">
                          {t("organizationHub.table.studentCount")}
                        </TableHead>
                        <TableHead className="whitespace-nowrap">
                          {t("organizationHub.table.status")}
                        </TableHead>
                        <TableHead className="hidden lg:table-cell whitespace-nowrap">
                          {t("organizationHub.table.createdAt")}
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {orgSchools.map((school) => (
                        <TableRow
                          key={school.id}
                          className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                          onClick={() => handleSchoolClick(school)}
                        >
                          <TableCell className="font-medium text-blue-600 dark:text-blue-400 whitespace-nowrap">
                            {school.display_name || school.name}
                          </TableCell>
                          <TableCell className="whitespace-nowrap">
                            {school.admin_name ? (
                              <div>
                                <div className="font-medium">
                                  {school.admin_name}
                                </div>
                                {school.admin_email && (
                                  <div className="text-xs text-gray-500 truncate max-w-[150px]">
                                    {school.admin_email}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </TableCell>
                          <TableCell className="hidden md:table-cell">
                            <span className="truncate block max-w-[200px]">
                              {school.contact_email || "-"}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-sm font-medium">
                              {school.classroom_count}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="px-2 py-1 rounded-md bg-purple-50 text-purple-700 text-sm font-medium">
                              {school.teacher_count}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="px-2 py-1 rounded-md bg-green-50 text-green-700 text-sm font-medium">
                              {school.student_count}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span
                              className={cn(
                                "px-2 py-1 rounded-full text-xs whitespace-nowrap",
                                school.is_active
                                  ? "bg-green-100 text-green-700"
                                  : "bg-gray-100 text-gray-700",
                              )}
                            >
                              {school.is_active
                                ? t("common.active")
                                : t("common.inactive")}
                            </span>
                          </TableCell>
                          <TableCell className="hidden lg:table-cell whitespace-nowrap">
                            {new Date(school.created_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {t("organizationHub.noSchools")}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="classrooms">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="classrooms">
              {t("organizationHub.tabs.classrooms")}
            </TabsTrigger>
            <TabsTrigger value="teachers">
              {t("organizationHub.tabs.teachers")}
            </TabsTrigger>
          </TabsList>

          {/* 班級列表 */}
          <TabsContent value="classrooms" className="mt-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{t("organizationHub.tabs.classrooms")}</CardTitle>
                  {hasManagementPermission && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button size="sm" disabled>
                            <Plus className="w-4 h-4 mr-2" />
                            {t("organizationHub.addClassroom")}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{t("common.comingSoon")}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingSchoolDetails ? (
                  <div className="text-center py-8 text-gray-500">
                    {t("common.loading")}
                  </div>
                ) : schoolClassrooms.length > 0 ? (
                  <div className="overflow-x-auto -mx-6 sm:mx-0">
                    <div className="inline-block min-w-full align-middle">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.classroomName")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.teacher")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.level")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap text-center">
                              {t("organizationHub.table.studentCount")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap text-center">
                              {t("organizationHub.table.assignmentCount")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.status")}
                            </TableHead>
                            <TableHead className="hidden lg:table-cell whitespace-nowrap">
                              {t("organizationHub.table.createdAt")}
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {schoolClassrooms.map((classroom) => (
                            <TableRow key={classroom.id}>
                              <TableCell className="font-medium">
                                {classroom.name}
                              </TableCell>
                              <TableCell className="whitespace-nowrap">
                                {classroom.teacher_name ? (
                                  <div>
                                    <div className="font-medium">
                                      {classroom.teacher_name}
                                    </div>
                                    {classroom.teacher_email && (
                                      <div className="text-xs text-gray-500 truncate max-w-[150px]">
                                        {classroom.teacher_email}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </TableCell>
                              <TableCell className="whitespace-nowrap">
                                {classroom.program_level}
                              </TableCell>
                              <TableCell className="text-center">
                                <span className="px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-sm font-medium">
                                  {classroom.student_count}
                                </span>
                              </TableCell>
                              <TableCell className="text-center">
                                <span className="px-2 py-1 rounded-md bg-purple-50 text-purple-700 text-sm font-medium">
                                  {classroom.assignment_count}
                                </span>
                              </TableCell>
                              <TableCell>
                                <span
                                  className={cn(
                                    "px-2 py-1 rounded-full text-xs whitespace-nowrap",
                                    classroom.is_active
                                      ? "bg-green-100 text-green-700"
                                      : "bg-gray-100 text-gray-700",
                                  )}
                                >
                                  {classroom.is_active
                                    ? t("common.active")
                                    : t("common.inactive")}
                                </span>
                              </TableCell>
                              <TableCell className="hidden lg:table-cell whitespace-nowrap">
                                {new Date(
                                  classroom.created_at,
                                ).toLocaleDateString()}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    {t("organizationHub.noClassrooms")}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 教師列表 */}
          <TabsContent value="teachers" className="mt-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{t("organizationHub.tabs.teachers")}</CardTitle>
                  {hasManagementPermission && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button size="sm" disabled>
                            <Plus className="w-4 h-4 mr-2" />
                            {t("organizationHub.addTeacher")}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{t("common.comingSoon")}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingSchoolDetails ? (
                  <div className="text-center py-8 text-gray-500">
                    {t("common.loading")}
                  </div>
                ) : schoolTeachers.length > 0 ? (
                  <div className="overflow-x-auto -mx-6 sm:mx-0">
                    <div className="inline-block min-w-full align-middle">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.teacherName")}
                            </TableHead>
                            <TableHead className="hidden sm:table-cell whitespace-nowrap">
                              {t("organizationHub.table.email")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.role")}
                            </TableHead>
                            <TableHead className="whitespace-nowrap">
                              {t("organizationHub.table.status")}
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {schoolTeachers.map((teacher) => (
                            <TableRow key={teacher.id}>
                              <TableCell className="font-medium">
                                <div>
                                  <div className="whitespace-nowrap">
                                    {teacher.name}
                                  </div>
                                  <div className="text-xs text-gray-500 truncate max-w-[150px] sm:hidden">
                                    {teacher.email}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell className="hidden sm:table-cell">
                                <span className="truncate block max-w-[200px]">
                                  {teacher.email}
                                </span>
                              </TableCell>
                              <TableCell>
                                <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700 whitespace-nowrap">
                                  {teacher.role}
                                </span>
                              </TableCell>
                              <TableCell>
                                <span
                                  className={cn(
                                    "px-2 py-1 rounded-full text-xs whitespace-nowrap",
                                    teacher.is_active
                                      ? "bg-green-100 text-green-700"
                                      : "bg-gray-100 text-gray-700",
                                  )}
                                >
                                  {teacher.is_active
                                    ? t("common.active")
                                    : t("common.inactive")}
                                </span>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    {t("organizationHub.noTeachers")}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* 編輯機構 Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{t("organizationHub.editOrganization")}</DialogTitle>
            <DialogDescription>
              {t("organizationHub.editOrganizationDescription")}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="display_name">
                {t("organizationHub.info.displayName")}
              </Label>
              <Input
                id="display_name"
                value={editFormData.display_name}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    display_name: e.target.value,
                  })
                }
                placeholder={t("organizationHub.displayNamePlaceholder")}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">
                {t("organizationHub.info.description")}
              </Label>
              <Textarea
                id="description"
                value={editFormData.description}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    description: e.target.value,
                  })
                }
                placeholder={t("organizationHub.descriptionPlaceholder")}
                rows={3}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="contact_email">
                {t("organizationHub.info.contactEmail")}
              </Label>
              <Input
                id="contact_email"
                type="email"
                value={editFormData.contact_email}
                onChange={(e) =>
                  setEditFormData({
                    ...editFormData,
                    contact_email: e.target.value,
                  })
                }
                placeholder={t("organizationHub.contactEmailPlaceholder")}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsEditDialogOpen(false)}
              disabled={isSaving}
            >
              {t("common.cancel")}
            </Button>
            <Button onClick={handleSaveEdit} disabled={isSaving}>
              {isSaving ? t("common.saving") : t("common.save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  ) : (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)] p-4">
      <div className="text-center text-gray-400">
        <Building2 className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <p className="text-base sm:text-lg">
          {t("organizationHub.selectPrompt")}
        </p>
      </div>
    </div>
  );
}

export default function OrganizationHub() {
  return (
    <TeacherLayout>
      <OrganizationHubContent />
    </TeacherLayout>
  );
}
