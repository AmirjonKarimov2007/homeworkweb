import {
  LayoutDashboard,
  GraduationCap,
  UserCog,
  UsersRound,
  Wallet,
  Receipt,
  ShieldCheck,
  User,
  Bell,
  BookOpen,
} from "lucide-react";

export type RouteItem = {
  label: string;
  href: string;
  roles: string[];
  icon: any;
};

export const getRoutes = (role?: string | null): RouteItem[] => {
  const items: RouteItem[] = [
    { label: "Bosh panel", href: "/dashboard", roles: ["SUPER_ADMIN", "ADMIN", "TEACHER", "STUDENT"], icon: LayoutDashboard },
    { label: "Talabalar", href: "/students", roles: ["SUPER_ADMIN", "ADMIN"], icon: GraduationCap },
    { label: "Oqituvchilar", href: "/teachers", roles: ["SUPER_ADMIN", "ADMIN"], icon: UserCog },
    { label: "Kurslar", href: "/courses", roles: ["SUPER_ADMIN", "ADMIN"], icon: BookOpen },
    { label: "Guruhlar", href: "/groups", roles: ["SUPER_ADMIN", "ADMIN"], icon: UsersRound },
    { label: "Guruhlar", href: "/my-groups", roles: ["TEACHER", "STUDENT"], icon: UsersRound },
    { label: "Moliya", href: "/finance", roles: ["SUPER_ADMIN", "ADMIN"], icon: Wallet },
    { label: "Tolovlar", href: "/payments", roles: ["SUPER_ADMIN", "ADMIN", "STUDENT"], icon: Receipt },
    { label: "Audit log", href: "/audit-logs", roles: ["SUPER_ADMIN"], icon: ShieldCheck },
    { label: "Profil", href: "/profile", roles: ["SUPER_ADMIN", "ADMIN", "TEACHER", "STUDENT"], icon: User },
    { label: "Xabarnomalar", href: "/notifications", roles: ["SUPER_ADMIN", "ADMIN", "TEACHER", "STUDENT"], icon: Bell },
  ];

  if (!role) return items;
  return items.filter((r) => r.roles.includes(role));
};
