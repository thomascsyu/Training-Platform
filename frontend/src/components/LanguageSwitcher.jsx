import { Languages } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useLanguage } from "@/contexts/LanguageContext";

export const LanguageSwitcher = () => {
  const { lang, switchLanguage } = useLanguage();

  return (
    <Select value={lang} onValueChange={switchLanguage}>
      <SelectTrigger className="w-[120px] rounded-sm border-slate-200" data-testid="language-switcher">
        <Languages className="w-4 h-4 mr-2" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="en">English</SelectItem>
        <SelectItem value="zh-TW">繁體中文</SelectItem>
      </SelectContent>
    </Select>
  );
};
