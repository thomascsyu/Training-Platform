import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Languages } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { uiLanguages } from "@/i18n";

export const LanguageSwitcher = () => {
  const { lang, switchLanguage } = useLanguage();

  return (
    <Select value={lang} onValueChange={switchLanguage}>
      <SelectTrigger className="w-[140px] rounded-sm border-slate-200" data-testid="language-switcher">
        <Languages className="w-4 h-4 mr-2" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {uiLanguages.map(({ value, label }) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
