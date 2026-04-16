import { ReactNode } from "react";
import { Sidebar } from "@/components/sidebar";
import { Topbar } from "@/components/topbar";
import { AuthGuard } from "@/components/auth-guard";
import { MobileBottomNav } from "@/components/mobile-bottom-nav";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-emerald-50/40 overflow-x-hidden">
        <Sidebar />
        <div className="flex-1 min-w-0">
          <Topbar />
          <main className="p-4 md:p-8 pb-24 md:pb-8 animate-in fade-in min-w-0">
            <div className="mx-auto w-full max-w-6xl min-w-0">{children}</div>
          </main>
        </div>
        <MobileBottomNav />
      </div>
    </AuthGuard>
  );
}
