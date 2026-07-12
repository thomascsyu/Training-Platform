import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle, Loader2, X } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

export const PaymentSuccessPage = () => {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("checking");
  const sessionId = searchParams.get("session_id");

  const pollPaymentStatus = useCallback(async (attempts = 0) => {
    if (attempts >= 5) {
      setStatus("timeout");
      return;
    }

    try {
      const { data } = await API.get(`/payments/status/${sessionId}`);
      if (data.payment_status === "paid") {
        setStatus("success");
      } else {
        setTimeout(() => pollPaymentStatus(attempts + 1), 2000);
      }
    } catch (e) {
      setStatus("error");
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    }
  }, [sessionId, pollPaymentStatus]);

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6" data-testid="payment-success-page">
      <Card className="w-full max-w-md card-swiss card-indexed animate-enter">
        <CardContent className="p-8 text-center">
          {status === "checking" && (
            <>
              <Loader2 className="w-12 h-12 animate-spin text-[#002FA7] mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">{t("payment.processing")}</h2>
              <p className="text-slate-600">{t("payment.pleaseWait")}</p>
            </>
          )}
          {status === "success" && (
            <>
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">{t("payment.successful")}</h2>
              <p className="text-slate-600 mb-6">{t("payment.enrolledInCourse")}</p>
              <Button 
                onClick={() => navigate("/my-courses")}
                className="btn-primary"
                data-testid="go-to-courses-btn"
              >
                {t("payment.goToCourses")}
              </Button>
            </>
          )}
          {(status === "error" || status === "timeout") && (
            <>
              <X className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">{t("payment.somethingWrong")}</h2>
              <p className="text-slate-600 mb-6">{t("payment.contactSupport")}</p>
              <Button 
                onClick={() => navigate("/dashboard")}
                variant="outline"
                className="rounded-sm"
              >
                {t("quiz.backToDashboard")}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

