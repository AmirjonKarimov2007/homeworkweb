"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { ArrowLeft, Clock, BookOpen, Upload, FileText, Paperclip } from "lucide-react";
import Link from "next/link";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface HomeworkDetail {
  id: number;
  title: string;
  lesson_id: number;
  instructions?: string;
  due_date?: string;
  created_by: number;
  created_at: string;
}

interface SubmissionStatus {
  status: string;
  submission?: {
    id: number;
    text?: string;
    attachments?: Array<{
      id: number;
      file_name: string;
      file_path: string;
    }>;
  };
}

export default function HomeworkDetailPage() {
  const params = useParams();
  const router = useRouter();
  const homeworkId = Number(params.id);
  const qc = useQueryClient();
  const { addToast } = useToast();
  const mounted = useMounted();
  const user = mounted ? getUser() : null;
  const isStudent = user?.role === "STUDENT";

  const [title, setTitle] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [instructions, setInstructions] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [editMode, setEditMode] = useState(false);

  // Student homework submission states
  const [openSubmitDialog, setOpenSubmitDialog] = useState(false);
  const [homeworkText, setHomeworkText] = useState("");
  const [homeworkFile, setHomeworkFile] = useState<File | null>(null);

  // Get student's submission status
  const { data: submissionStatus } = useQuery({
    queryKey: ["homework-submission", homeworkId],
    enabled: mounted && isStudent && !!homeworkId,
    queryFn: async () => {
      const response = await api.get(`/homework/${homeworkId}/my`);
      return response.data.data;
    },
  });

  // Submit homework mutation
  const submitHomework = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      if (homeworkText) formData.append("text", homeworkText);
      // File attachment removed

      return api.post(`/homework/${homeworkId}/submit`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
    },
    onSuccess: () => {
      setHomeworkText("");
      setHomeworkFile(null);
      setOpenSubmitDialog(false);
      qc.invalidateQueries({ queryKey: ["homework-submission", homeworkId] });
      addToast({ title: "Uy ishi yuborildi", description: "Muvaffaqiyatli yuborildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Yuborishda xatolik." });
    },
  });

  // Get homework details
  const { data: homework, isLoading } = useQuery({
    queryKey: ["homework", homeworkId],
    queryFn: async () => {
      const response = await api.get(`/homework/${homeworkId}`);
      return response.data.data.data;
    },
    enabled: mounted && !!homeworkId,
  });

  // Update homework mutation
  const update = useMutation({
    mutationFn: async () =>
      api.put(`/homework/${homeworkId}`, {
        title,
        lesson_id: Number(lessonId),
        instructions: instructions || null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["homework", homeworkId] });
      setEditMode(false);
      addToast({ title: "Uyga vazifa yangilandi", description: "Muvaffaqiyatli yangilandi" });
    },
    onError: (err: any) => {
      addToast({
        title: "Xatolik",
        description: err?.response?.data?.detail || "Yangilanish amalga oshmadi"
      });
    },
  });

  // Populate form when homework loads
  useEffect(() => {
    if (homework && !editMode) {
      setTitle(homework.title);
      setLessonId(homework.lesson_id.toString());
      setInstructions(homework.instructions || "");
      setDueDate(homework.due_date?.slice(0, 16) || "");
    }
  }, [homework, editMode]);

  const handleSave = () => {
    if (!title || !lessonId) {
      addToast({ title: "To'ldiring", description: "Sarlavha va dars ID kerak" });
      return;
    }
    update.mutate();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!homework) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Uyga vazifa topilmadi</h2>
            <p className="text-gray-600 mb-4">Bunday ID ga ega uyga vazifa mavjud emas</p>
            <Link href="/homework">
              <Button variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Orqaga
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Get homework attachments
  const { data: attachments } = useQuery({
    queryKey: ["homework-attachments", homeworkId],
    enabled: mounted && !!homeworkId,
    queryFn: async () => {
      const response = await api.get(`/homework/${homeworkId}/attachments`);
      return response.data.data;
    },
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/homework">
              <Button variant="ghost" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Uy vazifalar ro'yxati
              </Button>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">
              Uyga vazifa #{homework.id}
            </h1>
            <div></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {editMode ? (
          // Edit Mode - Form
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-emerald-600" />
                Uy vazifani yangilash
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="text-sm font-medium mb-2 block">Sarlavha</label>
                <Input
                  placeholder="Misol: Algebra 1-bob"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Dars ID</label>
                <Input
                  placeholder="Raqam kiriting"
                  type="number"
                  value={lessonId}
                  onChange={(e) => setLessonId(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Ko'rsatma (matn)</label>
                <textarea
                  className="w-full min-h-[120px] p-3 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="Vazifa tafsilotlari..."
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Tugash vaqti (ixtiyoriy)</label>
                <Input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleSave}
                  disabled={update.isPending}
                  className="flex-1"
                >
                  {update.isPending ? "Saqlanmoqda..." : "Yangilash"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setEditMode(false)}
                  className="px-6"
                >
                  Bekor qilish
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          // View Mode - Display only
          <div className="space-y-6">
            {/* Info Card */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      {homework.title}
                    </h2>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <BookOpen className="w-4 h-4" />
                        Dars #{homework.lesson_id}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        Yaratilgan: {new Date(homework.created_at).toLocaleDateString('uz-UZ')}
                      </div>
                    </div>
                  </div>
                  <Button
                    onClick={() => setEditMode(true)}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    Yangilash
                  </Button>
                </div>

                {homework.instructions && (
                  <div className="mt-6">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Ko'rsatmalar:</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-gray-800 whitespace-pre-wrap">{homework.instructions}</p>
                    </div>
                  </div>
                )}

                {homework.due_date && (
                  <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Tugash vaqti:</h3>
                    <Badge
                      variant={new Date(homework.due_date) > new Date() ? "default" : "destructive"}
                      className="text-sm"
                    >
                      {new Date(homework.due_date).toLocaleString('uz-UZ', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              {/* Student Submission Section */}
              {isStudent && submissionStatus && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-emerald-600" />
                      Uy ishi holatingiz
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <Badge
                          className={
                            submissionStatus.status === "ACCEPTED" ? "bg-emerald-100 text-emerald-800" :
                            submissionStatus.status === "REVIEWED" ? "bg-blue-100 text-blue-800" :
                            submissionStatus.status === "LATE" ? "bg-red-100 text-red-800" :
                            submissionStatus.status === "SUBMITTED" ? "bg-amber-100 text-amber-800" :
                            "bg-gray-100 text-gray-800"
                          }
                        >
                          {submissionStatus.status === "ACCEPTED" ? "Qabul qilingan" :
                           submissionStatus.status === "REVIEWED" ? "Tekshirilmoqda" :
                           submissionStatus.status === "LATE" ? "Kechikkan" :
                           submissionStatus.status === "SUBMITTED" ? "Yuborilgan" :
                           "Bajarish kerak"}
                        </Badge>
                      </div>

                      {submissionStatus.submission && (
                        <div className="space-y-3">
                          {submissionStatus.submission.text && (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Javob:</h4>
                              <div className="bg-gray-50 rounded-lg p-3">
                                <p className="text-gray-800 whitespace-pre-wrap">{submissionStatus.submission.text}</p>
                              </div>
                            </div>
                          )}

                          {submissionStatus.submission.attachments && submissionStatus.submission.attachments.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Yuklangan fayllar:</h4>
                              <div className="space-y-2">
                                {submissionStatus.submission.attachments.map((attachment: any) => (
                                  <div key={attachment.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                    <Paperclip className="w-4 h-4 text-gray-500" />
                                    <span className="text-sm text-gray-700">{attachment.file_name}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {submissionStatus.status === "NOT_SUBMITTED" && (
                        <div>
                          <Dialog open={openSubmitDialog} onOpenChange={setOpenSubmitDialog}>
                            <DialogTrigger asChild>
                              <Button className="w-full">
                                <Upload className="w-4 h-4 mr-2" />
                                Uy ishini yuborish
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>Uy ishini yuborish</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-4">
                                <div>
                                  <label htmlFor="homework-text" className="text-sm font-medium text-gray-700">
                                    Javob (matn)
                                  </label>
                                  <Textarea
                                    id="homework-text"
                                    placeholder="Vazifa javobingizni yozing..."
                                    value={homeworkText}
                                    onChange={(e) => setHomeworkText(e.target.value)}
                                    className="mt-1"
                                    rows={4}
                                  />
                                </div>
                                <div className="flex gap-2 pt-2">
                                  <Button
                                    onClick={() => submitHomework.mutate()}
                                    disabled={submitHomework.isPending}
                                    className="flex-1"
                                  >
                                    {submitHomework.isPending ? "Yuborilmoqda..." : "Yuborish"}
                                  </Button>
                                  <Button
                                    variant="outline"
                                    onClick={() => setOpenSubmitDialog(false)}
                                  >
                                    Bekor qilish
                                  </Button>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Teacher Actions */}
              {!isStudent && (
                <CardContent className="p-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-4">Tezkor amallar</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <Button
                      variant="outline"
                      onClick={() => setEditMode(true)}
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Tahrirlash
                    </Button>
                    <Button variant="outline">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
    Uloash
                    </Button>
                    <Button variant="outline">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
    O'chirish
                    </Button>
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
