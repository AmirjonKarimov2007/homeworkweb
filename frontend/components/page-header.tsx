import { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-emerald-900">{title}</h1>
        {description ? <p className="text-sm text-emerald-700">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
