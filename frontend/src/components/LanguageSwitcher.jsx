import { Languages } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useLanguage } from "@/contexts/LanguageContext";
import { languageNames, UI_LANGUAGES } from "@/i18n";

export const LanguageSwitcher = () => {
  const { lang, switchLanguage } = useLanguage();

  return (
    <Select value={lang} onValueChange={switchLanguage}>
      <SelectTrigger className="w-[130px] rounded-sm border-slate-200" data-testid="language-switcher">
        <Languages className="w-4 h-4 mr-2" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {UI_LANGUAGES.map((code) => (
          <SelectItem key={code} value={code}>{languageNames[code]}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
