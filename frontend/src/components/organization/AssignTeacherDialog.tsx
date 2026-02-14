import { useState, useEffect, useMemo, useRef } from "react";
import { apiClient, ApiError } from "@/lib/api";
import { logError } from "@/utils/errorLogger";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  Search,
  UserPlus,
  Building2,
  Users,
  Info,
  Loader2,
  X,
  UserX,
} from "lucide-react";

interface Classroom {
  id: string;
  name: string;
  teacher_name: string | null;
  teacher_id?: number | null;
}

interface SchoolTeacher {
  id: number;
  name: string;
  email: string;
  roles?: string[];
}

interface OrgTeacher {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
}

type TeacherOption = {
  id: number;
  name: string;
  email: string;
  source: "school" | "org";
  role: string;
};

interface AssignTeacherDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classroom: Classroom | null;
  teachers: SchoolTeacher[];
  organizationId: string;
  schoolId: string;
  onSuccess: () => void;
}

export function AssignTeacherDialog({
  open,
  onOpenChange,
  classroom,
  teachers,
  organizationId,
  schoolId,
  onSuccess,
}: AssignTeacherDialogProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orgTeachers, setOrgTeachers] = useState<OrgTeacher[]>([]);
  const [loadingOrg, setLoadingOrg] = useState(false);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteName, setInviteName] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch org teachers when dialog opens
  useEffect(() => {
    if (open && organizationId) {
      fetchOrgTeachers();
      setSearchQuery("");
      setShowInviteForm(false);
      setInviteName("");
    }
  }, [open, organizationId]);

  const fetchOrgTeachers = async () => {
    setLoadingOrg(true);
    try {
      const data = await apiClient.getOrganizationTeachers(organizationId);
      setOrgTeachers(data.filter((t) => t.is_active));
    } catch (error) {
      logError("Failed to fetch org teachers", error, { organizationId });
    } finally {
      setLoadingOrg(false);
    }
  };

  // Build unified teacher list with deduplication
  const schoolTeacherIds = useMemo(
    () => new Set(teachers.map((t) => t.id)),
    [teachers],
  );

  const allTeachers = useMemo((): {
    schoolTeachers: TeacherOption[];
    orgOnlyTeachers: TeacherOption[];
  } => {
    const schoolTeachers: TeacherOption[] = teachers.map((t) => ({
      id: t.id,
      name: t.name,
      email: t.email,
      source: "school" as const,
      role: t.roles?.[0] || "teacher",
    }));

    const orgOnlyTeachers: TeacherOption[] = orgTeachers
      .filter((t) => !schoolTeacherIds.has(t.id))
      .map((t) => ({
        id: t.id,
        name: t.name,
        email: t.email,
        source: "org" as const,
        role: t.role,
      }));

    return { schoolTeachers, orgOnlyTeachers };
  }, [teachers, orgTeachers, schoolTeacherIds]);

  // Filter by search query
  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    const filterFn = (t: TeacherOption) =>
      !q ||
      t.name.toLowerCase().includes(q) ||
      t.email.toLowerCase().includes(q);

    return {
      schoolTeachers: allTeachers.schoolTeachers.filter(filterFn),
      orgOnlyTeachers: allTeachers.orgOnlyTeachers.filter(filterFn),
    };
  }, [allTeachers, searchQuery]);

  const hasResults =
    filtered.schoolTeachers.length > 0 || filtered.orgOnlyTeachers.length > 0;

  // Check if search looks like an email with no results
  const isEmailSearch =
    searchQuery.includes("@") && searchQuery.includes(".");
  const showNoResultInvite =
    !hasResults && searchQuery.trim().length > 0 && !showInviteForm;

  const handleClose = () => {
    setSearchQuery("");
    setShowInviteForm(false);
    setInviteName("");
    onOpenChange(false);
  };

  const handleSelectTeacher = async (teacher: TeacherOption) => {
    if (!classroom) return;

    // If teacher is from org but not in school, add to school first
    if (teacher.source === "org") {
      setIsSubmitting(true);
      try {
        await apiClient.addTeacherToSchool(schoolId, {
          teacher_id: teacher.id,
          roles: ["teacher"],
        });
      } catch (error) {
        if (error instanceof ApiError && error.status !== 409) {
          logError("Failed to add teacher to school", error);
          toast.error("將教師加入分校失敗");
          setIsSubmitting(false);
          return;
        }
        // 409 = already in school, proceed with assignment
      }
    }

    // Assign to classroom
    setIsSubmitting(true);
    try {
      await apiClient.assignTeacherToClassroom(
        parseInt(classroom.id),
        teacher.id,
      );
      toast.success(`已指派 ${teacher.name} 為 ${classroom.name} 的導師`);
      onSuccess();
      handleClose();
    } catch (error) {
      logError("Failed to assign teacher", error, {
        classroomId: classroom.id,
        teacherId: teacher.id,
      });
      toast.error("指派導師失敗，請稍後再試");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUnassign = async () => {
    if (!classroom) return;

    setIsSubmitting(true);
    try {
      await apiClient.assignTeacherToClassroom(parseInt(classroom.id), null);
      toast.success("已取消導師指派");
      onSuccess();
      handleClose();
    } catch (error) {
      logError("Failed to unassign teacher", error, {
        classroomId: classroom.id,
      });
      toast.error("取消指派失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInviteAndAssign = async () => {
    if (!classroom || !inviteName.trim()) return;

    const email = searchQuery.trim();
    setIsSubmitting(true);

    try {
      // Step 1: Invite to organization
      let teacherId: number;
      try {
        const result = await apiClient.inviteTeacherToOrganization(
          organizationId,
          {
            email,
            name: inviteName.trim(),
            role: "teacher",
          },
        );
        teacherId = result.teacher_id;
      } catch (error) {
        if (error instanceof ApiError) {
          // Teacher may already be in org, try to find them
          const orgList =
            await apiClient.getOrganizationTeachers(organizationId);
          const existing = orgList.find((t) => t.email === email);
          if (existing) {
            teacherId = existing.id;
          } else {
            toast.error("邀請教師失敗");
            setIsSubmitting(false);
            return;
          }
        } else {
          throw error;
        }
      }

      // Step 2: Add to school
      try {
        await apiClient.addTeacherToSchool(schoolId, {
          teacher_id: teacherId,
          roles: ["teacher"],
        });
      } catch (error) {
        if (error instanceof ApiError && error.status !== 409) {
          toast.error("將教師加入分校失敗");
          setIsSubmitting(false);
          return;
        }
      }

      // Step 3: Assign to classroom
      await apiClient.assignTeacherToClassroom(
        parseInt(classroom.id),
        teacherId,
      );
      toast.success(
        `已邀請 ${inviteName.trim()} 並指派為 ${classroom.name} 的導師`,
      );
      onSuccess();
      handleClose();
    } catch (error) {
      logError("Failed to invite and assign teacher", error);
      toast.error("邀請並指派導師失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRoleBadge = (teacher: TeacherOption) => {
    if (teacher.source === "org") {
      return (
        <span className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 text-purple-700">
          機構教師
        </span>
      );
    }
    const roleMap: Record<string, { label: string; className: string }> = {
      school_admin: {
        label: "管理員",
        className: "bg-amber-100 text-amber-700",
      },
      school_director: {
        label: "主任",
        className: "bg-amber-100 text-amber-700",
      },
      teacher: { label: "教師", className: "bg-blue-100 text-blue-700" },
    };
    const info = roleMap[teacher.role] || roleMap.teacher;
    return (
      <span
        className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${info.className}`}
      >
        {info.label}
      </span>
    );
  };

  const getAvatarColor = (name: string) => {
    const colors = [
      "bg-blue-500",
      "bg-emerald-500",
      "bg-amber-500",
      "bg-purple-500",
      "bg-pink-500",
      "bg-cyan-500",
      "bg-rose-500",
      "bg-indigo-500",
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  const renderTeacherRow = (teacher: TeacherOption) => {
    const isCurrentTeacher = classroom?.teacher_id === teacher.id;
    return (
      <button
        key={`${teacher.source}-${teacher.id}`}
        type="button"
        className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-left transition-colors hover:bg-accent/50 disabled:opacity-50 ${
          isCurrentTeacher ? "bg-accent/30" : ""
        }`}
        onClick={() => handleSelectTeacher(teacher)}
        disabled={isSubmitting}
      >
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white ${getAvatarColor(teacher.name)}`}
        >
          {teacher.name.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-sm font-medium">{teacher.name}</span>
            {isCurrentTeacher && (
              <span className="shrink-0 text-[10px] text-muted-foreground">
                (目前導師)
              </span>
            )}
          </div>
          <p className="truncate text-xs text-muted-foreground">
            {teacher.email}
          </p>
        </div>
        {getRoleBadge(teacher)}
      </button>
    );
  };

  if (!classroom) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md p-0 gap-0">
        <DialogHeader className="px-6 pt-5 pb-3">
          <DialogTitle>
            {classroom.teacher_name ? "更換導師" : "指派導師"}
          </DialogTitle>
          <DialogDescription>
            搜尋教師姓名或 Email 來為「{classroom.name}」指派導師
          </DialogDescription>
        </DialogHeader>

        <div className="border-t" />

        {/* Search Input */}
        <div className="px-6 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              ref={inputRef}
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowInviteForm(false);
              }}
              placeholder="輸入姓名或 Email 搜尋..."
              className="pl-9 pr-8"
              autoFocus
              disabled={isSubmitting}
            />
            {searchQuery && (
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-sm p-0.5 text-muted-foreground hover:text-foreground"
                onClick={() => {
                  setSearchQuery("");
                  setShowInviteForm(false);
                  inputRef.current?.focus();
                }}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Teacher List */}
        {!showInviteForm && (
          <ScrollArea className="max-h-[320px] px-3">
            <div className="space-y-0.5 pb-2">
              {/* Unassign option - only when classroom has a teacher */}
              {classroom.teacher_id && !searchQuery && (
                <>
                  <button
                    type="button"
                    className="flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:bg-accent/50 disabled:opacity-50"
                    onClick={handleUnassign}
                    disabled={isSubmitting}
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-dashed border-muted-foreground/30">
                      <UserX className="h-3.5 w-3.5" />
                    </div>
                    <span>取消導師指派</span>
                  </button>
                  <div className="mx-2.5 my-1 border-t" />
                </>
              )}

              {/* School teachers group */}
              {filtered.schoolTeachers.length > 0 && (
                <>
                  <div className="flex items-center gap-1.5 px-2.5 py-1.5">
                    <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-[11px] font-semibold tracking-wide text-muted-foreground">
                      分校教師 ({filtered.schoolTeachers.length})
                    </span>
                  </div>
                  {filtered.schoolTeachers.map(renderTeacherRow)}
                </>
              )}

              {/* Org-only teachers group */}
              {filtered.orgOnlyTeachers.length > 0 && (
                <>
                  {filtered.schoolTeachers.length > 0 && (
                    <div className="mx-2.5 my-1 border-t" />
                  )}
                  <div className="flex items-center gap-1.5 px-2.5 py-1.5">
                    <Users className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-[11px] font-semibold tracking-wide text-muted-foreground">
                      機構教師 - 尚未加入此分校 (
                      {filtered.orgOnlyTeachers.length})
                    </span>
                  </div>
                  {filtered.orgOnlyTeachers.map(renderTeacherRow)}
                  <div className="flex items-center gap-1 px-2.5 py-1">
                    <Info className="h-3 w-3 text-muted-foreground" />
                    <span className="text-[11px] text-muted-foreground">
                      選擇機構教師將自動加入此分校
                    </span>
                  </div>
                </>
              )}

              {/* Loading state */}
              {loadingOrg && (
                <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  載入教師列表...
                </div>
              )}

              {/* No results - show invite option */}
              {showNoResultInvite && !loadingOrg && (
                <div className="space-y-3 px-2.5 py-2">
                  <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2.5">
                    <UserX className="h-5 w-5 shrink-0 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      找不到符合「{searchQuery}」的教師
                    </p>
                  </div>
                  {isEmailSearch && (
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 rounded-lg border border-dashed border-primary/30 bg-primary/5 px-3 py-2.5 text-left transition-colors hover:bg-primary/10"
                      onClick={() => setShowInviteForm(true)}
                    >
                      <UserPlus className="h-4 w-4 shrink-0 text-primary" />
                      <div>
                        <p className="text-sm font-medium text-primary">
                          邀請 {searchQuery} 為新教師
                        </p>
                        <p className="text-xs text-muted-foreground">
                          將加入機構、分校，並指派為此班導師
                        </p>
                      </div>
                    </button>
                  )}
                </div>
              )}

              {/* Empty state - no teachers at all */}
              {!loadingOrg &&
                !hasResults &&
                !searchQuery &&
                teachers.length === 0 &&
                orgTeachers.length === 0 && (
                  <div className="py-6 text-center text-sm text-muted-foreground">
                    目前沒有可指派的教師
                  </div>
                )}
            </div>
          </ScrollArea>
        )}

        {/* Invite Form */}
        {showInviteForm && (
          <div className="space-y-4 px-6 pb-2">
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
              <p className="text-sm font-medium text-primary">
                邀請新教師加入機構
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                此教師將自動加入機構 + 此分校，並成為此班導師
              </p>
            </div>

            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="invite-email">Email</Label>
                <Input
                  id="invite-email"
                  value={searchQuery}
                  disabled
                  className="bg-muted/50"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="invite-name">
                  姓名 <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="invite-name"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder="請輸入教師姓名"
                  autoFocus
                  disabled={isSubmitting}
                />
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="border-t" />
        <DialogFooter className="px-6 py-3">
          {showInviteForm ? (
            <>
              <Button
                variant="outline"
                onClick={() => setShowInviteForm(false)}
                disabled={isSubmitting}
                size="sm"
              >
                返回
              </Button>
              <Button
                onClick={handleInviteAndAssign}
                disabled={isSubmitting || !inviteName.trim()}
                size="sm"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    處理中...
                  </>
                ) : (
                  <>
                    <UserPlus className="mr-2 h-4 w-4" />
                    邀請並指派為導師
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
              size="sm"
            >
              取消
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
