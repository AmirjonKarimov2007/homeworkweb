"use client";

import { ToastProvider, ToastViewport, Toast, ToastTitle, ToastDescription } from "@/components/ui/toast";
import { useToast } from "@/components/ui/use-toast";
import type { ToastProps } from "@/components/ui/use-toast";

function ToastList() {
  const { toasts, removeToast } = useToast();

  return (
    <ToastProvider>
      {toasts.map((t, i) => (
        <Toast key={i} onOpenChange={() => removeToast(i)}>
          {t.title && <ToastTitle>{t.title}</ToastTitle>}
          {t.description && <ToastDescription>{t.description}</ToastDescription>}
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  );
}

export function Toaster() {
  return <ToastList />;
}
