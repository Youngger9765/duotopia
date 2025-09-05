import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  Headphones
} from 'lucide-react';

interface ListeningClozeProps {
  content: string;
  audioUrl: string;
  blanks: string[];
  userAnswers: string[];
  onAnswerChange: (index: number, value: string) => void;
  showAnswers?: boolean;
}

export default function ListeningClozeTemplate({
  content,
  audioUrl,
  blanks,
  userAnswers,
  onAnswerChange,
  showAnswers = false
}: ListeningClozeProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playCount, setPlayCount] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handlePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
      setPlayCount(prev => prev + 1);
    }
    setIsPlaying(!isPlaying);
  };

  const handleReplay = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    audioRef.current.play();
    setIsPlaying(true);
    setPlayCount(prev => prev + 1);
  };

  // Parse content and replace blanks with input fields
  const renderContent = () => {
    let blankIndex = 0;
    const parts = content.split(/___+/g);

    return parts.map((part, index) => (
      <span key={index}>
        {part}
        {index < parts.length - 1 && (
          <Input
            type="text"
            className="w-32 mx-2 inline-block"
            placeholder={`空格 ${blankIndex + 1}`}
            value={userAnswers[blankIndex] || ''}
            onChange={(e) => {
              const currentIndex = blankIndex;
              onAnswerChange(currentIndex, e.target.value);
            }}
            data-index={blankIndex++}
          />
        )}
      </span>
    ));
  };

  return (
    <div className="space-y-6">
      {/* Audio Player Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Headphones className="h-5 w-5" />
          聽力音檔
        </h3>

        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <Button
              onClick={handlePlayPause}
              size="lg"
              className="rounded-full"
            >
              {isPlaying ? (
                <Pause className="h-6 w-6" />
              ) : (
                <Play className="h-6 w-6" />
              )}
            </Button>

            <Button
              variant="outline"
              onClick={handleReplay}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              重播
            </Button>

            <Badge variant="secondary">
              已播放 {playCount} 次
            </Badge>
          </div>

          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={() => setIsPlaying(false)}
          />

          <p className="text-sm text-gray-600">
            💡 提示：可以重複播放音檔，仔細聆聽後填寫空格
          </p>
        </div>
      </div>

      {/* Fill in the blanks section */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-medium mb-4">填空作答</h3>
        <div className="text-lg leading-relaxed">
          {renderContent()}
        </div>
      </div>

      {/* Show answers if needed (for review) */}
      {showAnswers && (
        <div className="bg-green-50 rounded-lg p-6">
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            參考答案
          </h4>
          <div className="space-y-2">
            {blanks.map((answer, index) => (
              <div key={index} className="flex items-center gap-2">
                <Badge variant="outline">空格 {index + 1}</Badge>
                <span className="font-medium">{answer}</span>
                {userAnswers[index] === answer && (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
