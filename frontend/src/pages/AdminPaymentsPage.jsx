import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CreditCard, DollarSign, CheckCircle, Clock } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import StatCard from "@/components/enhanced/StatCard";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";

const STATUS_OPTIONS = ["all", "paid", "pending"];

const statusBadgeVariant = (status) => {
  switch (status) {
    case "paid":
      return "default";
    case "pending":
      return "secondary";
    default:
      return "outline";
  }
};

export const AdminPaymentsPage = () => {
  const { t } = useLanguage();
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryRes, txRes] = await Promise.all([
        API.get("/payments/summary"),
        API.get("/payments/transactions", {
          params: statusFilter !== "all" ? { status: statusFilter } : {},
        }),
      ]);
      setSummary(summaryRes.data);
      setTransactions(txRes.data);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatCurrency = (value, currency = "usd") => {
    const num = Number(value || 0);
    const code = (currency || "usd").toUpperCase();
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: code,
      }).format(num);
    } catch {
      return `${code} ${num.toFixed(2)}`;
    }
  };

  const formatDate = (value) => {
    if (!value) return "—";
    return new Date(value).toLocaleString();
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-payments-page">
        <PageHeader
          overline="Admin"
          title={t("adminPayments.title")}
          description={t("adminPayments.description")}
        >
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-48 rounded-sm" data-testid="status-filter-select">
              <SelectValue placeholder={t("adminPayments.filterByStatus")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("adminPayments.allStatuses")}</SelectItem>
              <SelectItem value="paid">{t("adminPayments.statusPaid")}</SelectItem>
              <SelectItem value="pending">{t("adminPayments.statusPending")}</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            className="rounded-sm"
            onClick={fetchData}
            data-testid="refresh-payments-btn"
          >
            {t("common.refresh")}
          </Button>
        </PageHeader>

        {summary && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              label={t("adminPayments.totalRevenue")}
              value={formatCurrency(summary.total_revenue)}
              icon={DollarSign}
              testId="payment-revenue-stat"
            />
            <StatCard
              label={t("adminPayments.paid")}
              value={summary.paid_count}
              icon={CheckCircle}
              testId="payment-paid-stat"
            />
            <StatCard
              label={t("adminPayments.pending")}
              value={summary.pending_count}
              icon={Clock}
              testId="payment-pending-stat"
            />
            <StatCard
              label={t("adminPayments.totalTransactions")}
              value={summary.total_transactions}
              icon={CreditCard}
              testId="payment-total-stat"
            />
          </div>
        )}

        {loading ? (
          <TableSkeleton rows={6} cols={5} />
        ) : transactions.length === 0 ? (
          <EmptyState
            icon={CreditCard}
            title={t("adminPayments.noTransactions")}
            description={t("adminPayments.noTransactionsHint")}
            testId="payments-empty"
          />
        ) : (
          <Card className="card-swiss overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left p-4 font-medium text-slate-600">{t("adminPayments.sessionId")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("adminPayments.course")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("adminPayments.student")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("adminPayments.amount")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("adminPayments.status")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("adminPayments.date")}</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="border-b border-slate-100" data-testid={`transaction-row-${tx.id}`}>
                      <td className="p-4 font-mono text-xs text-slate-600">{tx.session_id}</td>
                      <td className="p-4 text-slate-700">{tx.course_title}</td>
                      <td className="p-4 text-slate-700">{tx.user_name}</td>
                      <td className="p-4 font-medium text-slate-900">
                        {formatCurrency(tx.amount, tx.currency)}
                      </td>
                      <td className="p-4">
                        <Badge variant={statusBadgeVariant(tx.payment_status)} className="rounded-sm capitalize">
                          {tx.payment_status}
                        </Badge>
                      </td>
                      <td className="p-4 text-slate-500 text-sm">{formatDate(tx.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};
