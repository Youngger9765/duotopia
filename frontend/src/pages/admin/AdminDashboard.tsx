import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Crown, DollarSign } from "lucide-react";
import AdminSubscriptionDashboard from "./AdminSubscriptionDashboard";
import AdminBillingDashboard from "./AdminBillingDashboard";

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("subscription");

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Crown className="h-8 w-8 text-yellow-600" />
            管理員控制台
          </h1>
          <p className="text-muted-foreground mt-1">訂閱管理、費用監控</p>
        </div>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <TabsList className="grid w-full max-w-[500px] grid-cols-2 h-14 bg-white border-2 border-gray-200 p-1">
            <TabsTrigger
              value="subscription"
              className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-gradient-to-r data-[state=active]:from-yellow-500 data-[state=active]:to-yellow-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
            >
              <Crown className="h-5 w-5" />
              訂閱管理
            </TabsTrigger>
            <TabsTrigger
              value="billing"
              className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-gradient-to-r data-[state=active]:from-green-500 data-[state=active]:to-emerald-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200"
            >
              <DollarSign className="h-5 w-5" />
              GCP 費用
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
        </Tabs>
      </div>
    </div>
  );
}
