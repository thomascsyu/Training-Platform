import en from "./en";

// Only the default locale is bundled eagerly. The rest are code-split and
// fetched on demand by LanguageContext so switching/loading a non-English
// UI doesn't cost every visitor ~2,000 lines of unused translation strings.
export const localeLoaders = {
  en: () => Promise.resolve(en),
  "zh-TW": () => import("./zh-TW").then((m) => m.default),
  "zh-CN": () => import("./zh-CN").then((m) => m.default),
  ja: () => import("./ja").then((m) => m.default),
  ko: () => import("./ko").then((m) => m.default),
};

export const defaultTranslations = en;

export const languageNames = {
  en: "English",
  "zh-TW": "香港繁體中文",
  "zh-CN": "简体中文",
  ja: "日本語",
  ko: "한국어",
};

export const uiLanguages = [
  { value: "en", label: "English" },
  { value: "zh-TW", label: "香港繁體中文" },
  { value: "zh-CN", label: "简体中文" },
  { value: "ja", label: "日本語" },
  { value: "ko", label: "한국어" },
];

export const UI_LANGUAGES = uiLanguages.map(({ value }) => value);

export const courseLanguages = [
  { value: "en", label: "English" },
  { value: "zh-TW", label: "香港繁體中文 (Hong Kong Traditional Chinese)" },
  { value: "zh-CN", label: "简体中文 (Simplified Chinese)" },
  { value: "ja", label: "日本語 (Japanese)" },
  { value: "ko", label: "한국어 (Korean)" },
];

export const courseLanguageShortNames = {
  en: "EN",
  "zh-TW": "繁中",
  "zh-CN": "简中",
  ja: "日本",
  ko: "한국",
};

export const getCourseLanguageDisplay = (langCode, { short = false } = {}) => {
  const labels = short ? courseLanguageShortNames : languageNames;
  return labels[langCode] || langCode;
};

export default defaultTranslations;
