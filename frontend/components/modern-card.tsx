import { Card as UICard, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ModernCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export default function ModernCard({ title, children, className = "", action }: ModernCardProps) {
  return (
    <UICard className={`bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200 ${className}`}>
      {(title || action) && (
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            {title && <CardTitle className="text-lg font-semibold text-gray-800">{title}</CardTitle>}
            {action && (
              <div className="flex-shrink-0">
                {action}
              </div>
            )}
          </div>
        </CardHeader>
      )}
      <CardContent className="pt-0">
        {children}
      </CardContent>
    </UICard>
  );
}