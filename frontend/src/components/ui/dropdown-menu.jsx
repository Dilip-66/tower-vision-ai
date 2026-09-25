import { useEffect, useRef, useState } from "react";
import { cn } from "../../lib/utils";

/**
 * Minimal dropdown menu (no external dependency).
 * Closes on outside click or Escape.
 */
export function DropdownMenu({ trigger, children, align = "end", className }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    }

    function onKeyDown(event) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative inline-flex">
      <div onClick={() => setOpen((v) => !v)}>{trigger}</div>

      {open && (
        <div
          role="menu"
          className={cn(
            "absolute top-full z-40 mt-1 min-w-[180px] rounded-md border border-border bg-background p-1 shadow-sm",
            align === "end" ? "right-0" : "left-0",
            className
          )}
          onClick={() => setOpen(false)}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownMenuItem({ className, ...props }) {
  return (
    <button
      type="button"
      role="menuitem"
      className={cn(
        "flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-foreground transition-colors hover:bg-muted",
        className
      )}
      {...props}
    />
  );
}

export function DropdownMenuSeparator() {
  return <div className="my-1 h-px bg-border" />;
}

export function DropdownMenuLabel({ className, ...props }) {
  return <div className={cn("px-2 py-1.5 text-[11px] font-medium text-muted-foreground", className)} {...props} />;
}
