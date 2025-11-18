/**
 * SentenceMakingActivity - 造句練習主組件
 *
 * 功能：
 * - 獲取練習題目（根據艾賓浩斯記憶曲線選擇）
 * - 根據 answer_mode 決定使用 ListeningMode 或 WritingMode
 * - 管理答題狀態和進度
 * - 檢查達標狀態
 */

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api";
import { Loader2 } from "lucide-react";
import WritingModeTemplate from "./WritingModeTemplate";
import ListeningModeTemplate from "./ListeningModeTemplate";

interface PracticeWord {
  content_item_id: number;
  text: string;
  translation: string;
  example_sentence: string;
  example_sentence_translation: string;
  audio_url?: string;
  memory_strength: number;
  priority_score: number;
}

interface AnswerRecord {
  content_item_id: number;
  is_correct: boolean;
  time_spent_seconds: number;
  answer_data: {
    selected_words: string[];
    attempts: number;
  };
}

interface MasteryStatus {
  current_mastery: number;
  target_mastery: number;
  achieved: boolean;
  words_mastered: number;
  total_words: number;
}

interface SentenceMakingState {
  sessionId: number | null;
  answerMode: "listening" | "writing";
  words: PracticeWord[];
  currentIndex: number;
  answers: AnswerRecord[];
  loading: boolean;
  masteryStatus: MasteryStatus | null;
  completing: boolean;
}

interface SentenceMakingActivityProps {
  assignmentId: number;
  onComplete?: () => void;
}

const SentenceMakingActivity: React.FC<SentenceMakingActivityProps> = ({
  assignmentId,
  onComplete,
}) => {
  const [state, setState] = useState<SentenceMakingState>({
    sessionId: null,
    answerMode: "writing",
    words: [],
    currentIndex: 0,
    answers: [],
    loading: true,
    masteryStatus: null,
    completing: false,
  });

  // 初始化：獲取練習題目
  useEffect(() => {
    loadPracticeWords();
  }, [assignmentId]);

  const loadPracticeWords = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true }));

      const response = (await apiClient.get(
        `/api/students/assignments/${assignmentId}/practice-words`,
      )) as {
        session_id: number;
        answer_mode: "listening" | "writing";
        words: PracticeWord[];
      };

      setState((prev) => ({
        ...prev,
        sessionId: response.session_id,
        answerMode: response.answer_mode,
        words: response.words,
        currentIndex: 0,
        loading: false,
      }));
    } catch (error) {
      console.error("Failed to load practice words:", error);
      toast.error("無法載入練習題目");
      setState((prev) => ({ ...prev, loading: false }));
    }
  };

  // 提交答案
  const submitAnswer = async (answer: AnswerRecord) => {
    if (!state.sessionId) {
      toast.error("練習 session 不存在");
      return;
    }

    try {
      await apiClient.post(
        `/api/students/practice-sessions/${state.sessionId}/submit-answer`,
        answer,
      );

      // 記錄答案
      setState((prev) => ({
        ...prev,
        answers: [...prev.answers, answer],
      }));

      // 移動到下一題
      if (state.currentIndex < state.words.length - 1) {
        setState((prev) => ({ ...prev, currentIndex: prev.currentIndex + 1 }));
      } else {
        // 完成本輪練習，檢查達標狀態
        await checkMasteryStatus();
      }
    } catch (error) {
      console.error("Failed to submit answer:", error);
      toast.error("提交答案失敗");
    }
  };

  // 檢查達標狀態
  const checkMasteryStatus = async () => {
    try {
      setState((prev) => ({ ...prev, completing: true }));

      const status = (await apiClient.get(
        `/api/students/assignments/${assignmentId}/mastery-status`,
      )) as MasteryStatus;

      setState((prev) => ({
        ...prev,
        masteryStatus: status,
        completing: false,
      }));

      if (status.achieved) {
        toast.success("🎉 恭喜！您已達成目標熟悉度！");
        // 等待 2 秒後執行 onComplete
        setTimeout(() => {
          if (onComplete) {
            onComplete();
          }
        }, 2000);
      } else {
        const masteryPercent = (status.current_mastery * 100).toFixed(0);
        toast.info(
          `當前熟悉度：${masteryPercent}%，繼續加油！已掌握 ${status.words_mastered}/${status.total_words} 個單字`,
        );
        // 重新載入下一輪題目
        setTimeout(() => {
          loadPracticeWords();
        }, 1500);
      }
    } catch (error) {
      console.error("Failed to check mastery status:", error);
      toast.error("無法檢查作業完成度");
      setState((prev) => ({ ...prev, completing: false }));
    }
  };

  // Loading 狀態
  if (state.loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600">正在載入練習題目...</p>
      </div>
    );
  }

  // Completing 狀態（檢查達標中）
  if (state.completing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="h-12 w-12 animate-spin text-green-600 mb-4" />
        <p className="text-gray-600">正在計算您的學習進度...</p>
      </div>
    );
  }

  // 沒有題目
  if (state.words.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <p className="text-gray-600 mb-4">目前沒有需要練習的單字</p>
      </div>
    );
  }

  const currentWord = state.words[state.currentIndex];
  const progress = {
    current: state.currentIndex + 1,
    total: state.words.length,
  };

  // 根據 answer_mode 渲染對應的 Template
  return (
    <div className="sentence-making-activity">
      {state.answerMode === "listening" ? (
        <ListeningModeTemplate
          word={currentWord}
          onSubmit={submitAnswer}
          progress={progress}
        />
      ) : (
        <WritingModeTemplate
          word={currentWord}
          onSubmit={submitAnswer}
          progress={progress}
        />
      )}
    </div>
  );
};

export default SentenceMakingActivity;
