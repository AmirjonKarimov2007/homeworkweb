"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import ModernCard from "@/components/modern-card";
import ModernBadge from "@/components/modern-badge";
import ModernButton from "@/components/modern-button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { Calendar, BookOpen, Users } from "lucide-react";

export default function LessonsPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [title, setTitle] = useState("");
  const [groupId, setGroupId] = useState("");
  const [date, setDate] = useState("");
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["lessons"],
    queryFn: async () => {
      const response = (await api.get("/lessons")).data.data;
      // Sort by newest first
      if (response?.items) {
        response.items.sort((a: any, b: any) =>
          new Date(b.date || b.created_at).getTime() - new Date(a.date || a.created_at).getTime()
        );
      }
      return response;
    },
  });

  const capitalize = (str: string) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  const create = useMutation({
    mutationFn: async () => api.post("/lessons", { title, group_id: Number(groupId), date }),
    onSuccess: () => {
      setTitle("");
      setGroupId("");
      setDate("");
      qc.invalidateQueries({ queryKey: ["lessons"] });
      setOpen(false);
      addToast({ title: "Dars yaratildi", description: "Yangi dars ro‘yxatga qo‘shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Dars yaratilmadi." });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Darslar"
        description="Darslar ro‘yxati va boshqarish"
      />

      <ModernCard title="Darslarni boshqarish">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <ModernButton className="w-full">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Yangi dars qo‘shish
            </ModernButton>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Yangi dars yaratish</DialogTitle>
            </DialogHeader>
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
                <label className="text-sm font-medium text-gray-700 mb-2 block">Guruh ID</label>
                <Input
                  placeholder="Raqam kiriting"
                  value={groupId}
                  onChange={(e) => setGroupId(e.target.value)}
                  className="w-full"
                  type="number"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Sana</label>
                <Input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full"
                />
              </div>
              <ModernButton
                onClick={() => {
                  if (!title || !groupId || !date) {
                    addToast({ title: "To‘ldiring", description: "Barcha maydonlarni kiriting." });
                    return;
                  }
                  create.mutate();
                }}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                Saqlash
              </ModernButton>
            </div>
          </DialogContent>
        </Dialog>
      </ModernCard>

      <div className="space-y-3">
        {data?.items?.map((l: any) => (
          <ModernCard key={l.id} className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{capitalize(l.title)}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {l.date}
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      Guruh #{l.group_id}
                    </span>
                  </div>
                </div>
              </div>
              <ModernBadge variant="secondary">
                Aktiv
              </ModernBadge>
            </div>
          </ModernCard>
        ))}
        {(!data?.items || data.items.length === 0) && (
          <ModernCard className="text-center py-12">
            <div className="space-y-3">
              <div className="w-20 h-20 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                <BookOpen className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Hali darslar yo'q</h3>
              <p className="text-gray-600">Birinchi darsni qo'shish uchun yuqoridagi tugmani bosing</p>
            </div>
          </ModernCard>
        )}
      </div>
    </div>
  );
}
