import en from "./en";
import zhTW from "./zh-TW";
import zhCN from "./zh-CN";
import ja from "./ja";
import ko from "./ko";

export const translations = {
  en,
  "zh-TW": zhTW,
  "zh-CN": zhCN,
  ja,
  ko,
};

export const languageNames = {
  en: "English",
  "zh-TW": "繁體中文",
  "zh-CN": "简体中文",
  ja: "日本語",
  ko: "한국어",
};

export const uiLanguages = [
  { value: "en", label: "English" },
  { value: "zh-TW", label: "繁體中文" },
  { value: "zh-CN", label: "简体中文" },
  { value: "ja", label: "日本語" },
  { value: "ko", label: "한국어" },
];

export const UI_LANGUAGES = uiLanguages.map(({ value }) => value);

export const courseLanguages = [
  { value: "en", label: "English" },
  { value: "zh-TW", label: "繁體中文 (Traditional Chinese)" },
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

export default translations;
