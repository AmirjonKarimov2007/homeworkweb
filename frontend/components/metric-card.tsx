import { Card, CardContent } from "@/components/ui/card";
import { ReactNode } from "react";

export function MetricCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string | number;
  icon?: ReactNode;
}) {
  return (
    <Card className="hover:shadow-md transition">
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-emerald-600">{title}</div>
            <div className="text-2xl font-semibold text-emerald-900">{value}</div>
          </div>
          {icon ? (
            <div className="h-10 w-10 rounded-xl bg-emerald-600/10 flex items-center justify-center text-emerald-700">
              {icon}
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
