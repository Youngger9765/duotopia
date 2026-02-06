import { useState, useEffect, useCallback } from "react";
import TeacherLayout from "@/components/TeacherLayout";
import {
  useResourceMaterialsAPI,
  ResourceMaterial,
  ResourceMaterialDetail,
} from "@/hooks/useResourceMaterialsAPI";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Package,
  Copy,
  BookOpen,
  Layers,
  FileText,
  CheckCircle2,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

export default function ResourceMaterialsPage() {
  return (
    <TeacherLayout>
      <ResourceMaterialsInner />
    </TeacherLayout>
  );
}

function ResourceMaterialsInner() {
  const { loading, listMaterials, getMaterialDetail, copyMaterial } =
    useResourceMaterialsAPI();

  const [materials, setMaterials] = useState<ResourceMaterial[]>([]);
  const [selectedDetail, setSelectedDetail] =
    useState<ResourceMaterialDetail | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const [copyTarget, setCopyTarget] = useState<ResourceMaterial | null>(null);
  const [copying, setCopying] = useState(false);

  const fetchMaterials = useCallback(async () => {
    const result = await listMaterials("individual");
    setMaterials(result.materials);
  }, [listMaterials]);

  useEffect(() => {
    fetchMaterials();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleViewDetail = async (material: ResourceMaterial) => {
    const detail = await getMaterialDetail(material.id);
    if (detail) {
      setSelectedDetail(detail);
      setShowDetail(true);
    }
  };

  const handleCopyClick = (material: ResourceMaterial) => {
    setCopyTarget(material);
    setCopyDialogOpen(true);
  };

  const handleConfirmCopy = async () => {
    if (!copyTarget) return;
    setCopying(true);
    try {
      await copyMaterial(copyTarget.id, "individual");
      toast.success(`已複製「${copyTarget.name}」到我的教材`);
      setCopyDialogOpen(false);
      setCopyTarget(null);
      fetchMaterials(); // Refresh to update copied_today status
    } catch {
      toast.error("複製失敗，請稍後再試");
    } finally {
      setCopying(false);
    }
  };

  const getLevelBadgeColor = (level: string | null) => {
    const colors: Record<string, string> = {
      preA: "bg-gray-100 text-gray-700",
      A1: "bg-green-100 text-green-700",
      A2: "bg-blue-100 text-blue-700",
      B1: "bg-yellow-100 text-yellow-700",
      B2: "bg-orange-100 text-orange-700",
      C1: "bg-red-100 text-red-700",
      C2: "bg-purple-100 text-purple-700",
    };
    return level ? (colors[level] ?? "bg-gray-100 text-gray-700") : "";
  };

  if (showDetail && selectedDetail) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowDetail(false);
              setSelectedDetail(null);
            }}
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            返回列表
          </Button>
        </div>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{selectedDetail.name}</h1>
            {selectedDetail.description && (
              <p className="text-muted-foreground mt-1">
                {selectedDetail.description}
              </p>
            )}
            <div className="flex gap-2 mt-2">
              {selectedDetail.level && (
                <Badge
                  className={getLevelBadgeColor(selectedDetail.level)}
                  variant="secondary"
                >
                  {selectedDetail.level}
                </Badge>
              )}
              <Badge variant="outline">
                <Layers className="w-3 h-3 mr-1" />
                {selectedDetail.lesson_count} 個單元
              </Badge>
            </div>
          </div>
        </div>

        <Accordion type="multiple" className="space-y-2">
          {selectedDetail.lessons.map((lesson) => (
            <AccordionItem
              key={lesson.id}
              value={`lesson-${lesson.id}`}
              className="border rounded-lg px-4"
            >
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-muted-foreground" />
                  <span className="font-medium">{lesson.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {lesson.content_count} 內容
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-2 pl-6">
                  {lesson.contents.map((content) => (
                    <div
                      key={content.id}
                      className="flex items-center gap-2 py-2 px-3 rounded-md bg-muted/50"
                    >
                      <FileText className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">{content.title}</span>
                      <Badge variant="outline" className="text-xs ml-auto">
                        {content.item_count} 項目
                      </Badge>
                    </div>
                  ))}
                  {lesson.contents.length === 0 && (
                    <p className="text-sm text-muted-foreground py-2">
                      暫無內容
                    </p>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Package className="w-6 h-6 text-orange-500" />
        <div>
          <h1 className="text-2xl font-bold">資源教材包</h1>
          <p className="text-muted-foreground text-sm">
            瀏覽並複製公開的教材資源到你的教材庫
          </p>
        </div>
      </div>

      {/* Loading */}
      {loading && materials.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">載入中...</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && materials.length === 0 && (
        <div className="text-center py-12">
          <Package className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground">
            目前沒有可用的資源教材
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            稍後再來看看吧
          </p>
        </div>
      )}

      {/* Materials Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {materials.map((material) => (
          <Card
            key={material.id}
            className="hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleViewDetail(material)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <CardTitle className="text-base line-clamp-2">
                  {material.name}
                </CardTitle>
                {material.level && (
                  <Badge
                    className={getLevelBadgeColor(material.level)}
                    variant="secondary"
                  >
                    {material.level}
                  </Badge>
                )}
              </div>
              {material.description && (
                <CardDescription className="line-clamp-2">
                  {material.description}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                <span className="flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5" />
                  {material.lesson_count} 單元
                </span>
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  {material.content_count} 內容
                </span>
              </div>
              <Button
                size="sm"
                className="w-full"
                variant={material.copied_today ? "secondary" : "default"}
                disabled={material.copied_today}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCopyClick(material);
                }}
              >
                {material.copied_today ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    今日已複製
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-1" />
                    複製到我的教材
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Copy Confirmation Dialog */}
      <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>確認複製教材</DialogTitle>
            <DialogDescription>
              將「{copyTarget?.name}
              」複製到你的教材庫中。複製後你可以自由編輯內容。
              <br />
              <span className="text-xs text-muted-foreground">
                每個課程每天最多可複製 1 次
              </span>
            </DialogDescription>
          </DialogHeader>
          {copyTarget && (
            <div className="py-2 text-sm space-y-1">
              <p>
                <span className="font-medium">課程名稱：</span>
                {copyTarget.name}
              </p>
              <p>
                <span className="font-medium">包含：</span>
                {copyTarget.lesson_count} 個單元、{copyTarget.content_count}{" "}
                個內容
              </p>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCopyDialogOpen(false)}
              disabled={copying}
            >
              取消
            </Button>
            <Button onClick={handleConfirmCopy} disabled={copying}>
              {copying ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  複製中...
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-1" />
                  確認複製
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
