"use client";

import * as React from "react";

export type ToastProps = {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
};

type ToastContextType = {
  toasts: ToastProps[];
  addToast: (toast: ToastProps) => void;
  removeToast: (index: number) => void;
};

const ToastContext = React.createContext<ToastContextType | null>(null);

// Global reference for toast function
let addToastGlobal: ((toast: ToastProps) => void) | null = null;

export function ToastProviderRoot({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  const addToast = React.useCallback((toast: ToastProps) => {
    setToasts((prev) => [...prev, toast]);
  }, []);

  const removeToast = React.useCallback((index: number) => {
    setToasts((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // Store addToast function globally
  React.useEffect(() => {
    addToastGlobal = addToast;
    return () => {
      addToastGlobal = null;
    };
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProviderRoot");
  return ctx;
}

// Simple toast function that can be called directly
export function toast(props: ToastProps) {
  if (addToastGlobal) {
    addToastGlobal(props);
  }
}
