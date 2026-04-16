"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/ui/use-toast";
import Link from "next/link";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";

interface Student {
  id: number;
  full_name: string;
  phone: string;
}

interface Lesson {
  id: number;
  title: string;
  date: string;
}

export default function GroupDetailPage() {
  const params = useParams();
  const groupId = Number(params.id);
  const qc = useQueryClient();
  const { addToast } = useToast();
  const mounted = useMounted();
  const user = typeof window !== "undefined" ? getUser() : null;

  const [tab, setTab] = useState<"students" | "lessons">("students");
  const [openLesson, setOpenLesson] = useState(false);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonDate, setLessonDate] = useState("");
  const [lessonDesc, setLessonDesc] = useState("");

  const { data: group } = useQuery({
    queryKey: ["group", groupId],
    queryFn: async () => (await api.get(`/groups/${groupId}`)).data.data,
  });

  const { data: students } = useQuery({
    queryKey: ["group-students", groupId],
    queryFn: async () => (await api.get(`/groups/${groupId}/students`)).data.data,
  });


  const { data: lessons } = useQuery({
    queryKey: ["group-lessons", groupId],
    queryFn: async () => (await api.get(`/lessons?group_id=${groupId}`)).data.data,
  });


  const createLesson = useMutation({
    mutationFn: async () =>
      api.post("/lessons", {
        group_id: groupId,
        title: lessonTitle,
        date: lessonDate,
        description: lessonDesc || null,
        status: "YANGI",
      }),
    onSuccess: () => {
      setLessonTitle("");
      setLessonDate("");
      setLessonDesc("");
      qc.invalidateQueries({ queryKey: ["group-lessons", groupId] });
      setOpenLesson(false);
      addToast({ title: "Dars yaratildi", description: "Yangi dars guruhga qo‘shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yaratilmadi." });
    },
  });

  if (!mounted) return null;

  const canCreateLesson = user?.role === "SUPER_ADMIN" || user?.role === "ADMIN" || user?.role === "TEACHER";

  return (
    <div className="space-y-4">
      <PageHeader title={`Guruh: ${group?.name || ""}`} description="A’zolar va darslar." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">Jadval: {group?.schedule_time || "-"}</div>
        <div className="flex gap-2">
          <Button variant={tab === "students" ? "default" : "outline"} onClick={() => setTab("students")}>
            O‘quvchilar
          </Button>
          <Button variant={tab === "lessons" ? "default" : "outline"} onClick={() => setTab("lessons")}>
            Darslar
          </Button>
        </div>
      </div>

      {tab === "students" && (
        <div className="space-y-4">
          <div className="card p-4 flex items-center justify-between">
            <div className="text-sm text-emerald-700">Guruhdagi o‘quvchilar</div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Talaba</TableHead>
                <TableHead>Telefon</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {students?.map((s: Student) => (
                <TableRow key={s.id}>
                  <TableCell>{s.full_name}</TableCell>
                  <TableCell>{s.phone}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {tab === "lessons" && (
        <div className="space-y-4">
          <div className="card p-4 flex items-center justify-between">
            <div className="text-sm text-emerald-700">Guruh darslari</div>
            {canCreateLesson && (
              <Dialog open={openLesson} onOpenChange={setOpenLesson}>
                <DialogTrigger asChild>
                  <Button>Dars yaratish</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Yangi dars</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-3">
                    <Input placeholder="Dars mavzusi" value={lessonTitle} onChange={(e) => setLessonTitle(e.target.value)} />
                    <Input type="date" value={lessonDate} onChange={(e) => setLessonDate(e.target.value)} />
                    <Input placeholder="Qisqa izoh (ixtiyoriy)" value={lessonDesc} onChange={(e) => setLessonDesc(e.target.value)} />
                    <Button
                      onClick={() => {
                        if (!lessonTitle || !lessonDate) {
                          addToast({ title: "To‘ldiring", description: "Dars mavzusi va sanani kiriting." });
                          return;
                        }
                        createLesson.mutate();
                      }}
                    >
                      Saqlash
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            )}
          </div>

          <div className="space-y-2">
            {lessons?.items?.map((l: Lesson) => (
              <Link key={l.id} href={`/lessons/${l.id}`} className="card p-4 block hover:shadow-md transition">
                <div className="font-semibold text-emerald-900">{l.title}</div>
                <div className="text-sm text-emerald-700">{l.date}</div>
              </Link>
            ))}
            {lessons?.items?.length === 0 && (
              <div className="card p-6 text-center text-sm text-emerald-700">Hozircha darslar yo‘q.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
