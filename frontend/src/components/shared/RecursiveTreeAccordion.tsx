import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Edit, Trash2, GripVertical, LucideIcon } from "lucide-react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

export interface TreeNodeConfig {
  // Display config
  icon: LucideIcon;
  colorScheme: {
    bg: string;
    text: string;
    iconBg: string;
    iconText: string;
    hoverBg?: string;
  };

  // Data keys
  idKey: string; // 'id'
  nameKey: string; // 'name'
  descriptionKey?: string; // 'description'
  childrenKey?: string; // 'lessons', 'contents', etc.

  // Display fields (badges, metadata)
  displayFields?: {
    key: string;
    icon?: LucideIcon;
    suffix?: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render?: (value: any, item: any) => React.ReactNode;
    mobileOnly?: boolean;
    desktopOnly?: boolean;
  }[];

  // Behavior
  canEdit?: boolean;
  canDelete?: boolean;
  canDrag?: boolean;
  canExpand?: boolean; // false for leaf nodes

  // Child config (for next level)
  childConfig?: TreeNodeConfig;

  // Custom empty message
  emptyMessage?: string;
}

interface RecursiveTreeNodeProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  config: TreeNodeConfig;
  level: number;
  index: number;
  parentId?: string | number;

  // Event handlers
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onEdit?: (item: any, level: number, parentId?: string | number) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onDelete?: (item: any, level: number, parentId?: string | number) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onClick?: (item: any, level: number, parentId?: string | number) => void;
  onCreate?: (level: number, parentId: string | number) => void;
  onReorder?: (
    fromIndex: number,
    toIndex: number,
    level: number,
    parentId?: string | number
  ) => void;

  // Accordion state
  expandedValue: string;
  onExpandedChange: (value: string) => void;
}

function RecursiveTreeNode({
  data,
  config,
  level,
  index,
  parentId,
  onEdit,
  onDelete,
  onClick,
  onCreate,
  onReorder,
}: RecursiveTreeNodeProps) {
  const itemId = data[config.idKey];
  const itemName = data[config.nameKey];
  const itemDescription = config.descriptionKey ? data[config.descriptionKey] : null;
  const children = config.childrenKey ? data[config.childrenKey] : null;

  const accordionValue = `${level}-${itemId}`;

  // Child accordion state (for next level)
  const [childExpandedValue, setChildExpandedValue] = useState("");

  // @dnd-kit sortable hook
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: itemId,
    data: {
      type: "tree-node",
      level,
      index,
      parentId,
    },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // Render node (can be accordion or simple div)
  const nodeContent = (
    <div ref={setNodeRef} style={style} className="relative" data-dragging={isDragging ? "true" : "false"}>
      {config.canExpand !== false ? (
        // Expandable node - wrap in styled container
        <div className={`${config.colorScheme.bg} rounded-lg mb-2`}>
          <AccordionItem
            value={accordionValue}
            className={`border-none transition-opacity duration-200 ${isDragging ? "opacity-30" : ""}`}
          >
          <AccordionTrigger className="hover:no-underline group px-4 sm:px-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between w-full gap-3">
              <div className="flex items-start sm:items-center space-x-2 sm:space-x-3 flex-1">
                {/* Drag handle */}
                {config.canDrag && (
                  <div
                    {...attributes}
                    {...listeners}
                    className="hidden sm:block cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity select-none"
                    title="拖曳以重新排序"
                  >
                    <GripVertical className="h-5 w-5 text-gray-400" />
                  </div>
                )}

                {/* Icon */}
                <div className={`w-8 h-8 sm:w-10 sm:h-10 ${config.colorScheme.iconBg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                  <config.icon className={`h-4 w-4 sm:h-5 sm:w-5 ${config.colorScheme.iconText}`} />
                </div>

                {/* Name and description */}
                <div className="text-left flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="font-semibold text-sm sm:text-base dark:text-gray-100 truncate">
                      {itemName}
                    </h4>
                    {config.canEdit && onEdit && (
                      <div
                        className="h-7 w-7 sm:h-6 sm:w-6 p-0 inline-flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer flex-shrink-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          onEdit(data, level, parentId);
                        }}
                      >
                        <Edit className="h-4 w-4 sm:h-3 sm:w-3 dark:text-gray-400" />
                      </div>
                    )}
                  </div>
                  {itemDescription && (
                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">
                      {itemDescription}
                    </p>
                  )}

                  {/* Tags below description */}
                  {data.tags && Array.isArray(data.tags) && data.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {data.tags.map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Mobile: Display fields */}
                  {config.displayFields && (
                    <div className="flex items-center gap-2 mt-2 sm:hidden">
                      {config.displayFields
                        .filter((field) => !field.desktopOnly)
                        .map((field, idx) => (
                          <div key={idx}>
                            {field.render
                              ? field.render(data[field.key], data)
                              : field.icon && (
                                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                                    <field.icon className="h-3 w-3 mr-1" />
                                    <span>{data[field.key]}{field.suffix}</span>
                                  </div>
                                )}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Desktop: Display fields and delete */}
              <div className="hidden sm:flex items-center space-x-4 flex-shrink-0">
                {config.displayFields &&
                  config.displayFields
                    .filter((field) => !field.mobileOnly)
                    .map((field, idx) => (
                      <div key={idx}>
                        {field.render
                          ? field.render(data[field.key], data)
                          : field.icon && (
                              <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                                <field.icon className="h-4 w-4 mr-1" />
                                <span>{data[field.key]}{field.suffix}</span>
                              </div>
                            )}
                      </div>
                    ))}
                {config.canDelete && onDelete && (
                  <div
                    className="h-8 w-8 p-0 inline-flex items-center justify-center rounded hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(data, level, parentId);
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" />
                  </div>
                )}
              </div>

              {/* Mobile: Delete button */}
              {config.canDelete && onDelete && (
                <div className="sm:hidden absolute right-2 top-3">
                  <div
                    className="h-8 w-8 p-0 inline-flex items-center justify-center rounded hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(data, level, parentId);
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" />
                  </div>
                </div>
              )}
            </div>
          </AccordionTrigger>

          <AccordionContent>
            <div className={`${level > 0 ? 'pl-14' : 'pl-14'} pr-4 space-y-3`}>
              {config.childConfig ? (
                <>
                  <SortableContext
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    items={children?.map((child: any) => child[config.childConfig!.idKey]) || []}
                    strategy={verticalListSortingStrategy}
                  >
                    <Accordion
                      type="single"
                      collapsible
                      className="w-full"
                      value={childExpandedValue}
                      onValueChange={setChildExpandedValue}
                    >
                      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                      {children && children.length > 0 && children.map((child: any, childIndex: number) => (
                        <RecursiveTreeNode
                          key={child[config.childConfig!.idKey]}
                          data={child}
                          config={config.childConfig!}
                          level={level + 1}
                          index={childIndex}
                          parentId={itemId}
                          onEdit={onEdit}
                          onDelete={onDelete}
                          onClick={onClick}
                          onCreate={onCreate}
                          onReorder={onReorder}
                          expandedValue={childExpandedValue}
                          onExpandedChange={setChildExpandedValue}
                        />
                      ))}
                    </Accordion>
                  </SortableContext>
                  {onCreate && (
                    <button
                      onClick={() => onCreate(level + 1, itemId)}
                      className="w-full px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg border border-blue-200 hover:border-blue-300 transition-colors flex items-center justify-center gap-2"
                    >
                      <span>+</span>
                      <span>新增{config.childConfig?.nameKey === 'name' ? '單元' : '內容'}</span>
                    </button>
                  )}
                </>
              ) : (
                <div className="space-y-3">
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {children && children.length > 0 && children.map((child: any) => (
                    <div
                      key={child[config.childConfig!.idKey]}
                      className="p-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 cursor-pointer transition-colors"
                      onClick={() => onClick?.(child, level + 1, itemId)}
                    >
                      {child.name || child.title || "未命名"}
                    </div>
                  ))}
                </div>
              )}
              {!children || children.length === 0 ? (
                <p className="text-sm text-gray-500 py-4 text-center">
                  {config.childConfig?.emptyMessage || "暫無內容"}
                </p>
              ) : null}
            </div>
          </AccordionContent>
          </AccordionItem>
        </div>
      ) : (
        // Leaf node (no children)
        <div
          className={`p-3 ${config.colorScheme.bg} ${config.colorScheme.hoverBg || 'hover:bg-gray-100'} rounded-lg border border-gray-200 cursor-pointer transition-all duration-200 group ${isDragging ? "opacity-30" : ""}`}
          onClick={() => onClick?.(data, level, parentId)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              {config.canDrag && (
                <div
                  {...attributes}
                  {...listeners}
                  className="cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity select-none flex-shrink-0"
                >
                  <GripVertical className="h-4 w-4 text-gray-400" />
                </div>
              )}
              <div className={`w-8 h-8 ${config.colorScheme.iconBg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                <config.icon className={`h-4 w-4 ${config.colorScheme.iconText}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className={`font-medium text-sm ${config.colorScheme.text} truncate`}>
                    {itemName}
                  </p>
                </div>
                {itemDescription && (
                  <p className="text-xs text-gray-500 truncate">{itemDescription}</p>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0">
              {config.displayFields?.map((field, idx) => (
                <span key={idx} className="text-sm text-gray-500">
                  {field.render ? field.render(data[field.key], data) : `${data[field.key]}${field.suffix || ''}`}
                </span>
              ))}
              {config.canDelete && onDelete && (
                <div
                  className="h-6 w-6 p-0 inline-flex items-center justify-center rounded hover:bg-red-50 cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(data, level, parentId);
                  }}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </div>
              )}
            </div>
          </div>
          {/* Tags below for leaf nodes */}
          {data.tags && Array.isArray(data.tags) && data.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2 ml-11">
              {data.tags.map((tag: string, index: number) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );

  return nodeContent;
}

interface RecursiveTreeAccordionProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  config: TreeNodeConfig;
  title?: string;
  showCreateButton?: boolean;
  createButtonText?: string;
  onCreateClick?: () => void;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onEdit?: (item: any, level: number, parentId?: string | number) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onDelete?: (item: any, level: number, parentId?: string | number) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onClick?: (item: any, level: number, parentId?: string | number) => void;
  onCreate?: (level: number, parentId: string | number) => void;
  onReorder?: (
    fromIndex: number,
    toIndex: number,
    level: number,
    parentId?: string | number
  ) => void;
}

export function RecursiveTreeAccordion({
  data,
  config,
  title,
  showCreateButton,
  createButtonText = "新增",
  onCreateClick,
  onEdit,
  onDelete,
  onClick,
  onCreate,
  onReorder,
}: RecursiveTreeAccordionProps) {
  const [expandedValue, setExpandedValue] = useState("");
  const [activeId, setActiveId] = useState<string | number | null>(null);

  // Set up sensors for drag detection
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, // 5px movement required to start drag (reduced for better UX)
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Handle drag start
  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id);
  };

  // Handle drag end
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    console.log('[RecursiveTreeAccordion] Drag End:', {
      activeId: active.id,
      overId: over?.id,
      hasOnReorder: !!onReorder
    });

    if (over && active.id !== over.id && onReorder) {
      const activeData = active.data.current;
      const overData = over.data.current;

      console.log('[RecursiveTreeAccordion] Active/Over Data:', {
        active: activeData,
        over: overData
      });

      // Only reorder if they're at the same level and same parent
      if (
        activeData &&
        overData &&
        activeData.level === overData.level &&
        activeData.parentId === overData.parentId
      ) {
        const level = activeData.level;
        const parentId = activeData.parentId;

        // Use the index from the data directly
        const oldIndex = activeData.index;
        const newIndex = overData.index;

        if (oldIndex !== undefined && newIndex !== undefined) {
          console.log('[RecursiveTreeAccordion] Calling onReorder:', {
            oldIndex,
            newIndex,
            level,
            parentId
          });
          onReorder(oldIndex, newIndex, level, parentId);
        } else {
          console.warn('[RecursiveTreeAccordion] Invalid indices:', { oldIndex, newIndex });
        }
      } else {
        console.warn('[RecursiveTreeAccordion] Reorder rejected - different level or parent');
      }
    }

    setActiveId(null);
  };

  // Recursively find the active item in the tree with its config
  const findItemById = (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    items: any[],
    id: string | number,
    cfg: TreeNodeConfig
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ): { item: any; config: TreeNodeConfig } | null => {
    for (const item of items) {
      if (item[cfg.idKey] === id) {
        return { item, config: cfg };
      }
      if (cfg.childConfig && cfg.childrenKey && item[cfg.childrenKey]) {
        const found = findItemById(
          item[cfg.childrenKey],
          id,
          cfg.childConfig
        );
        if (found) return found;
      }
    }
    return null;
  };

  const activeData = activeId ? findItemById(data, activeId, config) : null;
  const activeItem = activeData?.item;
  const activeConfig = activeData?.config || config;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div>
        {(title || showCreateButton) && (
          <div className="flex items-center justify-between mb-4">
            {title && <h3 className="text-lg font-semibold">{title}</h3>}
            {showCreateButton && onCreateClick && (
              <button
                onClick={onCreateClick}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {createButtonText}
              </button>
            )}
          </div>
        )}

        {data.length > 0 ? (
          <SortableContext
            items={data.map((item) => item[config.idKey])}
            strategy={verticalListSortingStrategy}
          >
            <Accordion
              type="single"
              collapsible
              className="w-full"
              value={expandedValue}
              onValueChange={setExpandedValue}
            >
              {data.map((item, index) => (
                <RecursiveTreeNode
                  key={item[config.idKey]}
                  data={item}
                  config={config}
                  level={0}
                  index={index}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onClick={onClick}
                  onCreate={onCreate}
                  onReorder={onReorder}
                  expandedValue={expandedValue}
                  onExpandedChange={setExpandedValue}
                />
              ))}
            </Accordion>
          </SortableContext>
        ) : (
          <div className="text-center py-12 text-gray-500">
            {config.emptyMessage || "暫無資料"}
          </div>
        )}
      </div>

      {/* Drag overlay for visual feedback */}
      <DragOverlay>
        {activeItem && activeConfig ? (
          <div className="bg-blue-500 text-white px-3 py-2 rounded-lg shadow-lg text-sm font-medium">
            移動: {activeItem[activeConfig.nameKey] || activeItem.name || activeItem.title || "項目"}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
