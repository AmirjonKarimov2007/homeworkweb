"use client";

import * as React from "react";

type ToastProps = {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
};

type ToasterContextType = {
  toasts: ToastProps[];
  addToast: (toast: ToastProps) => void;
  removeToast: (index: number) => void;
};

const ToasterContext = React.createContext<ToasterContextType | null>(null);

// Global reference for the toast function
let addToastGlobal: ((toast: ToastProps) => void) | null = null;

export function ToastProviderRoot({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  const addToast = React.useCallback((toast: ToastProps) => {
    setToasts((prev) => [...prev, toast]);
  }, []);

  const removeToast = React.useCallback((index: number) => {
    setToasts((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // Store the addToast function globally
  React.useEffect(() => {
    addToastGlobal = addToast;
    return () => {
      addToastGlobal = null;
    };
  }, [addToast]);

  return (
    <ToasterContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToasterContext.Provider>
  );
}

export function useToaster() {
  const ctx = React.useContext(ToasterContext);
  if (!ctx) throw new Error("useToaster must be used within ToastProviderRoot");
  return ctx;
}

// Simple toast function that can be called directly
export function toast(props: ToastProps) {
  if (addToastGlobal) {
    addToastGlobal(props);
  }
}
