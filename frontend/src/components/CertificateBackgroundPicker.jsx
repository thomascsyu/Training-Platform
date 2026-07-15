import { CERTIFICATE_BACKGROUNDS, backgroundLabel } from "@/lib/certificateBackgrounds";
import { useLanguage } from "@/contexts/LanguageContext";

const swatchStyle = (id, primary, secondary) => {
  switch (id) {
    case "geometric":
      return {
        border: `1px solid ${primary}`,
        backgroundImage: `repeating-linear-gradient(45deg, ${primary}14, ${primary}14 4px, transparent 4px, transparent 8px)`,
      };
    case "waves":
      return {
        border: `1px solid ${secondary}`,
        boxShadow: `inset 0 -8px 0 ${primary}18`,
      };
    case "guilloche":
      return {
        border: `1px dashed ${primary}`,
        boxShadow: `inset 0 0 0 10px ${secondary}10`,
      };
    case "corners":
      return {
        border: `2px solid ${primary}`,
        outline: `1px solid ${secondary}`,
        outlineOffset: "3px",
      };
    default:
      return {
        border: `1px solid ${primary}`,
      };
  }
};

export const CertificateBackgroundPicker = ({
  value,
  onChange,
  primaryColor = "#002FA7",
  secondaryColor = "#0A0B10",
  testIdPrefix = "certificate-background",
}) => {
  const { t } = useLanguage();

  return (
    <div className="grid grid-cols-5 gap-2">
      {CERTIFICATE_BACKGROUNDS.map((key) => (
        <button
          key={key}
          type="button"
          onClick={() => onChange(key)}
          data-testid={`${testIdPrefix}-${key}`}
          className={`rounded-sm border p-1.5 text-center transition-colors ${
            value === key
              ? "border-[#002FA7] ring-1 ring-[#002FA7]"
              : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <div
            className="h-12 w-full rounded-sm bg-white"
            style={swatchStyle(key, primaryColor, secondaryColor)}
          />
          <span className="mt-1 block text-[10px] leading-tight text-slate-600">
            {backgroundLabel(t, key)}
          </span>
        </button>
      ))}
    </div>
  );
};
