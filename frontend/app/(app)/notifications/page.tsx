"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { useToast } from "@/components/ui/use-toast";
import { getUser } from "@/lib/auth";
import { Bell, Megaphone } from "lucide-react";
import { format } from "date-fns";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const user = typeof window !== "undefined" ? getUser() : null;
  const isAdmin = user?.role === "SUPER_ADMIN" || user?.role === "ADMIN";

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [target, setTarget] = useState<"students" | "teachers" | "group">("students");
  const [groupId, setGroupId] = useState("");

  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get("/notifications")).data.data,
  });

  const { data: groups } = useQuery({
    queryKey: ["groups-lite"],
    enabled: isAdmin,
    queryFn: async () => (await api.get("/groups?size=1000")).data.data,
  });

  const markRead = useMutation({
    mutationFn: async (id: number) => api.patch(`/notifications/${id}/read`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const sendNotification = useMutation({
    mutationFn: async () => {
      const payload: any = { title, body: body || null };
      if (target === "students") payload.role = "STUDENT";
      if (target === "teachers") payload.role = "TEACHER";
      if (target === "group") payload.group_id = Number(groupId);
      return api.post("/notifications/send", payload);
    },
    onSuccess: () => {
      setTitle("");
      setBody("");
      setGroupId("");
      addToast({ title: "Yuborildi", description: "Xabarnoma yuborildi." });
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Xabar yuborilmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Xabarnomalar" description="Siz uchun yangi xabarlar." />

      {isAdmin && (
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-2 text-emerald-900 font-semibold">
            <Megaphone className="h-5 w-5 text-emerald-700" />
            Xabar yuborish
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <Input placeholder="Sarlavha" value={title} onChange={(e) => setTitle(e.target.value)} />
            <select
              className="w-full rounded-xl border border-emerald-100 p-2 text-sm"
              value={target}
              onChange={(e) => setTarget(e.target.value as any)}
            >
              <option value="students">Barcha talabalar</option>
              <option value="teachers">Barcha o‘qituvchilar</option>
              <option value="group">Guruh bo‘yicha</option>
            </select>
          </div>
          {target === "group" && (
            <select
              className="w-full rounded-xl border border-emerald-100 p-2 text-sm"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
            >
              <option value="">Guruhni tanlang</option>
              {groups?.items?.map((g: any) => (
                <option key={g.id} value={g.id}>{g.name}</option>
              ))}
            </select>
          )}
          <textarea
            className="w-full rounded-xl border border-emerald-100 p-3 text-sm"
            rows={3}
            placeholder="Xabar matni (ixtiyoriy)"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <Button
            onClick={() => {
              if (!title) {
                addToast({ title: "Sarlavha kerak", description: "Xabar sarlavhasini kiriting." });
                return;
              }
              if (target === "group" && !groupId) {
                addToast({ title: "Guruh tanlang", description: "Guruh bo‘yicha yuborish uchun guruh tanlang." });
                return;
              }
              sendNotification.mutate();
            }}
          >
            Yuborish
          </Button>
        </div>
      )}

      <div className="space-y-2">
        {data?.map((n: any) => (
          <button
            key={n.id}
            onClick={() => markRead.mutate(n.id)}
            className={`w-full text-left card p-4 flex items-start gap-3 hover:shadow-card transition ${
              n.status === "SENT" ? "opacity-70" : ""
            }`}
          >
            <div className="h-10 w-10 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Bell className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <div className="font-semibold text-emerald-900">{n.title}</div>
                <div className="text-xs text-emerald-600">
                  {n.created_at ? format(new Date(n.created_at), "dd.MM HH:mm") : ""}
                </div>
              </div>
              {n.body && <div className="text-sm text-emerald-700 mt-1">{n.body}</div>}
              {n.status === "SENT" ? (
                <div className="mt-2 inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] text-emerald-700">
                  O‘qilgan
                </div>
              ) : (
                <div className="mt-2 inline-flex rounded-full bg-amber-50 px-2 py-0.5 text-[11px] text-amber-700">
                  Yangi
                </div>
              )}
            </div>
          </button>
        ))}
        {!data || data.length === 0 ? (
          <div className="card p-6 text-center text-sm text-emerald-700">
            Yangi xabarnoma yo‘q.
          </div>
        ) : null}
      </div>
    </div>
  );
}
