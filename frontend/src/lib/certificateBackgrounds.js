export const CERTIFICATE_BACKGROUNDS = [
  { id: "classic", label: "Classic Frame" },
  { id: "modern", label: "Modern Corners" },
  { id: "elegant", label: "Elegant Flourish" },
  { id: "minimal", label: "Minimal" },
  { id: "bold", label: "Bold Ribbon" },
];

export const DEFAULT_CERTIFICATE_BACKGROUND = "classic";

export const backgroundLabel = (t, idOrBg) => {
  const id = typeof idOrBg === "string" ? idOrBg : idOrBg?.id;
  if (!id) return "";
  const bg = CERTIFICATE_BACKGROUNDS.find((b) => b.id === id);
  const translationKey = `certificateBackgrounds.${id}`;
  const translated = t(translationKey);
  return translated !== translationKey ? translated : bg?.label || id;
};
