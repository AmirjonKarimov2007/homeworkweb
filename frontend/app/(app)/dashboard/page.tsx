"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { MetricCard } from "@/components/metric-card";
import { Card, CardContent } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { Users, UsersRound, Wallet, Bell, BookOpen, GraduationCap } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { useMounted } from "@/lib/use-mounted";
import { getUser } from "@/lib/auth";
import { formatMoneyDisplay } from "@/lib/format";

export default function DashboardPage() {
  const mounted = useMounted();
  const user = mounted ? getUser() : null;
  const isAdmin = user?.role === "SUPER_ADMIN" || user?.role === "ADMIN";
  const isTeacher = user?.role === "TEACHER";
  const isStudent = user?.role === "STUDENT";

  const { data, isLoading } = useQuery({
    queryKey: ["summary"],
    enabled: mounted && isAdmin,
    queryFn: async () => (await api.get("/reports/summary")).data.data,
  });

  const { data: debtDetails } = useQuery({
    queryKey: ["debt-details"],
    enabled: mounted && isAdmin,
    queryFn: async () => {
      const result = await api.get("/payments?status=OVERDUE");
      return result.data.data;
    },
  });

  const { data: myGroups } = useQuery({
    queryKey: ["my-groups"],
    enabled: mounted && (isTeacher || isStudent),
    queryFn: async () => (await api.get("/groups/mine")).data.data,
  });

  const { data: myPayments } = useQuery({
    queryKey: ["payments-mine"],
    enabled: mounted && isStudent,
    queryFn: async () => (await api.get("/payments/mine")).data.data,
  });

  const { data: myStudentsCount } = useQuery({
    queryKey: ["teacher-students-count", myGroups?.length],
    enabled: mounted && isTeacher && (myGroups?.length || 0) > 0,
    queryFn: async () => {
      const results = await Promise.all(
        (myGroups || []).map((g: any) => api.get(`/groups/${g.id}/students`))
      );
      const counts = results.map((r) => r.data.data.length);
      return counts.reduce((a, b) => a + b, 0);
    },
  });

  const { data: myHomeworkCount } = useQuery({
    queryKey: ["student-homework-count", myGroups?.length],
    enabled: mounted && isStudent && (myGroups?.length || 0) > 0,
    queryFn: async () => {
      const results = await Promise.all(
        (myGroups || []).map((g: any) => api.get(`/homework?group_id=${g.id}`))
      );
      const counts = results.map((r) => r.data.data.items.length);
      return counts.reduce((a, b) => a + b, 0);
    },
  });

  const chartData = [
    { name: "1-hafta", value: data?.monthly_income || 0 },
    { name: "2-hafta", value: (data?.monthly_income || 0) * 0.7 },
    { name: "3-hafta", value: (data?.monthly_income || 0) * 0.9 },
    { name: "4-hafta", value: (data?.monthly_income || 0) * 1.1 },
  ];

  const sortedInvoices = (myPayments || []).slice().sort((a: any, b: any) => {
    if (a.billing_year !== b.billing_year) return b.billing_year - a.billing_year;
    return b.billing_month - a.billing_month;
  });
  const currentInvoice = sortedInvoices.find((i: any) => i.status !== "PAID") || sortedInvoices[0];

  const { data: homeworkStats } = useQuery({
    queryKey: ["student-homework-stats", myGroups?.map((g: any) => g.id).join(",")],
    enabled: mounted && isStudent && (myGroups?.length || 0) > 0,
    queryFn: async () => {
      const tasksResp = await Promise.all(
        (myGroups || []).map((g: any) => api.get(`/homework?group_id=${g.id}&size=200`))
      );
      const tasks = tasksResp.flatMap((r) => r.data.data.items || []);
      if (tasks.length === 0) return { submitted: 0, notSubmitted: 0 };

      const statusResp = await Promise.all(
        tasks.map((t: any) => api.get(`/homework/${t.id}/my`))
      );
      let submitted = 0;
      let notSubmitted = 0;
      statusResp.forEach((r) => {
        const status = r.data.data.status;
        if (status && status !== "NOT_SUBMITTED") submitted += 1;
        else notSubmitted += 1;
      });
      return { submitted, notSubmitted };
    },
  });

  if (!mounted) return null;

  return (
    <div className="space-y-6">
      <PageHeader title="Bosh panel" description="Asosiy ko‘rsatkichlar va tezkor holat." />

      {isAdmin && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
            <MetricCard title="Talabalar soni" value={isLoading ? "..." : data?.total_students ?? "-"} icon={<Users className="h-5 w-5" />} />
            <MetricCard title="Faol guruhlar" value={isLoading ? "..." : data?.active_groups ?? "-"} icon={<UsersRound className="h-5 w-5" />} />
            <MetricCard
              title="Qarzdorlar soni"
              value={isLoading ? "..." : data?.debtors_count ?? "-"}
              icon={<Bell className="h-5 w-5" />}
            />
            <MetricCard
              title="Umumiy qarz"
              value={isLoading ? "..." : formatMoneyDisplay(data?.pending_payments)}
              icon={<Wallet className="h-5 w-5" />}
            />
            <MetricCard
              title="Oylik tushum"
              value={isLoading ? "..." : formatMoneyDisplay(data?.monthly_income)}
              icon={<Wallet className="h-5 w-5" />}
            />
          </div>

          <Card className="animate-in fade-in">
            <CardContent>
              <div className="mb-3 text-sm text-emerald-600">Oylik tushum dinamikasi</div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#0f6b46" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {isTeacher && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <MetricCard title="Mening guruhlarim" value={myGroups?.length ?? 0} icon={<UsersRound className="h-5 w-5" />} />
          <MetricCard title="Talabalarim" value={myStudentsCount ?? 0} icon={<GraduationCap className="h-5 w-5" />} />
          <MetricCard title="Bugungi darslar" value="-" icon={<BookOpen className="h-5 w-5" />} />
        </div>
      )}

      {isStudent && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard title="Mening guruhlarim" value={myGroups?.length ?? 0} icon={<UsersRound className="h-5 w-5" />} />
            <MetricCard title="Yuborilgan uy ishi" value={homeworkStats?.submitted ?? 0} icon={<BookOpen className="h-5 w-5" />} />
            <MetricCard title="Yuborilmagan" value={homeworkStats?.notSubmitted ?? 0} icon={<BookOpen className="h-5 w-5" />} />
            <MetricCard
              title="Qarzim"
              value={currentInvoice && currentInvoice.status !== "PAID" ? formatMoneyDisplay(currentInvoice.remaining_amount) : "0"}
              icon={<Bell className="h-5 w-5" />}
            />
          </div>

          <Card className="animate-in fade-in">
            <CardContent>
              <div className="mb-3 text-sm text-emerald-600">Uyga vazifa holati</div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: "Yuborilgan", value: homeworkStats?.submitted ?? 0 },
                        { name: "Yuborilmagan", value: homeworkStats?.notSubmitted ?? 0 },
                      ]}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={4}
                    >
                      <Cell fill="#0f6b46" />
                      <Cell fill="#f97316" />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
