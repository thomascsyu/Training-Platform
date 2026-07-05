import { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";
import { resolveUploadUrl } from "@/lib/resolveApiBaseUrl";

const resolveImageSrc = (url) => {
  const trimmed = (url || "").trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("blob:")) return trimmed;
  return resolveUploadUrl(trimmed);
};

export const CourseThumbnail = ({
  src,
  fallbackSrc,
  alt = "",
  className = "w-full h-full object-cover",
  fallbackClassName = "w-full h-full flex items-center justify-center bg-slate-100",
  fallbackIcon: FallbackIcon = BookOpen,
  fallbackIconClassName = "w-6 h-6 text-slate-300",
  testId,
  onLoad,
}) => {
  const [useFallbackSrc, setUseFallbackSrc] = useState(false);
  const [failed, setFailed] = useState(false);
  const activeSrc = useFallbackSrc ? fallbackSrc : src;
  const resolvedSrc = resolveImageSrc(activeSrc);

  useEffect(() => {
    setUseFallbackSrc(false);
    setFailed(false);
  }, [src, fallbackSrc]);

  if (!resolvedSrc || failed) {
    return (
      <div className={fallbackClassName} data-testid={testId ? `${testId}-fallback` : undefined}>
        <FallbackIcon className={fallbackIconClassName} />
      </div>
    );
  }

  return (
    <img
      src={resolvedSrc}
      alt={alt}
      className={className}
      onLoad={() => {
        onLoad?.(activeSrc);
      }}
      onError={() => {
        if (fallbackSrc && !useFallbackSrc) {
          setUseFallbackSrc(true);
          return;
        }
        setFailed(true);
      }}
      data-testid={testId}
    />
  );
};
