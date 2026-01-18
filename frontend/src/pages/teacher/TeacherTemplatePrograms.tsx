import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import TeacherLayout from "@/components/TeacherLayout";
import { ProgramTreeView } from "@/components/shared/ProgramTreeView";
import { useProgramAPI } from "@/hooks/useProgramAPI";
import { toast } from "sonner";
import { Program } from "@/types";

export default function TeacherTemplateProgramsNew() {
  const { t } = useTranslation();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);

  // Use unified Programs API
  const api = useProgramAPI({
    scope: 'teacher',
  });

  useEffect(() => {
    fetchTemplatePrograms();
  }, []);

  const fetchTemplatePrograms = async () => {
    try {
      setLoading(true);
      const data = await api.getPrograms();
      setPrograms(data);
    } catch (err) {
      console.error("Failed to fetch template programs:", err);
      toast.error(t("teacherTemplatePrograms.messages.loadFailed"));
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
            <p className="mt-4 text-gray-600">{t("common.loading")}</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="p-6 space-y-4">
        <ProgramTreeView
          programs={programs}
          showCreateButton
          createButtonText={t("teacherTemplatePrograms.buttons.addProgram")}
          scope="teacher"
          onRefresh={fetchTemplatePrograms}
        />
      </div>
    </TeacherLayout>
  );
}
