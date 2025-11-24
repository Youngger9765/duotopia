import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";

interface AdminLayoutProps {
  title: string;
  description: string;
  icon: LucideIcon;
  children: ReactNode;
}

/**
 * 統一的 Admin 頁面 Layout Component
 *
 * 確保所有 Admin 頁面有一致的：
 * - Container 寬度 (max-w-7xl)
 * - Header 樣式 (text-3xl, blue-600 icon)
 * - 間距系統 (py-8, mb-8, space-y-6)
 * - 背景顏色 (bg-gray-50)
 */
export default function AdminLayout({
  title,
  description,
  icon: Icon,
  children,
}: AdminLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* 統一的 Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Icon className="h-8 w-8 text-blue-600" />
            {title}
          </h1>
          <p className="text-muted-foreground mt-2 text-base">{description}</p>
        </div>

        {/* 內容區域 */}
        <div className="space-y-6">{children}</div>
      </div>
    </div>
  );
}
// test
// trigger deployment
// debug test
