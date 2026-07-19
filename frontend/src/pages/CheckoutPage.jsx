import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Loader2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PublicSiteHeader } from "@/components/PublicSiteHeader";
import { CourseThumbnail } from "@/components/CourseThumbnail";
import { API, formatError } from "@/lib/api";
import { getCoursePriceDisplay } from "@/lib/coursePricing";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";

export const CheckoutPage = () => {
  const { courseId } = useParams();
  const { user } = useAuth();
  const { lang, t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);

  const fetchCourse = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await API.get(`/courses/${courseId}`, { params: { lang } });
      if (data.is_free || !(data.price > 0)) {
        navigate(`/courses/${courseId}`, { replace: true });
        return;
      }

      const enrollRes = await API.get("/enrollments/my");
      const enrolled = enrollRes.data.find((e) => e.course_id === courseId);
      if (enrolled) {
        toast.info(t("payment.alreadyEnrolled"));
        navigate(`/courses/${courseId}`, { replace: true });
        return;
      }

      setCourse(data);
    } catch (e) {
      toast.error(formatError(e));
      navigate("/courses", { replace: true });
    } finally {
      setLoading(false);
    }
  }, [courseId, lang, navigate, t]);

  useEffect(() => {
    if (!user) {
      navigate(`/login?next=${encodeURIComponent(`/checkout/${courseId}`)}`, { replace: true });
      return;
    }
    fetchCourse();
  }, [user, courseId, fetchCourse, navigate]);

  useEffect(() => {
    if (searchParams.get("payment") === "canceled") {
      toast.info(t("payment.canceled"));
      const next = new URLSearchParams(searchParams);
      next.delete("payment");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams, t]);

  const handlePay = async () => {
    setPaying(true);
    try {
      const { data } = await API.post("/payments/checkout", {
        course_id: courseId,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (e) {
      toast.error(formatError(e));
      setPaying(false);
    }
  };

  if (!user || loading) {
    return (
      <div className="min-h-screen bg-[#F4F5F7]">
        <PublicSiteHeader />
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" data-testid="checkout-loading" />
        </div>
      </div>
    );
  }

  if (!course) return null;

  const pricing = getCoursePriceDisplay(course);
  const priceLabel = pricing.priceLabel;

  return (
    <div className="min-h-screen bg-[#F4F5F7]" data-testid="checkout-page">
      <PublicSiteHeader />
      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        <Button
          variant="ghost"
          className="mb-6 -ml-2 rounded-sm text-slate-600 hover:text-[#002FA7]"
          onClick={() => navigate(`/courses/${courseId}`)}
          data-testid="checkout-back-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("payment.backToCourse")}
        </Button>

        <div className="mb-8">
          <p className="text-sm font-medium text-[#002FA7] mb-1">{t("payment.checkout")}</p>
          <h1 className="font-display text-3xl tracking-tight text-[#0A0B10]">
            {t("payment.completePurchase")}
          </h1>
          <p className="mt-2 text-slate-600">{t("payment.reviewOrder")}</p>
        </div>

        <Card className="card-swiss">
          <CardHeader>
            <CardTitle className="text-lg">{t("payment.orderSummary")}</CardTitle>
            <CardDescription>{t("payment.secureStripe")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4 border border-slate-200 rounded-sm p-4">
              <div className="w-20 h-20 rounded-sm overflow-hidden bg-slate-100 shrink-0">
                <CourseThumbnail
                  src={course.thumbnail_url}
                  alt=""
                  className="w-full h-full object-cover"
                  fallbackClassName="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5"
                  fallbackIconClassName="w-7 h-7 text-[#002FA7]/40"
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate" data-testid="checkout-course-title">
                  {course.title}
                </p>
                <p className="text-sm text-slate-500">{t("payment.fullAccess")}</p>
                {pricing.hasOffer && (
                  <p className="text-xs text-amber-700 mt-1">{t("courses.specialOffer")}</p>
                )}
              </div>
              <div className="text-right" data-testid="checkout-course-price">
                {pricing.hasOffer && (
                  <p className="text-sm text-slate-400 line-through tabular-nums">
                    {pricing.originalPriceLabel}
                  </p>
                )}
                <p className="font-display text-xl tabular-nums">{priceLabel}</p>
              </div>
            </div>

            <Separator />

            <div className="flex justify-between text-sm">
              <span className="text-slate-600">{t("payment.total")}</span>
              <span className="font-display text-lg tabular-nums">{priceLabel}</span>
            </div>

            <div className="flex items-start gap-2 text-xs text-slate-500">
              <ShieldCheck className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
              <span>{t("payment.redirectNotice")}</span>
            </div>

            <div className="flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
              <Button
                variant="outline"
                className="rounded-sm"
                onClick={() => navigate(`/courses/${courseId}`)}
                disabled={paying}
                data-testid="checkout-cancel-btn"
              >
                {t("common.cancel")}
              </Button>
              <Button
                onClick={handlePay}
                className="btn-primary"
                disabled={paying}
                data-testid="checkout-pay-btn"
              >
                {paying ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>{t("payment.payAmount", { amount: priceLabel })}</>
                )}
              </Button>
            </div>

            <p className="text-center text-xs text-slate-400">
              {t("payment.termsHint")}{" "}
              <Link to={`/courses/${courseId}`} className="text-[#002FA7] hover:underline">
                {course.title}
              </Link>
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};
