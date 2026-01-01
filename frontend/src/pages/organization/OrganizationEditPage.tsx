import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Breadcrumb } from "@/components/organization/Breadcrumb";

export default function OrganizationEditPage() {
  const { orgId } = useParams<{ orgId: string }>();

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[{ label: "組織管理" }, { label: "組織詳情" }]}
      />

      <Card>
        <CardHeader>
          <CardTitle>組織編輯 - {orgId}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">組織 CRUD 功能開發中...</p>
          <p className="text-sm text-gray-500 mt-2">
            這裡將顯示組織的詳細資訊和編輯表單
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
