export interface QuickButton {
  label: string;
  value: string;
  variant?: "default" | "outline" | "secondary";
}

export interface TableColumn {
  key: string;
  label: string;
}

export interface TableData {
  columns: TableColumn[];
  rows: Record<string, string>[];
}

export interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  /** Quick-reply buttons shown below the message */
  buttons?: QuickButton[];
  /** Table data shown below the message */
  table?: TableData;
  /** Loading indicator */
  loading?: boolean;
}
