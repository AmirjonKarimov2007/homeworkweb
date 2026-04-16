"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { getUser } from "@/lib/auth";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader } from "@/components/page-header";
import { paymentStatusLabel } from "@/lib/labels";
import { useMounted } from "@/lib/use-mounted";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { Badge } from "@/components/ui/badge";
import { fileUrl } from "@/lib/file-url";
import { formatMoney, parseMoney, formatMoneyDisplay } from "@/lib/format";

const adminTabs = [
  { key: "overdue", label: "Qarzdorlar", status: "OVERDUE" },
  { key: "partial", label: "Qisman tolaganlar", status: "PARTIAL" },
  { key: "paid", label: "Tolanganlar", status: "PAID" },
  { key: "all", label: "Barchasi", status: null },
  { key: "receipts", label: "Cheklar", status: null },
];

function statusTone(status: string) {
  if (status === "PAID") return "bg-emerald-100 text-emerald-800";
  if (status === "PARTIAL") return "bg-amber-100 text-amber-800";
  return "bg-rose-100 text-rose-800";
}

function rowTone(status: string) {
  if (status === "PAID") return "bg-emerald-50/70";
  if (status === "PARTIAL") return "bg-amber-50/70";
  return "bg-rose-50/70";
}

export default function PaymentsPage() {
  const mounted = useMounted();
  const user = typeof window !== "undefined" ? getUser() : null;
  const isAdmin = user?.role === "SUPER_ADMIN" || user?.role === "ADMIN";
  const isStudent = user?.role === "STUDENT";
  const qc = useQueryClient();
  const { addToast } = useToast();

  const [tab, setTab] = useState("overdue");
  const [payOpen, setPayOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<any | null>(null);
  const [payAmount, setPayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("cash");
  const [payNote, setPayNote] = useState("");

  const [receiptOpen, setReceiptOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<any | null>(null);
  const [receiptAmount, setReceiptAmount] = useState("");
  const [receiptNote, setReceiptNote] = useState("");
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [confirmAmounts, setConfirmAmounts] = useState<Record<number, string>>({});

  const activeTab = adminTabs.find((t) => t.key === tab);
  const statusParam = activeTab?.status || undefined;

  const { data: adminInvoices } = useQuery({
    queryKey: ["payments", statusParam, tab],
    enabled: mounted && isAdmin && tab !== "receipts",
    queryFn: async () => {
      const url = statusParam ? `/payments?status=${statusParam}` : "/payments";
      return (await api.get(url)).data.data;
    },
  });

  const { data: receipts } = useQuery({
    queryKey: ["receipts"],
    enabled: mounted && isAdmin && tab === "receipts",
    queryFn: async () => (await api.get("/payments/receipts")).data.data,
  });

  const { data: students } = useQuery({
    queryKey: ["students-lite"],
    enabled: mounted && isAdmin,
    queryFn: async () => (await api.get("/students?size=1000")).data.data,
  });

  const { data: groups } = useQuery({
    queryKey: ["groups-lite"],
    enabled: mounted && isAdmin,
    queryFn: async () => (await api.get("/groups?size=1000")).data.data,
  });

  const { data: transactions } = useQuery({
    queryKey: ["payment-transactions", selectedInvoice?.id],
    enabled: mounted && isAdmin && !!selectedInvoice?.id,
    queryFn: async () => (await api.get(`/payments/transactions?invoice_id=${selectedInvoice.id}`)).data.data,
  });

  const { data: studentInvoices } = useQuery({
    queryKey: ["payments-mine"],
    enabled: mounted && isStudent,
    queryFn: async () => (await api.get("/payments/mine")).data.data,
  });

  const generateMonthly = useMutation({
    mutationFn: async () => api.post("/payments/generate-monthly"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payments"] });
      addToast({ title: "Yaratildi", description: "Oylik tolovlar yaratildi." });
    },
  });

  const payInvoice = useMutation({
    mutationFn: async () => {
      if (!selectedInvoice) return;
      return api.post(`/payments/${selectedInvoice.id}/pay`, {
        amount: Number(payAmount),
        payment_method: payMethod,
        note: payNote || null,
      });
    },
    onSuccess: () => {
      setPayOpen(false);
      setPayAmount("");
      setPayMethod("cash");
      setPayNote("");
      qc.invalidateQueries({ queryKey: ["payments"] });
      qc.invalidateQueries({ queryKey: ["payment-transactions"] });
      addToast({ title: "Tolov qabul qilindi", description: "Invoice yangilandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Tolov qabul qilinmadi." });
    },
  });

  const uploadReceipt = useMutation({
    mutationFn: async () => {
      if (!selectedPayment || !receiptFile) return;
      const fd = new FormData();
      fd.append("file", receiptFile);
      if (receiptAmount) fd.append("amount", receiptAmount);
      if (receiptNote) fd.append("note", receiptNote);
      return api.post(`/payments/${selectedPayment.id}/receipt`, fd);
    },
    onSuccess: () => {
      setReceiptOpen(false);
      setSelectedPayment(null);
      setReceiptAmount("");
      setReceiptNote("");
      setReceiptFile(null);
      qc.invalidateQueries({ queryKey: ["payments-mine"] });
      addToast({ title: "Yuborildi", description: "Chek yuborildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Chek yuborilmadi." });
    },
  });

  const confirmReceipt = useMutation({
    mutationFn: async (receipt: any) => {
      const fd = new FormData();
      const amount = confirmAmounts[receipt.id] || receipt.amount || "0";
      fd.append("amount_paid", amount);
      return api.post(`/payments/receipts/${receipt.id}/confirm`, fd);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["receipts"] });
      qc.invalidateQueries({ queryKey: ["payments"] });
      addToast({ title: "Tasdiqlandi", description: "Tolov tasdiqlandi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Chek tasdiqlanmadi." });
    },
  });

  const rejectReceipt = useMutation({
    mutationFn: async (receiptId: number) => api.post(`/payments/receipts/${receiptId}/reject`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["receipts"] });
      addToast({ title: "Rad etildi", description: "Chek rad etildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Chek rad etilmadi." });
    },
  });

  if (!mounted) return null;

  const adminItems = adminInvoices?.items || [];
  const receiptItems = receipts?.items || [];
  const studentMap = new Map((students?.items || []).map((s: any) => [s.id, s.full_name]));
  const groupMap = new Map((groups?.items || []).map((g: any) => [g.id, g.name]));

  const sortedStudentInvoices = (studentInvoices || []).slice().sort((a: any, b: any) => {
    if (a.billing_year !== b.billing_year) return b.billing_year - a.billing_year;
    return b.billing_month - a.billing_month;
  });
  const currentInvoice = sortedStudentInvoices.find((i: any) => i.status !== "PAID") || sortedStudentInvoices[0];

  return (
    <div className="space-y-4">
      <PageHeader title="Tolovlar" description="Tolovlar tarixi va holati." />

      {isAdmin && (
        <div className="card p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {adminTabs.map((t) => (
              <Button
                key={t.key}
                variant={tab === t.key ? "default" : "outline"}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </Button>
            ))}
          </div>
          <Button onClick={() => generateMonthly.mutate()} variant="outline">Oylik tolovlarni yaratish</Button>
        </div>
      )}

      {isStudent && currentInvoice && (
        <div className="card p-4">
          <div className="text-sm text-emerald-700">Joriy tolov</div>
          <div className="mt-2 flex flex-wrap items-center gap-4">
            <div className="text-lg font-semibold text-emerald-900">{formatMoneyDisplay(currentInvoice.amount_due)}</div>
            <Badge className="bg-emerald-100 text-emerald-800">{paymentStatusLabel[currentInvoice.status] || currentInvoice.status}</Badge>
            <div className="text-sm text-slate-600">Muddat: {currentInvoice.due_date}</div>
            <div className="text-sm text-slate-600">Qoldiq: {formatMoneyDisplay(currentInvoice.remaining_amount)}</div>
          </div>
          <div className="mt-2 text-xs text-slate-500">Tolov faqat admin tomonidan tasdiqlanadi.</div>
        </div>
      )}

      {isStudent && (
        <div className="card p-4">
          <div className="text-sm font-medium text-emerald-900 mb-2">Tolovlar tarixi</div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Oy</TableHead>
                <TableHead>Qarz</TableHead>
                <TableHead className="hidden md:table-cell">Tolangan</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Amal</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedStudentInvoices.map((p: any) => (
                <TableRow key={p.id}>
                  <TableCell>{p.month}</TableCell>
                  <TableCell>{formatMoneyDisplay(p.amount_due)}</TableCell>
                  <TableCell className="hidden md:table-cell">{formatMoneyDisplay(p.amount_paid)}</TableCell>
                  <TableCell>{paymentStatusLabel[p.status] || p.status}</TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      onClick={() => {
                        setSelectedPayment(p);
                        setReceiptOpen(true);
                      }}
                    >
                      Chek yuborish
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {sortedStudentInvoices.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-slate-500">Tolovlar topilmadi.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {isAdmin && tab !== "receipts" && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Talaba</TableHead>
              <TableHead className="hidden md:table-cell">Guruh</TableHead>
              <TableHead className="hidden md:table-cell">Oy</TableHead>
              <TableHead>Qarz</TableHead>
              <TableHead className="hidden md:table-cell">Tolangan</TableHead>
              <TableHead className="hidden md:table-cell">Qoldiq</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Amal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {adminItems.map((p: any) => (
              <TableRow key={p.id} className={tab === "all" ? rowTone(p.status) : ""}>
                <TableCell>{p.student_name || studentMap.get(p.student_id) || p.student_id}</TableCell>
                <TableCell className="hidden md:table-cell">{p.group_name || groupMap.get(p.group_id) || "-"}</TableCell>
                <TableCell className="hidden md:table-cell">{p.month}</TableCell>
                <TableCell>{formatMoneyDisplay(p.amount_due)}</TableCell>
                <TableCell className="hidden md:table-cell">{formatMoneyDisplay(p.amount_paid)}</TableCell>
                <TableCell className="hidden md:table-cell">{formatMoneyDisplay(p.remaining_amount)}</TableCell>
                <TableCell>
                  <Badge className={statusTone(p.status)}>
                    {paymentStatusLabel[p.status] || p.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedInvoice(p);
                      setPayOpen(true);
                    }}
                  >
                    Tolov qabul qilish
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {adminItems.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-slate-500">Tolovlar topilmadi.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}

      {isAdmin && tab === "receipts" && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Talaba</TableHead>
              <TableHead className="hidden md:table-cell">Tolov ID</TableHead>
              <TableHead>Summa</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Fayl</TableHead>
              <TableHead>Amal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {receiptItems.map((r: any) => (
              <TableRow key={r.id}>
                <TableCell>{studentMap.get(r.student_id) || r.student_id}</TableCell>
                <TableCell className="hidden md:table-cell">{r.payment_id}</TableCell>
                <TableCell>
                  <Input
                    value={formatMoney(confirmAmounts[r.id] ?? r.amount ?? "")}
                    onChange={(e) => {
                      const raw = parseMoney(e.target.value);
                      setConfirmAmounts((prev) => ({ ...prev, [r.id]: raw }));
                    }}
                    className="h-8"
                  />
                </TableCell>
                <TableCell>
                  <Badge className={r.status === "CONFIRMED" ? "bg-emerald-100 text-emerald-800" : r.status === "REJECTED" ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"}>
                    {r.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <a className="text-emerald-700 underline" href={fileUrl(r.receipt_path)}>
                    Fayl
                  </a>
                </TableCell>
                <TableCell className="flex gap-2">
                  <Button
                    size="sm"
                    disabled={r.status !== "PENDING_REVIEW"}
                    onClick={() => confirmReceipt.mutate(r)}
                  >
                    Tasdiqlash
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={r.status !== "PENDING_REVIEW"}
                    onClick={() => rejectReceipt.mutate(r.id)}
                  >
                    Rad etish
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {receiptItems.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500">Cheklar topilmadi.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}

      <Dialog open={payOpen} onOpenChange={setPayOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tolov qabul qilish</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Input
              placeholder="Summa"
              value={formatMoney(payAmount)}
              onChange={(e) => setPayAmount(parseMoney(e.target.value))}
            />
            <select
              className="w-full rounded-xl border border-emerald-100 p-2 text-sm"
              value={payMethod}
              onChange={(e) => setPayMethod(e.target.value)}
            >
              <option value="cash">Naqd</option>
              <option value="card">Karta</option>
              <option value="transfer">Perevod</option>
            </select>
            <Input placeholder="Izoh (ixtiyoriy)" value={payNote} onChange={(e) => setPayNote(e.target.value)} />
            <Button
              onClick={() => {
                if (!payAmount) {
                  addToast({ title: "Summa kerak", description: "Tolov summasini kiriting." });
                  return;
                }
                payInvoice.mutate();
              }}
            >
              Saqlash
            </Button>
            {transactions && transactions.length > 0 && (
              <div className="pt-2">
                <div className="text-xs uppercase text-slate-500 mb-2">Tolov tarixi</div>
                <div className="space-y-1 text-sm">
                  {transactions.map((t: any) => (
                    <div key={t.id} className="flex items-center justify-between rounded-lg bg-slate-50 p-2">
                      <div>{formatMoneyDisplay(t.amount)} {t.payment_method}</div>
                      <div className="text-xs text-slate-500">{t.created_at}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={receiptOpen} onOpenChange={setReceiptOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Chek yuborish</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Input
              placeholder="Summa (ixtiyoriy)"
              value={formatMoney(receiptAmount)}
              onChange={(e) => setReceiptAmount(parseMoney(e.target.value))}
            />
            <Input placeholder="Izoh (ixtiyoriy)" value={receiptNote} onChange={(e) => setReceiptNote(e.target.value)} />
            <Input type="file" onChange={(e) => setReceiptFile(e.target.files?.[0] || null)} />
            <Button
              onClick={() => {
                if (!receiptFile) {
                  addToast({ title: "Fayl kerak", description: "Chek faylini tanlang." });
                  return;
                }
                uploadReceipt.mutate();
              }}
            >
              Yuborish
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
