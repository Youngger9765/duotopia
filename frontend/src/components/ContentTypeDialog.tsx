import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ContentType {
  type: string;
  name: string;
  description: string;
  icon: string;
  recommended?: boolean;
}

const contentTypes: ContentType[] = [
  {
    type: 'reading_assessment',
    name: '朗讀評測',
    description: '學生朗讀課文，AI 評測發音準確度',
    icon: '📖',
    recommended: true
  },
  {
    type: 'speaking_practice',
    name: '口說練習',
    description: '自由口說練習，AI 提供即時回饋',
    icon: '🎙️',
    recommended: true
  },
  {
    type: 'speaking_scenario',
    name: '情境對話',
    description: '在特定情境下進行對話練習',
    icon: '💬'
  },
  {
    type: 'listening_cloze',
    name: '聽力填空',
    description: '聽音檔後填入缺少的單字',
    icon: '🎧'
  },
  {
    type: 'sentence_making',
    name: '造句練習',
    description: '使用指定單字或句型造句',
    icon: '✍️'
  },
  {
    type: 'speaking_quiz',
    name: '口說測驗',
    description: '回答問題測試口說能力',
    icon: '🎯'
  }
];

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
  lessonInfo
}: ContentTypeDialogProps) {
  const [loading, setLoading] = useState(false);

  const handleSelect = (contentType: ContentType) => {
    setLoading(true);
    onSelect({
      type: contentType.type,
      lessonId: lessonInfo.lessonId,
      programName: lessonInfo.programName,
      lessonName: lessonInfo.lessonName
    });
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent, contentType: ContentType) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSelect(contentType);
    }
  };

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={() => onClose()}>
      <DialogContent className="bg-white max-w-3xl" style={{ backgroundColor: 'white' }}>
        <DialogHeader>
          <DialogTitle>選擇內容類型</DialogTitle>
          <DialogDescription>
            為 「{lessonInfo.lessonName}」 選擇要新增的內容類型
          </DialogDescription>
        </DialogHeader>
        
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <span className="text-gray-500">處理中...</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 py-4">
            {contentTypes.map((contentType) => (
              <div
                key={contentType.type}
                data-testid={`content-type-card-${contentType.type}`}
                role="button"
                aria-label={`選擇${contentType.name}`}
                tabIndex={0}
                onClick={() => handleSelect(contentType)}
                onKeyDown={(e) => handleKeyDown(e, contentType)}
                className="p-4 border rounded-lg cursor-pointer transition-all hover:shadow-lg hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">{contentType.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{contentType.name}</h3>
                      {contentType.recommended && (
                        <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                          推薦
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
            取消
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}