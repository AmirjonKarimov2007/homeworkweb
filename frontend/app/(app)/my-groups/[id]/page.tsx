"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import ModernCard from "@/components/modern-card";
import ModernBadge from "@/components/modern-badge";
import ModernButton from "@/components/modern-button";

interface HomeworkItem {
  id: number;
  lesson_id: number;
  title?: string;
}

interface Lesson {
  id: number;
  title: string;
  date: string;
  description?: string;
}

interface Student {
  id: number;
  full_name: string;
  phone: string;
}

export default function MyGroupDetailPage() {
  const PAGE_SIZE = 6;
  // 1. Hooks (must be in the same order every render)
  const params = useParams();
  const groupId = Number(params.id);
  const qc = useQueryClient();
  const { addToast } = useToast();
  const mounted = useMounted();

  // 2. State variables
  const [tab, setTab] = useState<"students" | "lessons">("lessons");
  const [openLesson, setOpenLesson] = useState(false);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonDate, setLessonDate] = useState("");
  const [lessonDesc, setLessonDesc] = useState("");
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [openHomework, setOpenHomework] = useState(false);
  const [selectedHomework, setSelectedHomework] = useState<HomeworkItem | null>(null);
  const [homeworkText, setHomeworkText] = useState("");
  const [homeworkFile, setHomeworkFile] = useState<File | null>(null);
  const [lessonPage, setLessonPage] = useState(1);

  // 3. Derived state
  const user = typeof window !== "undefined" ? getUser() : null;
  const canCreateLesson = user?.role === "TEACHER" || user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";
  const isStudent = user?.role === "STUDENT";

  // 4. Data fetching queries
  const { data: enrollment } = useQuery({
    queryKey: ["enrollment", groupId],
    enabled: mounted && isStudent,
    queryFn: async () => (await api.get(`/groups/${groupId}/enrollment`)).data.data,
  });
  const submitHomework = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      if (homeworkText) formData.append("text", homeworkText);
      // File attachment removed

      if (!selectedHomework) return;

      return api.post(`/homework/${selectedHomework.id}/submit`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
    },
    onSuccess: () => {
      setHomeworkText("");
      setHomeworkFile(null);
      setSelectedHomework(null);
      setOpenHomework(false);
      qc.invalidateQueries({ queryKey: ["homework", groupId] });
      qc.invalidateQueries({ queryKey: ["homework-status", homeworkIds] });
      addToast({ title: "Uy ishi yuborildi", description: "Muvaffaqiyatli yuborildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Yuborishda xatolik." });
    },
  });

  const { data: group, error: groupError } = useQuery({
    queryKey: ["group", groupId],
    queryFn: async () => (await api.get(`/groups/${groupId}`)).data.data,
  });

  // Log group error
  if (groupError) {
    console.error("Error fetching group:", groupError);
  }

  const { data: lessons, error: teacherLessonsError } = useQuery({
    queryKey: ["lessons", groupId, lessonPage],
    enabled: mounted && !isStudent,
    queryFn: async () => {
      try {
        const response = await api.get(`/lessons?group_id=${groupId}&page=${lessonPage}&size=${PAGE_SIZE}`);
        return response.data.data;
      } catch (error) {
        console.error("Error fetching lessons:", error);
        return { items: [], total: 0, page: lessonPage, size: PAGE_SIZE };
      }
    },
  });

  const { data: allLessons, error: lessonsError } = useQuery({
    queryKey: ["student-lessons", groupId, lessonPage],
    enabled: mounted && isStudent,
    queryFn: async () => {
      try {
        const response = await api.get(`/lessons?group_id=${groupId}&page=${lessonPage}&size=${PAGE_SIZE}`);
        return response.data.data;
      } catch (error) {
        console.error("Error fetching lessons:", error);
        return { items: [], total: 0, page: lessonPage, size: PAGE_SIZE };
      }
    },
  });

  // Use allLessons for students instead of lessons
  const studentLessons = Array.isArray(allLessons) ? allLessons : (allLessons?.items || []);
  const currentLessonItems = isStudent ? studentLessons : (lessons?.items || []);

  // Sort lessons by newest first
  const sortedLessonItems = currentLessonItems.sort((a: any, b: any) =>
    new Date(b.date || b.created_at).getTime() - new Date(a.date || a.created_at).getTime()
  );

  const totalLessons = isStudent
    ? (Array.isArray(allLessons) ? studentLessons.length : (allLessons?.total || 0))
    : (lessons?.total || 0);
  const totalLessonPages = Math.max(1, Math.ceil(totalLessons / PAGE_SIZE));

  // Capitalize function
  const capitalize = (str: string) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  // Debug log
  console.log("Student lessons data:", {
    allLessons,
    studentLessons,
    studentLessonsLength: studentLessons.length,
    isStudent,
    groupId,
    isEnrolled,
    lessons: lessons?.items,
    lessonsLength: lessons?.items?.length
  });

  // Log errors
  if (teacherLessonsError) {
    console.error("Error fetching teacher lessons:", teacherLessonsError);
  }
  if (lessonsError) {
    console.error("Error fetching student lessons:", lessonsError);
  }

  const { data: students } = useQuery({
    queryKey: ["group-students", groupId],
    enabled: mounted && !isStudent,
    queryFn: async () => (await api.get(`/groups/${groupId}/students`)).data.data,
  });

  const { data: allStudents } = useQuery({
    queryKey: ["all-students"],
    enabled: mounted && !isStudent,
    queryFn: async () => (await api.get("/students")).data.data,
  });

  const removeStudentFromGroup = useMutation({
    mutationFn: async (studentId: number) => api.put(`/students/${studentId}/groups`, { group_ids: [] }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["group-students", groupId] });
      qc.invalidateQueries({ queryKey: ["all-students"] });
      addToast({ title: "O'chirildi", description: "Talaba guruhdan chiqarildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Talaba chiqarilmadi." });
    },
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

  // Enrollment check effect (must be after all data queries)
  useEffect(() => {
    if (isStudent && group) {
      // Check if student is enrolled through groups endpoint
      const checkEnrollment = async () => {
        try {
          const response = await api.get(`/groups/${groupId}/enrollment`);
          const data = response.data.data;
          setIsEnrolled(data.is_enrolled);
          console.log(`Student enrollment check for group ${groupId}:`, data.is_enrolled);
        } catch (error) {
          console.error("Error checking enrollment:", error);
          setIsEnrolled(false);
        }
      };
      checkEnrollment();
    }
  }, [isStudent, group, groupId]);

  useEffect(() => {
    setLessonPage(1);
  }, [groupId, isStudent, tab]);

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

    if (statuses.some((s: string) => s === "ACCEPTED")) {
      return { label: "Qabul qilingan", tone: "bg-emerald-100 text-emerald-800" };
    }
    if (statuses.some((s: string) => s === "REVIEWED")) {
      return { label: "Tekshirilmoqda", tone: "bg-blue-100 text-blue-800" };
    }
    if (statuses.some((s: string) => s === "LATE")) {
      return { label: "Kechikkan", tone: "bg-red-100 text-red-800" };
    }
    if (statuses.some((s: string) => s === "SUBMITTED")) {
      return { label: "Yuborilgan", tone: "bg-amber-100 text-amber-800" };
    }
    return { label: "Bajarish kerak", tone: "bg-orange-100 text-orange-800" };
  };

  
  if (!group) {
    return <div>Yuklanmoqda...</div>;
  }

  if (isStudent && !isEnrolled) {
    return (
      <div className="space-y-4">
        <PageHeader title="Xato" description="Siz bu guruhga a'zo emassiz." />
        <ModernCard className="text-center py-8">
          <p className="text-gray-600">Bu guruhga kirish uchun admin tomonidan tasdiqlanishingiz kerak.</p>
        </ModernCard>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PageHeader title={group?.name || "Guruh"} description={`Jadval: ${group?.schedule_time || "-"}`} />

      {!isStudent && (
        <ModernCard title="Guruh boshqaruvi" className="mb-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <ModernButton
              variant={tab === "students" ? "default" : "outline"}
              onClick={() => setTab("students")}
              className="flex-1"
            >
              O’quvchilar
            </ModernButton>
            <ModernButton
              variant={tab === "lessons" ? "default" : "outline"}
              onClick={() => setTab("lessons")}
              className="flex-1"
            >
              Darslar
            </ModernButton>
          </div>
        </ModernCard>
      )}

      {isStudent && (
        <div className="space-y-6">
          {/* Homework Submission Dialog */}
          {openHomework && selectedHomework && (
              <Dialog open={openHomework} onOpenChange={setOpenHomework}>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Uy ishini yuborish
                  </DialogTitle>
                </DialogHeader>
                <ModernCard>
                  <div className="space-y-6">
                    <div className="text-center py-4 border-b border-gray-200">
                      <h3 className="text-lg font-semibold text-gray-900">{selectedHomework.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">Vazifani to'liq bajarishingiz kerak</p>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <label htmlFor="homework-text" className="text-sm font-medium text-gray-700 mb-2 block">
                          Javob (matn)
                        </label>
                        <Textarea
                          id="homework-text"
                          placeholder="Vazifa javobingizni yozing..."
                          value={homeworkText}
                          onChange={(e) => setHomeworkText(e.target.value)}
                          className="w-full resize-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                          rows={6}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {homeworkText.length}/1000 belgi
                        </p>
                      </div>
                      <div className="flex flex-col gap-3 pt-4 sm:flex-row">
                        <ModernButton
                          onClick={() => submitHomework.mutate()}
                          disabled={submitHomework.isPending}
                          loading={submitHomework.isPending}
                          className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                        >
                          Yuborish
                        </ModernButton>
                        <ModernButton
                          variant="outline"
                          onClick={() => setOpenHomework(false)}
                          className="flex-1"
                        >
                          Bekor qilish
                        </ModernButton>
                      </div>
                    </div>
                  </div>
                </ModernCard>
              </DialogContent>
            </Dialog>
          )}
        </div>
      )}

      {(!isStudent && tab === "students") && (
        <ModernCard title="O'quvchilar ro'yxati">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Talaba</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Telefon</th>
                </tr>
              </thead>
              <tbody>
                {students?.map((s: Student) => (
                  <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-emerald-700">
                            {s.full_name.charAt(0)}
                          </span>
                        </div>
                        <span className="font-medium text-gray-900">{s.full_name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{s.phone}</td>
                    <td className="py-3 px-4">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => {
                          if (confirm(`${s.full_name} ni guruhdan chiqarishni istaysizmi?`)) {
                            removeStudentFromGroup.mutate(s.id);
                          }
                        }}
                      >
                        Chiqarish
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ModernCard>
      )}

      {(isStudent || tab === "lessons") && (
        <div className="space-y-4">
          {canCreateLesson && (
            <ModernCard title="Yangi dars yaratish" className="mb-6">
              <Dialog open={openLesson} onOpenChange={setOpenLesson}>
                <DialogTrigger asChild>
                  <ModernButton className="w-full">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Dars yaratish
                  </ModernButton>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Yangi dars</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Dars mavzusi</label>
                      <Input
                        placeholder="Misol: Algebra 1-bob"
                        value={lessonTitle}
                        onChange={(e) => setLessonTitle(e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Sana</label>
                      <Input
                        type="date"
                        value={lessonDate}
                        onChange={(e) => setLessonDate(e.target.value)}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Izoh (ixtiyoriy)</label>
                      <Textarea
                        placeholder="Dars haqida qisqa izoh..."
                        value={lessonDesc}
                        onChange={(e) => setLessonDesc(e.target.value)}
                        className="w-full"
                        rows={3}
                      />
                    </div>
                    <ModernButton
                      onClick={() => {
                        if (!lessonTitle || !lessonDate) {
                          addToast({ title: "To’ldiring", description: "Dars mavzusi va sanani kiriting." });
                          return;
                        }
                        createLesson.mutate();
                      }}
                      className="w-full"
                    >
                      Saqlash
                    </ModernButton>
                  </div>
                </DialogContent>
              </Dialog>
            </ModernCard>
          )}

          <div className="space-y-3">
            {sortedLessonItems.map((l: any) => {
              const lessonId = l.id || l.lesson_id;
              const status = computeLessonStatus(lessonId);
              const lessonHomeworks = homework?.items?.filter((h: HomeworkItem) => h.lesson_id === lessonId) || [];
              const hasHomework = lessonHomeworks.length > 0;

              return (
                <Link key={lessonId} href={`/lessons/${lessonId}`} className="group block">
                  <ModernCard className="hover:shadow-lg hover:scale-[1.02] transition-all duration-200">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="flex-1 space-y-2">
                        <h3 className="font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors">
                          {capitalize(l.title || l.name)}
                        </h3>
                        <div className="flex flex-col gap-2 text-sm text-gray-600 sm:flex-row sm:items-center sm:gap-4">
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {l.date || l.created_at?.split('T')[0]}
                          </span>
                        </div>
                        {(l.description || l.description_text) && (
                          <p className="text-sm text-gray-600 line-clamp-2 mt-2">
                            {l.description || l.description_text}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col gap-2 sm:min-w-[180px] sm:items-end">
                        <ModernBadge variant={status.label === "Qabul qilingan" ? "success" :
                                            status.label === "Tekshirilmoqda" ? "info" :
                                            status.label === "Kechikkan" ? "destructive" :
                                            status.label === "Yuborilgan" ? "warning" :
                                            status.label === "Bajarish kerak" ? "default" : "secondary"}>
                          {status.label}
                        </ModernBadge>
                        {isStudent && hasHomework && (
                          <ModernButton
                            size="sm"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setSelectedHomework(lessonHomeworks[0]);
                              setOpenHomework(true);
                            }}
                            className="text-xs"
                          >
                            Yuborish
                          </ModernButton>
                        )}
                      </div>
                    </div>
                  </ModernCard>
                </Link>
              );
            })}
            {sortedLessonItems.length === 0 && (
              <ModernCard className="text-center py-8">
                <div className="space-y-2">
                  <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <p className="text-gray-600">
                    {isStudent ? "Sizning guruhingizda hozircha darslar yo'q." : "Hozircha darslar yo'q."}
                  </p>
                  {isStudent ? (
                    <p className="text-sm text-gray-500">
                      O'qituvchi dars qo'shgandan so'ng bu yerda ko'rinadi. Iltimos biroz kuting.
                    </p>
                  ) : (
                    <p className="text-sm text-gray-500">
                      Yangi dars qo'shish uchun yuqoridagi "Dars yaratish" tugmasini bosing.
                    </p>
                  )}
                </div>
              </ModernCard>
            )}
            {totalLessons > PAGE_SIZE && (
              <ModernCard className="p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-gray-600">
                    Sahifa {lessonPage} / {totalLessonPages}
                  </p>
                  <div className="flex gap-2">
                    <ModernButton
                      variant="outline"
                      onClick={() => setLessonPage((prev) => Math.max(1, prev - 1))}
                      disabled={lessonPage === 1}
                      className="flex-1 sm:flex-none"
                    >
                      Oldingi
                    </ModernButton>
                    <ModernButton
                      variant="outline"
                      onClick={() => setLessonPage((prev) => Math.min(totalLessonPages, prev + 1))}
                      disabled={lessonPage >= totalLessonPages}
                      className="flex-1 sm:flex-none"
                    >
                      Keyingi
                    </ModernButton>
                  </div>
                </div>
              </ModernCard>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
