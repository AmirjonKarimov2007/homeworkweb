"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { useEffect, useState } from "react";
import { getUser, saveAuth } from "@/lib/auth";
import { fileUrl } from "@/lib/file-url";
import { Camera, UserCircle } from "lucide-react";

export default function ProfilePage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const localUser = typeof window !== "undefined" ? getUser() : null;
  const isStudent = localUser?.role === "STUDENT";

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get("/users/me")).data.data,
  });

  useEffect(() => {
    if (me) {
      setFullName(me.full_name || "");
      setPhone(me.phone || "");
      setEmail(me.email || "");
      const access = localStorage.getItem("access_token") || "";
      const refresh = localStorage.getItem("refresh_token") || "";
      if (access && refresh) saveAuth(access, refresh, me);
    }
  }, [me?.id]);

  const updateProfile = useMutation({
    mutationFn: async () => {
      const payload: any = { full_name: fullName };
      if (!isStudent) {
        payload.phone = phone;
        payload.email = email || null;
        if (password) payload.password = password;
      }
      return api.patch("/users/me", payload);
    },
    onSuccess: (res: any) => {
      const user = res.data.data;
      const access = localStorage.getItem("access_token") || "";
      const refresh = localStorage.getItem("refresh_token") || "";
      if (access && refresh) saveAuth(access, refresh, user);
      setPassword("");
      qc.invalidateQueries({ queryKey: ["me"] });
      addToast({ title: "Yangilandi", description: "Profil ma’lumotlari saqlandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Profil yangilanmadi." });
    },
  });

  const uploadAvatar = useMutation({
    mutationFn: async () => {
      if (!avatarFile) return;
      const fd = new FormData();
      fd.append("file", avatarFile);
      return api.post("/users/me/avatar", fd);
    },
    onSuccess: (res: any) => {
      const avatar_path = res.data.data.avatar_path;
      const access = localStorage.getItem("access_token") || "";
      const refresh = localStorage.getItem("refresh_token") || "";
      if (me && access && refresh) saveAuth(access, refresh, { ...me, avatar_path });
      setAvatarFile(null);
      qc.invalidateQueries({ queryKey: ["me"] });
      addToast({ title: "Avatar yangilandi", description: "Rasm muvaffaqiyatli yuklandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Avatar yuklanmadi." });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Profil" description="Shaxsiy ma’lumotlaringizni yangilang." />

      <div className="card p-6">
        <div className="flex flex-col gap-6 md:flex-row md:items-center">
          <div className="relative h-24 w-24">
            {me?.avatar_path ? (
              <img
                src={fileUrl(me.avatar_path)}
                alt="Avatar"
                className="h-24 w-24 rounded-3xl object-cover border border-emerald-200"
              />
            ) : (
              <div className="h-24 w-24 rounded-3xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                <UserCircle className="h-12 w-12" />
              </div>
            )}
            <label className="absolute -bottom-2 -right-2 cursor-pointer rounded-full bg-emerald-600 p-2 text-white shadow">
              <Camera className="h-4 w-4" />
              <input
                type="file"
                className="hidden"
                accept="image/*"
                onChange={(e) => setAvatarFile(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          <div className="flex-1 space-y-1">
            <div className="text-lg font-semibold text-emerald-900">{me?.full_name || "Profil"}</div>
            <div className="text-sm text-emerald-700">{me?.role}</div>
            {avatarFile && (
              <Button size="sm" className="mt-2" onClick={() => uploadAvatar.mutate()}>
                Avatarni yuklash
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="card p-6 space-y-4">
        <div className="text-sm font-semibold text-emerald-900">Profil ma’lumotlari</div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <div className="text-xs text-emerald-600 mb-1">Ism Familiya</div>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>

          {!isStudent && (
            <>
              <div>
                <div className="text-xs text-emerald-600 mb-1">Telefon</div>
                <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
              <div>
                <div className="text-xs text-emerald-600 mb-1">Email</div>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div>
                <div className="text-xs text-emerald-600 mb-1">Yangi parol</div>
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
              </div>
            </>
          )}
        </div>
        <Button onClick={() => updateProfile.mutate()}>Saqlash</Button>
      </div>
    </div>
  );
}
