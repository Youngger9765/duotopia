import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AlertTriangle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Program } from "@/types";

interface ProgramDialogProps {
  program: Program | null;
  dialogType: "create" | "edit" | "delete" | null;
  classroomId?: number;
  isTemplate?: boolean;
  onClose: () => void;
  onSave: (program: Program) => void;
  onDelete?: (programId: number) => void;
}

// Local form data type that makes id optional for creation
interface ProgramFormData {
  id?: number;
  name: string;
  description?: string;
  level?: string;
  estimated_hours?: number;
  classroom_id?: number;
  tags?: string[];
}

export function ProgramDialog({
  program,
  dialogType,
  classroomId,
  isTemplate = false,
  onClose,
  onSave,
  onDelete,
}: ProgramDialogProps) {
  const [formData, setFormData] = useState<ProgramFormData>({
    name: "",
    description: "",
    level: "A1",
    estimated_hours: 20,
    classroom_id: classroomId,
    tags: [],
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [tagInput, setTagInput] = useState("");

  useEffect(() => {
    if (program && (dialogType === "edit" || dialogType === "delete")) {
      setFormData({
        name: program.name,
        description: program.description || "",
        level: program.level || "A1",
        estimated_hours: program.estimated_hours || 20,
        classroom_id: program.classroom_id || classroomId,
        tags: program.tags || [],
      });
    } else if (dialogType === "create") {
      setFormData({
        name: "",
        description: "",
        level: "A1",
        estimated_hours: 20,
        classroom_id: classroomId,
        tags: [],
      });
    }
  }, [program, dialogType, classroomId]);

  const handleAddTag = () => {
    if (!tagInput) return;

    if ((formData.tags?.length || 0) >= 5) {
      setErrors({ ...errors, tags: "最多只能新增 5 個標籤" });
      return;
    }

    if (formData.tags?.includes(tagInput)) {
      setErrors({ ...errors, tags: "此標籤已存在" });
      return;
    }

    setFormData({
      ...formData,
      tags: [...(formData.tags || []), tagInput],
    });
    setTagInput("");
    setErrors({ ...errors, tags: "" });
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter((t) => t !== tag) || [],
    });
    if (errors.tags) {
      setErrors({ ...errors, tags: "" });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name?.trim()) {
      newErrors.name = "課程名稱為必填";
    }

    if (!formData.level) {
      newErrors.level = "程度為必填";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      if (dialogType === "create") {
        const newProgram = await apiClient.createProgram({
          name: formData.name,
          description: formData.description,
          level: formData.level,
          classroom_id: isTemplate ? undefined : (formData.classroom_id || classroomId),
          estimated_hours: formData.estimated_hours,
          tags: formData.tags,
          is_template: isTemplate,
        });
        // Ensure the new program has all required Program properties
        const completeProgram: Program = {
          ...(newProgram as Program),
          id: (newProgram as Program)?.id || 0, // Default ID if not provided
        };
        onSave(completeProgram);
      } else if (dialogType === "edit" && program?.id) {
        // For classroom programs, we might need different API endpoint
        // TODO: Check if this is a classroom program update
        await apiClient.updateProgram(program.id!, {
          name: formData.name,
          description: formData.description,
          level: formData.level,
          estimated_hours: formData.estimated_hours,
          tags: formData.tags,
        });
        // Ensure the updated program has all required Program properties
        const updatedProgram: Program = {
          ...program,
          ...formData,
          id: program.id,
        };
        onSave(updatedProgram);
      }
      onClose();
    } catch (error) {
      console.error("Failed to save program:", error);
      setErrors({ submit: "儲存失敗，請稍後再試" });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!program?.id || !onDelete) return;

    setLoading(true);
    try {
      await apiClient.deleteProgram(program.id);
      onDelete(program.id);
      onClose();
    } catch (error) {
      console.error("Failed to delete program:", error);
      alert("刪除失敗，請稍後再試");
    } finally {
      setLoading(false);
    }
  };

  if (!dialogType) return null;

  // Create/Edit Dialog
  if (dialogType === "create" || dialogType === "edit") {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent
          className="bg-white"
          style={{ backgroundColor: "white" }}
        >
          <DialogHeader>
            <DialogTitle>
              {dialogType === "create" ? "建立新課程" : "編輯課程"}
            </DialogTitle>
            <DialogDescription>
              {dialogType === "create"
                ? "為班級建立新的課程內容"
                : "修改課程資訊"}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div>
              <label htmlFor="name" className="text-sm font-medium">
                課程名稱 <span className="text-red-500">*</span>
              </label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.name ? "border-red-500" : ""}`}
                placeholder="例：五年級英語基礎課程"
              />
              {errors.name && (
                <p className="text-xs text-red-500 mt-1">{errors.name}</p>
              )}
            </div>

            <div>
              <label htmlFor="description" className="text-sm font-medium">
                課程描述
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="課程的簡短描述..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="level" className="text-sm font-medium">
                  程度 <span className="text-red-500">*</span>
                </label>
                <select
                  id="level"
                  value={formData.level}
                  onChange={(e) =>
                    setFormData({ ...formData, level: e.target.value })
                  }
                  className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.level ? "border-red-500" : ""}`}
                >
                  <option value="PREA">Pre-A</option>
                  <option value="A1">A1</option>
                  <option value="A2">A2</option>
                  <option value="B1">B1</option>
                  <option value="B2">B2</option>
                  <option value="C1">C1</option>
                  <option value="C2">C2</option>
                </select>
                {errors.level && (
                  <p className="text-xs text-red-500 mt-1">{errors.level}</p>
                )}
              </div>

              <div>
                <label htmlFor="hours" className="text-sm font-medium">
                  預估時數
                </label>
                <input
                  id="hours"
                  type="number"
                  value={formData.estimated_hours}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      estimated_hours: parseInt(e.target.value) || 0,
                    })
                  }
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                  placeholder="20"
                  min="1"
                />
              </div>
            </div>

            {/* Tags Input */}
            <div>
              <label htmlFor="tags" className="text-sm font-medium">
                標籤 <span className="text-gray-500 text-xs">(最多 5 個)</span>
              </label>
              <input
                id="tags"
                type="text"
                value={tagInput}
                onChange={(e) => {
                  setTagInput(e.target.value);
                  if (errors.tags) {
                    setErrors({ ...errors, tags: "" });
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
                className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.tags ? "border-red-500" : ""}`}
                placeholder="按 Enter 新增標籤"
                disabled={(formData.tags?.length || 0) >= 5}
              />
              {errors.tags && (
                <p className="text-xs text-red-500 mt-1">{errors.tags}</p>
              )}

              {formData.tags && formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-200"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-2 text-blue-500 hover:text-blue-700"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {errors.submit && (
              <p className="text-sm text-red-500 bg-red-50 p-2 rounded">
                {errors.submit}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={onClose} disabled={loading}>
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={loading}>
              {loading
                ? "處理中..."
                : dialogType === "create"
                  ? "建立"
                  : "儲存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  // Delete Confirmation Dialog
  if (dialogType === "delete" && program) {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent
          className="bg-white"
          style={{ backgroundColor: "white" }}
        >
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>確認刪除課程</span>
            </DialogTitle>
            <DialogDescription>
              確定要刪除課程「{program.name}
              」嗎？此操作將同時刪除所有相關的單元。
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">課程資料：</p>
              <p className="font-medium mt-1">{program.name}</p>
              {program.description && (
                <p className="text-sm text-gray-500 mt-1">
                  {program.description}
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={onClose} disabled={loading}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={loading}
            >
              {loading ? "刪除中..." : "確認刪除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return null;
}
