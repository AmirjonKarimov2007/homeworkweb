"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";

export default function LessonsPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [title, setTitle] = useState("");
  const [groupId, setGroupId] = useState("");
  const [date, setDate] = useState("");
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["lessons"],
    queryFn: async () => (await api.get("/lessons")).data.data,
  });

  const create = useMutation({
    mutationFn: async () => api.post("/lessons", { title, group_id: Number(groupId), date }),
    onSuccess: () => {
      setTitle("");
      setGroupId("");
      setDate("");
      qc.invalidateQueries({ queryKey: ["lessons"] });
      setOpen(false);
      addToast({ title: "Dars yaratildi", description: "Yangi dars ro‘yxatga qo‘shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yaratilmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Darslar" description="Darslar ro‘yxati va qo‘shish." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">Darslarni qo‘shish va boshqarish</div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Dars qo‘shish</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Yangi dars</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-1 gap-2">
              <Input placeholder="Sarlavha" value={title} onChange={(e) => setTitle(e.target.value)} />
              <Input placeholder="Guruh ID" value={groupId} onChange={(e) => setGroupId(e.target.value)} />
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
              <Button
                onClick={() => {
                  if (!title || !groupId || !date) {
                    addToast({ title: "To‘ldiring", description: "Barcha maydonlarni kiriting." });
                    return;
                  }
                  create.mutate();
                }}
              >
                Saqlash
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Sarlavha</TableHead>
            <TableHead>Sana</TableHead>
            <TableHead>Guruh</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items?.map((l: any) => (
            <TableRow key={l.id}>
              <TableCell>{l.title}</TableCell>
              <TableCell>{l.date}</TableCell>
              <TableCell>{l.group_id}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
