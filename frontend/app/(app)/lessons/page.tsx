"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import ModernCard from "@/components/modern-card";
import ModernBadge from "@/components/modern-badge";
import ModernButton from "@/components/modern-button";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/page-header";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { Calendar, BookOpen, Users, ChevronLeft, ChevronRight, Loader2, Edit2, Trash2 } from "lucide-react";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";

interface User {
  id: number;
  full_name: string;
  phone: string;
  email?: string | null;
  avatar_path?: string | null;
  role: string;
}

interface Group {
  id: number;
  name: string;
}

export default function LessonsPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const searchParams = useSearchParams();
  const group_id_param = searchParams.get("group_id");
  const [title, setTitle] = useState("");
  const [groupId, setGroupId] = useState(group_id_param || "");
  const [date, setDate] = useState("");
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);
  const ITEMS_PER_PAGE = 6;
  const [user, setUser] = useState<User | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [editingLesson, setEditingLesson] = useState<any>(null);
  const [editOpen, setEditOpen] = useState(false);
  const mounted = useMounted();

  useEffect(() => {
    if (mounted) {
      setUser(getUser());
    }
  }, [mounted]);

  // Fetch teacher's groups if they are a teacher
  const { data: groupsData } = useQuery({
    queryKey: ["teacher-groups"],
    queryFn: async () => {
      if (user?.role !== "TEACHER") return [];
      const res = await api.get("/groups?my_groups=true");
      return res.data?.data || [];
    },
    enabled: mounted && user?.role === "TEACHER",
  });

  useEffect(() => {
    if (groupsData) {
      setGroups(groupsData);
    }
  }, [groupsData]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["lessons", page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        size: ITEMS_PER_PAGE.toString(),
        group_id: groupId || ""
      });

      console.log("Fetching lessons with params:", params.toString(), "Role:", user?.role, "Group ID:", groupId);

      let res;
      if (user?.role === "TEACHER") {
        // Teacher can access all lessons (only their own groups are filtered in backend)
        res = await api.get(`/lessons?${params}`);
      } else {
        // Admin, Super Admin or other roles
        res = await api.get(`/lessons?${params}`);
      }

      const apiData = res.data?.data || { items: [], total: 0, page: 1, size: ITEMS_PER_PAGE };
      console.log("API data structure:", apiData);
      console.log("API response data:", res.data);
      return apiData;
    },
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    qc.invalidateQueries({ queryKey: ["lessons"] });
  }, [qc]);

  const capitalize = (str: string) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  const create = useMutation({
    mutationFn: async () => {
      if (!groupId) {
        throw new Error("Guruh tanlang");
      }
      return api.post("/lessons", { title, group_id: Number(groupId), date });
    },
    onSuccess: () => {
      setTitle("");
      setGroupId("");
      setDate("");
      setPage(1);
      qc.invalidateQueries({ queryKey: ["lessons"] });
      setOpen(false);
      addToast({ title: "Dars yaratildi", description: "Yangi dars ro’yxatga qo’shildi." });
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
      qc.invalidateQueries({ queryKey: ["lessons"] });
      addToast({ title: "Dars o’chirildi", description: "Dars ro’yxatdan olib tashlandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars o’chirilmadi." });
    },
  });

  const updateLesson = useMutation({
    mutationFn: async () => {
      if (!editingLesson.id) return;
      return api.patch(`/lessons/${editingLesson.id}`, {
        title: editingLesson.title,
        date: editingLesson.date,
        group_id: Number(editingLesson.group_id),
      });
    },
    onSuccess: () => {
      setEditingLesson(null);
      setEditOpen(false);
      qc.invalidateQueries({ queryKey: ["lessons"] });
      addToast({ title: "Dars yangilandi", description: "Dars ma’lumotlari yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yangilanmadi." });
    },
  });

  return (
    <div className="space-y-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      <PageHeader
        title="Darslar"
        description="Darslar ro‘yxati va boshqarish"
      />

      <ModernCard title="Darslarni boshqarish">
        <div className="space-y-3">
          <div className="space-y-3">
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <ModernButton className="w-full">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Yangi dars qo’shish
              </ModernButton>
            </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{editingLesson ? "Darni tahrirlash" : "Yangi dars yaratish"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Sarlavha</label>
                <Input
                  placeholder="Misol: Algebra 1-bob"
                  value={editingLesson ? editingLesson.title : title}
                  onChange={(e) => editingLesson ? setEditingLesson({...editingLesson, title: e.target.value}) : setTitle(e.target.value)}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  {user?.role === "TEACHER" ? "Guruhni tanlang" : "Guruh ID"}
                </label>
                {user?.role === "TEACHER" ? (
                  <select
                    value={editingLesson ? editingLesson.group_id : groupId}
                    onChange={(e) => editingLesson ? setEditingLesson({...editingLesson, group_id: e.target.value}) : setGroupId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">Guruhni tanlang</option>
                    {groups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    placeholder="Raqam kiriting"
                    value={editingLesson ? editingLesson.group_id : groupId}
                    onChange={(e) => editingLesson ? setEditingLesson({...editingLesson, group_id: e.target.value}) : setGroupId(e.target.value)}
                    className="w-full"
                    type="number"
                  />
                )}
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Sana</label>
                <Input
                  type="date"
                  value={editingLesson ? editingLesson.date : date}
                  onChange={(e) => editingLesson ? setEditingLesson({...editingLesson, date: e.target.value}) : setDate(e.target.value)}
                  className="w-full"
                />
              </div>
              <div className="flex gap-2">
                <ModernButton
                  onClick={() => {
                    if (!editingLesson) {
                      if (!title || !groupId || !date) {
                        addToast({ title: "To’ldiring", description: "Barcha maydonlarni kiriting." });
                        return;
                      }
                      create.mutate();
                    } else {
                      updateLesson.mutate();
                    }
                  }}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  {editingLesson ? "Yangilash" : "Saqlash"}
                </ModernButton>
                {editingLesson && (
                  <ModernButton
                    variant="outline"
                    onClick={() => {
                      setEditingLesson(null);
                      setEditOpen(false);
                    }}
                    className="flex-1"
                  >
                    Bekor qilish
                  </ModernButton>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>

          {/* Edit Dialog */}
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <DialogTrigger asChild>
              {/* Hidden trigger - the actual edit is handled by button click */}
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Darni tahrirlash</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">Sarlavha</label>
                  <Input
                    placeholder="Misol: Algebra 1-bob"
                    value={editingLesson?.title || ""}
                    onChange={(e) => setEditingLesson(prev => prev ? {...prev, title: e.target.value} : null)}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    {user?.role === "TEACHER" ? "Guruhni tanlang" : "Guruh ID"}
                  </label>
                  {user?.role === "TEACHER" ? (
                    <select
                      value={editingLesson?.group_id || ""}
                      onChange={(e) => setEditingLesson(prev => prev ? {...prev, group_id: e.target.value} : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="">Guruhni tanlang</option>
                      {groups.map((group) => (
                        <option key={group.id} value={group.id}>
                          {group.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <Input
                      placeholder="Raqam kiriting"
                      value={editingLesson?.group_id || ""}
                      onChange={(e) => setEditingLesson(prev => prev ? {...prev, group_id: e.target.value} : null)}
                      className="w-full"
                      type="number"
                    />
                  )}
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">Sana</label>
                  <Input
                    type="date"
                    value={editingLesson?.date || ""}
                    onChange={(e) => setEditingLesson(prev => prev ? {...prev, date: e.target.value} : null)}
                    className="w-full"
                  />
                </div>
                <div className="flex gap-2">
                  <ModernButton
                    onClick={() => updateLesson.mutate()}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                  >
                    Yangilash
                  </ModernButton>
                  <ModernButton
                    variant="outline"
                    onClick={() => {
                      setEditingLesson(null);
                      setEditOpen(false);
                    }}
                    className="flex-1"
                  >
                    Bekor qilish
                  </ModernButton>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading && (
          Array.from({ length: 6 }).map((_, index) => (
            <ModernCard key={index} className="p-5 animate-pulse">
              <div className="space-y-3">
                <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </ModernCard>
          ))
        )}

        {error && (
          <div className="md:col-span-2">
            <ModernCard className="text-center py-12 text-red-600">
              <h3 className="text-lg font-medium">Xatolik yuz berdi</h3>
              <p className="text-sm text-gray-600 mt-1">Iltimos, qayta urinib ko'ring</p>
            </ModernCard>
          </div>
        )}

        {!isLoading && data?.items?.map((l: any) => (
          <ModernCard key={l.id} className="hover:shadow-lg transition-all duration-200 hover:scale-[1.02] relative group sm:pr-12">
            <div className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1 pr-2 sm:pr-0">
                  <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <BookOpen className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 text-lg mb-2 truncate pr-16 sm:pr-0">{capitalize(l.title)}</h3>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>{l.date}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Users className="w-4 h-4" />
                        <span>Guruh #{l.group_id}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <ModernBadge variant="secondary" className="ml-2">
                    Aktiv
                  </ModernBadge>

                  {/* Edit/Delete buttons - always visible for admin/teacher on mobile, hover on desktop */}
                  {user?.role !== "STUDENT" && (
                    <div className="flex gap-1 transition-opacity justify-end">
                      {/* Desktop - only on hover */}
                      <div className="hidden sm:flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => {
                            setEditingLesson({
                              id: l.id,
                              title: l.title,
                              date: l.date,
                              group_id: l.group_id
                            });
                            setEditOpen(true);
                          }}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Tahrirlash"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
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
                          onClick={() => {
                            setEditingLesson({
                              id: l.id,
                              title: l.title,
                              date: l.date,
                              group_id: l.group_id
                            });
                            setEditOpen(true);
                          }}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Tahrirlash"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
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
                          onClick={() => {
                            setEditingLesson({
                              id: l.id,
                              title: l.title,
                              date: l.date,
                              group_id: l.group_id
                            });
                            setEditOpen(true);
                          }}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex-shrink-0"
                          title="Tahrirlash"
                        >
                          <Edit2 className="w-5 h-5 sm:w-4 sm:h-4" />
                        </button>
                        <button
                          onClick={() => {
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
              </div>
            </div>
          </ModernCard>
        ))}
        )}
        {!isLoading && (!data?.items || data.items.length === 0) && (
          <div className="md:col-span-2">
            <ModernCard className="text-center py-16">
              <div className="space-y-3">
                <div className="w-20 h-20 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                  <BookOpen className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900">Hali darslar yo'q</h3>
                <p className="text-gray-600 max-w-md mx-auto">Birinchi darsni qo'shish uchun yuqoridagi tugmani bosing</p>
              </div>
            </ModernCard>
          </div>
        )}
      </div>

      {data?.total && data.total > ITEMS_PER_PAGE && (
        <div className="mt-8 p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Jami: <span className="font-semibold text-gray-900">{data.total}</span> dars
            </div>
            <div className="flex items-center gap-3">
              <ModernButton
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1 || isLoading}
                className="flex items-center gap-2"
                variant="outline"
                size="sm"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ChevronLeft className="w-4 h-4" />
                )}
                Oldingi
              </ModernButton>
              <div className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 min-w-[100px] text-center">
                {page} / {data ? Math.ceil(data.total / ITEMS_PER_PAGE) : 1}
              </div>
              <ModernButton
                onClick={() => setPage(page + 1)}
                disabled={page >= (data ? Math.ceil(data.total / ITEMS_PER_PAGE) : 1) || isLoading}
                className="flex items-center gap-2"
                variant="outline"
                size="sm"
              >
                Keyingi
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </ModernButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
