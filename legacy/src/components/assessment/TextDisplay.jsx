import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TextDisplay({ text }) {
  const [isReading, setIsReading] = React.useState(false);

  const handleTextToSpeech = () => {
    if ('speechSynthesis' in window) {
      if (isReading) {
        speechSynthesis.cancel();
        setIsReading(false);
      } else {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'zh-CN';
        utterance.rate = 0.8;
        utterance.onend = () => setIsReading(false);
        speechSynthesis.speak(utterance);
        setIsReading(true);
      }
    } else {
      alert('您的瀏覽器不支援語音合成功能');
    }
  };

  return (
    <Card className="glass-effect border-0 shadow-lg w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            朗讀文本
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleTextToSpeech}
            className="flex items-center gap-2"
          >
            <Volume2 className="w-4 h-4" />
            {isReading ? "停止朗讀" : "示範朗讀"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="prose prose-lg max-w-none">
          <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-100">
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap text-lg">
              {text}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}