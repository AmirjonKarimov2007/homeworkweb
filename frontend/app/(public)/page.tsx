"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getLastPath, getUser } from "@/lib/auth";
import {
  BookOpen,
  Users,
  CalendarCheck,
  Wallet,
  Bot,
  ChartPie,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

const features = [
  {
    title: "Talabalar va guruhlar",
    desc: "Talabalarni tartibli yuriting, guruhlarga biriktiring va onboarding jarayonini boshqaring.",
    icon: Users,
  },
  {
    title: "Darslar va uy vazifalari",
    desc: "Dars yarating, uy vazifasi bering, matn yoki fayl korinishida topshiriq qabul qiling.",
    icon: BookOpen,
  },
  {
    title: "Davomat",
    desc: "Davomatni tez belgilang va yoqlik boyicha avtomatik ogohlantirish oling.",
    icon: CalendarCheck,
  },
  {
    title: "Moliya nazorati",
    desc: "Tolovlarni tasdiqlang, kvitansiyalarni boshqaring va oylik tushumni koring.",
    icon: Wallet,
  },
  {
    title: "Telegram bot",
    desc: "Eslatmalar yuboring, uy vazifasi va tolov kvitansiyalarini qabul qiling.",
    icon: Bot,
  },
  {
    title: "Hisobotlar",
    desc: "Talaba, davomat va moliya boyicha aniq korsatkichlarni koring.",
    icon: ChartPie,
  },
];

const stats = [
  { label: "Faol talabalar", value: "250+" },
  { label: "Guruhlar soni", value: "35" },
  { label: "Davomat aniqligi", value: "99%" },
  { label: "Tolov nazorati", value: "100%" },
];

const steps = [
  {
    title: "Talabalarni qoshish",
    desc: "Talabalarni royxatga qoshish va guruhlarga biriktirish.",
  },
  {
    title: "Guruhlarga biriktirish",
    desc: "Talabani bir nechta guruhga va tolov rejasiga boglash.",
  },
  {
    title: "Oqitish va nazorat",
    desc: "Dars, davomat, uy vazifa va materiallar bir joyda.",
  },
  {
    title: "Tolovlarni qabul qilish",
    desc: "Kvitansiyalar va tasdiqlar, oylik eslatmalar bilan.",
  },
];

const highlights = [
  "Rol boyicha aniq ruxsatlar",
  "Mobilga mos va tezkor UI",
  "Telegram eslatmalar va topshiriqlar",
  "Fayllar va materiallar kutubxonasi",
];

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    const user = getUser();
    if (user) {
      const last = getLastPath() || "/dashboard";
      router.replace(last);
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-hero">
      <header className="sticky top-0 z-10 border-b border-emerald-100/60 bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-emerald-600 text-white flex items-center justify-center font-bold">
              AM
            </div>
            <div className="leading-tight">
              <div className="text-lg font-semibold text-emerald-900">Arab tili markazi</div>
              <div className="text-xs text-emerald-600">CRM / LMS</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button className="bg-emerald-600 text-white hover:bg-emerald-700 shadow-md">Kirish</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6">
        <section className="grid gap-10 py-16 md:grid-cols-2">
          <div className="animate-in fade-in slide-in-from-bottom-4">
            <Badge variant="secondary" className="mb-4">Arab tili markazi uchun premium platforma</Badge>
            <h1 className="text-4xl font-bold text-emerald-900 leading-tight md:text-5xl">
              Arab tili markazlari uchun zamonaviy CRM va LMS
            </h1>
            <p className="mt-5 text-emerald-700 text-lg">
              Lidlar, talabalar, guruhlar, uy vazifalari, davomat, materiallar va tolovlarni bitta tizimda boshqaring.
              Minimal, qulay va professional dizayn - texnik bolmagan adminlar uchun ham oson.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/login">
                <Button size="lg" className="bg-emerald-600 text-white hover:bg-emerald-700 shadow-md">
                  Boshlash
                </Button>
              </Link>
            </div>
            <div className="mt-8 grid grid-cols-2 gap-4">
              {stats.map((s) => (
                <Card key={s.label}>
                  <CardContent>
                    <div className="text-sm text-emerald-600">{s.label}</div>
                    <div className="text-2xl font-semibold text-emerald-900">{s.value}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="relative animate-in fade-in slide-in-from-bottom-6">
            <div className="absolute -top-6 right-0 hidden h-40 w-40 rounded-full bg-emerald-100 blur-2xl md:block" />
            <Card className="relative overflow-hidden">
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-emerald-600/10 flex items-center justify-center">
                    <Sparkles className="text-emerald-700" />
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-emerald-900">Premium tizim imkoniyatlari</div>
                    <div className="text-sm text-emerald-700">Tez, toza va boshqarish oson</div>
                  </div>
                </div>
                <div className="mt-6 space-y-3">
                  {highlights.map((h) => (
                    <div key={h} className="flex items-center gap-2 rounded-xl border border-emerald-100 bg-white p-3">
                      <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                      <span className="text-sm text-emerald-800">{h}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="py-12">
          <div className="mb-8 text-center">
            <Badge variant="outline">Nimalar bor</Badge>
            <h2 className="mt-3 text-3xl font-semibold text-emerald-900">Markazingizga kerak bolgan hamma narsa</h2>
            <p className="mt-2 text-emerald-700">Minimal UI, kuchli workflow va real natijalar.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {features.map((f) => (
              <Card key={f.title} className="hover:shadow-md transition">
                <CardContent>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-emerald-600/10 flex items-center justify-center">
                      <f.icon className="text-emerald-700" />
                    </div>
                    <div className="text-lg font-semibold text-emerald-900">{f.title}</div>
                  </div>
                  <p className="mt-3 text-sm text-emerald-700">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="py-12">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardContent>
                <div className="text-sm text-emerald-600">Jarayon</div>
                <h3 className="text-2xl font-semibold text-emerald-900">Oddiy qadamlar, aniq natijalar</h3>
                <div className="mt-4 space-y-3">
                  {steps.map((s, idx) => (
                    <div key={s.title} className="flex items-start gap-3">
                      <div className="h-8 w-8 rounded-full bg-emerald-600 text-white flex items-center justify-center text-sm">
                        {idx + 1}
                      </div>
                      <div>
                        <div className="font-semibold text-emerald-900">{s.title}</div>
                        <div className="text-sm text-emerald-700">{s.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <div className="text-sm text-emerald-600">Kimlar uchun</div>
                <h3 className="text-2xl font-semibold text-emerald-900">Admin, oqituvchi va talaba</h3>
                <p className="mt-3 text-emerald-700 text-sm">
                  Rollar boyicha aniq huquqlar. Talabalar dars va uy vazifani koradi, oqituvchi dars jarayoniga
                  etibor beradi, admin esa moliya va umumiy boshqaruvni nazorat qiladi.
                </p>
                <div className="mt-4 grid gap-2 text-sm text-emerald-800">
                  <div>- Rol boyicha menyular va ruxsatlar</div>
                  <div>- Mobilga mos, tezkor interfeys</div>
                  <div>- Telegram eslatmalar va topshiriqlar</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="py-12">
          <Card className="bg-emerald-600 text-white">
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2 md:items-center">
                <div>
                  <div className="text-emerald-100">Bugun boshlang</div>
                  <div className="text-3xl font-semibold">Markazingizni zamonaviy boshqaring</div>
                  <p className="mt-2 text-emerald-100">
                    Tez ishga tushirish, toza dizayn va kuchli funksiyalar. Local yoki VPSda birdek qulay.
                  </p>
                </div>
                <div className="flex gap-3 md:justify-end">
                  <Link href="/login">
                    <Button variant="secondary" size="lg" className="shadow-md">Admin kirish</Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      <footer className="border-t border-emerald-100/60 bg-white/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 text-sm text-emerald-700">
          <div>(c) 2026 Arab tili markazi CRM</div>
          <div>FastAPI + Next.js asosida</div>
        </div>
      </footer>
    </div>
  );
}
