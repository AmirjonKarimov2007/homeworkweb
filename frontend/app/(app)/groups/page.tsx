"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/ui/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { formatMoney, parseMoney } from "@/lib/format";

export default function GroupsPage() {
  const PAGE_SIZE = 10;
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [name, setName] = useState("");
  const [schedule, setSchedule] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [durationMonths, setDurationMonths] = useState("");
  const [monthlyFee, setMonthlyFee] = useState("");
  const [paymentDay, setPaymentDay] = useState("5");
  const [paymentRequired, setPaymentRequired] = useState(true);
  const [courseId, setCourseId] = useState("");
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [editName, setEditName] = useState("");
  const [editSchedule, setEditSchedule] = useState("");
  const [editStartDate, setEditStartDate] = useState("");
  const [editEndDate, setEditEndDate] = useState("");
  const [editDurationMonths, setEditDurationMonths] = useState("");
  const [editMonthlyFee, setEditMonthlyFee] = useState("");
  const [editPaymentDay, setEditPaymentDay] = useState("5");
  const [editPaymentRequired, setEditPaymentRequired] = useState(true);
  const [editCourseId, setEditCourseId] = useState("");
  const [page, setPage] = useState(1);

  const capitalize = (str: string) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  const { data } = useQuery({
    queryKey: ["groups", page],
    queryFn: async () => {
      const res = await api.get(`/groups?page=${page}&size=${PAGE_SIZE}`);
      return res.data?.data || { items: [] };
    },
  });

  const { data: coursesData } = useQuery({
    queryKey: ["courses"],
    queryFn: async () => {
      const res = await api.get("/courses/active");
      return res.data?.data || [];
    },
  });

  const courseItems = Array.isArray(coursesData)
    ? coursesData
    : Array.isArray(coursesData?.items)
      ? coursesData.items
      : [];

  const create = useMutation({
    mutationFn: async () =>
      api.post("/groups", {
        name,
        schedule_time: schedule || null,
        start_date: startDate || null,
        end_date: endDate || null,
        duration_months: durationMonths ? Number(durationMonths) : null,
        monthly_fee: monthlyFee ? Number(monthlyFee) : null,
        payment_day: paymentDay ? Number(paymentDay) : 5,
        is_payment_required: paymentRequired,
        course_id: Number(courseId),
      }),
    onSuccess: () => {
      setName("");
      setSchedule("");
      setStartDate("");
      setEndDate("");
      setDurationMonths("");
      setMonthlyFee("");
      setPaymentDay("5");
      setPaymentRequired(true);
      setCourseId("");
      qc.invalidateQueries({ queryKey: ["groups"] });
      setOpen(false);
      addToast({ title: "Guruh yaratildi", description: "Guruh muvaffaqiyatli qoshildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Guruh yaratilmadi." });
    },
  });

  const handleCourseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedCourseId = e.target.value;
    setCourseId(selectedCourseId);
    if (selectedCourseId) {
      const course = courseItems.find((c: any) => c.id === Number(selectedCourseId));
      if (course) {
        setMonthlyFee(String(course.monthly_fee));
        if (course.duration_months) {
          setDurationMonths(String(course.duration_months));
        }
      }
    } else {
      setMonthlyFee("");
      setDurationMonths("");
    }
  };

  const handleEditCourseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedCourseId = e.target.value;
    setEditCourseId(selectedCourseId);
    if (selectedCourseId) {
      const course = courseItems.find((c: any) => c.id === Number(selectedCourseId));
      if (course) {
        setEditMonthlyFee(String(course.monthly_fee));
        if (course.duration_months) {
          setEditDurationMonths(String(course.duration_months));
        }
      }
    } else {
      setEditMonthlyFee("");
      setEditDurationMonths("");
    }
  };

  useEffect(() => {
    if (editing) {
      setEditName(editing.name || "");
      setEditSchedule(editing.schedule_time || "");
      setEditStartDate(editing.start_date || "");
      setEditEndDate(editing.end_date || "");
      setEditDurationMonths(editing.duration_months?.toString() || "");
      setEditMonthlyFee(editing.monthly_fee?.toString() || "");
      setEditPaymentDay(editing.payment_day?.toString() || "5");
      setEditPaymentRequired(editing.is_payment_required ?? true);
      setEditCourseId(editing.course_id?.toString() || "");
    }
  }, [editing]);

  const removeGroup = useMutation({
    mutationFn: async (groupId: number) => api.delete(`/groups/${groupId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["groups"] });
      addToast({ title: "Ochirildi", description: "Guruh o'chirildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Guruh o'chirilmadi." });
    },
  });

  const saveEdit = useMutation({
    mutationFn: async () => {
      if (!editing) return;
      await api.patch(`/groups/${editing.id}`, {
        name: editName || editing.name,
        schedule_time: editSchedule || editing.schedule_time,
        start_date: editStartDate || editing.start_date,
        end_date: editEndDate || editing.end_date,
        duration_months: editDurationMonths ? Number(editDurationMonths) : editing.duration_months,
        monthly_fee: editMonthlyFee ? Number(editMonthlyFee) : editing.monthly_fee,
        payment_day: editPaymentDay ? Number(editPaymentDay) : editing.payment_day,
        is_payment_required: editPaymentRequired,
        course_id: Number(editCourseId) || editing.course_id,
      });
    },
    onSuccess: () => {
      setEditOpen(false);
      setEditing(null);
      setEditPaymentDay("5");
      qc.invalidateQueries({ queryKey: ["groups"] });
      addToast({ title: "Yangilandi", description: "Guruh ma'lumotlari yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Guruh yangilanmadi." });
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Guruhlar" description="Guruhlarni boshqarish va azolarni biriktirish." />

      <div className="card p-4 flex items-center justify-between">
        <div className="text-sm text-emerald-700">Yangi guruh yaratish</div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Guruh qoshish</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Yangi guruh</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Input placeholder="Guruh nomi" value={name} onChange={(e) => setName(e.target.value)} />
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={courseId}
                onChange={handleCourseChange}
              >
                <option value="">Kursni tanlang</option>
                {courseItems.map((c: any) => (
                  <option key={c.id} value={c.id}>
                    {c.name} - {formatMoney(c.monthly_fee)} so'm {c.duration_months ? `(${c.duration_months} oy)` : ""}
                  </option>
                ))}
              </select>
              <Input placeholder="Jadval (masalan 19:00)" value={schedule} onChange={(e) => setSchedule(e.target.value)} />
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
                <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
                <Input type="number" placeholder="Necha oy" value={durationMonths} onChange={(e) => setDurationMonths(e.target.value)} />
              </div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <Input
                  placeholder="Oylik tolov"
                  value={formatMoney(monthlyFee)}
                  onChange={(e) => setMonthlyFee(parseMoney(e.target.value))}
                />
                <Input type="number" placeholder="Tolov kuni (1-31)" value={paymentDay} onChange={(e) => setPaymentDay(e.target.value)} />
              </div>
              <label className="flex items-center gap-2 text-sm text-emerald-800">
                <input type="checkbox" checked={paymentRequired} onChange={(e) => setPaymentRequired(e.target.checked)} />
                Tolov talab qilinadi
              </label>
                <Button
                  onClick={() => {
                    if (!name) {
                      addToast({ title: "Guruh nomini kiriting", description: "Bosh nom bilan saqlab bolmaydi." });
                      return;
                    }
                    if (!courseId) {
                      addToast({ title: "Kursni tanlang", description: "Kurs tanlash majburiy." });
                      return;
                    }
                    if (!startDate || !endDate || !durationMonths) {
                      addToast({ title: "Muddatni kiriting", description: "Boshlanish, tugash va oylar soni kerak." });
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

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Guruhni tahrirlash</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input placeholder="Guruh nomi" value={editName} onChange={(e) => setEditName(e.target.value)} />
            <select
              className="w-full p-2 border border-gray-300 rounded-md"
              value={editCourseId}
              onChange={handleEditCourseChange}
            >
              <option value="">Kursni tanlang</option>
              {courseItems.map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.name} - {formatMoney(c.monthly_fee)} so'm {c.duration_months ? `(${c.duration_months} oy)` : ""}
                </option>
              ))}
            </select>
            <Input placeholder="Jadval (masalan 19:00)" value={editSchedule} onChange={(e) => setEditSchedule(e.target.value)} />
            <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
              <Input type="date" value={editStartDate} onChange={(e) => setEditStartDate(e.target.value)} />
              <Input type="date" value={editEndDate} onChange={(e) => setEditEndDate(e.target.value)} />
              <Input type="number" placeholder="Necha oy" value={editDurationMonths} onChange={(e) => setEditDurationMonths(e.target.value)} />
            </div>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
              <Input
                placeholder="Oylik tolov"
                value={formatMoney(editMonthlyFee)}
                onChange={(e) => setEditMonthlyFee(parseMoney(e.target.value))}
              />
              <Input type="number" placeholder="Tolov kuni (1-31)" value={editPaymentDay} onChange={(e) => setEditPaymentDay(e.target.value)} />
            </div>
            <label className="flex items-center gap-2 text-sm text-emerald-800">
              <input type="checkbox" checked={editPaymentRequired} onChange={(e) => setEditPaymentRequired(e.target.checked)} />
              Tolov talab qilinadi
            </label>
            <Button
              onClick={() => {
                if (!editName) {
                  addToast({ title: "Guruh nomini kiriting", description: "Bosh nom bilan saqlab bolmaydi." });
                  return;
                }
                if (!editCourseId) {
                  addToast({ title: "Kursni tanlang", description: "Kurs tanlash majburiy." });
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

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nomi</TableHead>
            <TableHead>Kurs</TableHead>
            <TableHead>Jadval</TableHead>
            <TableHead>Muddat</TableHead>
            <TableHead>Amal</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items?.map((g: any) => (
            <TableRow key={g.id}>
              <TableCell>
                <Link className="text-emerald-700 hover:underline" href={`/groups/${g.id}`}>
                  {capitalize(g.name)}
                </Link>
              </TableCell>
              <TableCell>{capitalize(g.course?.name || "-")}</TableCell>
              <TableCell>{g.schedule_time || "-"}</TableCell>
              <TableCell>
                {g.start_date ? `${g.start_date}  ${g.end_date || "-"}` : "-"}
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditing(g);
                      setEditOpen(true);
                    }}
                  >
                    Tahrirlash
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => {
                      if (confirm("Guruhni o'chirmoqchimisiz?")) {
                        removeGroup.mutate(g.id);
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
    </div>
  );
}
