"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getUser, setLastPath } from "@/lib/auth";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);
  const [isAllowed, setIsAllowed] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (!user) {
      setIsAllowed(false);
      setIsReady(true);
      router.replace("/login");
      return;
    }

    if (pathname) {
      setLastPath(pathname);
    }
    setIsAllowed(true);
    setIsReady(true);
  }, [pathname, router]);

  if (!isReady || !isAllowed) {
    return null;
  }

  return <>{children}</>;
}
