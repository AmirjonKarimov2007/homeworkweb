"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/ui/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { formatMoney, parseMoney } from "@/lib/format";

export default function CoursesPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [name, setName] = useState("");
  const [monthlyFee, setMonthlyFee] = useState("");
  const [durationMonths, setDurationMonths] = useState("");
  const [description, setDescription] = useState("");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const { data } = useQuery({
    queryKey: ["courses"],
    queryFn: async () => {
      const res = await api.get("/courses", { params: { active: true } });
      return res.data?.data || { items: [] };
    },
  });

  const createMutation = useMutation({
    mutationFn: async () =>
      api.post("/courses", {
        name,
        monthly_fee: Number(monthlyFee),
        duration_months: durationMonths ? Number(durationMonths) : null,
        description: description || null,
      }),
    onSuccess: () => {
      setName("");
      setMonthlyFee("");
      setDurationMonths("");
      setDescription("");
      setEditingId(null);
      qc.invalidateQueries({ queryKey: ["courses"] });
      setOpen(false);
      addToast({ title: "Kurs yaratildi", description: "Kurs muvaffaqiyatli qoshildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Kurs yaratilmadi." });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (id: number) =>
      api.patch(`/courses/${id}`, {
        name,
        monthly_fee: Number(monthlyFee),
        duration_months: durationMonths ? Number(durationMonths) : null,
        description: description || null,
      }),
    onSuccess: () => {
      setName("");
      setMonthlyFee("");
      setDurationMonths("");
      setDescription("");
      setEditingId(null);
      qc.invalidateQueries({ queryKey: ["courses"] });
      setOpen(false);
      addToast({ title: "Kurs yangilandi", description: "Kurs muvaffaqiyatli yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Kurs yangilanmadi." });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (courseId: number) => api.delete(`/courses/${courseId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["courses"] });
      addToast({ title: "Ochirildi", description: "Kurs o'chirildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Kurs o'chirilmadi." });
    },
  });

  const handleEdit = (course: any) => {
    setName(course.name);
    setMonthlyFee(String(course.monthly_fee));
    setDurationMonths(course.duration_months ? String(course.duration_months) : "");
    setDescription(course.description || "");
    setEditingId(course.id);
    setOpen(true);
  };

  const handleSubmit = () => {
    if (!name) {
      addToast({ title: "Kurs nomini kiriting", description: "Kurs nomi majburiy." });
      return;
    }
    if (!monthlyFee) {
      addToast({ title: "Oylik to'lovni kiriting", description: "Oylik to'lov majburiy." });
      return;
    }
    if (editingId) {
      updateMutation.mutate(editingId);
    } else {
      createMutation.mutate();
    }
  };

  const handleDelete = (id: number) => {
    if (confirm("Kursni o'chirmoqchimisiz?")) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Kurslar" description="Kurslarni boshqarish va oylik to'lovlarini belgilash." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">Yangi kurs yaratish</div>
        <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) { setEditingId(null); setName(""); setMonthlyFee(""); setDurationMonths(""); setDescription(""); } }}>
          <DialogTrigger asChild>
            <Button>Kurs qoshish</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingId ? "Kursni tahrirlash" : "Yangi kurs"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Input placeholder="Kurs nomi" value={name} onChange={(e) => setName(e.target.value)} />
              <Input
                placeholder="Oylik to'lov"
                value={formatMoney(monthlyFee)}
                onChange={(e) => setMonthlyFee(parseMoney(e.target.value))}
              />
              <Input
                type="number"
                placeholder="Davomiylik (oylar)"
                value={durationMonths}
                onChange={(e) => setDurationMonths(e.target.value)}
              />
              <Input
                placeholder="Tavsif (ixtiyoriy)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <Button onClick={handleSubmit} className="w-full">
                {editingId ? "Saqlash" : "Yaratish"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nomi</TableHead>
            <TableHead>Oylik to'lov</TableHead>
            <TableHead>Davomiylik</TableHead>
            <TableHead>Tavsif</TableHead>
            <TableHead>Amal</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items?.map((c: any) => (
            <TableRow key={c.id}>
              <TableCell className="font-medium">{c.name}</TableCell>
              <TableCell>{formatMoney(c.monthly_fee)} so'm</TableCell>
              <TableCell>{c.duration_months ? `${c.duration_months} oy` : "-"}</TableCell>
              <TableCell className="text-sm text-gray-600">{c.description || "-"}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleEdit(c)}>
                    Tahrirlash
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(c.id)}
                  >
                    O'chirish
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
