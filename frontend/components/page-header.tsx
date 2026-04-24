import { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-3">
        {icon && <div className="text-emerald-600">{icon}</div>}
        <div>
          <h1 className="text-2xl font-semibold text-emerald-900">{title}</h1>
          {description ? <p className="text-sm text-emerald-700">{description}</p> : null}
        </div>
      </div>
      {action}
    </div>
  );
}
