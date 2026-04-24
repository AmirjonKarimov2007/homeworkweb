import { Badge as UIBadge } from "@/components/ui/badge";

interface ModernBadgeProps {
  children: React.ReactNode;
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info";
  className?: string;
}

export default function ModernBadge({ children, variant = "default", className = "" }: ModernBadgeProps) {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-200";

  const variantClasses = {
    default: "bg-emerald-100 text-emerald-800 hover:bg-emerald-200",
    secondary: "bg-gray-100 text-gray-800 hover:bg-gray-200",
    destructive: "bg-red-100 text-red-800 hover:bg-red-200",
    outline: "border border-gray-300 text-gray-700 bg-white hover:bg-gray-50",
    success: "bg-green-100 text-green-800 hover:bg-green-200",
    warning: "bg-amber-100 text-amber-800 hover:bg-amber-200",
    info: "bg-blue-100 text-blue-800 hover:bg-blue-200",
  };

  return (
    <UIBadge className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </UIBadge>
  );
}