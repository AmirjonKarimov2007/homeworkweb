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

export default function HomeworkPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [title, setTitle] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [instructions, setInstructions] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["homework"],
    queryFn: async () => (await api.get("/homework")).data.data,
  });

  const create = useMutation({
    mutationFn: async () =>
      api.post("/homework", {
        title,
        lesson_id: Number(lessonId),
        instructions: instructions || null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
      }),
    onSuccess: () => {
      setTitle("");
      setLessonId("");
      setInstructions("");
      setDueDate("");
      qc.invalidateQueries({ queryKey: ["homework"] });
      setOpen(false);
      addToast({ title: "Uyga vazifa saqlandi", description: "Uyga vazifa yaratildi/yangi­landi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Uyga vazifa saqlanmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Uy vazifalar" description="Uy vazifa ro‘yxati va qo‘shish." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">Uyga vazifalarni boshqarish</div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Uyga vazifa qo‘shish</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Uyga vazifa</DialogTitle>
            </DialogHeader>
            <div className="space-y-2">
              <Input placeholder="Sarlavha" value={title} onChange={(e) => setTitle(e.target.value)} />
              <Input placeholder="Dars ID" value={lessonId} onChange={(e) => setLessonId(e.target.value)} />
              <Input placeholder="Ko‘rsatma (matn)" value={instructions} onChange={(e) => setInstructions(e.target.value)} />
              <Input type="datetime-local" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
              <Button
                onClick={() => {
                  if (!title || !lessonId) {
                    addToast({ title: "To‘ldiring", description: "Sarlavha va dars ID kerak." });
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
            <TableHead>Dars</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items?.map((h: any) => (
            <TableRow key={h.id}>
              <TableCell>{h.title}</TableCell>
              <TableCell>{h.lesson_id}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
