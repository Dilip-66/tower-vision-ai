import { forwardRef } from "react";
import { cn } from "../../lib/utils";

const Progress = forwardRef(({ className, value = 0, indicatorClassName, ...props }, ref) => (
  <div
    ref={ref}
    role="progressbar"
    aria-valuemin={0}
    aria-valuemax={100}
    aria-valuenow={Math.round(value)}
    className={cn("relative h-1.5 w-full overflow-hidden rounded-full bg-secondary", className)}
    {...props}
  >
    <div
      className={cn("h-full rounded-full bg-primary transition-[width]", indicatorClassName)}
      style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
    />
  </div>
));
Progress.displayName = "Progress";

export { Progress };
