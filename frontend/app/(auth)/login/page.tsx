"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";
import { getLastPath, getUser, saveAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Lock, Phone } from "lucide-react";
import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";

const schema = z.object({
  login: z.string().min(3),
  password: z.string().min(6),
});

type FormData = z.infer<typeof schema>;

function unwrapLoginPayload(payload: any) {
  if (payload?.access_token && payload?.refresh_token && payload?.user) {
    return payload;
  }
  if (payload?.data?.access_token && payload?.data?.refresh_token && payload?.data?.user) {
    return payload.data;
  }
  return null;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const doLogin = useCallback(async (login: string, password: string) => {
    try {
      setError(null);
      setIsSubmitting(true);
      console.log("Login attempt:", { login, password });
      const res = await api.post("/auth/login", { login, password });
      console.log("Login response:", res.status, res.data);
      const payload = unwrapLoginPayload(res.data);

      if (!payload) {
        setError("Login javobi noto'g'ri formatda keldi.");
        return;
      }

      saveAuth(payload.access_token, payload.refresh_token, payload.user);
      const last = getLastPath() || "/dashboard";
      router.replace(last);
    } catch (err: any) {
      console.error("Login error:", err?.response?.data || err);
      if (err?.response?.status === 401) {
        setError("Login yoki parol noto'g'ri.");
      } else if (err?.response?.status === 403) {
        setError(err?.response?.data?.detail || "Kirishga ruxsat berilmadi.");
      } else {
        setError("Server bilan bog'lanishda xatolik. Qayta urinib ko'ring.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [router]);

  // Auto-login from URL params
  useEffect(() => {
    const user = getUser();
    if (user) {
      const last = getLastPath() || "/dashboard";
      router.replace(last);
      return;
    }

    const urlLogin = searchParams.get("login");
    const urlPassword = searchParams.get("password");

    if (urlLogin && urlPassword) {
      // Trim any leading/trailing spaces from URL decoded values
      const cleanLogin = urlLogin.trim();
      const cleanPassword = urlPassword.trim();
      console.log("Auto-login from URL:", { urlLogin, urlPassword, cleanLogin, cleanPassword });
      setValue("login", cleanLogin);
      setValue("password", cleanPassword);
      doLogin(cleanLogin, cleanPassword);
    }
  }, [searchParams, router, setValue, doLogin]);

  const onSubmit = async (data: FormData) => {
    await doLogin(data.login, data.password);
  };

  return (
    <div className="min-h-screen bg-hero flex items-center justify-center p-6">
      <Card className="w-full max-w-md animate-in fade-in shadow-xl border-emerald-100/60">
        <CardContent>
          <h1 className="text-2xl font-semibold text-emerald-900">Tizimga kirish</h1>
          <p className="text-sm text-emerald-700">Telefon yoki email va parolni kiriting.</p>

          {error ? (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
              {error}
            </div>
          ) : null}

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-3">
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-400" />
              <Input className="pl-9" placeholder="Telefon yoki email" {...register("login")} />
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-400" />
              <Input className="pl-9" type="password" placeholder="Parol" {...register("password")} />
            </div>
            <Button
              type="submit"
              className="w-full bg-emerald-600 text-white shadow-md hover:bg-emerald-700 transition"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Kutilmoqda..." : "Kirish"}
            </Button>
          </form>

          <div className="mt-4 text-xs text-emerald-600">Demo: +998900000001 / Admin123!@#</div>
        </CardContent>
      </Card>
    </div>
  );
}
