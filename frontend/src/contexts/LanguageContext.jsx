import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { defaultTranslations, localeLoaders, UI_LANGUAGES } from "@/i18n";

const LanguageContext = createContext(null);

export const useLanguage = () => useContext(LanguageContext);

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    const saved = localStorage.getItem("learnhub_lang");
    return UI_LANGUAGES.includes(saved) ? saved : "en";
  });
  // Non-default locales are fetched on demand; until a locale finishes
  // loading, `dict` keeps showing the previously loaded strings (English on
  // first load) rather than raw translation keys.
  const [dict, setDict] = useState(defaultTranslations);

  useEffect(() => {
    let cancelled = false;
    localeLoaders[lang]().then((loaded) => {
      if (!cancelled) setDict(loaded);
    });
    return () => {
      cancelled = true;
    };
  }, [lang]);

  const t = useCallback(
    (key, params = {}) => {
      const keys = key.split(".");
      let value = dict;
      for (const k of keys) {
        value = value?.[k];
      }
      if (typeof value !== "string") return key;
      return Object.entries(params).reduce(
        (text, [name, val]) => text.replace(`{${name}}`, String(val)),
        value
      );
    },
    [dict]
  );

  const switchLanguage = useCallback((newLang) => {
    if (UI_LANGUAGES.includes(newLang)) {
      setLang(newLang);
      localStorage.setItem("learnhub_lang", newLang);
    }
  }, []);

  const value = useMemo(
    () => ({ lang, t, switchLanguage }),
    [lang, t, switchLanguage]
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};
