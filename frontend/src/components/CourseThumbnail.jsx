import { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";
import { resolveUploadUrl } from "@/lib/resolveApiBaseUrl";

export const CourseThumbnail = ({
  src,
  alt = "",
  className = "w-full h-full object-cover",
  fallbackClassName = "w-full h-full flex items-center justify-center bg-slate-100",
  fallbackIcon: FallbackIcon = BookOpen,
  fallbackIconClassName = "w-6 h-6 text-slate-300",
  testId,
}) => {
  const [failed, setFailed] = useState(false);
  const resolvedSrc = resolveUploadUrl(src);

  useEffect(() => {
    setFailed(false);
  }, [src]);

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
      onError={() => setFailed(true)}
      data-testid={testId}
    />
  );
};
