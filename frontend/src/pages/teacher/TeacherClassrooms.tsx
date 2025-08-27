import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import TeacherLayout from '@/components/TeacherLayout';
import { TrendingUp } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ClassroomDetail {
  id: number;
  name: string;
  description?: string;
  student_count: number;
  students: Array<{
    id: number;
    name: string;
    email: string;
  }>;
}

export default function TeacherClassrooms() {
  const [classrooms, setClassrooms] = useState<ClassroomDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTeacherClassrooms() as ClassroomDetail[];
      setClassrooms(data);
    } catch (err) {
      console.error('Fetch classrooms error:', err);
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

  return (
    <TeacherLayout>
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-gray-900">我的班級</h2>
          <Button onClick={fetchClassrooms}>
            <TrendingUp className="h-4 w-4 mr-2" />
            重新載入
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {classrooms.map((classroom) => (
            <Card key={classroom.id}>
              <CardHeader>
                <CardTitle>{classroom.name}</CardTitle>
                <CardDescription>{classroom.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  {classroom.student_count} 位學生
                </p>
                <div className="space-y-2">
                  <h4 className="font-medium text-sm">學生列表：</h4>
                  <div className="grid grid-cols-1 gap-2">
                    {classroom.students.map((student) => (
                      <div key={student.id} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                        <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-xs font-medium text-blue-600">
                            {student.name.charAt(0)}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm font-medium">{student.name}</p>
                          <p className="text-xs text-gray-500">{student.email}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {classrooms.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">尚未建立班級</p>
          </div>
        )}
      </div>
    </TeacherLayout>
  );
}