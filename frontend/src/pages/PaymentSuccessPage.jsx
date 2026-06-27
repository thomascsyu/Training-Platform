import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle, Loader2, X } from "lucide-react";
import { API } from "@/lib/api";

export const PaymentSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("checking");
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    }
  }, [sessionId]);

  const pollPaymentStatus = async (attempts = 0) => {
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
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6" data-testid="payment-success-page">
      <Card className="w-full max-w-md bg-white border border-slate-200 rounded-sm">
        <CardContent className="p-8 text-center">
          {status === "checking" && (
            <>
              <Loader2 className="w-12 h-12 animate-spin text-[#002FA7] mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Processing Payment...</h2>
              <p className="text-slate-600">Please wait while we confirm your payment.</p>
            </>
          )}
          {status === "success" && (
            <>
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Payment Successful!</h2>
              <p className="text-slate-600 mb-6">You have been enrolled in the course.</p>
              <Button 
                onClick={() => navigate("/my-courses")}
                className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="go-to-courses-btn"
              >
                Go to My Courses
              </Button>
            </>
          )}
          {(status === "error" || status === "timeout") && (
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

