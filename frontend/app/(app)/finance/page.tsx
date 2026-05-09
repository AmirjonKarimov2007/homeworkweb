"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { MetricCard } from "@/components/metric-card";
import { Wallet, Bell, AlertTriangle } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { formatMoneyDisplay } from "@/lib/format";

export default function FinancePage() {
  const { data } = useQuery({
    queryKey: ["summary"],
    queryFn: async () => (await api.get("/reports/summary")).data.data,
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Moliya" description="To‘lovlar va tushumlar holati." />
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Oylik tushum" value={formatMoneyDisplay(data?.monthly_income)} icon={<Wallet className="h-5 w-5" />} />
        <MetricCard title="Kutilayotgan to‘lov" value={data?.pending_payments ?? "-"} icon={<Bell className="h-5 w-5" />} />
        <MetricCard title="Qarzdorlar" value={data?.debtors_count ?? "-"} icon={<AlertTriangle className="h-5 w-5" />} />
      </div>
    </div>
  );
}
