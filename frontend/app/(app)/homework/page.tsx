"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import ModernCard from "@/components/modern-card";
import ModernBadge from "@/components/modern-badge";
import ModernButton from "@/components/modern-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { BookOpen, Upload } from "lucide-react";
import Link from "next/link";

export default function HomeworkPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [title, setTitle] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [instructions, setInstructions] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editMode, setEditMode] = useState(false);

  // Formni tozalash funksiyasi
  const clearForm = () => {
    setTitle("");
    setLessonId("");
    setInstructions("");
    setDueDate("");
    setEditingId(null);
    setEditMode(false);
    console.log("Form tozalandi");
  };

  const { data } = useQuery({
    queryKey: ["homework"],
    queryFn: async () => (await api.get("/homework")).data.data.data,
  });

  const editHomework = (homework: any) => {
    console.log("Uyga vazifa yangilash:", homework);
    setTitle(homework.title);
    setLessonId(homework.lesson_id.toString());
    setInstructions(homework.instructions || "");
    setDueDate(homework.due_date ? new Date(homework.due_date).toISOString().slice(0, 16) : "");
    setEditingId(homework.id);
    setEditMode(true);
    setOpen(true);
  };

  const create = useMutation({
    mutationFn: async () =>
      api.post("/homework", {
        title,
        lesson_id: Number(lessonId),
        instructions: instructions || null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        allow_late_submission: true,
        max_revision_attempts: 2,
      }),
    onSuccess: () => {
      clearForm();
      qc.invalidateQueries({ queryKey: ["homework"] });
      setOpen(false);
      addToast({ title: "Uyga vazifa saqlandi", description: "Uyga vazifa yaratildi." });
    },
    onError: (err: any) => {
      console.error("Homework save error:", err);
      console.error("Xatolik detallari:", err?.response?.data);

      // Handle different error formats
      let errorMessage = "Uyga vazifa saqlanmadi. Iltimos qayta urinib ko'ring.";

      if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err?.response?.data) {
        // If it's an object with multiple errors
        const errors = err.response.data;
        if (typeof errors === 'object') {
          const firstError = Object.values(errors)[0];
          if (typeof firstError === 'string') {
            errorMessage = firstError;
          } else if ((firstError as any)?.msg || (firstError as any)?.message) {
            errorMessage = (firstError as any).msg || (firstError as any).message;
          }
        }
      }

      addToast({
        title: "Xatolik",
        description: typeof errorMessage === 'string' ? errorMessage : "Noma'lum xatolik yuz berdi"
      });
    },
  });

  const update = useMutation({
    mutationFn: async () =>
      api.put(`/homework/${editingId}`, {
        title,
        lesson_id: Number(lessonId),
        instructions: instructions || null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        allow_late_submission: true,
        max_revision_attempts: 2,
      }),
    onSuccess: () => {
      console.log("✅ Update successful");
      clearForm();
      qc.invalidateQueries({ queryKey: ["homework"] });
      setOpen(false);
      addToast({ title: "✅ Yangilandi", description: "Uyga vazifa muvaffaqiyatli yangilandi" });
    },
    onError: (err: any) => {
      console.error("❌ Update error:", err?.response?.status, err?.response?.data);
      let errorMessage = "Uyga vazifa yangilanmadi";

      if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message;
      }

      addToast({
        title: "❌ Xatolik",
        description: errorMessage
      });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Uy vazifalar"
        description="Uy vazifa ro‘yxati va boshqarish"
      />

      <ModernCard
        title="Uyga vazifalarni boshqarish"
        className="bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-emerald-800">Barcha vazifalar</span>
          </div>
          {editMode && (
            <ModernButton variant="outline" onClick={() => setOpen(false)}>
              Bekor qilish
            </ModernButton>
          )}
          <Dialog open={open} onOpenChange={(open) => {
            setOpen(open);
            if (!open) {
              clearForm();
            }
          }}>
            <DialogTrigger asChild>
              <ModernButton>
                <Upload className="w-4 h-4 mr-2" />
                Uyga vazifa qo’shish
              </ModernButton>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-emerald-600" />
                  {editMode ? "Uyga vazifani yangilash" : "Yangi uyga vazifa yaratish"}
                </DialogTitle>
              </DialogHeader>
              {editMode ? (
                <ModernCard>
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium text-blue-800">
                        Uyga vazifa №{editingId} ni yangilash
                      </span>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Sarlavha</label>
                      <Input
                        placeholder="Misol: Algebra 1-bob"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Dars ID</label>
                      <Input
                        placeholder="Raqam kiriting"
                        type="number"
                        value={lessonId}
                        onChange={(e) => setLessonId(e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Ko’rsatma (matn)</label>
                      <Textarea
                        placeholder="Vazifa tafsilotlari..."
                        value={instructions}
                        onChange={(e) => setInstructions(e.target.value)}
                        className="w-full resize-none"
                        rows={4}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Tugash vaqti (ixtiyoriy)</label>
                      <Input
                        type="datetime-local"
                        value={dueDate}
                        onChange={(e) => setDueDate(e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div className="flex gap-3 pt-2">
                      <ModernButton
                        onClick={() => {
                          console.log("Form yuborildi:", { title, lessonId, editMode, editingId });
                          if (!title || !lessonId) {
                            addToast({ title: "To’ldiring", description: "Sarlavha va dars ID kerak." });
                            return;
                          }
                          if (editMode) {
                            update.mutate();
                          } else {
                            create.mutate();
                          }
                        }}
                        loading={create.isPending || update.isPending}
                        className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                      >
                        {editMode ? "Yangilash" : "Saqlash"}
                      </ModernButton>
                      {editMode && (
                        <ModernButton
                          variant="outline"
                          onClick={() => {
                            clearForm();
                            setOpen(false);
                          }}
                          className="flex-1"
                        >
                          Yopish
                        </ModernButton>
                      )}
                    </div>
                  </div>
                </ModernCard>
              ) : (
                <div className="text-center py-8">
                  <BookOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-600 mb-2">Yangi uyga vazifa yaratish</p>
                  <p className="text-sm text-gray-500">
                    Yuqoridagi "Uyga vazifa qo’shish" tugmasini bosing
                  </p>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </ModernCard>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50%]">Sarlavha</TableHead>
                <TableHead className="w-[20%]">Dars</TableHead>
                <TableHead className="w-[20%]">Holati</TableHead>
                <TableHead className="w[10%] text-right">Amallar</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.items?.map((h: any) => (
                <TableRow key={h.id} className="hover:bg-gray-50/50">
                  <TableCell>
                    <div>
                      <div className="font-medium">{h.title}</div>
                      {h.instructions && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">{h.instructions}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs">
                      Dars #{h.lesson_id}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {h.due_date ? (
                      <Badge variant={new Date(h.due_date) > new Date() ? "default" : "destructive"}>
                        {new Date(h.due_date).toLocaleDateString('uz-UZ')}
                      </Badge>
                    ) : (
                      <Badge variant="outline">Cheksiz</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => editHomework(h)}
                        className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                      >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Yangilash
                      </Button>
                      <Link href={`/homework/${h.id}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Ko'rish
                        </Button>
                      </Link>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {(!data?.items || data.items.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>Hech qanday uyga vazifa topilmadi</p>
              <p className="text-sm mt-1">Iltimos birinchi uyga vazifani qo'shing</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
