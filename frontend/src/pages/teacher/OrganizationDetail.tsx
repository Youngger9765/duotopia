import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import { RolePermissionMatrix } from "@/components/organization/RolePermissionMatrix";
import { Shield } from "lucide-react";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_active: boolean;
}

interface TeacherInfo {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function OrganizationDetail() {
  const { orgId } = useParams<{ orgId: string }>();
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [teachers, setTeachers] = useState<TeacherInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [teachersLoading, setTeachersLoading] = useState(false);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [teacherId, setTeacherId] = useState("");
  const [role, setRole] = useState<"org_owner" | "org_admin">("org_admin");
  const [showPermissions, setShowPermissions] = useState(false);

  useEffect(() => {
    if (orgId) {
      fetchOrganization();
      fetchTeachers();
    }
  }, [orgId]);

  const fetchOrganization = async () => {
    try {
      const response = await fetch(`${API_URL}/api/organizations/${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setOrganization(data);
      }
    } catch (error) {
      console.error("Failed to fetch organization:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      setTeachersLoading(true);
      const response = await fetch(`${API_URL}/api/organizations/${orgId}/teachers`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setTeachers(data);
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
    } finally {
      setTeachersLoading(false);
    }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/api/organizations/${orgId}/teachers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          teacher_id: parseInt(teacherId),
          role: role,
        }),
      });

      if (response.ok) {
        setShowAddTeacher(false);
        setTeacherId("");
        setRole("org_admin");
        fetchTeachers();
        alert("教師已成功加入機構");
      } else {
        const error = await response.json();
        alert(`新增失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error("Add teacher failed:", error);
      alert("新增教師時發生錯誤");
    }
  };

  const handleRemoveTeacher = async (teacherId: number) => {
    if (!confirm("確定要移除此教師嗎？")) return;

    try {
      const response = await fetch(
        `/api/organizations/${orgId}/teachers/${teacherId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        fetchTeachers();
        alert("教師已移除");
      } else {
        const error = await response.json();
        alert(`移除失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error("Remove teacher failed:", error);
      alert("移除教師時發生錯誤");
    }
  };

  if (loading) return <div className="p-8">載入中...</div>;
  if (!organization) return <div className="p-8">找不到機構</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <button
          onClick={() => navigate("/teacher/organizations")}
          className="mb-4 px-4 py-2 border rounded hover:bg-gray-100"
        >
          ← 返回機構列表
        </button>

        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-3xl font-bold mb-4">
            {organization.display_name || organization.name}
          </h1>

          {organization.description && (
            <p className="text-gray-600 mb-4">{organization.description}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {organization.contact_email && (
              <div>
                <span className="font-semibold">聯絡電郵：</span>
                <span className="ml-2">{organization.contact_email}</span>
              </div>
            )}
            {organization.contact_phone && (
              <div>
                <span className="font-semibold">聯絡電話：</span>
                <span className="ml-2">{organization.contact_phone}</span>
              </div>
            )}
            {organization.address && (
              <div className="md:col-span-2">
                <span className="font-semibold">地址：</span>
                <span className="ml-2">{organization.address}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Permissions Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">權限管理</h2>
          <button
            onClick={() => setShowPermissions(!showPermissions)}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-2"
          >
            <Shield className="h-4 w-4" />
            {showPermissions ? "隱藏" : "查看"}角色權限矩陣
          </button>
        </div>
        {showPermissions && (
          <div className="bg-white rounded-lg shadow p-6">
            <RolePermissionMatrix />
          </div>
        )}
      </div>

      {/* Schools Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">分校管理</h2>
          <button
            onClick={() => navigate(`/teacher/organizations/${orgId}/schools`)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            管理分校
          </button>
        </div>
      </div>

      {/* Teachers Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">成員管理</h2>
          <button
            onClick={() => setShowAddTeacher(true)}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            + 新增成員
          </button>
        </div>

        {showAddTeacher && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-md w-full">
              <h3 className="text-xl font-bold mb-4">新增機構成員</h3>
              <form onSubmit={handleAddTeacher} className="space-y-4">
                <div>
                  <label className="block mb-2">教師 ID *</label>
                  <input
                    type="number"
                    required
                    value={teacherId}
                    onChange={(e) => setTeacherId(e.target.value)}
                    className="w-full border rounded px-3 py-2"
                    placeholder="輸入教師的 ID"
                  />
                </div>
                <div>
                  <label className="block mb-2">角色 *</label>
                  <select
                    value={role}
                    onChange={(e) =>
                      setRole(e.target.value as "org_owner" | "org_admin")
                    }
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="org_admin">機構管理員 (org_admin)</option>
                    <option value="org_owner">機構擁有人 (org_owner)</option>
                  </select>
                  <p className="text-sm text-gray-500 mt-1">
                    ⚠️ 每個機構只能有一個擁有人
                  </p>
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => setShowAddTeacher(false)}
                    className="px-4 py-2 border rounded hover:bg-gray-100"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    新增
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          {teachersLoading ? (
            <div className="p-4 text-center text-gray-500">載入中...</div>
          ) : teachers.length === 0 ? (
            <div className="p-4 text-center text-gray-500">尚無成員</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      姓名
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      電郵
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      角色
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      加入時間
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {teachers.map((t) => (
                    <tr key={t.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {t.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {t.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            t.role === "org_owner"
                              ? "bg-purple-100 text-purple-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {t.role === "org_owner" ? "機構擁有人" : "機構管理員"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(t.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleRemoveTeacher(t.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          移除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
