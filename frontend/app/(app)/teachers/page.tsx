"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { roleLabel } from "@/lib/labels";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { Badge } from "@/components/ui/badge";

export default function TeachersPage() {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [open, setOpen] = useState(false);
  const [groupIds, setGroupIds] = useState<number[]>([]);
  const [editingTeacher, setEditingTeacher] = useState<any>(null);
  const [editStep, setEditStep] = useState<"basic" | "password">("basic");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [tempPassword, setTempPassword] = useState("");

  const { data } = useQuery({
    queryKey: ["teachers"],
    queryFn: async () => {
      const res = await api.get("/teachers");
      return res.data?.data || { items: [] };
    },
  });

  const { data: groups, isLoading: groupsLoading } = useQuery({
    queryKey: ["groups"],
    queryFn: async () => {
      try {
        const res = await api.get("/groups", { params: { page: 1, size: 100 } });
        console.log("Groups response:", res.data);
        const groupsData = res.data?.data || { items: [] };
        console.log("Groups data:", groupsData);
        return groupsData;
      } catch (error) {
        console.error("Groups fetch error:", error);
        return { items: [] };
      }
    },
  });

  const create = useMutation({
    mutationFn: async () => {
      const payload = { full_name: fullName, phone, password: password || "Teacher123!@", group_ids: groupIds };
      return api.post("/teachers", payload);
    },
    onSuccess: () => {
      setFullName("");
      setPhone("");
      setPassword("");
      setConfirmPassword("");
      setGroupIds([]);
      qc.invalidateQueries({ queryKey: ["teachers"] });
      setOpen(false);
      addToast({ title: "O‘qituvchi qo‘shildi", description: "Yangi o‘qituvchi yaratildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "O‘qituvchi qo‘shilmadi." });
    },
  });

  const updateTeacher = useMutation({
    mutationFn: async () => {
      const payload: any = {
        full_name: fullName,
        phone: phone
      };

      // Only add password if provided and valid
      if (newPassword && newPassword.length >= 6) {
        payload.password = newPassword;
      }

      await api.patch(`/teachers/${editingTeacher.id}`, payload);

      // Update groups
      if (groupIds.length > 0) {
        await api.patch(`/teachers/${editingTeacher.id}/groups`, groupIds);
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teachers"] });
      setOpen(false);
      setEditingTeacher(null);
      setEditStep("basic");
      setFullName("");
      setPhone("");
      setGroupIds([]);
      setNewPassword("");
      setConfirmNewPassword("");
      addToast({ title: "O’qituvchi yangilandi", description: "O’qituvchi ma’lumotlari yangilandi." });
    },
    onError: (err: any) => {
      console.error("Teacher update error:", err);
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "O’qituvchi yangilanmadi." });
    },
  });

  const updatePasswordOnly = useMutation({
    mutationFn: async () => {
      if (newPassword.length < 6) {
        addToast({ title: "Xatolik", description: "Parol kamida 6 ta belgidan iborat bo’lishi kerak." });
        return;
      }
      if (newPassword !== confirmNewPassword) {
        addToast({ title: "Xatolik", description: "Parollar mos emas." });
        return;
      }

      await api.post(`/users/${editingTeacher.id}/password`, { password: newPassword });
    },
    onSuccess: () => {
      setNewPassword("");
      setConfirmNewPassword("");
      addToast({ title: "Parol yangilandi", description: "O’qituvchi paroli yangilandi." });
    },
    onError: (err: any) => {
      console.error("Password update error:", err);
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Parol yangilanmadi." });
    },
  });


  const showPassword = useMutation({
    mutationFn: async (teacherId: number) => api.get(`/users/${teacherId}/password`),
    onSuccess: (data) => {
      addToast({ title: "Parol", description: data.data.data.password });
      setTempPassword(data.data.data.password);
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Parol ko'rsatilmadi." });
    },
  });

  const removeTeacher = useMutation({
    mutationFn: async (teacherId: number) => api.delete(`/teachers/${teacherId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["teachers"] });
      addToast({ title: "Ochirildi", description: "O‘qituvchi o‘chirildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "O‘qituvchi o‘chirilmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="O‘qituvchilar" description="O‘qituvchilar ro‘yxati va qo‘shish." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">O’qituvchilar ro’yxatini to’ldiring</div>
        <Dialog open={open} onOpenChange={(newOpen) => {
          setOpen(newOpen);
          if (!newOpen) {
            // Reset all state when dialog closes
            setFullName("");
            setPhone("");
            setPassword("");
            setConfirmPassword("");
            setGroupIds([]);
            setEditingTeacher(null);
            setEditStep("basic");
            setNewPassword("");
            setConfirmNewPassword("");
          }
        }}>
          <DialogTrigger asChild>
            <Button>O’qituvchi qo’shish</Button>
          </DialogTrigger>
          <DialogContent className="max-w-md sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>{editingTeacher ? "O‘qituvchi yangilash" : "Yangi o‘qituvchi"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Input placeholder="Ism va familiya" value={fullName} onChange={(e) => setFullName(e.target.value)} />
              <Input placeholder="Telefon" value={phone} onChange={(e) => setPhone(e.target.value)} />
              {!editingTeacher && (
                <>
                  <Input type="password" placeholder="Parol (bo'sh qoldirsangiz 'Teacher123!@' beriladi)" value={password} onChange={(e) => setPassword(e.target.value)} />
                  <Input type="password" placeholder="Parolni tasdiqlang" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
                  {password && confirmPassword && password !== confirmPassword && (
                    <p className="text-sm text-red-600">Parollar mos emas</p>
                  )}
                </>
              )}

              {editingTeacher && (
                <div className="border-t pt-3 bg-yellow-50/50 p-3 rounded-lg">
                  <div className="text-sm font-medium text-emerald-900 mb-2">
                    <span className="text-amber-600">⚠️ Diqqat:</span> Parolni yangilgandan keyin o'qituvchi tizimga <strong className="text-amber-700">avvalgi paroli bilan</strong> qayta kirish shart.
                  </div>
                  <p className="text-xs text-gray-600 mb-3">
                    Shunda yangi parol bilan tizimga kirish mumkin bo'ladi.
                  </p>
                  <Input type="password" placeholder="Yangi parolni kiriting" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                  <Input type="password" placeholder="Parolni tasdiqlang" value={confirmNewPassword} onChange={(e) => setConfirmNewPassword(e.target.value)} />
                  {newPassword && confirmNewPassword && newPassword !== confirmNewPassword && (
                    <p className="text-sm text-red-600">Parollar mos emas</p>
                  )}
                </div>
              )}
              <div>
                <div className="text-sm font-medium text-emerald-900 mb-2">Guruhlar (kamida bittasi kerak)</div>
                {groupsLoading && <p className="text-sm text-gray-500">Guruhlar yuklanmoqda...</p>}
                {!groupsLoading && (!groups?.items || groups.items.length === 0) && (
                  <p className="text-sm text-red-600">Guruhlar mavjud emas yoki yuklashda xatolik</p>
                )}
                {!groupsLoading && groups?.items && groups.items.length > 0 && (
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
                    {groups.items.map((g: any) => (
                      <label key={g.id} className="flex items-center gap-2 rounded-xl border border-emerald-100 bg-white px-3 py-2 text-sm">
                        <input
                          type="checkbox"
                          checked={groupIds.includes(g.id)}
                          onChange={() =>
                            setGroupIds((prev) =>
                              prev.includes(g.id) ? prev.filter((x) => x !== g.id) : [...prev, g.id]
                            )
                          }
                          className="accent-emerald-600"
                        />
                        <span>{g.name}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
              <Button
                onClick={() => {
                  // Validate required fields
                  if (!fullName || !phone) {
                    addToast({ title: "Ma’lumot yetarli emas", description: "Ism va telefonni kiriting." });
                    return;
                  }
                  if (groupIds.length === 0) {
                    addToast({ title: "Guruh tanlang", description: "Kamida bitta guruhni belgilang." });
                    return;
                  }

                  // Validate password if editing
                  if (editingTeacher && newPassword) {
                    if (newPassword.length < 6) {
                      addToast({ title: "Parol juda qisqa", description: "Parol kamida 6 ta belgidan iborat bo’lishi kerak." });
                      return;
                    }
                    if (newPassword !== confirmNewPassword) {
                      addToast({ title: "Parollar mos emas", description: "Parol va tasdiqlash mos kelmayapti." });
                      return;
                    }
                  }

                  // Create or update teacher
                  if (editingTeacher) {
                    updateTeacher.mutate();
                  } else {
                    create.mutate();
                  }
                }}
              >
                {editingTeacher ? "Saqlash" : "Saqlash"}
              </Button>
              {editingTeacher && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setFullName("");
                    setPhone("");
                    setGroupIds([]);
                    setEditingTeacher(null);
                    setNewPassword("");
                    setConfirmNewPassword("");
                    setOpen(false);
                  }}
                >
                  Bekor qilish
                </Button>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Mobile Cards View */}
      <div className="md:hidden space-y-4">
        {data?.items?.map((t: any) => (
          <div key={t.id} className="card p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold">{t.full_name}</h3>
                <p className="text-sm text-gray-600">{t.phone}</p>
              </div>
              <Badge variant="secondary">{roleLabel[t.role] || t.role}</Badge>
            </div>

            {t.teacher_groups && t.teacher_groups.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-gray-700 mb-1">Guruhlar:</p>
                <div className="flex flex-wrap gap-1">
                  {t.teacher_groups.map((g: any) => (
                    <Badge key={g.id} variant="outline" className="text-xs">
                      {g.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 flex-wrap">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setFullName(t.full_name);
                  setPhone(t.phone);
                  setGroupIds(t.teacher_groups?.map((g: any) => g.id) || []);
                  setEditingTeacher(t);
                  setOpen(true);
                }}
              >
                Tahrirlash
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditingTeacher(t);
                  setNewPassword("");
                  setConfirmNewPassword("");
                  setShowPasswordDialog(true);
                }}
              >
                Parol
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  if (confirm("O’qituvchini o’chirmoqchimisiz?")) {
                    removeTeacher.mutate(t.id);
                  }
                }}
              >
                O’chirish
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="hidden sm:table-cell">Ism</TableHead>
              <TableHead className="hidden sm:table-cell">Telefon</TableHead>
              <TableHead className="hidden sm:table-cell">Rol</TableHead>
              <TableHead className="hidden lg:table-cell">Guruhlar</TableHead>
              <TableHead className="text-right">Amal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items?.map((t: any) => (
              <TableRow key={t.id}>
                <TableCell className="font-medium sm:hidden">
                  {t.full_name}
                </TableCell>
                <TableCell className="hidden sm:table-cell">{t.full_name}</TableCell>
                <TableCell className="hidden sm:table-cell">{t.phone}</TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Badge variant="secondary">{roleLabel[t.role] || t.role}</Badge>
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <div className="flex flex-wrap gap-1">
                    {t.teacher_groups?.map((g: any) => (
                      <Badge key={g.id} variant="outline" className="text-xs">
                        {g.name}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex flex-wrap gap-1 sm:gap-2 justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      className="hidden sm:inline-flex"
                      onClick={() => {
                        setFullName(t.full_name);
                        setPhone(t.phone);
                        setGroupIds(t.teacher_groups?.map((g: any) => g.id) || []);
                        setEditingTeacher(t);
                        setOpen(true);
                      }}
                    >
                      Tahrirlash
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => {
                        if (confirm("O‘qituvchini o‘chirmoqchimisiz?")) {
                          removeTeacher.mutate(t.id);
                        }
                      }}
                    >
                      O‘chirish
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Password Update Dialog */}
      {editingTeacher && (
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Parolni yangilash</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">O'qituvchi: <strong>{editingTeacher.full_name}</strong></p>
              <p className="text-xs text-gray-500 mb-2">
                Diqqat: Parolni o'zgartirgandan keyin o'qituvchi tizimga <strong>avvalgi paroli bilan</strong> qayta kirmog'i bo'lishi kerak. Shunda yangi parol bilan tizimga kirish mumkin bo'ladi.
              </p>
              <Input type="password" placeholder="Yangi parolni kiriting" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              <Input type="password" placeholder="Parolni tasdiqlang" value={confirmNewPassword} onChange={(e) => setConfirmNewPassword(e.target.value)} />
              {newPassword && confirmNewPassword && newPassword !== confirmNewPassword && (
                <p className="text-sm text-red-600">Parollar mos emas</p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => {
                    // Validate password
                    if (!newPassword) {
                      addToast({ title: "Xatolik", description: "Parolni kiriting." });
                      return;
                    }
                    if (newPassword.length < 6) {
                      addToast({ title: "Xatolik", description: "Parol kamida 6 ta belgidan iborat bo'lishi kerak." });
                      return;
                    }
                    if (newPassword !== confirmNewPassword) {
                      addToast({ title: "Xatolik", description: "Parollar mos emas." });
                      return;
                    }
                    // Update password (using users endpoint)
                    api.post(`/users/${editingTeacher.id}/password`, { password: newPassword })
                      .then(() => {
                        setNewPassword("");
                        setConfirmNewPassword("");
                        setShowPasswordDialog(false);
                        addToast({ title: "Parol yangilandi", description: "O'qituvchi paroli yangilandi. O'qituvchi avvalgi paroli bilan tizimga kira oladi." });
                        qc.invalidateQueries({ queryKey: ["teachers"] });
                      })
                      .catch((err: any) => {
                        const errorDetail = err?.response?.data?.detail || "Parol yangilanmadi";
                        const errorStatus = err?.response?.status;

                        if (errorStatus === 404) {
                          addToast({ title: "Backend xatosi", description: "Backend serverda password endpointi topilmadi. Backendni qayta ishlating." });
                        } else {
                          addToast({ title: "Xatolik", description: errorDetail });
                        }
                      });
                  }}
                  disabled={!newPassword}
                >
                  Parolni yangilash
                </Button>
                <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>
                  Bekor qilish
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
