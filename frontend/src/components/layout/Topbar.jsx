import { Activity, Menu } from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Separator } from "../ui/separator";
import { Tooltip } from "../ui/tooltip";

export function Topbar({ title, context, status, onOpenSidebar }) {
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur lg:px-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={onOpenSidebar}
        aria-label="Open navigation"
        className="lg:hidden"
      >
        <Menu className="h-4 w-4" />
      </Button>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold leading-tight">{title}</p>
        {context && <p className="truncate text-[11px] leading-tight text-muted-foreground">{context}</p>}
      </div>

      <Separator orientation="vertical" className="hidden h-5 sm:block" />

      <Tooltip label="Backend pipeline status" side="bottom">
        <Badge variant={status?.online === false ? "destructive" : "success"}>
          <Activity className="h-3 w-3" aria-hidden="true" />
          {status?.label || "System online"}
        </Badge>
      </Tooltip>
    </header>
  );
}
