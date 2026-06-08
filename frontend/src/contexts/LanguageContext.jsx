import { createContext, useContext, useState } from "react";
import { translations } from "@/i18n";

const UI_LANGUAGES = ["en", "zh-TW", "zh-CN", "ja", "ko"];

const LanguageContext = createContext(null);

export const useLanguage = () => useContext(LanguageContext);

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    const saved = localStorage.getItem("learnhub_lang");
    return UI_LANGUAGES.includes(saved) ? saved : "en";
  });

  const t = (key, params = {}) => {
    const keys = key.split(".");
    let value = translations[lang];
    for (const k of keys) {
      value = value?.[k];
    }
    if (typeof value !== "string") return key;
    return Object.entries(params).reduce(
      (text, [name, val]) => text.replace(`{${name}}`, String(val)),
      value
    );
  };

  const switchLanguage = (newLang) => {
    if (UI_LANGUAGES.includes(newLang)) {
      setLang(newLang);
      localStorage.setItem("learnhub_lang", newLang);
    }
  };

  return (
    <LanguageContext.Provider value={{ lang, t, switchLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
};
