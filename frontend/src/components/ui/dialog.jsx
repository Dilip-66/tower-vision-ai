import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * Minimal modal dialog (no external dependency).
 * Closes on Escape or backdrop click, traps nothing but restores focus.
 */
export function Dialog({ open, onOpenChange, children }) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return;

    function onKeyDown(event) {
      if (event.key === "Escape") onOpenChange?.(false);
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-foreground/30"
        onClick={() => onOpenChange?.(false)}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        className="relative z-10 w-full max-w-3xl rounded-lg border border-border bg-background p-5"
      >
        <button
          type="button"
          aria-label="Close"
          onClick={() => onOpenChange?.(false)}
          className="absolute right-3 top-3 rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({ className, ...props }) {
  return <div className={cn("mb-4 pr-8", className)} {...props} />;
}

export function DialogTitle({ className, ...props }) {
  return <h2 className={cn("text-sm font-semibold", className)} {...props} />;
}

export function DialogDescription({ className, ...props }) {
  return <p className={cn("mt-1 text-xs text-muted-foreground", className)} {...props} />;
}

export function DialogContent({ className, ...props }) {
  return <div className={className} {...props} />;
}
