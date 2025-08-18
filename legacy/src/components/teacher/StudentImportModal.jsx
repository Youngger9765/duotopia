
import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, Users, FileText, AlertCircle, Check, X, RefreshCw, Plus } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Class } from "@/api/entities";
import { ClassStudent } from "@/api/entities";
import { motion, AnimatePresence } from "framer-motion";
import { Input } from "@/components/ui/input";

export default function StudentImportModal({ onImportComplete, preselectedClassId, preselectedClassName }) {
    const [isOpen, setIsOpen] = useState(false);
    const [classes, setClasses] = useState([]);
    const [selectedClassId, setSelectedClassId] = useState(preselectedClassId || '');
    const [selectedClassName, setSelectedClassName] = useState(preselectedClassName || '');
    const [csvText, setCsvText] = useState('');
    const [parsedStudents, setParsedStudents] = useState([]);
    const [existingStudents, setExistingStudents] = useState([]);
    const [step, setStep] = useState(preselectedClassId ? 2 : 1);
    const [validationResult, setValidationResult] = useState({
        valid: [],
        errors: [],
        duplicates: [],
        emailDuplicates: [],
        emailConflicts: []
    });
    const [duplicateSelections, setDuplicateSelections] = useState({});
    const [processing, setProcessing] = useState(false);
    const [importResult, setImportResult] = useState(null);

    // 新班級建立相關狀態
    const [showNewClassForm, setShowNewClassForm] = useState(false);
    const [newClassData, setNewClassData] = useState({
        class_name: '',
        academic_year: new Date().getFullYear() + '學年度'
    });

    useEffect(() => {
        if (isOpen) {
            loadClasses();
            if (preselectedClassId) {
                loadExistingStudents(preselectedClassId);
            }
        }
    }, [isOpen, preselectedClassId]);

    const loadClasses = async () => {
        try {
            const classesData = await Class.filter({ is_active: true }, "-created_date");
            setClasses(classesData);
        } catch (error) {
            console.error("載入班級失敗:", error);
        }
    };

    const loadExistingStudents = async (classId) => {
        try {
            const students = await ClassStudent.filter({ class_id: classId });
            setExistingStudents(students);
        } catch (error) {
            console.error("載入班級學生失敗:", error);
        }
    };

    // Email 格式驗證函數
    const isValidEmail = (email) => {
        if (!email) return true; // Email 是選填的，如果為空則視為有效
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const handleClassSelect = async (classId) => {
        setSelectedClassId(classId);
        const selectedClass = classes.find(c => c.id === classId);
        setSelectedClassName(selectedClass?.class_name || '');

        await loadExistingStudents(classId);
        setStep(2);
    };

    const handleCreateNewClass = async () => {
        if (!newClassData.class_name.trim()) {
            alert('請輸入班級名稱');
            return;
        }

        try {
            const classData = {
                ...newClassData,
                created_by: 'poc_teacher',
                teachers: [{
                    teacher_id: 'poc_teacher',
                    role: '導師',
                    permissions: ['read', 'write', 'manage']
                }],
                is_active: true
            };

            const newClass = await Class.create(classData);
            setClasses(prev => [newClass, ...prev]);
            setSelectedClassId(newClass.id);
            setSelectedClassName(newClass.class_name);
            setExistingStudents([]);
            setShowNewClassForm(false);
            setNewClassData({
                class_name: '',
                academic_year: new Date().getFullYear() + '學年度'
            });
            setStep(2);
        } catch (error) {
            console.error("建立班級失敗:", error);
            alert('建立班級失敗，請重試');
        }
    };

    const handleParseAndValidate = () => {
        if (!csvText.trim()) {
            alert('請貼上CSV資料');
            return;
        }

        const lines = csvText.trim().split('\n');
        const hasHeader = lines[0].includes('姓名') || lines[0].includes('name');
        const dataLines = hasHeader ? lines.slice(1) : lines;

        const students = dataLines.map((line, index) => {
            const [name, student_id, email] = line.split(',').map(s => s.trim());
            return {
                raw: line,
                rowIndex: hasHeader ? index + 2 : index + 1,
                name,
                student_id,
                email: email || '' // 確保email不是undefined
            };
        });

        const valid = [];
        const errors = [];
        const duplicates = []; // 學號重複，需要使用者確認是否覆蓋更新
        const emailDuplicates = []; // Email在匯入清單中重複，視為錯誤，不會匯入
        const emailConflicts = []; // Email與班級中其他學生重複，需要使用者確認是否強制匯入

        // 建立現有學生的映射，用於快速查詢
        const existingStudentIdMap = new Map(existingStudents.map(s => [s.student_id, s]));
        const existingEmailMap = new Map(existingStudents.map(s => [s.email, s]));

        // 追蹤匯入清單內的重複項
        const importStudentIds = new Set();
        const importEmails = new Set();

        students.forEach(s => {
            let hasError = false;
            let errorReasons = [];

            // 1. 檢查必填欄位
            if (!s.name || !s.student_id) {
                errorReasons.push('姓名或學號為空');
                hasError = true;
            }

            // 2. 檢查email格式
            if (s.email && !isValidEmail(s.email)) {
                errorReasons.push('Email格式錯誤');
                hasError = true;
            }

            // 3. 檢查匯入清單內的學號重複
            if (s.student_id && importStudentIds.has(s.student_id)) {
                // 如果學號在匯入清單中重複，則此行視為錯誤
                errorReasons.push('學號在匯入清單中重複');
                hasError = true;
            } else if (s.student_id) {
                importStudentIds.add(s.student_id);
            }

            // 4. 檢查匯入清單內的email重複
            if (s.email && importEmails.has(s.email)) {
                // 如果email在匯入清單中重複，則此行放入emailDuplicates
                emailDuplicates.push({
                    ...s,
                    reason: `Email '${s.email}' 在匯入清單中重複`
                });
                hasError = true; // 視為錯誤，不進行後續處理
            } else if (s.email) {
                importEmails.add(s.email);
            }

            if (hasError) {
                errors.push({ ...s, reason: errorReasons.join('、') });
            } else {
                // 5. 檢查與現有學生的衝突
                const existingStudentByCurrentId = existingStudentIdMap.get(s.student_id);
                const existingStudentByCurrentEmail = existingEmailMap.get(s.email);

                if (existingStudentByCurrentId) {
                    // 學號重複 (更新現有學生)
                    duplicates.push({
                        ...s,
                        existing: existingStudentByCurrentId,
                        reason: '學號已存在於班級中'
                    });
                } else if (s.email && existingStudentByCurrentEmail) {
                    // Email衝突 (Email已被班級中其他學生使用)
                    emailConflicts.push({
                        ...s,
                        existing: existingStudentByCurrentEmail,
                        reason: `Email '${s.email}' 已被班級中學生 ${existingStudentByCurrentEmail.student_name} (${existingStudentByCurrentEmail.student_id}) 使用`
                    });
                } else {
                    // 無衝突，可以匯入
                    valid.push(s);
                }
            }
        });

        setValidationResult({ valid, errors, duplicates, emailDuplicates, emailConflicts });

        // 預設不匯入重複項
        const allDuplicateKeys = [
            ...duplicates.map(d => `student_${d.student_id}`),
            ...emailConflicts.map(d => `email_${d.email}`)
        ];
        setDuplicateSelections(
            allDuplicateKeys.reduce((acc, key) => ({ ...acc, [key]: false }), {})
        );

        setStep(3);
    };

    const handleFinalImport = async () => {
        setProcessing(true);

        // 準備要匯入的學生列表
        const validStudents = [...validationResult.valid];

        // 加入使用者選擇要覆蓋的學號重複學生
        const selectedDuplicates = validationResult.duplicates.filter(d =>
            duplicateSelections[`student_${d.student_id}`]
        );
        // 加入使用者選擇要強制匯入的Email衝突學生
        const selectedEmailConflicts = validationResult.emailConflicts.filter(d =>
            duplicateSelections[`email_${d.email}`]
        );

        const toImport = [...validStudents, ...selectedDuplicates, ...selectedEmailConflicts];

        let successCount = 0;
        let errorCount = 0; // Cumulative error count

        // Count initial errors from validation step that won't be processed
        let initialErrorCount = validationResult.errors.length + validationResult.emailDuplicates.length;
        errorCount += initialErrorCount;

        // Calculate skipped count
        let skippedCount = validationResult.duplicates.filter(d =>
            !duplicateSelections[`student_${d.student_id}`]
        ).length + validationResult.emailConflicts.filter(d =>
            !duplicateSelections[`email_${d.email}`]
        ).length;

        try {
            for (const student of toImport) {
                try {
                    const data = {
                        class_id: selectedClassId,
                        student_name: student.name,
                        student_id: student.student_id,
                        email: student.email || '',
                        join_date: new Date().toISOString().split('T')[0],
                        target_wpm: 230,
                        is_active: true
                    };

                    // If it's a duplicate (either student_id or email conflict), we update
                    if (student.existing) {
                        await ClassStudent.update(student.existing.id, data);
                    } else {
                        await ClassStudent.create(data);
                    }
                    successCount++;
                } catch (error) {
                    console.error(`匯入學生失敗: ${student.name}`, error);
                    errorCount++; // Increment error count for each failed import
                }
            }
        } catch (e) {
            console.error("匯入時發生錯誤:", e);
            // This catch block is for errors outside the individual student processing loop
            // For example, if ClassStudent.update/create is not a function.
            // It's less likely to hit if individual errors are handled.
        }

        setImportResult({
            successCount,
            errorCount,
            skippedCount
        });
        setStep(4);
        setProcessing(false);

        if (onImportComplete) {
            onImportComplete();
        }
    };

    const reset = () => {
        setCsvText('');
        setSelectedClassId(preselectedClassId || '');
        setSelectedClassName(preselectedClassName || '');
        setStep(preselectedClassId ? 2 : 1);
        setImportResult(null);
        setValidationResult({ valid: [], errors: [], duplicates: [], emailDuplicates: [], emailConflicts: [] });
        setExistingStudents([]);
        setShowNewClassForm(false);
        setNewClassData({
            class_name: '',
            academic_year: new Date().getFullYear() + '學年度'
        });
    };

    const downloadTemplate = () => {
        const csvContent = "姓名,學號,電子郵件\n張小明,S001,zhang@example.com\n李小華,S002,li@example.com\n王大志,S003,wang@example.com";
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'student_template.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => {
            setIsOpen(open);
            if (!open) setTimeout(reset, 300);
        }}>
            <DialogTrigger asChild>
                <Button className="gradient-bg text-white">
                    <Upload className="w-4 h-4 mr-2" /> 匯入學生資料
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>匯入學生資料</DialogTitle>
                </DialogHeader>

                <AnimatePresence mode="wait">
                    {/* Step 1: Class Selection */}
                    {step === 1 && (
                        <motion.div key="step1" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                            <div>
                                <Label htmlFor="class-select">選擇目標班級 *</Label>
                                <Select onValueChange={handleClassSelect} value={selectedClassId}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="請選擇要匯入學生的班級..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {classes.map(cls => (
                                            <SelectItem key={cls.id} value={cls.id}>
                                                {cls.class_name} {cls.academic_year && `(${cls.academic_year})`}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>

                                {classes.length === 0 && !showNewClassForm ? (
                                    <Alert className="mt-4">
                                        <AlertCircle className="h-4 w-4" />
                                        <AlertDescription>
                                            尚未建立任何班級，請先建立班級。
                                        </AlertDescription>
                                    </Alert>
                                ) : (
                                    !showNewClassForm && (
                                        <div className="mt-4">
                                            <Button
                                                variant="outline"
                                                onClick={() => setShowNewClassForm(true)}
                                                className="w-full"
                                            >
                                                <Plus className="w-4 h-4 mr-2" />
                                                或建立新班級
                                            </Button>
                                        </div>
                                    )
                                )}
                            </div>

                            {/* 新增班級表單 */}
                            <AnimatePresence>
                                {showNewClassForm && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="border rounded-lg p-4 bg-teal-50 overflow-hidden"
                                    >
                                        <div className="flex justify-between items-center mb-4">
                                            <h4 className="text-lg font-semibold">建立新班級</h4>
                                            <Button variant="ghost" size="sm" onClick={() => setShowNewClassForm(false)}>
                                                <X className="w-4 h-4" />
                                            </Button>
                                        </div>
                                        <div className="space-y-4">
                                            <div>
                                                <Label htmlFor="new-class-name">班級名稱 *</Label>
                                                <Input
                                                    id="new-class-name"
                                                    value={newClassData.class_name}
                                                    onChange={(e) => setNewClassData({ ...newClassData, class_name: e.target.value })}
                                                    placeholder="例如：三年甲班"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor="new-academic-year">學年度</Label>
                                                <Input
                                                    id="new-academic-year"
                                                    value={newClassData.academic_year}
                                                    onChange={(e) => setNewClassData({ ...newClassData, academic_year: e.target.value })}
                                                    placeholder="例如：2024學年度"
                                                />
                                            </div>
                                            <div className="flex justify-end gap-2">
                                                <Button variant="outline" onClick={() => setShowNewClassForm(false)}>
                                                    取消
                                                </Button>
                                                <Button onClick={handleCreateNewClass} className="gradient-bg text-white">
                                                    建立並選擇
                                                </Button>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    )}

                    {/* Step 2: CSV Input */}
                    {step === 2 && (
                        <motion.div key="step2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                <h4 className="font-semibold text-blue-900 mb-2">匯入至：{selectedClassName}</h4>
                                <p className="text-blue-800 text-sm">目前班級共有 {existingStudents.length} 位學生</p>
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <Label>CSV格式說明</Label>
                                    <Button variant="outline" size="sm" onClick={downloadTemplate}>
                                        <FileText className="w-4 h-4 mr-2" /> 下載範本
                                    </Button>
                                </div>
                                <div className="p-4 bg-gray-50 rounded-lg text-sm font-mono border">
                                    <div className="text-gray-600 mb-2">格式：姓名,學號,電子郵件</div>
                                    <div>張小明,S001,zhang@example.com</div>
                                    <div>李小華,S002,li@example.com</div>
                                    <div>王大志,S003,wang@example.com</div>
                                    <div className="text-red-600 mt-2 text-xs">
                                        ⚠️ 注意：學號在班級內必須唯一，且電子郵件在班級內也必須唯一。
                                    </div>
                                </div>
                            </div>

                            <div>
                                <Label htmlFor="csv-input">學生資料 (CSV格式) *</Label>
                                <Textarea
                                    id="csv-input"
                                    placeholder="貼上CSV格式的學生資料，可包含或不包含標題行..."
                                    value={csvText}
                                    onChange={(e) => setCsvText(e.target.value)}
                                    rows={10}
                                    className="font-mono text-sm"
                                />
                            </div>

                            <div className="flex justify-end gap-2">
                                <Button variant="outline" onClick={() => setStep(1)}>上一步</Button>
                                <Button onClick={handleParseAndValidate} disabled={!csvText.trim()}>
                                    驗證資料
                                </Button>
                            </div>
                        </motion.div>
                    )}

                    {/* Step 3: Validation Results */}
                    {step === 3 && (
                        <motion.div key="step3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                            <h3 className="font-semibold text-lg">資料驗證結果</h3>

                            {/* 錯誤資料 */}
                            {validationResult.errors.length > 0 && (
                                <Card className="border-red-200 bg-red-50">
                                    <CardHeader>
                                        <CardTitle className="text-red-800 flex items-center gap-2">
                                            <X className="w-5 h-5" />
                                            錯誤資料 ({validationResult.errors.length} 筆，將被忽略)
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        {validationResult.errors.map((s, i) => (
                                            <div key={i} className="p-2 bg-red-100 rounded text-sm">
                                                <strong>第 {s.rowIndex} 行:</strong> {s.reason} - "{s.raw}"
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>
                            )}

                            {/* Email 重複錯誤 */}
                            {validationResult.emailDuplicates.length > 0 && (
                                <Card className="border-red-200 bg-red-50">
                                    <CardHeader>
                                        <CardTitle className="text-red-800 flex items-center gap-2">
                                            <X className="w-5 h-5" />
                                            Email 在匯入清單中重複 ({validationResult.emailDuplicates.length} 筆，將被忽略)
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        {validationResult.emailDuplicates.map((s, i) => (
                                            <div key={i} className="p-2 bg-red-100 rounded text-sm">
                                                <strong>第 {s.rowIndex} 行:</strong> {s.reason} - {s.name} ({s.email})
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>
                            )}

                            {/* 學號重複處理 */}
                            {validationResult.duplicates.length > 0 && (
                                <Card className="border-yellow-200 bg-yellow-50">
                                    <CardHeader>
                                        <CardTitle className="text-yellow-800 flex items-center gap-2">
                                            <AlertCircle className="w-5 h-5" />
                                            學號重複處理 ({validationResult.duplicates.length} 筆)
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        {validationResult.duplicates.map(s => (
                                            <div key={`student-${s.student_id}`} className="flex items-center justify-between p-3 bg-yellow-100 rounded">
                                                <div>
                                                    <div className="font-medium">{s.name} ({s.student_id})</div>
                                                    <div className="text-xs text-yellow-700">
                                                        現有資料: {s.existing.student_name} - {s.existing.email || '無Email'}
                                                    </div>
                                                </div>
                                                <label className="flex items-center gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={duplicateSelections[`student_${s.student_id}`] || false}
                                                        onChange={(e) => setDuplicateSelections({
                                                            ...duplicateSelections,
                                                            [`student_${s.student_id}`]: e.target.checked
                                                        })}
                                                        className="w-4 h-4"
                                                    />
                                                    <span className="text-sm">覆蓋更新</span>
                                                </label>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>
                            )}

                            {/* Email 衝突處理 */}
                            {validationResult.emailConflicts.length > 0 && (
                                <Card className="border-orange-200 bg-orange-50">
                                    <CardHeader>
                                        <CardTitle className="text-orange-800 flex items-center gap-2">
                                            <AlertCircle className="w-5 h-5" />
                                            Email 衝突處理 ({validationResult.emailConflicts.length} 筆)
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        {validationResult.emailConflicts.map(s => (
                                            <div key={`email-${s.email}`} className="flex items-center justify-between p-3 bg-orange-100 rounded">
                                                <div>
                                                    <div className="font-medium">{s.name} ({s.student_id})</div>
                                                    <div className="text-xs text-orange-700">
                                                        {s.reason}
                                                    </div>
                                                </div>
                                                <label className="flex items-center gap-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={duplicateSelections[`email_${s.email}`] || false}
                                                        onChange={(e) => setDuplicateSelections({
                                                            ...duplicateSelections,
                                                            [`email_${s.email}`]: e.target.checked
                                                        })}
                                                        className="w-4 h-4"
                                                    />
                                                    <span className="text-sm">強制匯入 (會更新該Email舊學生的資料)</span>
                                                </label>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>
                            )}

                            {/* 新增學生 */}
                            {validationResult.valid.length > 0 && (
                                <Card className="border-green-200 bg-green-50">
                                    <CardHeader>
                                        <CardTitle className="text-green-800 flex items-center gap-2">
                                            <Check className="w-5 h-5" />
                                            新增學生 ({validationResult.valid.length} 筆)
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                            {validationResult.valid.map((s, i) => (
                                                <div key={i} className="p-2 bg-green-100 rounded text-sm">
                                                    {s.name} ({s.student_id}) {s.email && `- ${s.email}`}
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            <div className="flex justify-end gap-2 pt-4">
                                <Button variant="outline" onClick={() => setStep(2)}>返回修改</Button>
                                <Button
                                    onClick={handleFinalImport}
                                    disabled={processing || (
                                        validationResult.valid.length === 0 &&
                                        Object.values(duplicateSelections).every(v => !v) && // No valid students AND no selected duplicates/conflicts
                                        validationResult.errors.length === 0 && // No errors to prevent pressing if nothing is valid/selected
                                        validationResult.emailDuplicates.length === 0
                                    )}
                                    className="gradient-bg text-white"
                                >
                                    {processing ? '匯入中...' : '確認匯入'}
                                </Button>
                            </div>
                        </motion.div>
                    )}

                    {/* Step 4: Results */}
                    {step === 4 && (
                        <motion.div key="step4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center space-y-6 p-8">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                                <Check className="w-8 h-8 text-green-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900">匯入完成！</h3>
                            <div className="space-y-2 text-lg">
                                <div className="flex items-center justify-center gap-2 text-green-600">
                                    <Check className="w-5 h-5"/>
                                    成功匯入 {importResult.successCount} 位學生
                                </div>
                                {importResult.errorCount > 0 && (
                                    <div className="flex items-center justify-center gap-2 text-red-600">
                                        <X className="w-5 h-5"/>
                                        {importResult.errorCount} 筆資料因錯誤被忽略
                                    </div>
                                )}
                                {importResult.skippedCount > 0 && (
                                    <div className="flex items-center justify-center gap-2 text-yellow-600">
                                        <RefreshCw className="w-5 h-5"/>
                                        {importResult.skippedCount} 筆重複資料被跳過
                                    </div>
                                )}
                            </div>
                            <Button onClick={() => setIsOpen(false)} className="gradient-bg text-white">
                                完成
                            </Button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </DialogContent>
        </Dialog>
    );
}
