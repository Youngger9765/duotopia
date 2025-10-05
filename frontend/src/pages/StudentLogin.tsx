import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ArrowLeft, ChevronRight, Home } from "lucide-react";
import { useStudentAuthStore, StudentUser } from "@/stores/studentAuthStore";
import { authService } from "@/services/authService";
import { teacherService } from "@/services/teacherService";

interface TeacherHistory {
  email: string;
  name: string;
  lastUsed: Date;
}

interface Classroom {
  id: number;
  name: string;
  studentCount: number;
}

interface Student {
  id: number;
  name: string;
  email: string;
  avatar?: string;
}

export default function StudentLogin() {
  const navigate = useNavigate();
  const { login } = useStudentAuthStore();

  // Multi-step form state
  const [step, setStep] = useState(1);
  const [teacherEmail, setTeacherEmail] = useState("");
  const [, setSelectedTeacher] = useState<TeacherHistory | null>(null);
  const [teacherHistory, setTeacherHistory] = useState<TeacherHistory[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<Classroom | null>(
    null,
  );
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load teacher history from localStorage
  useEffect(() => {
    const history = localStorage.getItem("teacherHistory");
    if (history) {
      setTeacherHistory(JSON.parse(history));
    }
  }, []);

  // Step 1: Teacher selection
  const handleTeacherSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      // Validate teacher email exists
      const response = await teacherService.validateTeacher(teacherEmail);
      if (response.valid) {
        const teacher = {
          email: teacherEmail,
          name: response.name,
          lastUsed: new Date(),
        };

        // Save to history
        const updatedHistory = [
          teacher,
          ...teacherHistory.filter((t) => t.email !== teacherEmail),
        ].slice(0, 5); // Keep last 5 teachers

        localStorage.setItem("teacherHistory", JSON.stringify(updatedHistory));
        setTeacherHistory(updatedHistory);
        setSelectedTeacher(teacher);

        // Load classrooms for this teacher
        const classroomsData =
          await teacherService.getPublicClassrooms(teacherEmail);
        setClassrooms(classroomsData);
        setStep(2);
      } else {
        setError("找不到此教師帳號");
      }
    } catch {
      setError("無法驗證教師帳號，請稍後再試");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Classroom selection
  const handleClassroomSelect = async (classroom: Classroom) => {
    setLoading(true);
    setError("");
    try {
      setSelectedClassroom(classroom);
      // Load students for this classroom
      const studentsData = await teacherService.getClassroomStudents(
        classroom.id,
      );
      // Sort students by ID
      const sortedStudents = [...studentsData].sort((a, b) => a.id - b.id);
      setStudents(sortedStudents);
      setStep(3);
    } catch {
      setError("無法載入班級學生資料");
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Student selection
  const handleStudentSelect = (student: Student) => {
    setSelectedStudent(student);
    setStep(4);
  };

  // Step 4: Password submission
  const handleLogin = async () => {
    if (!selectedStudent) return;

    setLoading(true);
    setError("");
    try {
      const response = await authService.studentLogin({
        id: selectedStudent.id,
        password: password,
      });

      if (response.access_token) {
        login(response.access_token, {
          ...response.user,
          student_number:
            response.user.student_number || response.user.id.toString(),
          classroom_id: selectedClassroom?.id || 0,
          classroom_name: selectedClassroom?.name,
          teacher_name: teacherHistory.find((t) => t.email === teacherEmail)
            ?.name,
        } as StudentUser);
        navigate("/student/dashboard");
      }
    } catch {
      setError("密碼錯誤，請重新輸入");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setError("");
    if (step > 1) {
      setStep(step - 1);
    }
  };

  // Avatar component
  const Avatar = ({
    name,
    size = "normal",
  }: {
    name: string;
    size?: "normal" | "small";
  }) => {
    const colors = [
      "bg-blue-500",
      "bg-green-500",
      "bg-purple-500",
      "bg-pink-500",
      "bg-yellow-500",
    ];
    const colorIndex = name.charCodeAt(0) % colors.length;
    const sizeClasses =
      size === "small" ? "w-12 h-12 text-lg" : "w-20 h-20 text-2xl";

    return (
      <div
        className={`${sizeClasses} ${colors[colorIndex]} rounded-full flex items-center justify-center text-white font-bold`}
      >
        {name.charAt(0).toUpperCase()}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center justify-center p-4">
      {/* Home link */}
      <div className="absolute top-4 left-4">
        <Link to="/">
          <Button
            variant="ghost"
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <Home className="h-4 w-4" />
            <span>返回首頁</span>
          </Button>
        </Link>
      </div>

      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-blue-600 flex items-center justify-center gap-2">
          <span className="text-4xl">🚀</span>
          嗨，歡迎來到 Duotopia！
        </h1>
      </div>

      <Card className="w-full max-w-2xl">
        <CardHeader>
          {step > 1 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBack}
              className="mb-2 w-fit"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {/* Step 1: Teacher Email */}
          {step === 1 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-center">
                請輸入老師 Email
              </h2>

              <div className="space-y-4">
                <Input
                  type="email"
                  placeholder="teacher@example.com"
                  value={teacherEmail}
                  onChange={(e) => setTeacherEmail(e.target.value)}
                  className="text-lg py-6"
                  onKeyPress={(e) => e.key === "Enter" && handleTeacherSubmit()}
                />

                <Button
                  onClick={handleTeacherSubmit}
                  disabled={!teacherEmail || loading}
                  className="w-full py-6 text-lg bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                >
                  下一步
                </Button>
              </div>

              {/* Demo 教師快捷鍵 */}
              <div className="mt-6 pt-6 border-t">
                <p className="text-sm text-gray-600 mb-3">快速測試：</p>
                <Button
                  variant="outline"
                  className="w-full py-4 bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border-purple-200"
                  onClick={() => {
                    setTeacherEmail("demo@duotopia.com");
                  }}
                >
                  <span className="text-purple-600 font-medium">
                    🎯 使用 Demo 教師 (demo@duotopia.com)
                  </span>
                </Button>
              </div>

              {teacherHistory.length > 0 && (
                <div className="space-y-3 mt-6">
                  <p className="text-sm text-gray-600">
                    或選擇最近使用過的老師：
                  </p>
                  <div className="space-y-2">
                    {teacherHistory
                      .filter((t) => t.email !== "demo@duotopia.com")
                      .map((teacher) => (
                        <Button
                          key={teacher.email}
                          variant="outline"
                          className="w-full justify-start py-4"
                          onClick={() => {
                            setTeacherEmail(teacher.email);
                            handleTeacherSubmit();
                          }}
                        >
                          {teacher.email}
                        </Button>
                      ))}
                  </div>
                </div>
              )}

              {error && <p className="text-red-500 text-center">{error}</p>}
            </div>
          )}

          {/* Step 2: Classroom Selection */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-center">
                請選擇你的班級和名字
              </h2>

              <div className="space-y-3">
                {classrooms.map((classroom) => (
                  <Button
                    key={classroom.id}
                    variant="outline"
                    className="w-full justify-between py-6 text-left"
                    onClick={() => handleClassroomSelect(classroom)}
                  >
                    <span className="text-lg font-medium">
                      {classroom.name}
                    </span>
                    <ChevronRight className="h-5 w-5" />
                  </Button>
                ))}
              </div>

              {error && <p className="text-red-500 text-center">{error}</p>}
            </div>
          )}

          {/* Step 3: Student Selection */}
          {step === 3 && selectedClassroom && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold">
                  {selectedClassroom.name}
                </h2>
                <p className="text-gray-600 mt-1">請選擇你的名字</p>
              </div>

              <div className="grid grid-cols-3 sm:grid-cols-4 gap-4">
                {students.map((student) => (
                  <button
                    key={student.id}
                    onClick={() => handleStudentSelect(student)}
                    className="flex flex-col items-center gap-2 p-4 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Avatar name={student.name} />
                    <span className="text-sm font-medium">{student.name}</span>
                  </button>
                ))}
              </div>

              {error && <p className="text-red-500 text-center">{error}</p>}
            </div>
          )}

          {/* Step 4: Password */}
          {step === 4 && selectedStudent && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-semibold">
                  你好，{selectedStudent.name}！
                </h2>
              </div>

              <div className="space-y-4">
                <Input
                  type="password"
                  placeholder="請輸入你的密碼"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="text-lg py-6"
                  onKeyPress={(e) => e.key === "Enter" && handleLogin()}
                />

                <Button
                  onClick={handleLogin}
                  disabled={!password || loading}
                  className="w-full py-6 text-lg bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                >
                  登入
                </Button>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setSelectedStudent(null);
                    setPassword("");
                    setError("");
                    setStep(3);
                  }}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  選擇其他學生
                </Button>
              </div>

              {error && <p className="text-red-500 text-center">{error}</p>}

              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800 font-medium mb-1">
                  💡 測試提示
                </p>
                <p className="text-xs text-yellow-700">
                  Demo 學生預設密碼：
                  <span className="font-mono font-bold">20120101</span>
                </p>
                <p className="text-xs text-gray-600 mt-2">
                  正式使用時，密碼為學生的生日 (格式：YYYYMMDD)
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
