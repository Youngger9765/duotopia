import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import toast from "react-hot-toast";
import { Edit2, Trash2 } from "lucide-react";

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

interface DeleteConfirmationState {
  isOpen: boolean;
  schoolId?: string;
  schoolName?: string;
}

export default function SchoolManagement() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const [schools, setSchools] = useState<School[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>(orgId || "");
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingSchool, setEditingSchool] = useState<School | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] =
    useState<DeleteConfirmationState>({
      isOpen: false,
    });
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
      const response = await fetch(`${API_URL}/api/organizations`, {
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
      const response = await fetch(
        `${API_URL}/api/schools?organization_id=${organizationId}`,
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

  const resetForm = () => {
    setFormData({
      organization_id: selectedOrgId,
      name: "",
      display_name: "",
      description: "",
      contact_email: "",
      contact_phone: "",
      address: "",
    });
  };

  const handleEdit = (school: School) => {
    setEditingSchool(school);
    setFormData({
      organization_id: school.organization_id,
      name: school.name,
      display_name: school.display_name || "",
      description: school.description || "",
      contact_email: school.contact_email || "",
      contact_phone: "",
      address: "",
    });
    setShowEditForm(true);
  };

  const handleDelete = (school: School) => {
    setDeleteConfirmation({
      isOpen: true,
      schoolId: school.id,
      schoolName: school.display_name || school.name,
    });
  };

  const confirmDelete = async () => {
    if (!deleteConfirmation.schoolId) return;

    setDeleting(true);
    try {
      const response = await fetch(
        `${API_URL}/api/schools/${deleteConfirmation.schoolId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        toast.success("學校已成功刪除");
        setSchools(schools.filter((s) => s.id !== deleteConfirmation.schoolId));
        setDeleteConfirmation({ isOpen: false });
      } else {
        const error = await response.json();
        toast.error(`刪除失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error("Delete failed:", error);
      toast.error("刪除學校時發生錯誤");
    } finally {
      setDeleting(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/api/schools`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("學校已成功創建");
        setShowCreateForm(false);
        resetForm();
        fetchSchools(selectedOrgId);
      } else {
        const error = await response.json();
        toast.error(`創建失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error("Create failed:", error);
      toast.error("創建學校時發生錯誤");
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSchool) return;

    try {
      const response = await fetch(
        `${API_URL}/api/schools/${editingSchool.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(formData),
        },
      );

      if (response.ok) {
        toast.success("學校已成功更新");
        setShowEditForm(false);
        setEditingSchool(null);
        resetForm();
        fetchSchools(selectedOrgId);
      } else {
        const error = await response.json();
        toast.error(`更新失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error("Update failed:", error);
      toast.error("更新學校時發生錯誤");
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

      {/* Create Modal */}
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
                  onClick={() => {
                    setShowCreateForm(false);
                    resetForm();
                  }}
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

      {/* Edit Modal */}
      {showEditForm && editingSchool && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">編輯學校</h2>
            <form onSubmit={handleUpdate} className="space-y-4">
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
                  onClick={() => {
                    setShowEditForm(false);
                    setEditingSchool(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  更新
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmation.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h2 className="text-xl font-bold text-red-600 mb-4">確認刪除</h2>
            <p className="text-gray-700 mb-6">
              確定要刪除學校「{deleteConfirmation.schoolName}
              」嗎？此操作無法復原。
            </p>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setDeleteConfirmation({ isOpen: false })}
                disabled={deleting}
                className="px-4 py-2 border rounded hover:bg-gray-100 disabled:opacity-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? "刪除中..." : "刪除"}
              </button>
            </div>
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
                className="border rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                <div
                  className="cursor-pointer"
                  onClick={() => navigate(`/teacher/schools/${school.id}`)}
                >
                  <h3 className="text-xl font-semibold mb-2">
                    {school.display_name || school.name}
                  </h3>
                  {school.description && (
                    <p className="text-gray-600 mb-4">{school.description}</p>
                  )}
                  <div className="text-sm text-gray-500">
                    {school.contact_email && (
                      <div>📧 {school.contact_email}</div>
                    )}
                    <div>
                      創建時間:{" "}
                      {new Date(school.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 mt-4 pt-4 border-t">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(school);
                    }}
                    className="flex-1 px-3 py-2 border rounded hover:bg-gray-100 flex items-center justify-center gap-2"
                  >
                    <Edit2 className="h-4 w-4" />
                    編輯
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(school);
                    }}
                    disabled={deleting}
                    className="flex-1 px-3 py-2 border border-red-300 text-red-600 rounded hover:bg-red-50 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    刪除
                  </button>
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
