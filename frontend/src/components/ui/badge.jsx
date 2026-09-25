import { forwardRef } from "react";
import { cn } from "../../lib/utils";

const VARIANTS = {
  default: "border-transparent bg-secondary text-secondary-foreground",
  outline: "border-border text-foreground",
  success: "border-transparent bg-emerald-50 text-emerald-700",
  destructive: "border-transparent bg-red-50 text-red-700",
  warning: "border-transparent bg-amber-50 text-amber-700",
  info: "border-transparent bg-slate-100 text-slate-700",
};

const Badge = forwardRef(({ className, variant = "default", ...props }, ref) => (
  <span
    ref={ref}
    className={cn(
      "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium leading-4",
      VARIANTS[variant],
      className
    )}
    {...props}
  />
));
Badge.displayName = "Badge";

export { Badge };
