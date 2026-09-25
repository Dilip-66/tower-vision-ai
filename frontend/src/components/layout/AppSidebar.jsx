import { useState } from "react";
import {
  BarChart3,
  History,
  LayoutDashboard,
  ScanSearch,
  Settings,
  TowerControl,
  X,
} from "lucide-react";
import { cn } from "../../lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, active: true },
  { label: "Inspections", icon: ScanSearch },
  { label: "History", icon: History },
  { label: "Analytics", icon: BarChart3 },
  { label: "Settings", icon: Settings },
];

export function AppSidebar({ open, onOpenChange }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-foreground/20 lg:hidden"
          onClick={() => onOpenChange(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-border bg-background",
          "transition-transform duration-200 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between gap-2 border-b border-border px-4">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <TowerControl className="h-4 w-4" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold leading-tight">Tower Vision AI</p>
              <p className="truncate text-[11px] leading-tight text-muted-foreground">Tower inspection</p>
            </div>
          </div>

          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => onOpenChange(false)}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground lg:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 p-3" aria-label="Main">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.label}
              type="button"
              aria-current={item.active ? "page" : undefined}
              className={cn(
                "flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                item.active
                  ? "bg-secondary font-medium text-secondary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="border-t border-border p-3">
          <div className="rounded-md bg-muted px-3 py-2.5">
            <p className="text-[11px] font-medium text-foreground">Detection model</p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">YOLO11n · conf ≥ 0.25</p>
          </div>
        </div>
      </aside>
    </>
  );
}
