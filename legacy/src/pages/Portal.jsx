
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Mail, Users, User as UserIcon, Heart, CheckCircle2, GraduationCap, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { User } from '@/api/entities';
import { ClassStudent } from '@/api/entities';
import { Class } from '@/api/entities';
import { createPageUrl } from '@/utils';

export default function PortalPage() {
    const [loginType, setLoginType] = useState(null); // null, 'teacher', 'student'
    const [currentStep, setCurrentStep] = useState('teacher-email'); // student login steps
    const [teacherEmail, setTeacherEmail] = useState('');
    const [availableClasses, setAvailableClasses] = useState([]);
    const [selectedClass, setSelectedClass] = useState(null);
    const [classStudents, setClassStudents] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleTeacherLogin = async () => {
        setLoading(true);
        try {
            // 核心修正：使用 loginWithRedirect 並指定回調頁面
            const callbackUrl = new URL(createPageUrl("TeacherDashboard"), window.location.origin).href;
            await User.loginWithRedirect(callbackUrl);
        } catch (error) {
            console.error('教師登入失敗:', error);
            setError('登入失敗，請重試');
            setLoading(false);
        }
    };

    const handleStudentLoginStart = () => {
        setLoginType('student');
        setCurrentStep('teacher-email');
    };

    const handleTeacherEmailSubmit = async () => {
        if (!teacherEmail.trim()) {
            setError('請輸入老師的 Email');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const classes = await Class.filter({ created_by: teacherEmail });
            
            if (!classes || classes.length === 0) {
                setError('找不到該老師的班級，請檢查 Email 是否正確');
                setLoading(false);
                return;
            }

            setAvailableClasses(classes);
            setCurrentStep('class-selection');
        } catch (error) {
            console.error('載入班級失敗:', error);
            setError('載入班級資料失敗，請稍後再試');
        } finally {
            setLoading(false);
        }
    };

    const handleClassSelection = async (classData) => {
        setSelectedClass(classData);
        setLoading(true);

        try {
            const students = await ClassStudent.filter({ class_id: classData.id });
            setClassStudents(students || []);
            setCurrentStep('student-selection');
        } catch (error) {
            console.error('載入學生失敗:', error);
            setError('載入學生資料失敗，請稍後再試');
        } finally {
            setLoading(false);
        }
    };

    const handleStudentSelection = (student) => {
        setSelectedStudent(student);
        setCurrentStep('password');
        setPassword('');
        setError('');
    };

    const handleStudentPasswordSubmit = async () => {
        if (!password.trim()) {
            setError('請輸入密碼');
            return;
        }

        setLoading(true);
        setError('');

        try {
            console.log('[Portal] 準備調用學生認證函式');
            console.log('[Portal] 學生Email:', selectedStudent.email);

            const { studentAuthenticator } = await import('@/api/functions');
            
            console.log('[Portal] 調用後端函數...');
            const response = await studentAuthenticator({
                student_email: selectedStudent.email,
                password: password
            });

            console.log('[Portal] 後端回應:', response);

            const responseData = response.data || response;
            
            if (response.status >= 400 || !responseData.success) {
                console.error('[Portal] 認證失敗:', responseData.error);
                setError(responseData.error || '登入失敗，請稍後再試');
                setLoading(false);
                return;
            }

            console.log('[Portal] 認證成功，準備跳轉');
            
            if (responseData.redirect_url) {
                window.location.href = responseData.redirect_url;
            } else {
                window.location.href = createPageUrl("Assignments");
            }

        } catch (error) {
            console.error('[Portal] 學生登入過程中發生錯誤:', error);
            setError('系統暫時無法使用，請稍後再試');
            setLoading(false);
        }
    };

    const goBack = () => {
        if (currentStep === 'teacher-email') {
            setLoginType(null);
        } else if (currentStep === 'class-selection') {
            setCurrentStep('teacher-email');
        } else if (currentStep === 'student-selection') {
            setCurrentStep('class-selection');
        } else if (currentStep === 'password') {
            setCurrentStep('student-selection');
        }
        setError('');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-100 via-purple-50 to-pink-100 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <AnimatePresence mode="wait">
                    {/* 初始角色選擇畫面 */}
                    {!loginType && (
                        <motion.div
                            key="role-selection"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-2xl">
                                <CardHeader className="text-center pb-6">
                                    <motion.div 
                                        className="text-5xl mb-4"
                                        animate={{ rotate: [0, 10, -10, 0] }}
                                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                    >
                                        🚀
                                    </motion.div>
                                    <CardTitle className="text-2xl font-bold text-transparent bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text">
                                        嗨，歡迎來到 Duotopia！
                                    </CardTitle>
                                    <p className="text-gray-600 mt-2">請選擇您的身份以開始使用</p>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <Button 
                                        onClick={handleTeacherLogin}
                                        disabled={loading}
                                        className="w-full h-14 text-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200"
                                    >
                                        <GraduationCap className="w-6 h-6 mr-3" />
                                        我是教師 (Google 登入)
                                    </Button>

                                    <Button 
                                        onClick={handleStudentLoginStart}
                                        disabled={loading}
                                        variant="outline"
                                        className="w-full h-14 text-lg border-2 border-blue-200 hover:border-blue-400 text-blue-600 hover:text-blue-700 hover:bg-blue-50 shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200"
                                    >
                                        <BookOpen className="w-6 h-6 mr-3" />
                                        我是學生
                                    </Button>

                                    {loading && (
                                        <div className="text-center text-sm text-gray-500">
                                            處理中...
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}

                    {/* 學生登入流程 - 步驟1: 老師Email */}
                    {loginType === 'student' && currentStep === 'teacher-email' && (
                        <motion.div
                            key="teacher-email"
                            initial={{ opacity: 0, x: 300 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -300 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-2xl">
                                <CardHeader>
                                    <div className="flex items-center gap-3 mb-2">
                                        <Button variant="ghost" size="sm" onClick={goBack} className="p-2">
                                            <ArrowLeft className="w-4 h-4" />
                                        </Button>
                                        <div>
                                            <CardTitle className="text-xl">學生登入</CardTitle>
                                            <p className="text-sm text-gray-600">步驟 1/4</p>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="text-center mb-6">
                                        <div className="text-4xl mb-3">👨‍🏫</div>
                                        <h3 className="text-lg font-medium text-gray-800">請輸入您的老師 Email</h3>
                                        <p className="text-sm text-gray-600 mt-2">我們需要找到您所屬的班級</p>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="relative">
                                            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                            <Input 
                                                type="email"
                                                placeholder="teacher@example.com"
                                                value={teacherEmail}
                                                onChange={(e) => setTeacherEmail(e.target.value)}
                                                onKeyPress={(e) => e.key === 'Enter' && handleTeacherEmailSubmit()}
                                                className="pl-10 h-12 text-center text-lg border-2 focus:border-blue-400"
                                                disabled={loading}
                                            />
                                        </div>

                                        {error && (
                                            <div className="text-red-600 text-sm text-center bg-red-50 p-3 rounded-lg">
                                                {error}
                                            </div>
                                        )}

                                        <Button 
                                            onClick={handleTeacherEmailSubmit}
                                            disabled={loading || !teacherEmail.trim()}
                                            className="w-full h-12 text-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white"
                                        >
                                            {loading ? '搜尋中...' : '下一步'}
                                        </Button>
                                        {/* 加入快捷選項 */}
                                        {(!teacherEmail || teacherEmail !== 'youngtsai@junyiacademy.org') && (
                                            <div className="mt-4">
                                                <p className="text-sm text-gray-500 text-center mb-2">或選擇最近使用過的老師：</p>
                                                <button
                                                    onClick={() => setTeacherEmail('youngtsai@junyiacademy.org')}
                                                    className="w-full px-4 py-3 bg-gradient-to-r from-cyan-400 to-blue-500
                                                            text-white rounded-full hover:shadow-lg transition-all"
                                                >
                                                    youngtsai@junyiacademy.org
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}

                    {/* 學生登入流程 - 步驟2: 班級選擇 */}
                    {loginType === 'student' && currentStep === 'class-selection' && (
                        <motion.div
                            key="class-selection"
                            initial={{ opacity: 0, x: 300 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -300 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-2xl">
                                <CardHeader>
                                    <div className="flex items-center gap-3 mb-2">
                                        <Button variant="ghost" size="sm" onClick={goBack} className="p-2">
                                            <ArrowLeft className="w-4 h-4" />
                                        </Button>
                                        <div>
                                            <CardTitle className="text-xl">選擇班級</CardTitle>
                                            <p className="text-sm text-gray-600">步驟 2/4</p>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-center mb-6">
                                        <div className="text-4xl mb-3">🏫</div>
                                        <h3 className="text-lg font-medium text-gray-800">請選擇您的班級</h3>
                                        <p className="text-sm text-gray-600 mt-2">找到 {availableClasses.length} 個班級</p>
                                    </div>

                                    <div className="space-y-3 max-h-60 overflow-y-auto">
                                        {availableClasses.map((cls) => (
                                            <Button
                                                key={cls.id}
                                                onClick={() => handleClassSelection(cls)}
                                                variant="outline"
                                                disabled={loading}
                                                className="w-full h-auto p-4 hover:bg-blue-50 hover:border-blue-300 text-left justify-start"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <Users className="w-5 h-5 text-blue-600" />
                                                    <div>
                                                        <div className="font-medium text-gray-800">{cls.class_name}</div>
                                                        {cls.difficulty_level && (
                                                            <Badge variant="secondary" className="mt-1">
                                                                {cls.difficulty_level}
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </div>
                                            </Button>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}

                    {/* 學生登入流程 - 步驟3: 學生選擇 */}
                    {loginType === 'student' && currentStep === 'student-selection' && (
                        <motion.div
                            key="student-selection"
                            initial={{ opacity: 0, x: 300 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -300 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-2xl">
                                <CardHeader>
                                    <div className="flex items-center gap-3 mb-2">
                                        <Button variant="ghost" size="sm" onClick={goBack} className="p-2">
                                            <ArrowLeft className="w-4 h-4" />
                                        </Button>
                                        <div>
                                            <CardTitle className="text-xl">選擇學生</CardTitle>
                                            <p className="text-sm text-gray-600">步驟 3/4</p>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-center mb-6">
                                        <div className="text-4xl mb-3">👨‍🎓</div>
                                        <h3 className="text-lg font-medium text-gray-800">請找到您的姓名</h3>
                                        <p className="text-sm text-gray-600 mt-2">{selectedClass?.class_name} - {classStudents.length} 位學生</p>
                                    </div>

                                    <div className="space-y-3 max-h-60 overflow-y-auto">
                                        {classStudents.map((student) => (
                                            <Button
                                                key={student.id}
                                                onClick={() => handleStudentSelection(student)}
                                                variant="outline"
                                                disabled={loading}
                                                className="w-full h-auto p-4 hover:bg-green-50 hover:border-green-300 text-left justify-start"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <UserIcon className="w-5 h-5 text-green-600" />
                                                    <div>
                                                        <div className="font-medium text-gray-800">{student.student_name}</div>
                                                        <div className="text-sm text-gray-500">{student.email}</div>
                                                    </div>
                                                </div>
                                            </Button>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}

                    {/* 學生登入流程 - 步驟4: 密碼輸入 */}
                    {loginType === 'student' && currentStep === 'password' && (
                        <motion.div
                            key="password"
                            initial={{ opacity: 0, x: 300 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -300 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-2xl">
                                <CardHeader>
                                    <div className="flex items-center gap-3 mb-2">
                                        <Button variant="ghost" size="sm" onClick={goBack} className="p-2">
                                            <ArrowLeft className="w-4 h-4" />
                                        </Button>
                                        <div>
                                            <CardTitle className="text-xl">密碼驗證</CardTitle>
                                            <p className="text-sm text-gray-600">步驟 4/4</p>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="text-center">
                                        <div className="text-4xl mb-3">🎉</div>
                                        <h3 className="text-xl font-bold text-transparent bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text">
                                            你好，{selectedStudent?.student_name}！
                                        </h3>
                                        <p className="text-gray-600 mt-2">請輸入您的密碼</p>
                                    </div>

                                    <div className="space-y-4">
                                        <Input
                                            type="password"
                                            placeholder="請輸入您的密碼"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && handleStudentPasswordSubmit()}
                                            className="h-12 text-center text-lg border-2 focus:border-green-400"
                                            disabled={loading}
                                        />

                                        <div className="text-center text-sm text-gray-500">
                                            預設密碼為您的生日 (格式: 20090828)
                                        </div>

                                        {error && (
                                            <div className="text-red-600 text-sm text-center bg-red-50 p-3 rounded-lg">
                                                {error}
                                            </div>
                                        )}

                                        <Button 
                                            onClick={handleStudentPasswordSubmit}
                                            disabled={loading || !password.trim()}
                                            className="w-full h-12 text-lg bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 text-white"
                                        >
                                            {loading ? '登入中...' : '登入'}
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
