// Selectable certificate background artworks. Keep the keys in sync with the
// backend (`backend/certificate_template.py` -> CERTIFICATE_BACKGROUNDS).
export const CERTIFICATE_BACKGROUNDS = [
  "plain",
  "geometric",
  "waves",
  "guilloche",
  "corners",
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
