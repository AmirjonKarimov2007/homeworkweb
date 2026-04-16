"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader } from "@/components/page-header";

export default function AuditLogsPage() {
  const { data } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: async () => (await api.get("/audit-logs")).data.data,
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Audit log" description="Muhim harakatlar tarixi." />
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Amal</TableHead>
            <TableHead>Entity</TableHead>
            <TableHead>Foydalanuvchi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.map((l: any) => (
            <TableRow key={l.id}>
              <TableCell>{l.action}</TableCell>
              <TableCell>{l.entity_type} #{l.entity_id}</TableCell>
              <TableCell>{l.user_id}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
