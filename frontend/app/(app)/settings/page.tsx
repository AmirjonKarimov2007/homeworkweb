"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useToast } from "@/components/ui/use-toast";
import { getUser } from "@/lib/auth";

export default function SettingsPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const user = typeof window !== "undefined" ? getUser() : null;
  const isSuper = user?.role === "SUPER_ADMIN";

  const [key, setKey] = useState("");
  const [value, setValue] = useState("");

  const { data } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => (await api.get("/settings")).data.data,
  });

  const saveSetting = useMutation({
    mutationFn: async () => api.post("/settings", { key, value: value || null }),
    onSuccess: () => {
      setKey("");
      setValue("");
      qc.invalidateQueries({ queryKey: ["settings"] });
      addToast({ title: "Saqlangan", description: "Sozlama yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Sozlama saqlanmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Sozlamalar" description="Tizim sozlamalarini boshqarish." />

      {isSuper && (
        <div className="card p-4 space-y-3">
          <div className="text-sm font-semibold text-emerald-900">Yangi sozlama</div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <Input placeholder="Key" value={key} onChange={(e) => setKey(e.target.value)} />
            <Input placeholder="Value" value={value} onChange={(e) => setValue(e.target.value)} />
          </div>
          <Button
            onClick={() => {
              if (!key) {
                addToast({ title: "Key kerak", description: "Sozlama kalitini kiriting." });
                return;
              }
              saveSetting.mutate();
            }}
          >
            Saqlash
          </Button>
        </div>
      )}

      <div className="card p-4">
        <div className="text-sm font-semibold text-emerald-900 mb-2">Mavjud sozlamalar</div>
        <div className="space-y-2">
          {data?.map((s: any) => (
            <div key={s.key} className="flex items-center justify-between rounded-xl border border-emerald-100 bg-white px-4 py-2 text-sm">
              <div className="font-medium text-emerald-900">{s.key}</div>
              <div className="text-emerald-700">{s.value ?? "-"}</div>
            </div>
          ))}
          {!data || data.length === 0 ? (
            <div className="text-sm text-emerald-700">Hozircha sozlamalar yo‘q.</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
