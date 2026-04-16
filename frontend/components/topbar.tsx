"use client";

import { usePathname } from "next/navigation";
import { MobileNav } from "@/components/mobile-nav";
import { getRoutes } from "@/lib/routes";
import { getUser } from "@/lib/auth";
import { useMounted } from "@/lib/use-mounted";

export function Topbar() {
  const pathname = usePathname();
  const user = typeof window !== "undefined" ? getUser() : null;
  const mounted = useMounted();
  const route = getRoutes(user?.role).find(
    (r) => pathname === r.href || pathname.startsWith(r.href + "/")
  );
  const title = route?.label || "Bosh panel";

  if (!mounted) return null;

  return (
    <header className="flex items-center justify-between border-b border-emerald-100 bg-white px-4 py-3 md:px-8">
      <div className="flex items-center gap-3">
        <MobileNav />
        <div className="text-lg font-semibold text-emerald-900">{title}</div>
      </div>
      <div className="hidden md:block text-sm text-emerald-700">
        {user ? `${user.full_name} • ${user.role}` : "Arab tili markazi"}
      </div>
    </header>
  );
}
