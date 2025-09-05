import * as React from 'react';
import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
  disabled?: boolean;
  className?: string;
}

export function TagInput({
  value = [],
  onChange,
  placeholder = '輸入後按 Enter 新增標籤',
  maxTags = 10,
  disabled = false,
  className = '',
}: TagInputProps) {
  const [inputValue, setInputValue] = React.useState('');
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag();
    } else if (e.key === 'Backspace' && inputValue === '' && value.length > 0) {
      // Remove last tag when backspace is pressed with empty input
      removeTag(value.length - 1);
    }
  };

  const addTag = () => {
    const newTag = inputValue.trim();

    // Validate tag
    if (!newTag) return;
    if (value.includes(newTag)) {
      setInputValue('');
      return; // Don't add duplicate tags
    }
    if (value.length >= maxTags) {
      alert(`最多只能新增 ${maxTags} 個標籤`);
      return;
    }

    onChange([...value, newTag]);
    setInputValue('');
  };

  const removeTag = (indexToRemove: number) => {
    onChange(value.filter((_, index) => index !== indexToRemove));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    // If user types comma, add tag instead
    if (newValue.endsWith(',')) {
      setInputValue(newValue.slice(0, -1));
      addTag();
    } else {
      setInputValue(newValue);
    }
  };

  const handleInputBlur = () => {
    // Add tag when input loses focus if there's content
    if (inputValue.trim()) {
      addTag();
    }
  };

  return (
    <div className={`w-full ${className}`}>
      <div
        className="flex flex-wrap gap-2 p-2 border rounded-md min-h-[42px] cursor-text bg-white"
        onClick={() => inputRef.current?.focus()}
      >
        {value.map((tag, index) => (
          <Badge
            key={`${tag}-${index}`}
            variant="secondary"
            className="px-2 py-1 gap-1 hover:bg-secondary/80"
          >
            <span className="text-sm">{tag}</span>
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeTag(index);
                }}
                className="ml-1 hover:text-destructive transition-colors"
                aria-label={`移除標籤 ${tag}`}
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </Badge>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onBlur={handleInputBlur}
          placeholder={value.length === 0 ? placeholder : ''}
          disabled={disabled}
          className="flex-1 min-w-[120px] outline-none bg-transparent text-sm placeholder:text-muted-foreground disabled:cursor-not-allowed"
        />
      </div>
      {value.length > 0 && (
        <p className="text-xs text-muted-foreground mt-1">
          {value.length} 個標籤 {maxTags && `(最多 ${maxTags} 個)`}
        </p>
      )}
    </div>
  );
}

// Pre-defined tag suggestions
export interface TagSuggestion {
  value: string;
  label: string;
  category?: string;
}

interface TagInputWithSuggestionsProps extends TagInputProps {
  suggestions?: TagSuggestion[];
  showSuggestions?: boolean;
}

export function TagInputWithSuggestions({
  value = [],
  onChange,
  suggestions = [],
  showSuggestions = true,
  ...props
}: TagInputWithSuggestionsProps) {
  const availableSuggestions = suggestions.filter(
    (s) => !value.includes(s.value)
  );

  const handleSuggestionClick = (tag: string) => {
    if (!value.includes(tag) && value.length < (props.maxTags || 10)) {
      onChange([...value, tag]);
    }
  };

  return (
    <div className="space-y-2">
      <TagInput value={value} onChange={onChange} {...props} />

      {showSuggestions && availableSuggestions.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">建議標籤（點擊新增）：</p>
          <div className="flex flex-wrap gap-1">
            {availableSuggestions.slice(0, 8).map((suggestion) => (
              <Badge
                key={suggestion.value}
                variant="outline"
                className="cursor-pointer hover:bg-secondary transition-colors"
                onClick={() => handleSuggestionClick(suggestion.value)}
              >
                <span className="text-xs">{suggestion.label}</span>
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
