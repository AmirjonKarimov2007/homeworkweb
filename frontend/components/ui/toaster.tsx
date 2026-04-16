"use client";

import { ToastProvider, ToastViewport, Toast, ToastTitle, ToastDescription } from "@/components/ui/toast";
import { useToaster } from "@/components/ui/use-toast";

function ToastList() {
  const { toasts, removeToast } = useToaster();

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
