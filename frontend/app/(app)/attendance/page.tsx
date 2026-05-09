"use client";

import { useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { PageHeader } from "@/components/page-header";

export default function AttendancePage() {
  const [lessonId, setLessonId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [status, setStatus] = useState("PRESENT");

  const mark = useMutation({
    mutationFn: async () =>
      api.post("/attendance", { lesson_id: Number(lessonId), student_id: Number(studentId), status }),
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Davomat" description="Dars bo‘yicha davomatni belgilang." />

      <div className="card p-4 grid grid-cols-1 gap-2 md:grid-cols-4">
        <Input placeholder="Dars ID" value={lessonId} onChange={(e) => setLessonId(e.target.value)} />
        <Input placeholder="Talaba ID" value={studentId} onChange={(e) => setStudentId(e.target.value)} />
        <Input placeholder="Status (PRESENT/ABSENT/LATE/EXCUSED)" value={status} onChange={(e) => setStatus(e.target.value)} />
        <Button onClick={() => mark.mutate()}>Belgilang</Button>
      </div>
    </div>
  );
}
