import { TreeNodeConfig } from "./RecursiveTreeAccordion";
import { BookOpen, ListOrdered, FileText, Clock } from "lucide-react";

// Content layer config (leaf nodes)
const contentConfig: TreeNodeConfig = {
  icon: FileText,
  colorScheme: {
    bg: "bg-gray-50",
    text: "text-gray-900",
    iconBg: "bg-purple-100",
    iconText: "text-purple-600",
    hoverBg: "hover:bg-gray-100",
  },
  idKey: "id",
  nameKey: "title",
  descriptionKey: "items_count", // Shows "X 個項目"
  canEdit: false,
  canDelete: true,
  canDrag: true,
  canExpand: false, // Leaf node
  displayFields: [],
  emptyMessage: "暫無內容",
};

// Lesson layer config
const lessonConfig: TreeNodeConfig = {
  icon: ListOrdered,
  colorScheme: {
    bg: "bg-white",
    text: "text-gray-900",
    iconBg: "bg-green-100",
    iconText: "text-green-600",
  },
  idKey: "id",
  nameKey: "name",
  descriptionKey: "description",
  childrenKey: "contents",
  canEdit: true,
  canDelete: true,
  canDrag: true,
  canExpand: true,
  displayFields: [
    {
      key: "estimated_minutes",
      icon: Clock,
      suffix: " 分鐘",
      render: (value) => (
        <span className="text-sm text-gray-500">{value || 30} 分鐘</span>
      ),
    },
  ],
  childConfig: contentConfig,
  emptyMessage: "暫無單元",
};

// Program layer config (top level)
export const programTreeConfig: TreeNodeConfig = {
  icon: BookOpen,
  colorScheme: {
    bg: "bg-white border border-gray-200 shadow-sm hover:shadow-md",
    text: "text-gray-900",
    iconBg: "bg-blue-100 dark:bg-blue-900",
    iconText: "text-blue-600 dark:text-blue-400",
  },
  idKey: "id",
  nameKey: "name",
  descriptionKey: "description",
  childrenKey: "lessons",
  canEdit: true,
  canDelete: true,
  canDrag: true,
  canExpand: true,
  displayFields: [
    {
      key: "level",
      render: (level: string) => {
        const levelColors: Record<string, string> = {
          A1: "bg-green-100 text-green-800",
          A2: "bg-blue-100 text-blue-800",
          B1: "bg-yellow-100 text-yellow-800",
          B2: "bg-orange-100 text-orange-800",
          C1: "bg-red-100 text-red-800",
          C2: "bg-purple-100 text-purple-800",
        };
        const color = levelColors[level?.toUpperCase()] || "bg-gray-100 text-gray-800";
        return (
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
            {level || "A1"}
          </span>
        );
      },
    },
    {
      key: "estimated_hours",
      icon: Clock,
      render: (hours) =>
        hours ? (
          <>
            <span className="hidden sm:inline">{hours} 小時</span>
            <span className="sm:hidden">{hours}h</span>
          </>
        ) : null,
    },
  ],
  childConfig: lessonConfig,
  emptyMessage: "暫無課程",
};

// Usage example in a component:
/*
import { RecursiveTreeAccordion } from "@/components/shared/RecursiveTreeAccordion";
import { programTreeConfig } from "@/components/shared/programTreeConfig";

function MyComponent() {
  const [programs, setPrograms] = useState<Program[]>([]);

  return (
    <RecursiveTreeAccordion
      data={programs}
      config={programTreeConfig}
      title="課程列表"
      showCreateButton
      createButtonText="新增課程"
      onCreateClick={() => handleCreateProgram()}
      onEdit={(item, level, parentId) => {
        // level 0 = program, 1 = lesson, 2 = content
        if (level === 0) handleEditProgram(item.id);
        else if (level === 1) handleEditLesson(parentId, item.id);
      }}
      onDelete={(item, level, parentId) => {
        if (level === 0) handleDeleteProgram(item.id);
        else if (level === 1) handleDeleteLesson(parentId, item.id);
        else if (level === 2) handleDeleteContent(parentId, item.id);
      }}
      onClick={(item, level, parentId) => {
        if (level === 2) handleContentClick(item); // Only handle content clicks
      }}
      onReorder={(fromIndex, toIndex, level, parentId) => {
        if (level === 0) handleReorderPrograms(fromIndex, toIndex);
        else if (level === 1) handleReorderLessons(parentId, fromIndex, toIndex);
        else if (level === 2) handleReorderContents(parentId, fromIndex, toIndex);
      }}
    />
  );
}
*/
