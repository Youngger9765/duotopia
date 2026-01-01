import { useState, useEffect } from "react";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface Teacher {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

interface InviteTeacherToSchoolDialogProps {
  schoolId: string;
  organizationId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function InviteTeacherToSchoolDialog({
  schoolId,
  organizationId,
  open,
  onOpenChange,
  onSuccess,
}: InviteTeacherToSchoolDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [loadingTeachers, setLoadingTeachers] = useState(false);
  const [activeTab, setActiveTab] = useState<"existing" | "new">("existing");

  // For existing teacher selection
  const [orgTeachers, setOrgTeachers] = useState<Teacher[]>([]);
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>("");
  const [selectedRoleExisting, setSelectedRoleExisting] = useState<string>("teacher");

  // For new teacher invitation
  const [newTeacherData, setNewTeacherData] = useState({
    email: "",
    name: "",
    role: "teacher",
  });

  useEffect(() => {
    if (open) {
      fetchOrgTeachers();
      setActiveTab("existing");
      setSelectedTeacherId("");
      setSelectedRoleExisting("teacher");
      setNewTeacherData({ email: "", name: "", role: "teacher" });
    }
  }, [open]);

  const fetchOrgTeachers = async () => {
    try {
      setLoadingTeachers(true);

      const response = await fetch(
        `${API_URL}/api/organizations/${organizationId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setOrgTeachers(data.filter((t: Teacher) => t.is_active));
      }
    } catch (error) {
      console.error("Failed to fetch org teachers:", error);
    } finally {
      setLoadingTeachers(false);
    }
  };

  const handleSubmitExisting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeacherId) {
      toast.error("請選擇教師");
      return;
    }

    setLoading(true);

    try {
      // Add existing org teacher to school
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/teachers`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            teacher_id: parseInt(selectedTeacherId),
            roles: [selectedRoleExisting],
          }),
        }
      );

      if (response.ok) {
        toast.success("教師已加入學校");
        onSuccess();
        onOpenChange(false);
        setSelectedTeacherId("");
      } else {
        const data = await response.json();
        toast.error(data.detail || "加入學校失敗");
      }
    } catch (error) {
      console.error("Failed to add teacher to school:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTeacherData.email || !newTeacherData.name) {
      toast.error("請填寫所有必填欄位");
      return;
    }

    setLoading(true);

    try {
      // Step 1: Invite to organization first
      const orgResponse = await fetch(
        `${API_URL}/api/organizations/${organizationId}/teachers/invite`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            email: newTeacherData.email,
            name: newTeacherData.name,
            role: "teacher",
          }),
        }
      );

      if (!orgResponse.ok) {
        const errorData = await orgResponse.json();
        if (!errorData.detail?.includes("已在組織中")) {
          toast.error(errorData.detail || "邀請失敗");
          setLoading(false);
          return;
        }
      }

      // Step 2: Get teacher ID
      let teacherId: number;

      if (orgResponse.ok) {
        const orgData = await orgResponse.json();
        teacherId = orgData.teacher_id;
      } else {
        const teachersResponse = await fetch(
          `${API_URL}/api/organizations/${organizationId}/teachers`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!teachersResponse.ok) {
          toast.error("無法獲取教師資訊");
          setLoading(false);
          return;
        }

        const teachers = await teachersResponse.json();
        const existingTeacher = teachers.find(
          (t: any) => t.email === newTeacherData.email
        );

        if (!existingTeacher) {
          toast.error("無法找到教師");
          setLoading(false);
          return;
        }

        teacherId = existingTeacher.id;
      }

      // Step 3: Add to school
      const schoolResponse = await fetch(
        `${API_URL}/api/schools/${schoolId}/teachers`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            teacher_id: teacherId,
            roles: [newTeacherData.role],
          }),
        }
      );

      if (schoolResponse.ok) {
        toast.success("教師已加入學校");
        onSuccess();
        onOpenChange(false);
        setNewTeacherData({ email: "", name: "", role: "teacher" });
      } else {
        const data = await schoolResponse.json();
        toast.error(data.detail || "加入學校失敗");
      }
    } catch (error) {
      console.error("Failed to invite teacher to school:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>邀請教師加入學校</DialogTitle>
          <DialogDescription>
            從組織選擇現有教師，或邀請新教師加入
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "existing" | "new")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="existing">從組織選擇</TabsTrigger>
            <TabsTrigger value="new">獨立邀請</TabsTrigger>
          </TabsList>

          {/* Tab 1: Select from organization */}
          <TabsContent value="existing">
            <form onSubmit={handleSubmitExisting} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="existing-teacher">選擇教師</Label>
                {loadingTeachers ? (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    載入教師列表...
                  </div>
                ) : (
                  <Select
                    value={selectedTeacherId}
                    onValueChange={setSelectedTeacherId}
                  >
                    <SelectTrigger id="existing-teacher">
                      <SelectValue placeholder="請選擇教師" />
                    </SelectTrigger>
                    <SelectContent>
                      {orgTeachers.map((teacher) => (
                        <SelectItem
                          key={teacher.id}
                          value={teacher.id.toString()}
                        >
                          {teacher.name} ({teacher.email})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                {!loadingTeachers && orgTeachers.length === 0 && (
                  <p className="text-sm text-gray-500">
                    組織內尚無其他教師，請使用「獨立邀請」
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="role-existing">角色</Label>
                <Select
                  value={selectedRoleExisting}
                  onValueChange={setSelectedRoleExisting}
                >
                  <SelectTrigger id="role-existing">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="teacher">教師</SelectItem>
                    <SelectItem value="school_director">主任</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={loading}
                >
                  取消
                </Button>
                <Button
                  type="submit"
                  disabled={loading || !selectedTeacherId}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      加入中...
                    </>
                  ) : (
                    "加入學校"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>

          {/* Tab 2: Invite new teacher */}
          <TabsContent value="new">
            <form onSubmit={handleSubmitNew} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new-name">
                  姓名 <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="new-name"
                  value={newTeacherData.name}
                  onChange={(e) =>
                    setNewTeacherData({ ...newTeacherData, name: e.target.value })
                  }
                  required
                  placeholder="輸入姓名"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-email">
                  Email <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="new-email"
                  type="email"
                  value={newTeacherData.email}
                  onChange={(e) =>
                    setNewTeacherData({ ...newTeacherData, email: e.target.value })
                  }
                  required
                  placeholder="example@email.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="role-new">角色</Label>
                <Select
                  value={newTeacherData.role}
                  onValueChange={(value) =>
                    setNewTeacherData({ ...newTeacherData, role: value })
                  }
                >
                  <SelectTrigger id="role-new">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="teacher">教師</SelectItem>
                    <SelectItem value="school_director">主任</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="rounded-lg bg-blue-50 p-3">
                <p className="text-sm text-blue-900">
                  💡 新教師將同時加入組織和此學校
                </p>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={loading}
                >
                  取消
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      邀請中...
                    </>
                  ) : (
                    "邀請教師"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
