// Selectable certificate background artworks. Keep the keys in sync with the
// backend (`backend/certificate_template.py` -> CERTIFICATE_BACKGROUNDS).
export const CERTIFICATE_BACKGROUNDS = [
  "plain",
  "geometric",
  "waves",
  "guilloche",
  "corners",
];

export const DEFAULT_CERTIFICATE_BACKGROUND = "plain";

// Translate a background key to a human label using the i18n `t` helper,
// falling back to the raw key when no translation is available.
export const backgroundLabel = (t, key) => {
  const label = t(`certificateBackgrounds.${key}`);
  return label === `certificateBackgrounds.${key}` ? key : label;
};
