import { createContext, useContext, useState } from "react";
import { translations } from "@/i18n";

const LanguageContext = createContext(null);

export const useLanguage = () => useContext(LanguageContext);

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    const saved = localStorage.getItem("learnhub_lang");
    return saved || "en";
  });

  const t = (key) => {
    const keys = key.split(".");
    let value = translations[lang];
    for (const k of keys) {
      value = value?.[k];
    }
    return value || key;
  };

  const switchLanguage = (newLang) => {
    if (["en", "zh-TW"].includes(newLang)) {
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
