import { useTranslation } from "react-i18next";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Globe } from "lucide-react";

const languages = [
  { code: "zh-TW", name: "繁體中文" },
  { code: "en", name: "English" },
];

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
  };

  // Normalize language code (e.g., "zh-TW-TW" -> "zh-TW", "en-US" -> "en")
  const normalizedLanguage = i18n.language.startsWith("zh") ? "zh-TW" : "en";

  return (
    <Select value={normalizedLanguage} onValueChange={handleLanguageChange}>
      <SelectTrigger className="w-9 sm:w-[140px] px-2 sm:px-3 border-0 sm:border bg-transparent sm:bg-background shadow-none sm:shadow-sm [&>svg.opacity-50]:hidden sm:[&>svg.opacity-50]:block">
        <Globe className="h-5 w-5 text-gray-500 sm:hidden" />
        <div className="hidden sm:flex sm:items-center sm:gap-2">
          <Globe className="h-4 w-4 text-gray-500" />
          <SelectValue placeholder={t("common.selectLanguage")} />
        </div>
      </SelectTrigger>
      <SelectContent>
        {languages.map((lang) => (
          <SelectItem key={lang.code} value={lang.code}>
            {lang.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
