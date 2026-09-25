import { Card } from "../ui/card";
import { cn } from "../../lib/utils";

export function StatCard({ label, value, icon: Icon, tone = "neutral", hint }) {
  const tones = {
    neutral: "text-muted-foreground",
    positive: "text-emerald-600",
  };

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="mt-1.5 text-2xl font-semibold leading-none tracking-tight tabular-nums">{value}</p>
          {hint && <p className="mt-1.5 truncate text-[11px] text-muted-foreground">{hint}</p>}
        </div>

        {Icon && (
          <span className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted", tones[tone])}>
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
        )}
      </div>
    </Card>
  );
}
