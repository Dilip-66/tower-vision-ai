import { useEffect, useRef, useState } from "react";
import { cn } from "../../lib/utils";

/**
 * Lightweight tooltip (no external dependency).
 * Shows on hover and keyboard focus with a small delay.
 */
export function Tooltip({ label, children, side = "top", className }) {
  const [open, setOpen] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  function show() {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setOpen(true), 250);
  }

  function hide() {
    clearTimeout(timer.current);
    setOpen(false);
  }

  const position =
    side === "bottom"
      ? "top-full mt-1.5 left-1/2 -translate-x-1/2"
      : "bottom-full mb-1.5 left-1/2 -translate-x-1/2";

  return (
    <span
      className={cn("relative inline-flex", className)}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {open && label ? (
        <span
          role="tooltip"
          className={cn(
            "pointer-events-none absolute z-50 whitespace-nowrap rounded bg-foreground px-2 py-1 text-[11px] font-medium text-background shadow-sm",
            position
          )}
        >
          {label}
        </span>
      ) : null}
    </span>
  );
}
