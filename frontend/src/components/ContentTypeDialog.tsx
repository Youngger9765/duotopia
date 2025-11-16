import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useTranslation } from "react-i18next";

interface ContentType {
  type: string;
  name: string;
  description: string;
  icon: string;
  recommended?: boolean;
  disabled?: boolean;
}

// Note: Content types are now defined inside the component to access t()

interface ContentTypeDialogProps {
  open: boolean;
  onClose: () => void;
  onSelect: (selection: {
    type: string;
    lessonId: number;
    programName: string;
    lessonName: string;
  }) => void;
  lessonInfo: {
    programName: string;
    lessonName: string;
    lessonId: number;
  };
}

export default function ContentTypeDialog({
  open,
  onClose,
  onSelect,
  lessonInfo,
}: ContentTypeDialogProps) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);

  const contentTypes: ContentType[] = [
    {
      type: "reading_assessment",
      name: t("dialogs.contentTypeDialog.types.reading_assessment.name"),
      description: t(
        "dialogs.contentTypeDialog.types.reading_assessment.description",
      ),
      icon: "📖",
      recommended: true,
      disabled: false,
    },
    {
      type: "speaking_practice",
      name: t("dialogs.contentTypeDialog.types.speaking_practice.name"),
      description: t(
        "dialogs.contentTypeDialog.types.speaking_practice.description",
      ),
      icon: "🎙️",
      recommended: true,
      disabled: true,
    },
    {
      type: "speaking_scenario",
      name: t("dialogs.contentTypeDialog.types.speaking_scenario.name"),
      description: t(
        "dialogs.contentTypeDialog.types.speaking_scenario.description",
      ),
      icon: "💬",
      disabled: true,
    },
    {
      type: "listening_cloze",
      name: t("dialogs.contentTypeDialog.types.listening_cloze.name"),
      description: t(
        "dialogs.contentTypeDialog.types.listening_cloze.description",
      ),
      icon: "🎧",
      disabled: true,
    },
    {
      type: "sentence_making",
      name: t("dialogs.contentTypeDialog.types.sentence_making.name"),
      description: t(
        "dialogs.contentTypeDialog.types.sentence_making.description",
      ),
      icon: "✍️",
      disabled: false,
    },
    {
      type: "speaking_quiz",
      name: t("dialogs.contentTypeDialog.types.speaking_quiz.name"),
      description: t(
        "dialogs.contentTypeDialog.types.speaking_quiz.description",
      ),
      icon: "🎯",
      disabled: true,
    },
  ];

  const handleSelect = (contentType: ContentType) => {
    if (contentType.disabled) return;

    setLoading(true);
    onSelect({
      type: contentType.type,
      lessonId: lessonInfo.lessonId,
      programName: lessonInfo.programName,
      lessonName: lessonInfo.lessonName,
    });
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent, contentType: ContentType) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleSelect(contentType);
    }
  };

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={() => onClose()}>
      <DialogContent
        className="bg-white max-w-3xl"
        style={{ backgroundColor: "white" }}
      >
        <DialogHeader>
          <DialogTitle>{t("dialogs.contentTypeDialog.title")}</DialogTitle>
          <DialogDescription>
            {t("dialogs.contentTypeDialog.description", {
              lessonName: lessonInfo.lessonName,
            })}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <span className="text-gray-500">
              {t("dialogs.contentTypeDialog.processing")}
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 py-4">
            {contentTypes.map((contentType) => (
              <div
                key={contentType.type}
                data-testid={`content-type-card-${contentType.type}`}
                role="button"
                aria-label={`選擇${contentType.name}`}
                aria-disabled={contentType.disabled}
                tabIndex={contentType.disabled ? -1 : 0}
                onClick={() => handleSelect(contentType)}
                onKeyDown={(e) => handleKeyDown(e, contentType)}
                className={`p-4 border rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 ${
                  contentType.disabled
                    ? "opacity-50 cursor-not-allowed bg-gray-50"
                    : "cursor-pointer hover:shadow-lg hover:border-blue-400"
                }`}
              >
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">{contentType.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{contentType.name}</h3>
                      {contentType.recommended && !contentType.disabled && (
                        <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                          {t("dialogs.contentTypeDialog.recommended")}
                        </span>
                      )}
                      {contentType.disabled && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                          {t("dialogs.contentTypeDialog.comingSoon")}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {contentType.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            {t("dialogs.contentTypeDialog.cancel")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
