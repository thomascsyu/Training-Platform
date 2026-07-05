import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ImagePlus, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { uploadThumbnail, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { CourseThumbnail } from "@/components/CourseThumbnail";

const ACCEPTED_TYPES = "image/jpeg,image/png,.jpg,.jpeg,.png";

export const ThumbnailUpload = ({
  value,
  onChange,
  testId = "course-thumbnail-upload",
}) => {
  const { t } = useLanguage();
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [localPreview, setLocalPreview] = useState(null);
  const localPreviewRef = useRef(null);

  const clearLocalPreview = () => {
    if (localPreviewRef.current) {
      URL.revokeObjectURL(localPreviewRef.current);
      localPreviewRef.current = null;
    }
    setLocalPreview(null);
  };

  useEffect(() => () => clearLocalPreview(), []);

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    const isAllowedType =
      file.type === "image/jpeg" ||
      file.type === "image/png" ||
      /\.(jpe?g|png)$/i.test(file.name);
    if (!isAllowedType) {
      toast.error(t("courses.invalidImageType"));
      return;
    }

    clearLocalPreview();
    const objectUrl = URL.createObjectURL(file);
    localPreviewRef.current = objectUrl;
    setLocalPreview(objectUrl);

    setUploading(true);
    try {
      const { url } = await uploadThumbnail(file);
      onChange(url);
      toast.success(t("courses.thumbnailUploaded"));
    } catch (error) {
      clearLocalPreview();
      toast.error(formatError(error));
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = () => {
    clearLocalPreview();
    onChange("");
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handlePreviewLoad = (loadedSrc) => {
    if (loadedSrc === value) {
      clearLocalPreview();
    }
  };

  const previewSrc = value || localPreview;

  return (
    <div className="space-y-2" data-testid={testId}>
      <Label>{t("courses.uploadThumbnail")}</Label>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="w-full sm:w-40 h-24 bg-slate-100 border border-slate-200 rounded-sm overflow-hidden flex items-center justify-center shrink-0">
          {previewSrc ? (
            <CourseThumbnail
              src={value || localPreview}
              fallbackSrc={localPreview && value ? localPreview : undefined}
              alt={t("courses.uploadThumbnail")}
              fallbackIcon={ImagePlus}
              fallbackIconClassName="w-8 h-8 text-slate-300"
              testId={`${testId}-preview`}
              onLoad={handlePreviewLoad}
            />
          ) : (
            <ImagePlus className="w-8 h-8 text-slate-300" />
          )}
        </div>
        <div className="flex-1 space-y-2">
          <Input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            onChange={handleFileChange}
            disabled={uploading}
            className="rounded-sm cursor-pointer"
            data-testid={`${testId}-input`}
          />
          <p className="text-xs text-slate-500">{t("courses.thumbnailHint")}</p>
          {previewSrc && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRemove}
              disabled={uploading}
              className="rounded-sm"
              data-testid={`${testId}-remove`}
            >
              <X className="w-4 h-4 mr-2" />
              {t("courses.removeThumbnail")}
            </Button>
          )}
          {uploading && (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              {t("courses.uploadingThumbnail")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
