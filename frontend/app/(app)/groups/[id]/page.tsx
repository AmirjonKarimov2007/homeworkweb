"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useState, useEffect } from "react";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/ui/use-toast";
import Link from "next/link";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";
import { ChevronLeft, ChevronRight, Loader2, Edit2, Trash2 } from "lucide-react";

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
  const [editingLesson, setEditingLesson] = useState<any>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [page, setPage] = useState(1);
  const ITEMS_PER_PAGE = 6;

  const { data: group } = useQuery({
    queryKey: ["group", groupId],
    queryFn: async () => (await api.get(`/groups/${groupId}`)).data.data,
  });

  const { data: students } = useQuery({
    queryKey: ["group-students", groupId],
    queryFn: async () => (await api.get(`/groups/${groupId}/students`)).data.data,
  });


  const { data: lessons, isLoading: lessonsLoading } = useQuery({
    queryKey: ["group-lessons", groupId, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        group_id: groupId.toString(),
        page: page.toString(),
        size: ITEMS_PER_PAGE.toString()
      });
      console.log("Fetching group lessons with params:", params.toString());
      const res = await api.get(`/lessons?${params}`);
      return res.data?.data || { items: [], total: 0, page: 1, size: ITEMS_PER_PAGE };
    },
    staleTime: 0,
    refetchOnMount: true,
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
      setPage(1);
      qc.invalidateQueries({ queryKey: ["group-lessons", groupId] });
      setOpenLesson(false);
      addToast({ title: "Dars yaratildi", description: "Yangi dars guruhga qo‘shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yaratilmadi." });
    },
  });

  const deleteLesson = useMutation({
    mutationFn: async (lessonId: number) => {
      return api.delete(`/lessons/${lessonId}`);
    },
    onSuccess: () => {
      setPage(1);
      qc.invalidateQueries({ queryKey: ["group-lessons", groupId] });
      addToast({ title: "Dars o'chirildi", description: "Dars ro'yxatdan olib tashlandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars o'chirilmadi." });
    },
  });

  const updateLesson = useMutation({
    mutationFn: async () => {
      if (!editingLesson?.id) return;
      return api.patch(`/lessons/${editingLesson.id}`, {
        title: editingLesson.title,
        date: editingLesson.date,
        description: editingLesson.description || null,
      });
    },
    onSuccess: () => {
      setEditingLesson(null);
      setEditOpen(false);
      qc.invalidateQueries({ queryKey: ["group-lessons", groupId] });
      addToast({ title: "Dars yangilandi", description: "Dars ma'lumotlari yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yangilanmadi." });
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
            {lessonsLoading && (
              Array.from({ length: 6 }).map((_, index) => (
                <div key={index} className="card p-4 animate-pulse">
                  <div className="h-6 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))
            )}

            {!lessonsLoading && lessons?.items?.map((l: Lesson) => (
              <div key={l.id} className="card p-4 hover:shadow-md transition relative group sm:pr-12">
                <Link href={`/lessons/${l.id}`} className="block">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1 pr-2 sm:pr-0">
                      <div className="min-w-0">
                        <div className="font-semibold text-emerald-900 truncate pr-16 sm:pr-0">{l.title}</div>
                        <div className="text-sm text-emerald-700">{l.date}</div>
                      </div>
                    </div>
                    {canCreateLesson && (
                      <div className="flex gap-1 transition-opacity justify-end">
                        {/* Desktop - only on hover */}
                        <div className="hidden sm:flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              setEditingLesson({
                                id: l.id,
                                title: l.title,
                                date: l.date,
                                description: l.description || ""
                              });
                              setEditOpen(true);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Tahrirlash"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              if (confirm("Haqiqatan ham bu darsni o'chirishni xohlaysiz?")) {
                                deleteLesson.mutate(l.id);
                              }
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="O'chirish"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Mobile - always visible on the side */}
                        <div className="hidden sm:flex absolute right-2 top-1/2 -translate-y-1/2 flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              setEditingLesson({
                                id: l.id,
                                title: l.title,
                                date: l.date,
                                description: l.description || ""
                              });
                              setEditOpen(true);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Tahrirlash"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              if (confirm("Haqiqatan ham bu darsni o'chirishni xohlaysiz?")) {
                                deleteLesson.mutate(l.id);
                              }
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="O'chirish"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Mobile - always visible at bottom */}
                        <div className="flex sm:hidden gap-1 pt-2">
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              setEditingLesson({
                                id: l.id,
                                title: l.title,
                                date: l.date,
                                description: l.description || ""
                              });
                              setEditOpen(true);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex-shrink-0"
                            title="Tahrirlash"
                          >
                            <Edit2 className="w-5 h-5 sm:w-4 sm:h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              if (confirm("Haqiqatan ham bu darsni o'chirishni xohlaysiz?")) {
                                deleteLesson.mutate(l.id);
                              }
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
                            title="O'chirish"
                          >
                            <Trash2 className="w-5 h-5 sm:w-4 sm:h-4" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </Link>
              </div>
            ))}

            {!lessonsLoading && (!lessons?.items || lessons.items.length === 0) && (
              <div className="card p-6 text-center text-sm text-emerald-700">Hozircha darslar yo‘q.</div>
            )}
          </div>

          {/* Pagination */}
          {lessons && lessons.total > ITEMS_PER_PAGE && (
            <div className="mt-6 p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-gray-600">
                  Jami: <span className="font-semibold text-gray-900">{lessons.total}</span> dars
                </div>
                <div className="flex items-center gap-3">
                  <Button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Oldingi
                  </Button>
                  <div className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 min-w-[100px] text-center">
                    {page} / {Math.ceil(lessons.total / ITEMS_PER_PAGE)}
                  </div>
                  <Button
                    onClick={() => setPage(page + 1)}
                    disabled={page >= Math.ceil(lessons.total / ITEMS_PER_PAGE)}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    Keyingi
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Darni tahrirlash</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Sarlavha</label>
              <Input
                placeholder="Dars mavzusi"
                value={editingLesson?.title || ""}
                onChange={(e) => setEditingLesson(prev => prev ? {...prev, title: e.target.value} : null)}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Sana</label>
              <Input
                type="date"
                value={editingLesson?.date || ""}
                onChange={(e) => setEditingLesson(prev => prev ? {...prev, date: e.target.value} : null)}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Qisqa izoh (ixtiyoriy)</label>
              <Input
                placeholder="Qisqa izoh (ixtiyoriy)"
                value={editingLesson?.description || ""}
                onChange={(e) => setEditingLesson(prev => prev ? {...prev, description: e.target.value} : null)}
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => updateLesson.mutate()}
                className="flex-1"
              >
                Yangilash
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setEditingLesson(null);
                  setEditOpen(false);
                }}
                className="flex-1"
              >
                Bekor qilish
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
