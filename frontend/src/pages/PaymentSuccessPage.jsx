import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle, Loader2, X } from "lucide-react";
import { API } from "@/lib/api";

const MAX_ATTEMPTS = 10;
const POLL_DELAY_MS = 2500;

export const PaymentSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("checking");
  const [receipt, setReceipt] = useState(null);
  const sessionId = searchParams.get("session_id");

  const pollPaymentStatus = useCallback(async (attempts = 0) => {
    if (attempts >= MAX_ATTEMPTS) {
      setStatus("timeout");
      return;
    }

    try {
      const { data } = await API.get(`/payments/status/${sessionId}`);
      if (data.payment_status === "paid") {
        setReceipt({
          courseId: data.course_id,
          courseTitle: data.course_title,
          amount: data.amount,
          currency: data.currency,
        });
        setStatus("success");
      } else {
        setTimeout(() => pollPaymentStatus(attempts + 1), POLL_DELAY_MS);
      }
    } catch (e) {
      setStatus("error");
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    } else {
      setStatus("error");
    }
  }, [sessionId, pollPaymentStatus]);

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6" data-testid="payment-success-page">
      <Card className="w-full max-w-md card-swiss card-indexed animate-enter">
        <CardContent className="p-8 text-center">
          {status === "checking" && (
            <>
              <Loader2 className="w-12 h-12 animate-spin text-[#002FA7] mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Processing Payment...</h2>
              <p className="text-slate-600">Please wait while we confirm your payment with Stripe.</p>
            </>
          )}
          {status === "success" && (
            <>
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Payment Successful!</h2>
              <p className="text-slate-600 mb-4">You have been enrolled in the course.</p>
              {receipt?.courseTitle && (
                <div className="border border-slate-200 rounded-sm p-4 mb-6 text-left text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-600">Course</span>
                    <span className="font-medium">{receipt.courseTitle}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Amount paid</span>
                    <span className="font-medium tabular-nums">
                      {receipt.amount?.toFixed(2)} {receipt.currency?.toUpperCase()}
                    </span>
                  </div>
                </div>
              )}
              <div className="flex flex-col gap-2">
                {receipt?.courseId && (
                  <Button
                    onClick={() => navigate(`/courses/${receipt.courseId}`)}
                    className="btn-primary"
                    data-testid="go-to-course-btn"
                  >
                    Start Learning
                  </Button>
                )}
                <Button
                  onClick={() => navigate("/my-courses")}
                  variant={receipt?.courseId ? "outline" : undefined}
                  className={receipt?.courseId ? "rounded-sm" : "btn-primary"}
                  data-testid="go-to-courses-btn"
                >
                  Go to My Courses
                </Button>
              </div>
            </>
          )}
          {status === "timeout" && (
            <>
              <Loader2 className="w-16 h-16 text-amber-500 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Still confirming...</h2>
              <p className="text-slate-600 mb-6">
                Your payment may still be processing. This can take a minute — you can check again or view your
                courses, your enrollment will appear once confirmed.
              </p>
              <div className="flex flex-col gap-2">
                <Button onClick={() => { setStatus("checking"); pollPaymentStatus(); }} className="btn-primary" data-testid="retry-status-btn">
                  Check Again
                </Button>
                <Button onClick={() => navigate("/my-courses")} variant="outline" className="rounded-sm">
                  Go to My Courses
                </Button>
              </div>
            </>
          )}
          {status === "error" && (
            <>
              <X className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Something went wrong</h2>
              <p className="text-slate-600 mb-6">Please contact support if the issue persists.</p>
              <Button
                onClick={() => navigate("/dashboard")}
                variant="outline"
                className="rounded-sm"
              >
                Back to Dashboard
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
