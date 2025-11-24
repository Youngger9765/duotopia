import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Crown, DollarSign, AlertTriangle } from "lucide-react";
import AdminSubscriptionDashboard from "./AdminSubscriptionDashboard";
import AdminBillingDashboard from "./AdminBillingDashboard";
import AdminAudioErrorDashboard from "./AdminAudioErrorDashboard";
import AdminLayout from "@/components/admin/AdminLayout";

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("subscription");

  return (
    <AdminLayout
      title="管理員控制台"
      description="訂閱管理、費用監控、錯誤追蹤"
      icon={Crown}
    >
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full max-w-[750px] grid-cols-3 h-14 bg-white border-2 border-gray-200 p-1">
          <TabsTrigger
            value="subscription"
            className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <Crown className="h-5 w-5" />
            訂閱管理
          </TabsTrigger>
          <TabsTrigger
            value="billing"
            className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <DollarSign className="h-5 w-5" />
            GCP 費用
          </TabsTrigger>
          <TabsTrigger
            value="audio-errors"
            className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
          >
            <AlertTriangle className="h-5 w-5" />
            錄音錯誤
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
      </Tabs>
    </AdminLayout>
  );
}
