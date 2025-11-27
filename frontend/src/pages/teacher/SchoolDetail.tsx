import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface School {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_active: boolean;
}

interface SchoolTeacherInfo {
  id: number;
  email: string;
  name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
}

export default function SchoolDetail() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const navigate = useNavigate();
  const [school, setSchool] = useState<School | null>(null);
  const [teachers, setTeachers] = useState<SchoolTeacherInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [teachersLoading, setTeachersLoading] = useState(false);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [teacherId, setTeacherId] = useState('');
  const [roles, setRoles] = useState<string[]>(['teacher']);

  useEffect(() => {
    if (schoolId) {
      fetchSchool();
      fetchTeachers();
    }
  }, [schoolId]);

  const fetchSchool = async () => {
    try {
      const token = localStorage.getItem('teacherToken');
      const response = await fetch(`/api/schools/${schoolId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSchool(data);
      }
    } catch (error) {
      console.error('Failed to fetch school:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      setTeachersLoading(true);
      const token = localStorage.getItem('teacherToken');
      const response = await fetch(`/api/schools/${schoolId}/teachers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setTeachers(data);
      }
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
    } finally {
      setTeachersLoading(false);
    }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('teacherToken');
      const response = await fetch(`/api/schools/${schoolId}/teachers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          teacher_id: parseInt(teacherId),
          roles: roles
        })
      });

      if (response.ok) {
        setShowAddTeacher(false);
        setTeacherId('');
        setRoles(['teacher']);
        fetchTeachers();
        alert('教師已成功加入學校');
      } else {
        const error = await response.json();
        alert(`新增失敗: ${error.detail}`);
      }
    } catch (error) {
      console.error('Add teacher failed:', error);
      alert('新增教師時發生錯誤');
    }
  };

  const handleRoleToggle = (role: string) => {
    if (roles.includes(role)) {
      setRoles(roles.filter(r => r !== role));
    } else {
      setRoles([...roles, role]);
    }
  };

  if (loading) return <div className="p-8">載入中...</div>;
  if (!school) return <div className="p-8">找不到學校</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <button
          onClick={() => navigate('/teacher/schools')}
          className="mb-4 px-4 py-2 border rounded hover:bg-gray-100"
        >
          ← 返回學校列表
        </button>

        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-3xl font-bold mb-4">{school.display_name || school.name}</h1>

          {school.description && (
            <p className="text-gray-600 mb-4">{school.description}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {school.contact_email && (
              <div>
                <span className="font-semibold">聯絡電郵：</span>
                <span className="ml-2">{school.contact_email}</span>
              </div>
            )}
            {school.contact_phone && (
              <div>
                <span className="font-semibold">聯絡電話：</span>
                <span className="ml-2">{school.contact_phone}</span>
              </div>
            )}
            {school.address && (
              <div className="md:col-span-2">
                <span className="font-semibold">地址：</span>
                <span className="ml-2">{school.address}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Teachers Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">教師管理</h2>
          <button
            onClick={() => setShowAddTeacher(true)}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            + 新增教師
          </button>
        </div>

        {showAddTeacher && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-md w-full">
              <h3 className="text-xl font-bold mb-4">新增學校教師</h3>
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
                  <label className="block mb-2">角色 * (可多選)</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={roles.includes('school_admin')}
                        onChange={() => handleRoleToggle('school_admin')}
                        className="mr-2"
                      />
                      <span>分校校長 (school_admin)</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={roles.includes('teacher')}
                        onChange={() => handleRoleToggle('teacher')}
                        className="mr-2"
                      />
                      <span>教師 (teacher)</span>
                    </label>
                  </div>
                  {roles.length === 0 && (
                    <p className="text-sm text-red-500 mt-1">至少選擇一個角色</p>
                  )}
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
                    disabled={roles.length === 0}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
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
            <div className="p-4 text-center text-gray-500">尚無教師</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">姓名</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">電郵</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">加入時間</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {teachers.map((t) => (
                    <tr key={t.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{t.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex gap-1">
                          {t.roles.map((role) => (
                            <span key={role} className={`px-2 py-1 text-xs rounded ${
                              role === 'school_admin' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                            }`}>
                              {role === 'school_admin' ? '分校校長' : '教師'}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(t.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => alert('移除功能需實作')}
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

      {/* Classrooms Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">班級管理</h2>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={() => alert('班級管理功能開發中...')}
          >
            管理班級
          </button>
        </div>
        <div className="bg-white rounded-lg shadow p-4 text-gray-500 text-center">
          班級列表功能開發中...
        </div>
      </div>
    </div>
  );
}
