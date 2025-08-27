import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import TeacherLayout from '@/components/TeacherLayout';
import { ArrowLeft, Users, BookOpen, Plus, Settings } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ClassroomInfo {
  id: number;
  name: string;
  description?: string;
  level?: string;
  student_count: number;
  students: Array<{
    id: number;
    name: string;
    email: string;
  }>;
  program_count?: number;
}

export default function ClassroomDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [classroom, setClassroom] = useState<ClassroomInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchClassroomDetail();
    }
  }, [id]);

  const fetchClassroomDetail = async () => {
    try {
      setLoading(true);
      const classrooms = await apiClient.getTeacherClassrooms() as ClassroomInfo[];
      const currentClassroom = classrooms.find(c => c.id === Number(id));
      
      if (currentClassroom) {
        setClassroom(currentClassroom);
      } else {
        console.error('Classroom not found');
        navigate('/teacher/classrooms');
      }
    } catch (err) {
      console.error('Fetch classroom error:', err);
      navigate('/teacher/classrooms');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">載入中...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  if (!classroom) {
    return (
      <TeacherLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">找不到班級資料</p>
          <Button 
            className="mt-4"
            onClick={() => navigate('/teacher/classrooms')}
          >
            返回班級列表
          </Button>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/teacher/classrooms')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回
            </Button>
            <div>
              <h2 className="text-3xl font-bold text-gray-900">{classroom.name}</h2>
              {classroom.description && (
                <p className="text-gray-600 mt-1">{classroom.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              班級設定
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">學生數</p>
                <p className="text-2xl font-bold">{classroom.student_count}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">課程數</p>
                <p className="text-2xl font-bold">{classroom.program_count || 0}</p>
              </div>
              <BookOpen className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">等級</p>
                <p className="text-2xl font-bold">{classroom.level || 'A1'}</p>
              </div>
              <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 font-bold">L</span>
              </div>
            </div>
          </div>
        </div>

        {/* Students Section */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">學生列表</h3>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              新增學生
            </Button>
          </div>
          
          {classroom.students.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {classroom.students.map((student) => (
                <div key={student.id} className="border rounded-lg p-3 hover:bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-blue-600">
                        {student.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-sm">{student.name}</p>
                      <p className="text-xs text-gray-500">{student.email}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">此班級尚無學生</p>
              <Button className="mt-4" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                新增第一位學生
              </Button>
            </div>
          )}
        </div>

        {/* Programs Section */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">課程列表</h3>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              指派課程
            </Button>
          </div>
          
          <div className="text-center py-8">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">尚未指派課程</p>
            <Button className="mt-4" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              指派第一個課程
            </Button>
          </div>
        </div>
      </div>
    </TeacherLayout>
  );
}