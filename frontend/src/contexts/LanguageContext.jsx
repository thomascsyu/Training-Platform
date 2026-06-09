import { createContext, useContext, useState } from "react";
import { translations, UI_LANGUAGES } from "@/i18n";

const LanguageContext = createContext(null);

export const useLanguage = () => useContext(LanguageContext);

const lookup = (lang, key) => {
  const keys = key.split(".");
  let value = translations[lang];
  for (const k of keys) {
    value = value?.[k];
  }
  return value;
};

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    const saved = localStorage.getItem("learnhub_lang");
    return UI_LANGUAGES.includes(saved) ? saved : "en";
  });

  const t = (key) => lookup(lang, key) ?? lookup("en", key) ?? key;

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
