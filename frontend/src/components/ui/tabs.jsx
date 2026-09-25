import { createContext, useContext, useState } from "react";
import { cn } from "../../lib/utils";

const TabsContext = createContext(null);

export function Tabs({ defaultValue, value, onValueChange, className, children }) {
  const [internal, setInternal] = useState(defaultValue);
  const active = value ?? internal;

  const setValue = (next) => {
    setInternal(next);
    onValueChange?.(next);
  };

  return (
    <TabsContext.Provider value={{ value: active, setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ className, children }) {
  return (
    <div role="tablist" className={cn("inline-flex items-center gap-1 rounded-md bg-muted p-1", className)}>
      {children}
    </div>
  );
}

export function TabsTrigger({ value, className, children }) {
  const ctx = useContext(TabsContext);
  const isActive = ctx?.value === value;

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => ctx?.setValue(value)}
      className={cn(
        "rounded px-3 py-1 text-xs font-medium transition-colors",
        isActive ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
        className
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, className, children }) {
  const ctx = useContext(TabsContext);
  if (ctx?.value !== value) return null;

  return (
    <div role="tabpanel" className={cn("mt-4", className)}>
      {children}
    </div>
  );
}
