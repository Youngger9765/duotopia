import { useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ChatMessage, QuickButton, TableData } from "./types";

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap",
          isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900",
        )}
      >
        {message.loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          message.content
        )}
      </div>
    </div>
  );
}

function QuickButtons({
  buttons,
  onSelect,
}: {
  buttons: QuickButton[];
  onSelect: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {buttons.map((btn) => (
        <Button
          key={btn.value}
          variant={btn.variant ?? "outline"}
          size="sm"
          className="h-auto px-3 py-1.5 text-xs"
          onClick={() => onSelect(btn.value)}
        >
          {btn.label}
        </Button>
      ))}
    </div>
  );
}

function MessageTable({ table }: { table: TableData }) {
  return (
    <div className="overflow-x-auto rounded border text-xs">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-gray-50">
            {table.columns.map((col) => (
              <th
                key={col.key}
                className="px-2 py-1.5 text-left font-medium text-gray-600"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i} className="border-b last:border-b-0">
              {table.columns.map((col) => (
                <td key={col.key} className="px-2 py-1.5">
                  {col.key === "status" ? (
                    <Badge
                      variant={
                        row[col.key]?.includes("⚠")
                          ? "destructive"
                          : "secondary"
                      }
                      className="text-[10px]"
                    >
                      {row[col.key]}
                    </Badge>
                  ) : (
                    row[col.key]
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  onButtonSelect?: (messageId: string, value: string) => void;
}

export function ChatMessages({ messages, onButtonSelect }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <ScrollArea className="flex-1">
      <div className="space-y-3 p-4">
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-2">
            <MessageBubble message={msg} />
            {msg.table && <MessageTable table={msg.table} />}
            {msg.buttons && msg.buttons.length > 0 && onButtonSelect && (
              <QuickButtons
                buttons={msg.buttons}
                onSelect={(value) => onButtonSelect(msg.id, value)}
              />
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
