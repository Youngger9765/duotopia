import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import type { ChatMessage } from "./types";

interface ChatContainerProps {
  title: string;
  messages: ChatMessage[];
  onSend: (text: string) => void;
  onButtonSelect: (messageId: string, value: string) => void;
  onBack: () => void;
  inputDisabled?: boolean;
  inputPlaceholder?: string;
}

export function ChatContainer({
  title,
  messages,
  onSend,
  onButtonSelect,
  onBack,
  inputDisabled = false,
  inputPlaceholder,
}: ChatContainerProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Sub-header with back button */}
      <div className="flex items-center gap-2 border-b px-3 py-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onBack}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm font-medium">{title}</span>
      </div>

      {/* Messages */}
      <ChatMessages messages={messages} onButtonSelect={onButtonSelect} />

      {/* Input */}
      <ChatInput
        onSend={onSend}
        disabled={inputDisabled}
        placeholder={inputPlaceholder}
      />
    </div>
  );
}
