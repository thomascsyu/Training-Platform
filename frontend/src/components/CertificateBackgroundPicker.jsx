import { CERTIFICATE_BACKGROUNDS } from "@/lib/certificateBackgrounds";

const swatchStyle = (id, primary, secondary) => {
  switch (id) {
    case "modern":
      return {
        border: `1px solid ${primary}`,
        boxShadow: `inset 0 0 0 6px ${secondary}22`,
      };
    case "elegant":
      return {
        border: `1px dashed ${secondary}`,
        outline: `2px solid ${primary}`,
        outlineOffset: "2px",
      };
    case "minimal":
      return {
        borderBottom: `2px solid ${primary}`,
      };
    case "bold":
      return {
        border: `4px solid ${primary}`,
        background: `${secondary}14`,
      };
    default:
      return {
        border: `3px double ${primary}`,
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
  return (
    <div className="grid grid-cols-5 gap-2">
      {CERTIFICATE_BACKGROUNDS.map((bg) => (
        <button
          key={bg.id}
          type="button"
          onClick={() => onChange(bg.id)}
          data-testid={`${testIdPrefix}-${bg.id}`}
          className={`rounded-sm border p-1.5 text-center transition-colors ${
            value === bg.id
              ? "border-[#002FA7] ring-1 ring-[#002FA7]"
              : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <div
            className="h-12 w-full rounded-sm bg-white"
            style={swatchStyle(bg.id, primaryColor, secondaryColor)}
          />
          <span className="mt-1 block text-[10px] leading-tight text-slate-600">
            {bg.label}
          </span>
        </button>
      ))}
    </div>
  );
};
