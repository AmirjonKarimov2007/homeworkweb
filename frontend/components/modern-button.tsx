import { Button as UIButton } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import type { MouseEventHandler, ReactNode } from "react";

interface ModernButtonProps {
  children: ReactNode;
  variant?: "default" | "secondary" | "destructive" | "outline" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
  loading?: boolean;
  disabled?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  className?: string;
  type?: "button" | "submit" | "reset";
}

export default function ModernButton({
  children,
  variant = "default",
  size = "default",
  loading = false,
  disabled = false,
  onClick,
  className = "",
  type = "button",
}: ModernButtonProps) {
  const baseClasses = "inline-flex items-center justify-center font-medium transition-all duration-200 hover:scale-105 active:scale-95";

  return (
    <UIButton
      variant={variant}
      size={size}
      disabled={disabled || loading}
      onClick={onClick}
      type={type}
      className={`${baseClasses} ${className}`}
    >
      {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {children}
    </UIButton>
  );
}
