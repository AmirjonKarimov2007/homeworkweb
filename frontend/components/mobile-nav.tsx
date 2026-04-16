"use client";

import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { getRoutes } from "@/lib/routes";
import { getUser, logout } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMounted } from "@/lib/use-mounted";
import { LogOut } from "lucide-react";

export function MobileNav() {
  const user = typeof window !== "undefined" ? getUser() : null;
  const router = useRouter();
  const mounted = useMounted();
  const items = getRoutes(user?.role);

  if (!mounted) return null;

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="md:hidden">☰</Button>
      </SheetTrigger>
      <SheetContent>
        <div className="mb-6 text-lg font-semibold text-emerald-900">Menyu</div>
        <nav className="space-y-2">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm hover:bg-emerald-50">
                {Icon && <Icon className="h-4 w-4 text-emerald-700" />}
                {item.label}
              </Link>
            );
          })}
        </nav>
        <Button
          variant="outline"
          className="mt-6 w-full flex items-center gap-2 border-emerald-200 text-emerald-800 hover:bg-emerald-50 rounded-xl shadow-sm"
          onClick={() => {
            logout();
            router.replace("/login");
            router.refresh();
          }}
        >
          <LogOut className="h-4 w-4" />
          Chiqish
        </Button>
      </SheetContent>
    </Sheet>
  );
}
