"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { roleLabel } from "@/lib/labels";
import { useToast } from "@/components/ui/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

export default function StudentsPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [groupIds, setGroupIds] = useState<number[]>([]);
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [editFullName, setEditFullName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editPassword, setEditPassword] = useState("");
  const [editGroupIds, setEditGroupIds] = useState<number[]>([]);

  const { data } = useQuery({
    queryKey: ["students"],
    queryFn: async () => (await api.get("/students")).data.data,
  });

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: async () => (await api.get("/groups")).data.data,
  });

  const { data: studentGroups } = useQuery({
    queryKey: ["student-groups", editing?.id],
    enabled: !!editing?.id,
    queryFn: async () => (await api.get(`/students/${editing.id}/groups`)).data.data,
  });

  const toggleGroup = (id: number) => {
    setGroupIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const create = useMutation({
    mutationFn: async () =>
      api.post("/students", {
        full_name: fullName,
        phone,
        email: email || null,
        password: password || "Student123!@#",
        group_ids: groupIds,
      }),
    onSuccess: (res: any) => {
      setFullName("");
      setPhone("");
      setEmail("");
      setPassword("");
      setGroupIds([]);
      qc.invalidateQueries({ queryKey: ["students"] });
      setOpen(false);
      addToast({
        title: "Talaba yaratildi",
        description: `Parol: ${res.data.data.password || password}`,
      });
    },
    onError: (err: any) => {
      addToast({
        title: "Xatolik",
        description: err?.response?.data?.detail || "Talaba yaratilmadi.",
      });
    },
  });

  const saveEdit = useMutation({
    mutationFn: async () => {
      if (!editing) return;
      await api.patch(`/students/${editing.id}`, {
        full_name: editFullName || editing.full_name,
        phone: editPhone || editing.phone,
        email: editEmail || null,
        password: editPassword || undefined,
      });
      await api.put(`/students/${editing.id}/groups`, { group_ids: editGroupIds });
    },
    onSuccess: () => {
      setEditOpen(false);
      setEditing(null);
      setEditPassword("");
      qc.invalidateQueries({ queryKey: ["students"] });
      addToast({ title: "Yangilandi", description: "Talaba ma’lumotlari yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Talaba yangilanmadi." });
    },
  });

  const removeStudent = useMutation({
    mutationFn: async (studentId: number) => api.delete(`/students/${studentId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      addToast({ title: "Ochirildi", description: "Talaba o'chirildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Talaba o'chirilmadi." });
    },
  });

  useEffect(() => {
    if (editing) {
      setEditFullName(editing.full_name || "");
      setEditPhone(editing.phone || "");
      setEditEmail(editing.email || "");
      setEditPassword("");
    }
  }, [editing]);

  useEffect(() => {
    if (studentGroups) {
      const active = studentGroups
        .filter((g: any) => g.status === "ACTIVE")
        .map((g: any) => g.group_id);
      setEditGroupIds(active);
    }
  }, [studentGroups]);

  return (
    <div className="space-y-4">
      <PageHeader title="Talabalar" description="Talabalar ro‘yxati va qo‘shish." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">Talaba qo‘shish va guruhga biriktirish</div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Talaba qo‘shish</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Yangi talaba</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                <Input placeholder="Ism va familiya" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                <Input placeholder="Telefon" value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                <Input placeholder="Email (ixtiyoriy)" value={email} onChange={(e) => setEmail(e.target.value)} />
                <Input
                  type="password"
                  placeholder="Parol (ixtiyoriy)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div>
                <div className="text-sm font-medium text-emerald-900 mb-2">Guruhlar (kamida bittasi kerak)</div>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                  {groups?.items?.map((g: any) => (
                    <label key={g.id} className="flex items-center gap-2 rounded-xl border border-emerald-100 bg-white px-3 py-2 text-sm">
                      <input
                        type="checkbox"
                        checked={groupIds.includes(g.id)}
                        onChange={() => toggleGroup(g.id)}
                        className="accent-emerald-600"
                      />
                      <span>{g.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <Button
                onClick={() => {
                  if (!fullName || !phone) {
                    addToast({ title: "Ma’lumot yetarli emas", description: "Ism va telefonni kiriting." });
                    return;
                  }
                  if (groupIds.length === 0) {
                    addToast({ title: "Guruh tanlang", description: "Kamida bitta guruhni belgilang." });
                    return;
                  }
                  create.mutate();
                }}
              >
                Saqlash
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Ism</TableHead>
            <TableHead>Telefon</TableHead>
            <TableHead>Rol</TableHead>
            <TableHead>Amal</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items?.map((s: any) => (
            <TableRow key={s.id}>
              <TableCell>{s.full_name}</TableCell>
              <TableCell>{s.phone}</TableCell>
              <TableCell>{roleLabel[s.role] || s.role}</TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditing(s);
                      setEditOpen(true);
                    }}
                  >
                    Tahrirlash
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => {
                      if (confirm("Talabani o'chirmoqchimisiz?")) {
                        removeStudent.mutate(s.id);
                      }
                    }}
                  >
                    O'chirish
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Talabani tahrirlash</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <Input placeholder="Ism va familiya" value={editFullName} onChange={(e) => setEditFullName(e.target.value)} />
              <Input placeholder="Telefon" value={editPhone} onChange={(e) => setEditPhone(e.target.value)} />
            </div>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <Input placeholder="Email (ixtiyoriy)" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} />
              <Input
                type="password"
                placeholder="Parol (ixtiyoriy)"
                value={editPassword}
                onChange={(e) => setEditPassword(e.target.value)}
              />
            </div>
            <div>
              <div className="text-sm font-medium text-emerald-900 mb-2">Guruhlar</div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                {groups?.items?.map((g: any) => (
                  <label key={g.id} className="flex items-center gap-2 rounded-xl border border-emerald-100 bg-white px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      checked={editGroupIds.includes(g.id)}
                      onChange={() =>
                        setEditGroupIds((prev) =>
                          prev.includes(g.id) ? prev.filter((x) => x !== g.id) : [...prev, g.id]
                        )
                      }
                      className="accent-emerald-600"
                    />
                    <span>{g.name}</span>
                  </label>
                ))}
              </div>
            </div>
            <Button
              onClick={() => {
                if (!editFullName || !editPhone) {
                  addToast({ title: "Ma’lumot yetarli emas", description: "Ism va telefonni kiriting." });
                  return;
                }
                saveEdit.mutate();
              }}
            >
              Saqlash
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
