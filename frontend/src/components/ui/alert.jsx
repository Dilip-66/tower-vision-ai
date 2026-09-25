import { forwardRef } from "react";
import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { cn } from "../../lib/utils";

const ICONS = {
  destructive: XCircle,
  warning: AlertTriangle,
  success: CheckCircle2,
  info: Info,
};

const TONES = {
  destructive: "border-red-200 bg-red-50 text-red-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  info: "border-border bg-muted text-foreground",
};

const Alert = forwardRef(({ className, variant = "info", children, ...props }, ref) => {
  const Icon = ICONS[variant] || Info;

  return (
    <div
      ref={ref}
      role="alert"
      className={cn("flex items-start gap-2.5 rounded-md border p-3 text-xs leading-5", TONES[variant], className)}
      {...props}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div className="min-w-0">{children}</div>
    </div>
  );
});
Alert.displayName = "Alert";

export { Alert };
