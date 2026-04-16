"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { getUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { useToast } from "@/components/ui/use-toast";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { useMounted } from "@/lib/use-mounted";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface HomeworkItem {
  id: number;
  lesson_id: number;
}

interface Lesson {
  id: number;
  title: string;
  date: string;
}

interface Student {
  id: number;
  full_name: string;
  phone: string;
}

export default function MyGroupDetailPage() {
  const params = useParams();
  const groupId = Number(params.id);
  const qc = useQueryClient();
  const { addToast } = useToast();
  const mounted = useMounted();
  const user = typeof window !== "undefined" ? getUser() : null;
  const canCreateLesson = user?.role === "TEACHER" || user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";
  const isStudent = user?.role === "STUDENT";

  const [tab, setTab] = useState<"students" | "lessons">("lessons");
  const [openLesson, setOpenLesson] = useState(false);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonDate, setLessonDate] = useState("");
  const [lessonDesc, setLessonDesc] = useState("");

  const { data: group } = useQuery({
    queryKey: ["group", groupId],
    queryFn: async () => (await api.get(`/groups/${groupId}`)).data.data,
  });

  const { data: lessons } = useQuery({
    queryKey: ["lessons", groupId],
    queryFn: async () => (await api.get(`/lessons?group_id=${groupId}`)).data.data,
  });

  const { data: students } = useQuery({
    queryKey: ["group-students", groupId],
    enabled: mounted && !isStudent,
    queryFn: async () => (await api.get(`/groups/${groupId}/students`)).data.data,
  });

  const { data: homework } = useQuery({
    queryKey: ["homework", groupId],
    queryFn: async () => (await api.get(`/homework?group_id=${groupId}`)).data.data,
  });

  const homeworkIds = homework?.items?.map((h: HomeworkItem) => h.id).join(",") || "";

  const { data: homeworkStatuses } = useQuery({
    queryKey: ["homework-status", homeworkIds],
    enabled: mounted && isStudent && !!homeworkIds,
    queryFn: async () => {
      const pairs = await Promise.all(
        homework.items.map(async (h: HomeworkItem) => {
          const res = await api.get(`/homework/${h.id}/my`);
          return [h.id, res.data.data.status] as [number, string];
        })
      );
      return Object.fromEntries(pairs) as Record<number, string>;
    },
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
      qc.invalidateQueries({ queryKey: ["lessons", groupId] });
      setOpenLesson(false);
      addToast({ title: "Dars yaratildi", description: "Yangi dars guruhga qo‘shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yaratilmadi." });
    },
  });

  if (!mounted) return null;

  const computeLessonStatus = (lessonId: number): { label: string; tone: string } => {
    const lessonHomeworks = homework?.items?.filter((h: HomeworkItem) => h.lesson_id === lessonId) || [];
    if (lessonHomeworks.length === 0) return { label: "Uyga vazifa yo‘q", tone: "bg-slate-100 text-slate-700" };

    if (!isStudent) {
      return { label: "Uyga vazifa bor", tone: "bg-emerald-50 text-emerald-700" };
    }

    const statuses = lessonHomeworks.map((h: HomeworkItem) => homeworkStatuses?.[h.id] || "NOT_SUBMITTED");
  if (statuses.some((s: string) => s === "REVIEWED" || s === "ACCEPTED")) {
    return { label: "Tekshirildi", tone: "bg-emerald-100 text-emerald-800" };
  }
  if (statuses.some((s: string) => s !== "NOT_SUBMITTED")) {
    return { label: "Bajarilgan", tone: "bg-amber-100 text-amber-800" };
  }
  return { label: "Yangi", tone: "bg-slate-100 text-slate-700" };
};

  return (
    <div className="space-y-4">
      <PageHeader title={group?.name || "Guruh"} description={`Jadval: ${group?.schedule_time || "-"}`} />

      {!isStudent && (
        <div className="card p-4 flex items-center justify-between">
          <div className="text-sm text-emerald-700">Guruh boshqaruvi</div>
          <div className="flex gap-2">
            <Button variant={tab === "students" ? "default" : "outline"} onClick={() => setTab("students")}>
              O‘quvchilar
            </Button>
            <Button variant={tab === "lessons" ? "default" : "outline"} onClick={() => setTab("lessons")}>
              Darslar
            </Button>
          </div>
        </div>
      )}

      {isStudent && (
        <div className="card p-4 text-sm text-emerald-700">
          Darslar ro‘yxati va uyga vazifa holatini ko‘ring.
        </div>
      )}

      {(!isStudent && tab === "students") && (
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
      )}

      {(isStudent || tab === "lessons") && (
        <div className="space-y-4">
          {canCreateLesson && (
            <div className="card p-4 flex items-center justify-between">
              <div className="text-sm text-emerald-700">Yangi dars yaratish</div>
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
                          addToast({ title: "To’ldiring", description: "Dars mavzusi va sanani kiriting." });
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
            </div>
          )}

          <div className="space-y-2">
            {lessons?.items?.map((l: Lesson) => {
              const status = computeLessonStatus(l.id);
              return (
                <Link key={l.id} href={`/lessons/${l.id}`} className="card p-4 block hover:shadow-md transition">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold text-emerald-900">{l.title}</div>
                      <div className="text-sm text-emerald-700">{l.date}</div>
                    </div>
                    <Badge className={status.tone}>{status.label}</Badge>
                  </div>
                </Link>
              );
            })}
            {lessons?.items?.length === 0 && (
              <div className="card p-6 text-center text-sm text-emerald-700">Hozircha darslar yo‘q.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
