import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

interface School {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface Organization {
  id: string;
  name: string;
  display_name?: string;
}

export default function SchoolManagement() {
  const { orgId } = useParams<{ orgId: string }>();
  const [schools, setSchools] = useState<School[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>(orgId || "");
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    organization_id: orgId || "",
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

  useEffect(() => {
    if (selectedOrgId) {
      fetchSchools(selectedOrgId);
      setFormData((prev) => ({ ...prev, organization_id: selectedOrgId }));
    }
  }, [selectedOrgId]);

  const fetchOrganizations = async () => {
    try {
      const token = localStorage.getItem("teacherToken");
      const response = await fetch("/api/organizations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setOrganizations(data);
        if (data.length > 0 && !selectedOrgId) {
          setSelectedOrgId(data[0].id);
        }
      }
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
    }
  };

  const fetchSchools = async (organizationId: string) => {
    try {
      setLoading(true);
      const token = localStorage.getItem("teacherToken");
      const response = await fetch(
        `/api/schools?organization_id=${organizationId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (response.ok) {
        const data = await response.json();
        setSchools(data);
      }
    } catch (error) {
      console.error("Failed to fetch schools:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("teacherToken");
      const response = await fetch("/api/schools", {
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
          organization_id: selectedOrgId,
          name: "",
          display_name: "",
          description: "",
          contact_email: "",
          contact_phone: "",
          address: "",
        });
        fetchSchools(selectedOrgId);
      } else {
        const error = await response.json();
        alert(`Failed to create school: ${error.detail}`);
      }
    } catch (error) {
      console.error("Create failed:", error);
      alert("Error creating school");
    }
  };

  if (loading && organizations.length === 0)
    return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold">學校管理</h1>
          <button
            onClick={() => navigate("/teacher/organizations")}
            className="px-4 py-2 border rounded hover:bg-gray-100"
          >
            ← 返回機構列表
          </button>
        </div>

        {/* Organization selector */}
        {organizations.length > 0 && (
          <div className="mb-6">
            <label className="block mb-2 font-semibold">選擇機構：</label>
            <select
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
              className="w-full max-w-md border rounded px-3 py-2"
            >
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.display_name || org.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedOrgId && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + 新增學校
          </button>
        )}
      </div>

      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">創建新學校</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block mb-2">學校名稱 *</label>
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

      {loading ? (
        <div className="text-center py-12">載入中...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schools.map((school) => (
              <div
                key={school.id}
                className="border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => navigate(`/teacher/schools/${school.id}`)}
              >
                <h3 className="text-xl font-semibold mb-2">
                  {school.display_name || school.name}
                </h3>
                {school.description && (
                  <p className="text-gray-600 mb-4">{school.description}</p>
                )}
                <div className="text-sm text-gray-500">
                  {school.contact_email && <div>📧 {school.contact_email}</div>}
                  <div>
                    創建時間: {new Date(school.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {schools.length === 0 && selectedOrgId && (
            <div className="text-center py-12 text-gray-500">
              <p>此機構尚無學校，點擊上方按鈕創建第一個學校</p>
            </div>
          )}
        </>
      )}

      {organizations.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>請先創建機構</p>
          <button
            onClick={() => navigate("/teacher/organizations")}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            前往機構管理
          </button>
        </div>
      )}
    </div>
  );
}
