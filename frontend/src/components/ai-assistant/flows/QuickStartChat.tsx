import { useState, useCallback } from "react";
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
  message: string;
  navButtons: NavButton[];
}

const STEPS: Step[] = [
  {
    message:
      "歡迎使用 Duotopia！讓我一步步帶您上手 🎉\n\n**Step 1／5 — 建立班級**\n到「我的班級」新增您的第一個班級，填寫班級名稱和等級即可。\n\n完成後回來點「完成，下一步」繼續！",
    navButtons: [{ label: "前往我的班級", path: "/teacher/classrooms" }],
  },
  {
    message:
      "很好！接下來：\n\n**Step 2／5 — 新增學生**\n在班級中新增學生，或到「所有學生」用 CSV 批次匯入。\n\n完成後回來點「完成，下一步」繼續！",
    navButtons: [{ label: "前往所有學生", path: "/teacher/students" }],
  },
  {
    message:
      "學生加好了！接著準備教材：\n\n**Step 3／5 — 準備教材**\n到「資源教材包」瀏覽現成教材，找到適合的點「複製」就能加到自己的帳號。\n\n完成後回來點「完成，下一步」繼續！",
    navButtons: [
      { label: "瀏覽資源教材包", path: "/teacher/resource-materials" },
    ],
  },
  {
    message:
      "教材準備好了！現在來派作業：\n\n**Step 4／5 — 派發作業**\n回到「我的班級」，進入班級後用剛才複製的教材建立作業，指派給學生。\n\n完成後回來點「完成，下一步」繼續！",
    navButtons: [{ label: "前往我的班級", path: "/teacher/classrooms" }],
  },
  {
    message:
      "最後一步！\n\n**Step 5／5 — 分享給學生**\n點選右側工具列的「分享」按鈕，讓學生掃描 QR code 加入班級。\n\n也可以直接把下方的「學生登入頁」連結傳給學生，學生登入後就可以開始寫作業囉！\n\n完成後回來點「全部完成！」",
    navButtons: [
      { label: "前往儀表板", path: "/teacher/dashboard" },
      {
        label: "學生登入頁",
        path: "/student/login?teacher_email={teacherEmail}",
      },
    ],
  },
];

const COMPLETION_MESSAGE =
  "恭喜您完成所有基本設定！🎉\n\n您已經學會了建立班級、新增學生、準備教材、派發作業和分享給學生。\n\n如果還有其他問題，可以隨時使用「找功能」來尋找您需要的頁面。";

let _id = 0;
function nextId() {
  return `qs-${++_id}`;
}

export function QuickStartChat() {
  const { exitFlow } = useAiAssistant();
  const teacherEmail = useTeacherAuthStore((s) => s.user?.email ?? "");
  const [step, setStep] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    buildStepMessage(STEPS[0], 0, teacherEmail),
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

        if (nextStep < STEPS.length) {
          setMessages((prev) => [
            ...prev.map((m) => ({ ...m, buttons: undefined })),
            buildStepMessage(STEPS[nextStep], nextStep, teacherEmail),
          ]);
        } else {
          setMessages((prev) => [
            ...prev.map((m) => ({ ...m, buttons: undefined })),
            {
              id: nextId(),
              role: "assistant",
              content: COMPLETION_MESSAGE,
              buttons: [{ label: "回到主選單", value: "back-to-menu" }],
            },
          ]);
        }
        return;
      }

      if (value === "back-to-menu") {
        exitFlow();
      }
    },
    [step, exitFlow, teacherEmail],
  );

  return (
    <ChatContainer
      title="新手快速指引"
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
  teacherEmail: string,
): ChatMessage {
  const isLast = stepIndex === STEPS.length - 1;

  const navBtns: QuickButton[] = s.navButtons.map((btn) => ({
    label: `${btn.label} →`,
    value: `navigate:${btn.path.replace("{teacherEmail}", encodeURIComponent(teacherEmail))}`,
  }));

  return {
    id: nextId(),
    role: "assistant",
    content: s.message,
    buttons: [
      ...navBtns,
      {
        label: isLast ? "全部完成！ ✓" : "完成，下一步 →",
        value: "next-step",
        variant: "default",
      },
    ],
  };
}
