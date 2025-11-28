/**
 * 統一組織管理中心 - Notion Style 側邊欄
 * 整合機構管理和學校管理
 */

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Building2,
  School,
  Search,
  Plus,
  Settings,
  Menu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import TeacherLayout from "@/components/TeacherLayout";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface SchoolData {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

type NodeType = "organization" | "school";

interface SelectedNode {
  type: NodeType;
  id: string;
  data: Organization | SchoolData;
}

interface NodeStats {
  schoolCount?: number;
  teacherCount?: number;
  studentCount?: number;
  classroomCount?: number;
}

interface SchoolFormData {
  name: string;
  display_name: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  address: string;
}

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
}

export default function OrganizationHub() {
  const { t } = useTranslation();
  const token = useTeacherAuthStore((state) => state.token);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [schools, setSchools] = useState<Record<string, SchoolData[]>>({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [nodeStats, setNodeStats] = useState<NodeStats>({});
  const [statsLoading, setStatsLoading] = useState(false);
  const [expandedOrgs, setExpandedOrgs] = useState<string[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // 新增學校相關 state
  const [isAddSchoolDialogOpen, setIsAddSchoolDialogOpen] = useState(false);
  const [selectedOrgForNewSchool, setSelectedOrgForNewSchool] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [schoolFormData, setSchoolFormData] = useState<SchoolFormData>({
    name: "",
    display_name: "",
    description: "",
    contact_email: "",
    contact_phone: "",
    address: "",
  });

  // 學校詳細資料 state
  const [schoolTeachers, setSchoolTeachers] = useState<Teacher[]>([]);
  const [schoolClassrooms, setSchoolClassrooms] = useState<Classroom[]>([]);
  const [isLoadingSchoolDetails, setIsLoadingSchoolDetails] = useState(false);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/organizations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setOrganizations(data);
        // 自動展開第一個機構
        if (data.length > 0) {
          setExpandedOrgs([data[0].id]);
          fetchSchools(data[0].id);
        }
      }
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSchools = async (orgId: string) => {
    try {
      const response = await fetch(`/api/schools?organization_id=${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSchools((prev) => ({ ...prev, [orgId]: data }));
      }
    } catch (error) {
      console.error("Failed to fetch schools:", error);
    }
  };

  const fetchNodeStats = async (type: NodeType, id: string) => {
    try {
      setStatsLoading(true);

      if (type === "organization") {
        // Fetch organization stats
        const [schoolsRes, teachersRes] = await Promise.all([
          fetch(`/api/schools?organization_id=${id}`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`/api/organizations/${id}/teachers`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        let schoolCount = 0;
        let teacherCount = 0;
        let studentCount = 0;

        if (schoolsRes.ok) {
          const schoolsData = await schoolsRes.json();
          schoolCount = schoolsData.length;
        }

        if (teachersRes.ok) {
          const teachersData = await teachersRes.json();
          teacherCount = teachersData.length;
        }

        // TODO: Fetch total student count across all classrooms
        setNodeStats({
          schoolCount,
          teacherCount,
          studentCount,
        });
      } else if (type === "school") {
        // Fetch school stats
        const [teachersRes, classroomsRes] = await Promise.all([
          fetch(`/api/schools/${id}/teachers`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`/api/classrooms?school_id=${id}`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        let teacherCount = 0;
        let classroomCount = 0;
        let studentCount = 0;

        if (teachersRes.ok) {
          const teachersData = await teachersRes.json();
          teacherCount = teachersData.length;
        }

        if (classroomsRes.ok) {
          const classroomsData = await classroomsRes.json();
          classroomCount = classroomsData.length;

          // Fetch student count for each classroom
          const studentCounts = await Promise.all(
            classroomsData.map(async (classroom: any) => {
              try {
                const res = await fetch(`/api/classrooms/${classroom.id}/students`, {
                  headers: { Authorization: `Bearer ${token}` },
                });
                if (res.ok) {
                  const students = await res.json();
                  return students.length;
                }
                return 0;
              } catch {
                return 0;
              }
            })
          );

          studentCount = studentCounts.reduce((sum, count) => sum + count, 0);
        }

        setNodeStats({
          teacherCount,
          classroomCount,
          studentCount,
        });
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
        fetch(`/api/schools/${schoolId}/teachers`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`/api/classrooms?school_id=${schoolId}`, {
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

  const handleNodeClick = (type: NodeType, data: Organization | SchoolData) => {
    setSelectedNode({ type, id: data.id, data });
    fetchNodeStats(type, data.id);

    // 如果是學校節點，載入詳細資料
    if (type === "school") {
      fetchSchoolDetails(data.id);
    } else {
      // 清空學校詳細資料
      setSchoolTeachers([]);
      setSchoolClassrooms([]);
    }

    // Close sidebar on mobile after selection
    setIsSidebarOpen(false);
  };

  const handleOrgExpand = (orgId: string) => {
    if (!schools[orgId]) {
      fetchSchools(orgId);
    }
  };

  const handleAddSchoolClick = (orgId: string) => {
    setSelectedOrgForNewSchool(orgId);
    setSchoolFormData({
      name: "",
      display_name: "",
      description: "",
      contact_email: "",
      contact_phone: "",
      address: "",
    });
    setIsAddSchoolDialogOpen(true);
  };

  const handleSchoolFormChange = (
    field: keyof SchoolFormData,
    value: string
  ) => {
    setSchoolFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmitNewSchool = async () => {
    if (!selectedOrgForNewSchool || !schoolFormData.name) {
      return;
    }

    try {
      setIsSubmitting(true);
      const response = await fetch("/api/schools", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          organization_id: selectedOrgForNewSchool,
          ...schoolFormData,
        }),
      });

      if (response.ok) {
        // 重新載入該機構的學校列表
        await fetchSchools(selectedOrgForNewSchool);
        setIsAddSchoolDialogOpen(false);
        setSchoolFormData({
          name: "",
          display_name: "",
          description: "",
          contact_email: "",
          contact_phone: "",
          address: "",
        });
      } else {
        const error = await response.json();
        alert(`新增學校失敗: ${error.detail || "未知錯誤"}`);
      }
    } catch (error) {
      console.error("Failed to create school:", error);
      alert("新增學校時發生錯誤");
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredOrganizations = organizations.filter((org) =>
    (org.display_name || org.name).toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-gray-500">{t("common.loading")}</div>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="flex h-[calc(100vh-4rem)] bg-gray-50 relative">
      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* 左側 Notion-style 側邊欄 */}
      <aside className={cn(
        "w-64 bg-white border-r border-gray-200 flex flex-col",
        "fixed lg:static inset-y-0 left-0 z-50 transform transition-transform duration-300",
        "lg:translate-x-0",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-3 lg:hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </Button>
            <span className="font-semibold">{t("organizationHub.title")}</span>
          </div>

          {/* 搜尋框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              type="text"
              placeholder={t("organizationHub.search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-gray-50"
            />
          </div>
        </div>

        {/* 組織樹狀列表 */}
        <ScrollArea className="flex-1">
          <div className="p-2">
            <Accordion
              type="multiple"
              value={expandedOrgs}
              onValueChange={setExpandedOrgs}
              className="space-y-1"
            >
              {filteredOrganizations.map((org) => (
                <AccordionItem
                  key={org.id}
                  value={org.id}
                  className="border-none"
                >
                  <AccordionTrigger
                    onClick={() => {
                      handleOrgExpand(org.id);
                      handleNodeClick("organization", org);
                    }}
                    className={cn(
                      "hover:no-underline hover:bg-gray-100 rounded-md px-2 py-2",
                      selectedNode?.type === "organization" &&
                        selectedNode.id === org.id &&
                        "bg-blue-50"
                    )}
                  >
                    <div className="flex items-center gap-2 flex-1">
                      <Building2 className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium truncate">
                        {org.display_name || org.name}
                      </span>
                    </div>
                  </AccordionTrigger>

                  <AccordionContent className="pb-0 pt-1">
                    <div className="pl-6 space-y-1">
                      {schools[org.id]?.map((school) => (
                        <button
                          key={school.id}
                          onClick={() => handleNodeClick("school", school)}
                          className={cn(
                            "w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-gray-100 text-left",
                            selectedNode?.type === "school" &&
                              selectedNode.id === school.id &&
                              "bg-blue-50"
                          )}
                        >
                          <School className="w-4 h-4 text-green-600" />
                          <span className="text-sm truncate">
                            {school.display_name || school.name}
                          </span>
                        </button>
                      ))}

                      {schools[org.id]?.length === 0 && (
                        <div className="text-xs text-gray-400 px-2 py-1">
                          {t("organizationHub.noSchools")}
                        </div>
                      )}

                      {/* 新增學校按鈕 */}
                      <button
                        onClick={() => handleAddSchoolClick(org.id)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-gray-100 text-left text-gray-500 hover:text-gray-700"
                      >
                        <Plus className="w-4 h-4" />
                        <span className="text-sm">{t("organizationHub.addSchool")}</span>
                      </button>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </ScrollArea>

        {/* 新增按鈕 */}
        <div className="p-4 border-t border-gray-200">
          <Button variant="outline" size="sm" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            {t("organizationHub.addOrganization")}
          </Button>
        </div>
      </aside>

      {/* 右側主要內容區 */}
      <main className="flex-1 overflow-auto">
        {selectedNode ? (
          <div className="p-4 md:p-8 max-w-5xl mx-auto">
            {/* Mobile Menu Button */}
            <Button
              variant="outline"
              size="sm"
              className="lg:hidden mb-4"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="w-4 h-4 mr-2" />
              {t("organizationHub.menu")}
            </Button>

            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div className="flex items-center gap-3 flex-1">
                {selectedNode.type === "organization" ? (
                  <Building2 className="w-6 h-6 text-blue-600 flex-shrink-0" />
                ) : (
                  <School className="w-6 h-6 text-green-600 flex-shrink-0" />
                )}
                <div className="min-w-0">
                  <h1 className="text-xl sm:text-2xl font-bold truncate">
                    {selectedNode.data.display_name || selectedNode.data.name}
                  </h1>
                  <p className="text-sm text-gray-500">
                    {selectedNode.type === "organization"
                      ? t("organizationHub.organization")
                      : t("organizationHub.school")}
                  </p>
                </div>
              </div>
              <Button variant="outline" size="sm" className="flex-shrink-0">
                <Settings className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">{t("organizationHub.edit")}</span>
              </Button>
            </div>

            {/* 統計卡片 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {selectedNode.type === "organization" ? (
                <>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {t("organizationHub.stats.schoolCount")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : nodeStats.schoolCount || 0}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {t("organizationHub.stats.teacherCount")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : nodeStats.teacherCount || 0}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {t("organizationHub.stats.studentCount")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : nodeStats.studentCount || 0}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {t("organizationHub.stats.teacherCount")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : nodeStats.teacherCount || 0}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {t("organizationHub.stats.classroomCount")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : nodeStats.classroomCount || 0}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {t("organizationHub.stats.studentCount")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {statsLoading ? "..." : nodeStats.studentCount || 0}
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </div>

            {/* 詳細資訊 */}
            <Card>
              <CardHeader>
                <CardTitle>{t("organizationHub.info.title")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">
                    {t("organizationHub.info.name")}
                  </label>
                  <p className="mt-1">{selectedNode.data.name}</p>
                </div>

                {selectedNode.data.display_name && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      {t("organizationHub.info.displayName")}
                    </label>
                    <p className="mt-1">{selectedNode.data.display_name}</p>
                  </div>
                )}

                {selectedNode.data.description && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      {t("organizationHub.info.description")}
                    </label>
                    <p className="mt-1">{selectedNode.data.description}</p>
                  </div>
                )}

                {selectedNode.data.contact_email && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">
                      {t("organizationHub.info.contactEmail")}
                    </label>
                    <p className="mt-1">{selectedNode.data.contact_email}</p>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium text-gray-600">
                    {t("organizationHub.info.createdAt")}
                  </label>
                  <p className="mt-1">
                    {new Date(selectedNode.data.created_at).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* 學校管理 Tabs */}
            {selectedNode.type === "school" && (
              <Tabs defaultValue="classrooms" className="mt-6">
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
                        <Button size="sm">
                          <Plus className="w-4 h-4 mr-2" />
                          {t("organizationHub.addClassroom")}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {isLoadingSchoolDetails ? (
                        <div className="text-center py-8 text-gray-500">
                          {t("common.loading")}
                        </div>
                      ) : schoolClassrooms.length > 0 ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{t("organizationHub.table.classroomName")}</TableHead>
                              <TableHead>{t("organizationHub.table.level")}</TableHead>
                              <TableHead>{t("organizationHub.table.status")}</TableHead>
                              <TableHead>{t("organizationHub.table.createdAt")}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {schoolClassrooms.map((classroom) => (
                              <TableRow key={classroom.id}>
                                <TableCell className="font-medium">
                                  {classroom.name}
                                </TableCell>
                                <TableCell>{classroom.program_level}</TableCell>
                                <TableCell>
                                  <span
                                    className={cn(
                                      "px-2 py-1 rounded-full text-xs",
                                      classroom.is_active
                                        ? "bg-green-100 text-green-700"
                                        : "bg-gray-100 text-gray-700"
                                    )}
                                  >
                                    {classroom.is_active
                                      ? t("common.active")
                                      : t("common.inactive")}
                                  </span>
                                </TableCell>
                                <TableCell>
                                  {new Date(
                                    classroom.created_at
                                  ).toLocaleDateString()}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
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
                        <Button size="sm">
                          <Plus className="w-4 h-4 mr-2" />
                          {t("organizationHub.addTeacher")}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {isLoadingSchoolDetails ? (
                        <div className="text-center py-8 text-gray-500">
                          {t("common.loading")}
                        </div>
                      ) : schoolTeachers.length > 0 ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{t("organizationHub.table.teacherName")}</TableHead>
                              <TableHead>{t("organizationHub.table.email")}</TableHead>
                              <TableHead>{t("organizationHub.table.role")}</TableHead>
                              <TableHead>{t("organizationHub.table.status")}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {schoolTeachers.map((teacher) => (
                              <TableRow key={teacher.id}>
                                <TableCell className="font-medium">
                                  {teacher.name}
                                </TableCell>
                                <TableCell>{teacher.email}</TableCell>
                                <TableCell>
                                  <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700">
                                    {teacher.role}
                                  </span>
                                </TableCell>
                                <TableCell>
                                  <span
                                    className={cn(
                                      "px-2 py-1 rounded-full text-xs",
                                      teacher.is_active
                                        ? "bg-green-100 text-green-700"
                                        : "bg-gray-100 text-gray-700"
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
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full p-4">
            <Button
              variant="outline"
              size="sm"
              className="lg:hidden mb-8"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="w-4 h-4 mr-2" />
              {t("organizationHub.openMenu")}
            </Button>
            <div className="text-center text-gray-400">
              <Building2 className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-base sm:text-lg">{t("organizationHub.selectPrompt")}</p>
            </div>
          </div>
        )}
      </main>

      {/* 新增學校 Dialog */}
      <Dialog open={isAddSchoolDialogOpen} onOpenChange={setIsAddSchoolDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{t("organizationHub.addSchoolDialog.title")}</DialogTitle>
            <DialogDescription>
              {t("organizationHub.addSchoolDialog.description")}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">
                {t("organizationHub.addSchoolDialog.name")} *
              </Label>
              <Input
                id="name"
                placeholder={t("organizationHub.addSchoolDialog.namePlaceholder")}
                value={schoolFormData.name}
                onChange={(e) => handleSchoolFormChange("name", e.target.value)}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="display_name">
                {t("organizationHub.addSchoolDialog.displayName")}
              </Label>
              <Input
                id="display_name"
                placeholder={t("organizationHub.addSchoolDialog.displayNamePlaceholder")}
                value={schoolFormData.display_name}
                onChange={(e) =>
                  handleSchoolFormChange("display_name", e.target.value)
                }
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">
                {t("organizationHub.addSchoolDialog.description")}
              </Label>
              <Textarea
                id="description"
                placeholder={t("organizationHub.addSchoolDialog.descriptionPlaceholder")}
                value={schoolFormData.description}
                onChange={(e) =>
                  handleSchoolFormChange("description", e.target.value)
                }
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="contact_email">
                  {t("organizationHub.addSchoolDialog.contactEmail")}
                </Label>
                <Input
                  id="contact_email"
                  type="email"
                  placeholder="school@example.com"
                  value={schoolFormData.contact_email}
                  onChange={(e) =>
                    handleSchoolFormChange("contact_email", e.target.value)
                  }
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="contact_phone">
                  {t("organizationHub.addSchoolDialog.contactPhone")}
                </Label>
                <Input
                  id="contact_phone"
                  type="tel"
                  placeholder="+886-2-1234-5678"
                  value={schoolFormData.contact_phone}
                  onChange={(e) =>
                    handleSchoolFormChange("contact_phone", e.target.value)
                  }
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="address">
                {t("organizationHub.addSchoolDialog.address")}
              </Label>
              <Input
                id="address"
                placeholder={t("organizationHub.addSchoolDialog.addressPlaceholder")}
                value={schoolFormData.address}
                onChange={(e) => handleSchoolFormChange("address", e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAddSchoolDialogOpen(false)}
              disabled={isSubmitting}
            >
              {t("common.cancel")}
            </Button>
            <Button
              type="submit"
              onClick={handleSubmitNewSchool}
              disabled={isSubmitting || !schoolFormData.name}
            >
              {isSubmitting ? t("common.submitting") : t("common.submit")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </TeacherLayout>
  );
}
