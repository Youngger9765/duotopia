import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { ChatContainer } from "../chat/ChatContainer";
import { useAiAssistant } from "../useAiAssistant";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import type { ChatMessage, QuickButton } from "../chat/types";

interface NavButton {
  label: string;
  /** Use "{teacherEmail}" as placeholder — replaced at runtime */
  path: string;
}

interface Step {
  messageKey: string;
  navButtons: NavButton[];
}

function getSteps(t: (key: string) => string): Step[] {
  return [
    {
      messageKey: "aiAssistant.quickStart.step1",
      navButtons: [
        {
          label: t("aiAssistant.quickStart.goToClassrooms"),
          path: "/teacher/classrooms",
        },
      ],
    },
    {
      messageKey: "aiAssistant.quickStart.step2",
      navButtons: [
        {
          label: t("aiAssistant.quickStart.goToStudents"),
          path: "/teacher/students",
        },
      ],
    },
    {
      messageKey: "aiAssistant.quickStart.step3",
      navButtons: [
        {
          label: t("aiAssistant.quickStart.browseResources"),
          path: "/teacher/resource-materials",
        },
      ],
    },
    {
      messageKey: "aiAssistant.quickStart.step4",
      navButtons: [
        {
          label: t("aiAssistant.quickStart.goToClassrooms"),
          path: "/teacher/classrooms",
        },
      ],
    },
    {
      messageKey: "aiAssistant.quickStart.step5",
      navButtons: [
        {
          label: t("aiAssistant.quickStart.goToDashboard"),
          path: "/teacher/dashboard",
        },
        {
          label: t("aiAssistant.quickStart.studentLogin"),
          path: "/student/login?teacher_email={teacherEmail}",
        },
      ],
    },
  ];
}

let _id = 0;
function nextId() {
  return `qs-${++_id}`;
}

export function QuickStartChat() {
  const { t } = useTranslation();
  const { exitFlow } = useAiAssistant();
  const teacherEmail = useTeacherAuthStore((s) => s.user?.email ?? "");
  const steps = getSteps(t);
  const [step, setStep] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    buildStepMessage(steps[0], 0, steps.length, teacherEmail, t),
  ]);

  const handleButtonSelect = useCallback(
    (_messageId: string, value: string) => {
      if (value.startsWith("navigate:")) {
        const path = value.replace("navigate:", "");
        window.open(path, "_blank");
        return;
      }

      if (value === "next-step") {
        const nextStep = step + 1;
        setStep(nextStep);

        if (nextStep < steps.length) {
          setMessages((prev) => [
            ...prev.map((m) => ({ ...m, buttons: undefined })),
            buildStepMessage(
              steps[nextStep],
              nextStep,
              steps.length,
              teacherEmail,
              t,
            ),
          ]);
        } else {
          setMessages((prev) => [
            ...prev.map((m) => ({ ...m, buttons: undefined })),
            {
              id: nextId(),
              role: "assistant",
              content: t("aiAssistant.quickStart.completionMessage"),
              buttons: [
                {
                  label: t("aiAssistant.quickStart.backToMenu"),
                  value: "back-to-menu",
                },
              ],
            },
          ]);
        }
        return;
      }

      if (value === "back-to-menu") {
        exitFlow();
      }
    },
    [step, exitFlow, teacherEmail, steps, t],
  );

  return (
    <ChatContainer
      title={t("aiAssistant.quickStart.title")}
      messages={messages}
      onSend={() => {}}
      onButtonSelect={handleButtonSelect}
      onBack={exitFlow}
      inputDisabled
      inputPlaceholder=""
    />
  );
}

function buildStepMessage(
  s: Step,
  stepIndex: number,
  totalSteps: number,
  teacherEmail: string,
  t: (key: string) => string,
): ChatMessage {
  const isLast = stepIndex === totalSteps - 1;

  const navBtns: QuickButton[] = s.navButtons.map((btn) => ({
    label: `${btn.label} →`,
    value: `navigate:${btn.path.replace("{teacherEmail}", encodeURIComponent(teacherEmail))}`,
  }));

  return {
    id: nextId(),
    role: "assistant",
    content: t(s.messageKey),
    buttons: [
      ...navBtns,
      {
        label: isLast
          ? t("aiAssistant.quickStart.allDone")
          : t("aiAssistant.quickStart.nextStep"),
        value: "next-step",
        variant: "default",
      },
    ],
  };
}
