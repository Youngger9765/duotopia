import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Crown, DollarSign, AlertTriangle, Building } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import AdminSubscriptionDashboard from "./AdminSubscriptionDashboard";
import AdminBillingDashboard from "./AdminBillingDashboard";
import AdminAudioErrorDashboard from "./AdminAudioErrorDashboard";
import AdminLayout from "@/components/admin/AdminLayout";
// import TeacherUsageCard from "@/components/organization/TeacherUsageCard";

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("subscription");
  const navigate = useNavigate();

  return (
    <AdminLayout
      title="管理員控制台"
      description="訂閱管理、費用監控、錯誤追蹤"
      icon={Crown}
    >
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4 md:space-y-6"
      >
        <TabsList className="grid w-full max-w-[1000px] grid-cols-4 h-auto md:h-14 bg-white border-2 border-gray-200 p-1">
          <TabsTrigger
            value="subscription"
            className="flex items-center justify-center gap-1.5 md:gap-2 text-xs md:text-base font-semibold py-2 md:py-0 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <Crown className="h-4 w-4 md:h-5 md:w-5 flex-shrink-0" />
            <span className="hidden sm:inline">訂閱管理</span>
            <span className="sm:hidden">訂閱</span>
          </TabsTrigger>
          <TabsTrigger
            value="billing"
            className="flex items-center justify-center gap-1.5 md:gap-2 text-xs md:text-base font-semibold py-2 md:py-0 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <DollarSign className="h-4 w-4 md:h-5 md:w-5 flex-shrink-0" />
            <span className="hidden sm:inline">GCP 費用</span>
            <span className="sm:hidden">費用</span>
          </TabsTrigger>
          <TabsTrigger
            value="audio-errors"
            className="flex items-center justify-center gap-1.5 md:gap-2 text-xs md:text-base font-semibold py-2 md:py-0 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <AlertTriangle className="h-4 w-4 md:h-5 md:w-5 flex-shrink-0" />
            <span className="hidden sm:inline">錄音錯誤</span>
            <span className="sm:hidden">錯誤</span>
          </TabsTrigger>
          <TabsTrigger
            value="organizations"
            className="flex items-center justify-center gap-1.5 md:gap-2 text-xs md:text-base font-semibold py-2 md:py-0 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <Building className="h-4 w-4 md:h-5 md:w-5 flex-shrink-0" />
            <span className="hidden sm:inline">組織管理</span>
            <span className="sm:hidden">組織</span>
          </TabsTrigger>
        </TabsList>

        {/* Subscription Management Tab */}
        <TabsContent value="subscription" className="space-y-4">
          <AdminSubscriptionDashboard />
        </TabsContent>

        {/* GCP Billing Tab */}
        <TabsContent value="billing" className="space-y-4">
          <AdminBillingDashboard />
        </TabsContent>

        {/* Audio Error Monitoring Tab */}
        <TabsContent value="audio-errors" className="space-y-4">
          <AdminAudioErrorDashboard />
        </TabsContent>

        {/* Organization Management Tab */}
        <TabsContent value="organizations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>組織管理</CardTitle>
              <CardDescription>
                創建和管理機構，分配組織擁有人權限
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <Button
                  onClick={() => navigate("/admin/organizations/create")}
                  className="flex items-center gap-2"
                >
                  <Building className="h-4 w-4" />
                  創建機構
                </Button>
              </div>
              <p className="text-sm text-gray-600">
                機構創建功能可以讓平台管理員為已註冊的老師創建組織並指派擁有人權限。
              </p>

              {/* Add teacher usage example (optional - requires org ID) */}
              {/* <TeacherUsageCard organizationId="example-org-id" /> */}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </AdminLayout>
  );
}
