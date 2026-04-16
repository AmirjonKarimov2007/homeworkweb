"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getRoutes } from "@/lib/routes";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";

const adminNav = ["/dashboard", "/groups", "/students", "/payments", "/notifications", "/profile"];
const teacherNav = ["/dashboard", "/my-groups", "/notifications", "/profile"];
const studentNav = ["/dashboard", "/my-groups", "/payments", "/notifications", "/profile"];

export function MobileBottomNav() {
  const mounted = useMounted();
  const pathname = usePathname();
  const user = typeof window !== "undefined" ? getUser() : null;
  const role = user?.role;

  if (!mounted || !role) return null;

  const items = getRoutes(role);
  const allow = role === "SUPER_ADMIN" || role === "ADMIN" ? adminNav : role === "TEACHER" ? teacherNav : studentNav;
  const navItems = items.filter((i) => allow.includes(i.href));

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 md:hidden">
      <div className="border-t border-emerald-100 bg-white/95 backdrop-blur pb-[env(safe-area-inset-bottom)] shadow-[0_-8px_24px_rgba(15,107,70,0.08)]">
        <div className="grid" style={{ gridTemplateColumns: `repeat(${Math.max(navItems.length, 3)}, minmax(0, 1fr))` }}>
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center gap-1 px-2 py-2 text-[11px] ${
                  active ? "text-emerald-700" : "text-slate-500"
                }`}
              >
                {Icon && <Icon className={`h-5 w-5 ${active ? "text-emerald-700" : "text-slate-400"}`} />}
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
