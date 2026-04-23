"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useEffect, useMemo, useState } from "react";
import { fileUrl } from "@/lib/file-url";
import { Pencil, XCircle, Check } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

type FileAttachment = {
  id: number;
  file_name: string;
  file_path: string;
};

type AttachmentLink = {
  id: number;
  name: string;
  url: string;
};

function statusBadge(status?: string) {
  if (status === "REVIEWED" || status === "ACCEPTED") {
    return { label: "Tekshirildi", tone: "bg-emerald-100 text-emerald-800" };
  }
  if (status === "REVISION_REQUESTED") {
    return { label: "Qayta yuborish", tone: "bg-rose-100 text-rose-700" };
  }
  if (status === "LATE") {
    return { label: "Kechikkan", tone: "bg-orange-100 text-orange-800" };
  }
  if (status === "SUBMITTED") {
    return { label: "Bajarilgan", tone: "bg-amber-100 text-amber-800" };
  }
  return { label: "Yangi", tone: "bg-slate-100 text-slate-700" };
}

function isImageFile(name: string) {
  const lower = name.toLowerCase();
  return lower.endsWith(".png") || lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".gif") || lower.endsWith(".webp");
}

export default function LessonDetailPage() {
  const params = useParams();
  const lessonId = Number(params.id);
  const mounted = useMounted();
  const { addToast } = useToast();
  const qc = useQueryClient();
  const user = typeof window !== "undefined" ? getUser() : null;
  const isStudent = user?.role === "STUDENT";
  const canEdit = user?.role === "SUPER_ADMIN" || user?.role === "ADMIN" || user?.role === "TEACHER";

  const [hwTitle, setHwTitle] = useState("");
  const [hwInstructions, setHwInstructions] = useState("");
  const [hwDue, setHwDue] = useState("");
  const [lessonFile, setLessonFile] = useState<File | null>(null);
  const [homeworkFile, setHomeworkFile] = useState<File | null>(null);
  const [submissionText, setSubmissionText] = useState("");
  const [submissionFile, setSubmissionFile] = useState<File | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [tab, setTab] = useState<"homework" | "submissions">("homework");
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any | null>(null);
  const [selectedSubmission, setSelectedSubmission] = useState<any | null>(null);

  const { data: lesson } = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: async () => (await api.get(`/lessons/${lessonId}`)).data.data,
  });

  const { data: group } = useQuery({
    queryKey: ["group", lesson?.group_id],
    enabled: !!lesson?.group_id,
    queryFn: async () => (await api.get(`/groups/${lesson.group_id}`)).data.data,
  });

  const { data: lessonAttachments } = useQuery({
    queryKey: ["lesson-attachments", lessonId],
    queryFn: async () => (await api.get(`/lessons/${lessonId}/attachments`)).data.data,
  });

  const { data: homeworks } = useQuery({
    queryKey: ["lesson-homework", lessonId],
    queryFn: async () => (await api.get(`/homework?lesson_id=${lessonId}`)).data.data,
  });

  const homework = homeworks?.items?.[0] || null;

  const { data: homeworkAttachments } = useQuery({
    queryKey: ["homework-attachments", homework?.id],
    enabled: !!homework?.id,
    queryFn: async () => (await api.get(`/homework/${homework.id}/attachments`)).data.data,
  });

  const { data: students } = useQuery({
    queryKey: ["group-students", lesson?.group_id],
    enabled: mounted && !!lesson?.group_id && !isStudent,
    queryFn: async () => (await api.get(`/groups/${lesson.group_id}/students`)).data.data,
  });

  const { data: submissions } = useQuery({
    queryKey: ["homework-submissions", homework?.id],
    enabled: mounted && !!homework?.id && !isStudent,
    queryFn: async () => (await api.get(`/homework/${homework.id}/submissions`)).data.data,
  });

  const { data: myStatus } = useQuery({
    queryKey: ["my-homework-status", homework?.id],
    enabled: mounted && !!homework?.id && isStudent,
    queryFn: async () => (await api.get(`/homework/${homework.id}/my`)).data.data,
  });

  const submission = myStatus?.submission;

  useEffect(() => {
    if (!editMode) {
      setSubmissionText(submission?.text || "");
    }
    if (!submission) {
      setEditMode(false);
    }
  }, [submission?.id, editMode]);

  useEffect(() => {
    if (homework) {
      setHwTitle(homework.title || "");
      setHwInstructions(homework.instructions || "");
      setHwDue(homework.due_date ? new Date(homework.due_date).toISOString().slice(0, 16) : "");
    } else {
      setHwTitle("");
      setHwInstructions("");
      setHwDue("");
    }
  }, [homework?.id]);

  const createOrUpdateHomework = useMutation({
    mutationFn: async () => {
      if (homework) {
        // UPDATE existing homework
        return api.put(`/homework/${homework.id}`, {
          lesson_id: lessonId,
          title: hwTitle,
          instructions: hwInstructions || null,
          due_date: hwDue ? new Date(hwDue).toISOString() : null,
        });
      } else {
        // CREATE new homework
        return api.post("/homework", {
          lesson_id: lessonId,
          title: hwTitle,
          instructions: hwInstructions || null,
          due_date: hwDue ? new Date(hwDue).toISOString() : null,
        });
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lesson-homework", lessonId] });
      addToast({ title: "✅ Saqlandi", description: homework ? "Uyga vazifa yangilandi" : "Uyga vazifa yaratildi" });
    },
    onError: (err: any) => {
      addToast({ title: "❌ Xatolik", description: err?.response?.data?.detail || "Uyga vazifa saqlanmadi." });
    },
  });

  const uploadLessonFile = useMutation({
    mutationFn: async () => {
      if (!lessonFile) return;
      const fd = new FormData();
      fd.append("file", lessonFile);
      return api.post(`/lessons/${lessonId}/attachments`, fd);
    },
    onSuccess: () => {
      setLessonFile(null);
      qc.invalidateQueries({ queryKey: ["lesson-attachments", lessonId] });
      addToast({ title: "Fayl biriktirildi", description: "Darsga fayl qo'shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Fayl yuklanmadi." });
    },
  });

  const uploadHomeworkFile = useMutation({
    mutationFn: async () => {
      if (!homework || !homeworkFile) return;
      const fd = new FormData();
      fd.append("file", homeworkFile);
      return api.post(`/homework/${homework.id}/attachments`, fd);
    },
    onSuccess: () => {
      setHomeworkFile(null);
      qc.invalidateQueries({ queryKey: ["homework-attachments", homework?.id] });
      addToast({ title: "Fayl biriktirildi", description: "Uyga vazifaga fayl qo'shildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Fayl yuklanmadi." });
    },
  });

  const markReviewed = useMutation({
    mutationFn: async (submissionId: number) =>
      api.patch(`/homework/submissions/${submissionId}`, { status: "REVIEWED" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["homework-submissions", homework?.id] });
      addToast({ title: "Tekshirildi", description: "Uyga vazifa tekshirildi deb belgilandi." });
    },
  });

  const markRevision = useMutation({
    mutationFn: async (submissionId: number) =>
      api.patch(`/homework/submissions/${submissionId}`, { status: "REVISION_REQUESTED" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["homework-submissions", homework?.id] });
      qc.invalidateQueries({ queryKey: ["my-homework-status", homework?.id] });
      addToast({ title: "Bekor qilindi", description: "Talabaga qayta yuborish belgilandi." });
    },
  });

  const lessonLinks = useMemo<AttachmentLink[]>(() => {
    return (lessonAttachments || []).map((a: FileAttachment) => ({
      id: a.id,
      name: a.file_name,
      url: fileUrl(a.file_path),
    }));
  }, [lessonAttachments]);

  const homeworkLinks = useMemo<AttachmentLink[]>(() => {
    return (homeworkAttachments || []).map((a: FileAttachment) => ({
      id: a.id,
      name: a.file_name,
      url: fileUrl(a.file_path),
    }));
  }, [homeworkAttachments]);

  const submitHomework = useMutation({
    mutationFn: async () => {
      if (!homework) return;
      const fd = new FormData();
      if (submissionText) fd.append("text", submissionText);
      if (submissionFile) fd.append("file", submissionFile);
      return api.post(`/homework/${homework.id}/submit`, fd);
    },
    onSuccess: () => {
      setSubmissionText("");
      setSubmissionFile(null);
      setEditMode(false);
      qc.invalidateQueries({ queryKey: ["my-homework-status", homework?.id] });
      qc.invalidateQueries({ queryKey: ["homework-submissions", homework?.id] });
      addToast({ title: "Yuborildi", description: "Uyga vazifa muvaffaqiyatli yuborildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Uyga vazifa yuborilmadi." });
    },
  });

  const removeAttachment = useMutation({
    mutationFn: async (attachmentId: number) => {
      if (!submission) return;
      return api.delete(`/homework/submissions/${submission.id}/attachments/${attachmentId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-homework-status", homework?.id] });
      addToast({ title: "O'chirildi", description: "Fayl o'chirildi." });
    },
    onError: (err: any) => {
      addToast({ title: "Xatolik", description: err?.response?.data?.detail || "Fayl o'chirilmadi." });
    },
  });

  if (!mounted) return null;

  const status = statusBadge(myStatus?.status);
  const showTabs = !isStudent;

  return (
    <div className="space-y-4">
      <PageHeader title={lesson?.title || "Dars"} description={`Guruh: ${group?.name || "-"}`} />

      <div className="card p-4 space-y-2">
        <div className="text-sm text-emerald-700">Sana: {lesson?.date || "-"}</div>
        {lesson?.description && <div className="text-sm text-slate-700">{lesson.description}</div>}
      </div>

      <div className="card p-4 space-y-3">
        <div className="text-sm font-medium text-emerald-900">Dars fayllari</div>
        {canEdit && (
          <div className="flex flex-col gap-2 md:flex-row">
            <Input type="file" onChange={(e) => setLessonFile(e.target.files?.[0] || null)} />
            <Button disabled={!lessonFile} onClick={() => uploadLessonFile.mutate()}>
              Fayl biriktirish
            </Button>
          </div>
        )}
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {lessonLinks.map((a) => (
            <a key={a.id} href={a.url} className="block rounded-xl border border-emerald-100 p-2 text-sm text-emerald-700">
              {isImageFile(a.name) && (
                <img src={a.url} alt={a.name} className="mb-2 h-40 w-full rounded-lg bg-slate-50 object-contain" />
              )}
              {a.name}
            </a>
          ))}
          {lessonLinks.length === 0 && <div className="text-sm text-slate-500">Hozircha fayl yo'q.</div>}
        </div>
      </div>

      {showTabs && (
        <div className="card p-2">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={tab === "homework" ? "default" : "outline"}
              onClick={() => setTab("homework")}
            >
              Uy ishi
            </Button>
            <Button
              variant={tab === "submissions" ? "default" : "outline"}
              onClick={() => setTab("submissions")}
            >
              O'quvchilarning uyga vazifalari
            </Button>
          </div>
        </div>
      )}

      {(!showTabs || tab === "homework") && (
      <div className="card p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm font-medium text-emerald-900">Uyga vazifa</div>
          {isStudent && <Badge className={status.tone}>{status.label}</Badge>}
        </div>

        {canEdit && (
          <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
            <Input placeholder="Sarlavha" value={hwTitle} onChange={(e) => setHwTitle(e.target.value)} />
            <Input placeholder="Ko'rsatma (matn)" value={hwInstructions} onChange={(e) => setHwInstructions(e.target.value)} />
            <Input type="datetime-local" value={hwDue} onChange={(e) => setHwDue(e.target.value)} />
          </div>
        )}

        {homework && (
          <div className="text-sm text-slate-700">
            <div>Sarlavha: {homework.title}</div>
            {homework.instructions && <div>Matn: {homework.instructions}</div>}
            {homework.due_date && <div>Muddat: {new Date(homework.due_date).toLocaleString()}</div>}
          </div>
        )}

        {canEdit && (
          <div className="flex flex-col gap-2 md:flex-row">
            <Input type="file" onChange={(e) => setHomeworkFile(e.target.files?.[0] || null)} />
            <Button disabled={!homeworkFile || !homework} onClick={() => uploadHomeworkFile.mutate()}>
              Foto/fayl biriktirish
            </Button>
            <Button
              onClick={() => {
                if (!hwTitle) {
                  addToast({ title: "Sarlavha kiriting", description: "Uyga vazifa nomi kerak." });
                  return;
                }
                createOrUpdateHomework.mutate();
              }}
            >
              {homework ? "Uyga vazifani yangilash" : "Uyga vazifa yaratish"}
            </Button>
          </div>
        )}

        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {homeworkLinks.map((a) => (
            <a key={a.id} href={a.url} className="block rounded-xl border border-emerald-100 p-2 text-sm text-emerald-700">
              {isImageFile(a.name) && (
                <img src={a.url} alt={a.name} className="mb-2 h-40 w-full rounded-lg bg-slate-50 object-contain" />
              )}
              {a.name}
            </a>
          ))}
          {homeworkLinks.length === 0 && <div className="text-sm text-slate-500">Fayl biriktirilmagan.</div>}
        </div>

        {isStudent && homework && submission && !editMode && (
          <div className="rounded-xl border border-emerald-100 p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-medium text-emerald-900">Yuborilgan uyga vazifa</div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEditMode(true);
                  setSubmissionText(submission?.text || "");
                }}
              >
                <Pencil className="mr-2 h-4 w-4" />
                Tahrirlash
              </Button>
            </div>
            <div className="text-sm text-slate-700 space-y-1">
              <div className="text-xs uppercase text-slate-500">Matn</div>
              <div className="rounded-lg bg-slate-50 p-3">{submission.text || "Matn yo'q"}</div>
            </div>
            <div>
              <div className="text-xs uppercase text-slate-500 mb-2">Fayllar</div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                {(submission.attachments || []).map((a: FileAttachment) => (
                  <a
                    key={a.id}
                    href={fileUrl(a.file_path)}
                    className="block rounded-xl border border-emerald-100 p-2 text-sm text-emerald-700"
                  >
                    {isImageFile(a.file_name) && (
                      <img
                        src={fileUrl(a.file_path)}
                        alt={a.file_name}
                        className="mb-2 h-40 w-full rounded-lg bg-slate-50 object-contain"
                      />
                    )}
                    {a.file_name}
                  </a>
                ))}
                {(submission.attachments || []).length === 0 && (
                  <div className="text-sm text-slate-500">Fayl biriktirilmagan.</div>
                )}
              </div>
            </div>
          </div>
        )}

        {isStudent && homework && (!submission || editMode || myStatus?.status === "REVISION_REQUESTED") && (
          <div className="rounded-xl border border-emerald-100 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-emerald-900">
                {submission ? "Uyga vazifani tahrirlash" : "Uyga vazifa topshirish"}
              </div>
              {editMode && submission && (
                <Button variant="outline" size="sm" onClick={() => setEditMode(false)}>
                  Bekor qilish
                </Button>
              )}
            </div>
            <textarea
              className="w-full rounded-xl border border-emerald-100 p-3 text-sm"
              rows={4}
              placeholder="Matn yozing..."
              value={submissionText}
              onChange={(e) => setSubmissionText(e.target.value)}
            />
            {submission && (submission.attachments || []).length > 0 && (
              <div className="space-y-2">
                <div className="text-xs uppercase text-slate-500">Yuklangan fayllar</div>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                  {(submission.attachments || []).map((a: FileAttachment) => (
                    <div key={a.id} className="rounded-xl border border-emerald-100 p-2 text-sm">
                      {isImageFile(a.file_name) && (
                        <img
                          src={fileUrl(a.file_path)}
                          alt={a.file_name}
                          className="mb-2 h-32 w-full rounded-lg bg-slate-50 object-contain"
                        />
                      )}
                      <div className="truncate">{a.file_name}</div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2"
                        onClick={() => removeAttachment.mutate(a.id)}
                      >
                        O'chirish
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <Input type="file" onChange={(e) => setSubmissionFile(e.target.files?.[0] || null)} />
            <Button onClick={() => submitHomework.mutate()} disabled={!submissionText && !submissionFile}>
              {submission ? "Yangilash" : "Yuborish"}
            </Button>
          </div>
        )}
      </div>
      )}

      {!isStudent && homework && tab === "submissions" && (
        <div className="card p-4">
          <div className="text-sm font-medium text-emerald-900 mb-2">O'quvchilar holati</div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Talaba</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Matn</TableHead>
                <TableHead>Fayl</TableHead>
                <TableHead>Amal</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {students?.map((s: any) => {
                const submission = (submissions || []).find((sub: any) => sub.student_id === s.id);
                const badge = statusBadge(submission?.status);
                const files = submission?.attachments || [];
                return (
                  <TableRow
                    key={`${homework.id}-${s.id}`}
                    className="cursor-pointer"
                    onClick={() => {
                      setSelectedStudent(s);
                      setSelectedSubmission(submission || null);
                      setDetailOpen(true);
                    }}
                  >
                    <TableCell>{s.full_name}</TableCell>
                    <TableCell>
                      <Badge className={badge.tone}>{badge.label}</Badge>
                    </TableCell>
                    <TableCell className="max-w-[220px] truncate">{submission?.text || "-"}</TableCell>
                    <TableCell>
                      {files.length > 0 ? (
                        <div className="flex flex-col gap-1">
                          {files.map((f: any, idx: number) => (
                            <a key={f.id} className="text-emerald-700 underline" href={fileUrl(f.file_path)}>
                              Fayl {idx + 1}
                            </a>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {submission ? (
                        <div className="flex flex-wrap gap-2">
                          <Button size="sm" onClick={(e) => { e.stopPropagation(); markReviewed.mutate(submission.id); }}>
                            <Check className="mr-2 h-4 w-4" />
                            Tekshirildi
                          </Button>
                          <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); markRevision.mutate(submission.id); }}>
                            <XCircle className="mr-2 h-4 w-4" />
                            Bekor qilish
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}

      {homework === null && !canEdit && (
        <div className="card p-6 text-center text-sm text-emerald-700">Uyga vazifa hali qo'shilmagan.</div>
      )}

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Uyga vazifa tafsiloti</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="text-sm text-emerald-800">
              <span className="font-semibold">Talaba:</span> {selectedStudent?.full_name || "-"}
            </div>
            {selectedSubmission ? (
              <>
                <div className="text-sm text-emerald-800">
                  <span className="font-semibold">Status:</span> {selectedSubmission.status}
                </div>
                <div className="text-sm text-slate-700">
                  <div className="text-xs uppercase text-slate-500">Matn</div>
                  <div className="rounded-lg bg-slate-50 p-3">{selectedSubmission.text || "Matn yo'q"}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-slate-500 mb-2">Fayllar</div>
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                    {(selectedSubmission.attachments || []).map((a: FileAttachment) => (
                      <a
                        key={a.id}
                        href={fileUrl(a.file_path)}
                        className="block rounded-xl border border-emerald-100 p-2 text-sm text-emerald-700"
                      >
                        {isImageFile(a.file_name) && (
                          <img
                            src={fileUrl(a.file_path)}
                            alt={a.file_name}
                            className="mb-2 h-40 w-full rounded-lg bg-slate-50 object-contain"
                          />
                        )}
                        {a.file_name}
                      </a>
                    ))}
                    {(selectedSubmission.attachments || []).length === 0 && (
                      <div className="text-sm text-slate-500">Fayl biriktirilmagan.</div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => markReviewed.mutate(selectedSubmission.id)}>
                    <Check className="mr-2 h-4 w-4" />
                    Tekshirildi
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => markRevision.mutate(selectedSubmission.id)}>
                    <XCircle className="mr-2 h-4 w-4" />
                    Bekor qilish
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-sm text-slate-600">Bu talaba hali uyga vazifa yubormagan.</div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
