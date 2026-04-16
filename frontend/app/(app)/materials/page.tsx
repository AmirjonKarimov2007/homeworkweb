"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader } from "@/components/page-header";

export default function MaterialsPage() {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [type, setType] = useState("PDF");
  const [file, setFile] = useState<File | null>(null);

  const { data } = useQuery({
    queryKey: ["materials"],
    queryFn: async () => (await api.get("/materials")).data.data,
  });

  const upload = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("title", title);
      form.append("type", type);
      if (file) form.append("file", file);
      return api.post("/materials", form);
    },
    onSuccess: () => {
      setTitle("");
      setFile(null);
      qc.invalidateQueries({ queryKey: ["materials"] });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Materiallar" description="Fayl va link materiallarni yuklang." />

      <div className="card p-4 grid grid-cols-1 gap-2 md:grid-cols-4">
        <Input placeholder="Sarlavha" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Input placeholder="Turi (PDF/AUDIO/VIDEO/LINK/DOCUMENT)" value={type} onChange={(e) => setType(e.target.value)} />
        <Input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <Button onClick={() => upload.mutate()}>Yuklash</Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nomi</TableHead>
            <TableHead>Turi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.map((m: any) => (
            <TableRow key={m.id}>
              <TableCell>{m.title}</TableCell>
              <TableCell>{m.type}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
