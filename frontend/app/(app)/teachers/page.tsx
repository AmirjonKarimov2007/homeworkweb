"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { roleLabel } from "@/lib/labels";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";

export default function TeachersPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [open, setOpen] = useState(false);
  const [groupIds, setGroupIds] = useState<number[]>([]);

  const { data } = useQuery({
    queryKey: ["teachers"],
    queryFn: async () => (await api.get("/teachers")).data.data,
  });

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: async () => (await api.get("/groups")).data.data,
  });

  const create = useMutation({
    mutationFn: async () =>
      api.post("/teachers", { full_name: fullName, phone, password: "Teacher123!@#", group_ids: groupIds }),
    onSuccess: () => {
      setFullName("");
      setPhone("");
      setGroupIds([]);
      qc.invalidateQueries({ queryKey: ["teachers"] });
      setOpen(false);
      addToast({ title: "O‘qituvchi qo‘shildi", description: "Yangi o‘qituvchi yaratildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "O‘qituvchi qo‘shilmadi." });
    },
  });

  const removeTeacher = useMutation({
    mutationFn: async (teacherId: number) => api.delete(`/teachers/${teacherId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teachers"] });
      addToast({ title: "Ochirildi", description: "O‘qituvchi o‘chirildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "O‘qituvchi o‘chirilmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="O‘qituvchilar" description="O‘qituvchilar ro‘yxati va qo‘shish." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">O‘qituvchilar ro‘yxatini to‘ldiring</div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>O‘qituvchi qo‘shish</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Yangi o‘qituvchi</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Input placeholder="Ism va familiya" value={fullName} onChange={(e) => setFullName(e.target.value)} />
              <Input placeholder="Telefon" value={phone} onChange={(e) => setPhone(e.target.value)} />
              <div>
                <div className="text-sm font-medium text-emerald-900 mb-2">Guruhlar (kamida bittasi kerak)</div>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                  {groups?.items?.map((g: any) => (
                    <label key={g.id} className="flex items-center gap-2 rounded-xl border border-emerald-100 bg-white px-3 py-2 text-sm">
                      <input
                        type="checkbox"
                        checked={groupIds.includes(g.id)}
                        onChange={() =>
                          setGroupIds((prev) =>
                            prev.includes(g.id) ? prev.filter((x) => x !== g.id) : [...prev, g.id]
                          )
                        }
                        className="accent-emerald-600"
                      />
                      <span>{g.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <Button
                onClick={() => {
                  if (!fullName || !phone) {
                    addToast({ title: "Ma’lumot yetarli emas", description: "Ism va telefonni kiriting." });
                    return;
                  }
                  if (groupIds.length === 0) {
                    addToast({ title: "Guruh tanlang", description: "Kamida bitta guruhni belgilang." });
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
            <TableHead>Ism</TableHead>
            <TableHead>Telefon</TableHead>
            <TableHead>Rol</TableHead>
            <TableHead>Amal</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items?.map((t: any) => (
            <TableRow key={t.id}>
              <TableCell>{t.full_name}</TableCell>
              <TableCell>{t.phone}</TableCell>
              <TableCell>{roleLabel[t.role] || t.role}</TableCell>
              <TableCell>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => {
                    if (confirm("O‘qituvchini o‘chirmoqchimisiz?")) {
                      removeTeacher.mutate(t.id);
                    }
                  }}
                >
                  O‘chirish
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
