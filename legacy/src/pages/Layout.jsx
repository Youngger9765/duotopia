
import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { Mic, BookOpen, BarChart3, Settings, School, LayoutGrid, Building2, LogOut, ListChecks, Undo, GraduationCap, User } from "lucide-react";
import { User as UserEntity } from "@/api/entities"; // Renamed User from entities to avoid conflict
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button"; // Assuming Button component is available from this path

const studentNavItems = [
  {
    title: "作業",
    url: createPageUrl("Assignments"), // Changed URL for Assignments
    icon: ListChecks,
  },
  {
    title: "課堂練習", // New item added
    url: createPageUrl("StudentDashboard"),
    icon: BookOpen,
  },
  {
    title: "統計報告",
    url: createPageUrl("Statistics"),
    icon: BarChart3,
  },
];

export default function Layout({ children, currentPageName }) {
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState(null); // **新增：當前用戶狀態**

  useEffect(() => {
    // **核心修正：移除 studentView 相關邏輯，因為學生現在是真實登入**
    const loadCurrentUser = async () => {
      try {
        const user = await UserEntity.me();
        setCurrentUser(user);
        console.log("當前登入用戶:", user);
      } catch (error) {
        console.error("載入當前用戶失敗:", error);
        setCurrentUser(null);
      }
    };

    loadCurrentUser();
  }, [location.pathname]);

  const getDefaultPageUrl = () => {
    // **核心修正：將 Portal 設為預設頁面**
    return createPageUrl("Portal");
  };

  // When on root path, redirect to the default page.
  useEffect(() => {
    if (location.pathname === '/') {
      window.location.href = getDefaultPageUrl();
    }
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      // **核心修正：確保完全清理 session**
      await UserEntity.logout();
      
      // 清理任何本地儲存的資料
      sessionStorage.clear();
      localStorage.removeItem('studentView'); // 如果有的話
      
      // 跳轉到安全的登出頁面
      window.location.href = createPageUrl("Portal");
    } catch (error) {
      console.error('登出過程發生錯誤:', error);
      // 即使出錯也強制跳轉
      window.location.href = createPageUrl("Portal");
    }
  };

  // **核心修正：移除不安全的 exitStudentView 函式**
  // 因為現在學生是真實登入，不需要"退出學生視角"的概念

  // **核心修正：針對統一登入頁面隱藏側邊欄**
  if (currentPageName === 'Portal') {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <SidebarProvider>
      <style>{`
        :root {
          --primary: 168 85% 45%;
          --primary-foreground: 210 40% 98%;
          --secondary: 210 40% 96%;
          --secondary-foreground: 222.2 84% 4.9%;
          --accent: 168 85% 95%;
          --accent-foreground: 168 85% 25%;
          --background: 0 0% 100%;
          --foreground: 222.2 84% 4.9%;
          --muted: 210 40% 96%;
          --muted-foreground: 215.4 16.3% 46.9%;
          --border: 214.3 31.8% 91.4%;
          --ring: 168 85% 45%;
        }
        
        body {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          background: linear-gradient(135deg, #f8fffe 0%, #f0fdfc 100%);
          min-height: 100vh;
        }
        
        .gradient-bg {
          background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
        }
        
        .glass-effect {
          backdrop-filter: blur(12px);
          background: rgba(255, 255, 255, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }
      `}</style>
      <div className="min-h-screen flex w-full">
        <Sidebar className="border-r border-gray-100 bg-white/50 backdrop-blur-sm flex flex-col">
          <SidebarHeader className="border-b border-gray-100 p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 gradient-bg rounded-xl flex items-center justify-center shadow-lg">
                <Mic className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-gray-900 text-lg">朗讀評估</h2>
                <p className="text-xs text-gray-500">AI語音分析系統</p>
              </div>
            </div>
          </SidebarHeader>
          
          <SidebarContent className="p-4 flex-grow flex flex-col">
            <div>
              <SidebarGroup>
                <SidebarGroupLabel className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2">
                  功能導航
                </SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {studentNavItems.map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton 
                          asChild 
                          className={`hover:bg-teal-50 hover:text-teal-700 transition-all duration-200 rounded-xl mb-1 ${
                            location.pathname === item.url ? 'bg-teal-50 text-teal-700 shadow-sm' : ''
                          }`}
                        >
                          <Link to={item.url} className="flex items-center gap-3 px-4 py-3">
                            <item.icon className="w-5 h-5" />
                            <span className="font-medium">{item.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
              
              {/* **核心修正：根據用戶角色動態顯示管理功能** */}
              {currentUser?.role !== 'student' && (
                <SidebarGroup>
                  <SidebarGroupLabel className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2">
                    管理功能
                  </SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      <SidebarMenuItem>
                        <SidebarMenuButton 
                          asChild 
                          className={`hover:bg-teal-50 hover:text-teal-700 transition-all duration-200 rounded-xl mb-1 ${
                            location.pathname === createPageUrl("AssignHomework") ? 'bg-teal-50 text-teal-700 shadow-sm' : ''
                          }`}
                        >
                          <Link to={createPageUrl("AssignHomework")} className="flex items-center gap-3 px-4 py-3">
                            <ListChecks className="w-5 h-5" />
                            <span className="font-medium">指派作業</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                      <SidebarMenuItem>
                        <SidebarMenuButton 
                          asChild 
                          className={`hover:bg-teal-50 hover:text-teal-700 transition-all duration-200 rounded-xl mb-1 ${
                            location.pathname === createPageUrl("GradingDashboard") ? 'bg-teal-50 text-teal-700 shadow-sm' : ''
                          }`}
                        >
                          <Link to={createPageUrl("GradingDashboard")} className="flex items-center gap-3 px-4 py-3">
                            <GraduationCap className="w-5 h-5" />
                            <span className="font-medium">批改作業</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                      <SidebarMenuItem>
                        <SidebarMenuButton 
                          asChild 
                          className={`hover:bg-teal-50 hover:text-teal-700 transition-all duration-200 rounded-xl mb-1 ${
                            location.pathname === createPageUrl("TeacherDashboard") ? 'bg-teal-50 text-teal-700 shadow-sm' : ''
                          }`}
                        >
                          <Link to={createPageUrl("TeacherDashboard")} className="flex items-center gap-3 px-4 py-3">
                            <School className="w-5 h-5" />
                            <span className="font-medium">教師管理台</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                      <SidebarMenuItem>
                        <SidebarMenuButton 
                          asChild 
                          className={`hover:bg-teal-50 hover:text-teal-700 transition-all duration-200 rounded-xl mb-1 ${
                            location.pathname === createPageUrl("SchoolManagement") ? 'bg-teal-50 text-teal-700 shadow-sm' : ''
                          }`}
                        >
                          <Link to={createPageUrl("SchoolManagement")} className="flex items-center gap-3 px-4 py-3">
                            <Building2 className="w-5 h-5" />
                            <span className="font-medium">校級師生管理</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              )}
            </div>

            <div className="mt-auto">
              <SidebarMenu>
                <SidebarMenuItem>
                  <div className="px-4 py-2 mb-2">
                    {/* **修正：顯示當前真實用戶身份** */}
                    {currentUser ? (
                      <div className="text-xs text-gray-500 mb-1">
                        <div className="flex items-center gap-1">
                          {currentUser.role === 'student' ? (
                            <User className="w-3 h-3" />
                          ) : (
                            <GraduationCap className="w-3 h-3" />
                          )}
                          <span>
                            {currentUser.role === 'student' ? '學生' : '教師'}: {currentUser.full_name || currentUser.email}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400 mb-1">
                        未登入
                      </div>
                    )}
                  </div>
                  <SidebarMenuButton 
                    onClick={handleLogout}
                    className="hover:bg-red-50 hover:text-red-700 transition-all duration-200 rounded-xl mb-1 text-gray-600"
                  >
                    <div className="flex items-center gap-3 px-4 py-3">
                      <LogOut className="w-5 h-5" />
                      <span className="font-medium">登出</span>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </div>
          </SidebarContent>
        </Sidebar>

        <main className="flex-1 flex flex-col">
          <header className="bg-white/80 backdrop-blur-sm border-b border-gray-100 px-6 py-4 md:hidden">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="hover:bg-gray-100 p-2 rounded-lg transition-colors duration-200" />
              <h1 className="text-xl font-bold text-gray-900">朗讀評估</h1>
            </div>
          </header>

          <div className="flex-1 overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
