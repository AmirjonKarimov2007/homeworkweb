"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { MetricCard } from "@/components/metric-card";
import { Users, CalendarCheck, ClipboardCheck } from "lucide-react";
import { PageHeader } from "@/components/page-header";

export default function ReportsPage() {
  const { data } = useQuery({
    queryKey: ["summary"],
    queryFn: async () => (await api.get("/reports/summary")).data.data,
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Hisobotlar" description="Asosiy ko‘rsatkichlar." />
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Talabalar" value={data?.total_students ?? "-"} icon={<Users className="h-5 w-5" />} />
        <MetricCard title="Bugungi davomat" value={data?.today_attendance ?? "-"} icon={<CalendarCheck className="h-5 w-5" />} />
        <MetricCard title="Kutilayotgan uy vazifa" value={data?.pending_homework ?? "-"} icon={<ClipboardCheck className="h-5 w-5" />} />
      </div>
    </div>
  );
}
