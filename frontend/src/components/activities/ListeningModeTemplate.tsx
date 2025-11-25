/**
 * ListeningModeTemplate - 聽力模式組件
 *
 * 功能：
 * - 自動播放例句音檔
 * - 學生聽音檔後選擇單字組成句子
 * - 可以重播音檔
 */

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { CheckCircle2, XCircle, Volume2, Loader2 } from "lucide-react";
import ProgressIndicator from "./shared/ProgressIndicator";
import WordChoicePanel from "./shared/WordChoicePanel";

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

interface ListeningModeTemplateProps {
  word: PracticeWord;
  onSubmit: (answer: AnswerRecord) => void;
  progress: { current: number; total: number };
}

const ListeningModeTemplate: React.FC<ListeningModeTemplateProps> = ({
  word,
  onSubmit,
  progress,
}) => {
  const [selectedWords, setSelectedWords] = useState<string[]>([]);
  const [availableWords, setAvailableWords] = useState<string[]>([]);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState(Date.now());
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioPlayed, setAudioPlayed] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 初始化：打亂例句單字
  useEffect(() => {
    resetQuestion();
  }, [word]);

  // 自動播放音檔
  useEffect(() => {
    if (word.audio_url && !audioPlayed) {
      playAudio();
    }
  }, [word.audio_url, audioPlayed]);

  const resetQuestion = () => {
    const words = word.example_sentence
      .replace(/[,!?.]/g, "") // 移除標點
      .split(" ")
      .filter((w) => w.length > 0);

    // 隨機打亂
    const shuffled = [...words].sort(() => Math.random() - 0.5);
    setAvailableWords(shuffled);
    setSelectedWords([]);
    setAttempts(0);
    setStartTime(Date.now());
    setShowResult(false);
    setIsCorrect(false);
    setAudioPlayed(false);
  };

  const playAudio = () => {
    if (!word.audio_url) {
      toast.error("此題目沒有音檔");
      return;
    }

    setAudioPlaying(true);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }

    const audio = new Audio(word.audio_url);
    audioRef.current = audio;

    audio.onended = () => {
      setAudioPlaying(false);
      setAudioPlayed(true);
    };

    audio.onerror = () => {
      setAudioPlaying(false);
      toast.error("音檔載入失敗");
    };

    audio.play().catch((error) => {
      console.error("Audio play error:", error);
      setAudioPlaying(false);
      toast.error("音檔播放失敗");
    });
  };

  const correctWords = word.example_sentence
    .replace(/[,!?.]/g, "")
    .split(" ")
    .filter((w) => w.length > 0);

  const handleWordClick = (clickedWord: string) => {
    setAttempts((prev) => prev + 1);

    const nextIndex = selectedWords.length;
    const correctWord = correctWords[nextIndex];

    if (clickedWord === correctWord) {
      // 正確：添加到答案區
      const newSelectedWords = [...selectedWords, clickedWord];
      setSelectedWords(newSelectedWords);

      // 只移除一個匹配的單字（處理重複單字情況）
      setAvailableWords((prev) => {
        const index = prev.indexOf(clickedWord);
        if (index > -1) {
          return [...prev.slice(0, index), ...prev.slice(index + 1)];
        }
        return prev;
      });

      // 檢查是否完成
      if (newSelectedWords.length === correctWords.length) {
        // 全部答對，提交答案
        const timeSpent = Math.floor((Date.now() - startTime) / 1000);
        setIsCorrect(true);
        setShowResult(true);

        // 延遲提交，讓學生看到正確提示
        setTimeout(() => {
          onSubmit({
            content_item_id: word.content_item_id,
            is_correct: true,
            time_spent_seconds: timeSpent,
            answer_data: {
              selected_words: newSelectedWords,
              attempts,
            },
          });
        }, 1500);
      }
    } else {
      // 錯誤：顯示提示
      toast.error("這個單字的位置不對，再試試看！", {
        duration: 2000,
      });
    }
  };

  const handleRemoveWord = (index: number) => {
    const removedWord = selectedWords[index];
    setSelectedWords(selectedWords.slice(0, index));
    setAvailableWords([...availableWords, removedWord]);
  };

  return (
    <div className="listening-mode max-w-4xl mx-auto p-6">
      {/* 進度條 */}
      <ProgressIndicator current={progress.current} total={progress.total} />

      {/* 音檔播放區 */}
      <div className="audio-section mt-8 mb-8 p-6 bg-purple-50 rounded-lg border-2 border-purple-200">
        <div className="text-center">
          {!audioPlayed && audioPlaying && (
            <div className="mb-4">
              <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-2" />
              <p className="text-purple-700 font-medium">正在播放例句音檔...</p>
              <p className="text-sm text-purple-600 mt-1">請仔細聆聽</p>
            </div>
          )}

          {!audioPlaying && (
            <div className="mb-4">
              <div className="text-lg font-semibold text-gray-800 mb-2">
                請聽音檔，然後選擇正確的單字組成句子
              </div>
              <Button
                onClick={playAudio}
                variant="outline"
                className="border-purple-300 hover:bg-purple-50"
              >
                <Volume2 className="mr-2 h-5 w-5" />
                {audioPlayed ? "重播音檔" : "播放音檔"}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 單字資訊 */}
      <div className="word-info mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-sm font-medium text-gray-600">
              本題單字：
            </span>
            <span className="text-xl font-bold text-purple-600 ml-2">
              {word.text}
            </span>
          </div>
          <div className="h-6 w-px bg-gray-300"></div>
          <div>
            <span className="text-sm font-medium text-gray-600">
              中文意思：
            </span>
            <span className="text-lg text-gray-800 ml-2">
              {word.translation}
            </span>
          </div>
        </div>
      </div>

      {/* 答案區 */}
      <div className="answer-area mb-8">
        <div className="text-sm font-medium mb-3 text-gray-700">
          答案區（按順序點擊下方單字）：
        </div>
        <div className="flex flex-wrap gap-2 min-h-[80px] p-4 bg-white border-2 border-gray-300 rounded-lg">
          {selectedWords.map((w, idx) => (
            <button
              key={idx}
              onClick={() => handleRemoveWord(idx)}
              className="px-4 py-2 bg-purple-100 border-2 border-purple-300 rounded-lg hover:bg-purple-200 transition-colors"
            >
              {w}
            </button>
          ))}
          {/* 空白框提示 */}
          {Array.from({
            length: correctWords.length - selectedWords.length,
          }).map((_, idx) => (
            <div
              key={`empty-${idx}`}
              className="px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg w-20"
            />
          ))}
        </div>
      </div>

      {/* 單字選擇區 */}
      <WordChoicePanel
        words={availableWords}
        onWordClick={handleWordClick}
        disabled={showResult}
        variant="listening"
      />

      {/* 結果提示 */}
      {showResult && (
        <div
          className={`mt-6 p-4 rounded-lg flex items-center gap-3 ${
            isCorrect
              ? "bg-green-50 border-2 border-green-300"
              : "bg-red-50 border-2 border-red-300"
          }`}
        >
          {isCorrect ? (
            <>
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <div>
                <div className="font-semibold text-green-800">答對了！</div>
                <div className="text-sm text-green-700">
                  正確句子：{word.example_sentence}
                </div>
                <div className="text-sm text-green-600 mt-1">
                  正在準備下一題...
                </div>
              </div>
            </>
          ) : (
            <>
              <XCircle className="h-6 w-6 text-red-600" />
              <div>
                <div className="font-semibold text-red-800">再試試看！</div>
              </div>
            </>
          )}
        </div>
      )}

      {/* 統計資訊 */}
      <div className="mt-6 text-center text-sm text-gray-500">
        嘗試次數：{attempts}
      </div>
    </div>
  );
};

export default ListeningModeTemplate;
