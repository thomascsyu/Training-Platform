import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Loader2, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { uploadCertificateBackground, formatError, API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

const ACCEPTED_TYPES = "image/jpeg,image/png,.jpg,.jpeg,.png";

export const CertificateBackgroundUpload = ({
  value,
  onChange,
  disabled = false,
  requireLandscape = false,
  previewAspectClass = "aspect-[11/8.5]",
  testId = "certificate-background-upload",
}) => {
  const { t } = useLanguage();
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
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

  const absoluteUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http") || url.startsWith("blob:")) return url;
    const base = API.defaults?.baseURL || "";
    return `${base}${url}`;
  };

  const processFile = async (file) => {
    if (!file) return;
    const isAllowedType =
      file.type === "image/jpeg" ||
      file.type === "image/png" ||
      /\.(jpe?g|png)$/i.test(file.name);
    if (!isAllowedType) {
      toast.error(t("certificateBuilder.invalidImageType"));
      return;
    }

    if (requireLandscape) {
      const isLandscape = await new Promise((resolve) => {
        const img = new Image();
        const objectUrl = URL.createObjectURL(file);
        img.onload = () => {
          URL.revokeObjectURL(objectUrl);
          resolve(img.naturalWidth > img.naturalHeight);
        };
        img.onerror = () => {
          URL.revokeObjectURL(objectUrl);
          resolve(false);
        };
        img.src = objectUrl;
      });
      if (!isLandscape) {
        toast.error(t("certificateTemplates.landscapeBackgroundRequired"));
        return;
      }
    }

    clearLocalPreview();
    const objectUrl = URL.createObjectURL(file);
    localPreviewRef.current = objectUrl;
    setLocalPreview(objectUrl);

    setUploading(true);
    try {
      const { url } = await uploadCertificateBackground(file);
      onChange(url);
      toast.success(t("certificateBuilder.backgroundUploaded"));
      clearLocalPreview();
    } catch (error) {
      clearLocalPreview();
      toast.error(formatError(error));
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    await processFile(file);
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setDragOver(false);
    if (disabled || uploading) return;
    const file = event.dataTransfer.files?.[0];
    await processFile(file);
  };

  const handleRemove = () => {
    clearLocalPreview();
    onChange(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const previewSrc = absoluteUrl(value) || localPreview;

  return (
    <div className="space-y-2" data-testid={testId}>
      <Label>{t("certificateBuilder.backgroundImage")}</Label>
      <div
        className={`border border-dashed rounded-sm p-4 transition-colors ${
          dragOver ? "border-[#002FA7] bg-blue-50" : "border-slate-300 bg-slate-50"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled && !uploading) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        data-testid={`${testId}-dropzone`}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className={`w-full sm:w-48 bg-white border border-slate-200 rounded-sm overflow-hidden flex items-center justify-center shrink-0 ${previewAspectClass}`}>
            {previewSrc ? (
              <img
                src={previewSrc}
                alt={t("certificateBuilder.backgroundImage")}
                className="w-full h-full object-cover"
                data-testid={`${testId}-preview`}
              />
            ) : (
              <Upload className="w-8 h-8 text-slate-300" />
            )}
          </div>
          <div className="flex-1 space-y-2">
            <p className="text-sm text-slate-600">{t("certificateBuilder.backgroundHint")}</p>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_TYPES}
              onChange={handleFileChange}
              disabled={disabled || uploading}
              className="block w-full text-sm text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-sm file:border-0 file:bg-[#002FA7] file:text-white file:cursor-pointer cursor-pointer"
              data-testid={`${testId}-input`}
            />
            {previewSrc && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleRemove}
                disabled={disabled || uploading}
                className="rounded-sm"
                data-testid={`${testId}-remove`}
              >
                <X className="w-4 h-4 mr-2" />
                {t("certificateBuilder.removeBackground")}
              </Button>
            )}
            {uploading && (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                {t("certificateBuilder.uploadingBackground")}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
