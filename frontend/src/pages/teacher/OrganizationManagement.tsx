import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import TeacherLayout from "@/components/TeacherLayout";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

export default function OrganizationManagement() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);

  const [formData, setFormData] = useState({
    name: "",
    display_name: "",
    description: "",
    contact_email: "",
    contact_phone: "",
    address: "",
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      console.log("🔍 Fetching organizations with token:", token?.substring(0, 20) + "...");

      const response = await fetch("/api/organizations", {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log("📡 API Response status:", response.status);

      if (response.ok) {
        const data = await response.json();
        console.log("✅ Organizations data:", data);
        setOrganizations(data);
      } else {
        const error = await response.text();
        console.error("❌ API Error:", response.status, error);
      }
    } catch (error) {
      console.error("❌ Failed to fetch organizations:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/organizations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setShowCreateForm(false);
        setFormData({
          name: "",
          display_name: "",
          description: "",
          contact_email: "",
          contact_phone: "",
          address: "",
        });
        fetchOrganizations();
      } else {
        alert("Failed to create organization");
      }
    } catch (error) {
      console.error("Create failed:", error);
      alert("Error creating organization");
    }
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="p-8">Loading...</div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="p-8 max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">機構管理</h1>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + 新增機構
          </button>
        </div>

      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">創建新機構</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block mb-2">機構名稱 *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block mb-2">顯示名稱</label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) =>
                    setFormData({ ...formData, display_name: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block mb-2">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                  rows={3}
                />
              </div>
              <div>
                <label className="block mb-2">聯絡電郵</label>
                <input
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_email: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block mb-2">聯絡電話</label>
                <input
                  type="tel"
                  value={formData.contact_phone}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_phone: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  創建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {organizations.map((org) => (
          <div
            key={org.id}
            className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/teacher/organizations/${org.id}`)}
          >
            <h3 className="text-xl font-semibold mb-2">
              {org.display_name || org.name}
            </h3>
            {org.description && (
              <p className="text-gray-600 mb-4">{org.description}</p>
            )}
            <div className="text-sm text-gray-500">
              {org.contact_email && <div>📧 {org.contact_email}</div>}
              <div>
                創建時間: {new Date(org.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        ))}
      </div>

      {organizations.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>尚無機構，點擊上方按鈕創建第一個機構</p>
        </div>
      )}
    </div>
  </TeacherLayout>
  );
}
