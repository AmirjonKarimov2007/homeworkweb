"use client";

import Link from "next/link";
import { getRoutes } from "@/lib/routes";
import { getUser, logout } from "@/lib/auth";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { useMounted } from "@/lib/use-mounted";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const mounted = useMounted();
  const user = typeof window !== "undefined" ? getUser() : null;

  const items = getRoutes(user?.role);

  if (!mounted) return null;

  return (
    <aside className="hidden md:flex h-screen w-72 flex-col sidebar-gradient text-white md:sticky md:top-0 md:self-start">
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-white/10 text-white flex items-center justify-center font-bold">
            AM
          </div>
          <div className="leading-tight">
            <div className="text-lg font-semibold">Arab tili markazi</div>
            <div className="text-xs text-emerald-100">CRM / LMS</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-4">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                active ? "bg-white/15" : "hover:bg-white/10"
              }`}
            >
              {Icon && <Icon className="h-4 w-4" />}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4">
        <Button
          className="w-full flex items-center gap-2 rounded-xl border border-white/20 bg-white/10 text-white hover:bg-white/20 shadow-sm"
          onClick={() => {
            logout();
            router.replace("/login");
            router.refresh();
          }}
        >
          <LogOut className="h-4 w-4" />
          Chiqish
        </Button>
      </div>
    </aside>
  );
}
