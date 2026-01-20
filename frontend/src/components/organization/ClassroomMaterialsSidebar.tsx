import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import { logError } from "@/utils/errorLogger";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Plus, Search, Check } from "lucide-react";
import { toast } from "sonner";
import { useProgramCopy } from "@/hooks/useProgramCopy";

interface Program {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

interface ClassroomMaterialsSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classroomId: number;
  classroomName: string;
  schoolId: string;
  organizationId?: string;
  onSuccess?: () => void;
}

export function ClassroomMaterialsSidebar({
  open,
  onOpenChange,
  classroomId,
  classroomName,
  schoolId,
  organizationId,
  onSuccess,
}: ClassroomMaterialsSidebarProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const { copyProgram } = useProgramCopy();
  
  const [classroomPrograms, setClassroomPrograms] = useState<Program[]>([]);
  const [schoolPrograms, setSchoolPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProgramIds, setSelectedProgramIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (open && classroomId && schoolId) {
      setSearchTerm("");
      setSelectedProgramIds(new Set());
      fetchClassroomPrograms();
    }
  }, [open, classroomId, schoolId]);

  const fetchClassroomPrograms = async () => {
    try {
      setLoading(true);
      const programs = await apiClient.getClassroomPrograms(classroomId);
      const classroomProgramsData = programs || [];
      setClassroomPrograms(classroomProgramsData);
      // 獲取班級教材後，立即更新可用教材列表
      await fetchSchoolPrograms(classroomProgramsData);
    } catch (error) {
      logError("Failed to fetch classroom programs", error, { classroomId });
      toast.error("載入班級教材失敗");
    } finally {
      setLoading(false);
    }
  };

  const fetchSchoolPrograms = async (currentClassroomPrograms: Program[] = classroomPrograms) => {
    try {
      const response = await fetch(`${API_URL}/api/schools/${schoolId}/programs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const programs = await response.json();
        // 過濾掉已經在班級中的教材
        const classroomProgramIds = new Set(currentClassroomPrograms.map((p) => p.id));
        const available = (programs || []).filter(
          (p: Program) => !classroomProgramIds.has(p.id)
        );
        setSchoolPrograms(available);
      }
    } catch (error) {
      logError("Failed to fetch school programs", error, { schoolId });
      toast.error("載入學校教材失敗");
    }
  };

  const handleAddPrograms = async () => {
    if (selectedProgramIds.size === 0) {
      toast.error("請選擇至少一個教材");
      return;
    }

    try {
      // 使用 copyProgram hook 複製教材到班級
      for (const programId of selectedProgramIds) {
        await copyProgram({
          programId,
          targetScope: "classroom",
          targetId: classroomId.toString(),
        });
      }
      
      toast.success("教材已成功加入班級");
      setSelectedProgramIds(new Set());
      await fetchClassroomPrograms();
      onSuccess?.();
    } catch (error) {
      logError("Failed to add programs to classroom", error, {
        classroomId,
        programIds: Array.from(selectedProgramIds),
      });
      toast.error("加入教材失敗");
    }
  };

  const toggleProgramSelection = (programId: number) => {
    setSelectedProgramIds((prev) => {
      const next = new Set(prev);
      if (next.has(programId)) {
        next.delete(programId);
      } else {
        next.add(programId);
      }
      return next;
    });
  };

  const filteredSchoolPrograms = schoolPrograms.filter((program) =>
    searchTerm
      ? program.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        program.description?.toLowerCase().includes(searchTerm.toLowerCase())
      : true
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{classroomName} - 教材清單</SheetTitle>
          <SheetDescription>
            管理此班級的教材，可以從學校教材中添加教材
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* 班級教材列表 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700">班級教材 ({classroomPrograms.length})</h3>
            </div>
            <ScrollArea className="h-[200px] border rounded-md p-3">
              {classroomPrograms.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <BookOpen className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">尚無教材</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {classroomPrograms.map((program) => (
                    <div
                      key={program.id}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div className="flex-1">
                        <div className="font-medium text-sm">{program.name}</div>
                        {program.description && (
                          <div className="text-xs text-gray-500 mt-1">{program.description}</div>
                        )}
                      </div>
                      <Badge variant={program.is_active ? "default" : "secondary"} className="ml-2">
                        {program.is_active ? "啟用" : "停用"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* 添加教材區塊 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700">
                從學校添加教材 ({selectedProgramIds.size} 已選擇)
              </h3>
              {selectedProgramIds.size > 0 && (
                <Button size="sm" onClick={handleAddPrograms}>
                  <Plus className="h-4 w-4 mr-1" />
                  加入班級
                </Button>
              )}
            </div>

            {/* 搜尋框 */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜尋教材（名稱、描述）"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* 可用教材列表 */}
            <ScrollArea className="h-[250px] border rounded-md p-3">
              {filteredSchoolPrograms.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <BookOpen className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">
                    {searchTerm ? "找不到符合條件的教材" : "沒有可用的教材"}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredSchoolPrograms.map((program) => {
                    const isSelected = selectedProgramIds.has(program.id);
                    return (
                      <div
                        key={program.id}
                        onClick={() => toggleProgramSelection(program.id)}
                        className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-blue-50 border border-blue-200"
                            : "bg-gray-50 hover:bg-gray-100"
                        }`}
                      >
                        <div className="flex-1">
                          <div className="font-medium text-sm">{program.name}</div>
                          {program.description && (
                            <div className="text-xs text-gray-500 mt-1">{program.description}</div>
                          )}
                        </div>
                        {isSelected && (
                          <Badge variant="default" className="bg-blue-600 ml-2">
                            <Check className="h-3 w-3 mr-1" />
                            已選
                          </Badge>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

