"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { ToastProviderRoot } from "@/components/ui/use-toast";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={client}>
      <ToastProviderRoot>
        {children}
        <Toaster />
      </ToastProviderRoot>
    </QueryClientProvider>
  );
}
