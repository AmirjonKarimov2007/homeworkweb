"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";

export default function MyGroupsPage() {
  const { data } = useQuery({
    queryKey: ["my-groups"],
    queryFn: async () => (await api.get("/groups/mine")).data.data,
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Mening guruhlarim" description="Biriktirilgan guruhlar ro‘yxati." />
      <div className="space-y-3">
        {data?.map((g: any) => (
          <Link key={g.id} href={`/my-groups/${g.id}`} className="card p-4 block hover:shadow-md transition">
            <div className="font-semibold text-emerald-900">{g.name}</div>
            <div className="text-sm text-emerald-700">{g.schedule_time}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
