import { AlertTriangle, CheckCircle2, CircleDashed, ShieldCheck, XCircle } from "lucide-react";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { formatNumber } from "../../lib/format";

const STATES = {
  ready: { label: "Ready", variant: "outline", icon: CircleDashed },
  passed: { label: "Passed", variant: "success", icon: CheckCircle2 },
  warning: { label: "Warning", variant: "warning", icon: AlertTriangle },
  failed: { label: "Failed", variant: "destructive", icon: XCircle },
};

/**
 * Compact quality gate summary.
 * Only shows metric detail when the backend actually returned metrics.
 */
export function QualityGate({ state = "ready", metrics, reasons = [] }) {
  const config = STATES[state] || STATES.ready;
  const Icon = config.icon;

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div className="space-y-1">
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            Image quality
          </CardTitle>
          <CardDescription>Validated before detection runs.</CardDescription>
        </div>

        <Badge variant={config.variant}>
          <Icon className="h-3 w-3" aria-hidden="true" />
          {config.label}
        </Badge>
      </CardHeader>

      {reasons.length > 0 && (
        <CardContent className="pt-0">
          <ul className="space-y-1">
            {reasons.map((reason) => (
              <li key={reason} className="text-xs capitalize text-red-700">
                {String(reason).replaceAll("_", " ")}
              </li>
            ))}
          </ul>
        </CardContent>
      )}

      {metrics && (
        <CardContent className="pt-0">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-3">
            <Metric label="Sharpness" value={formatNumber(metrics.sharpness, 1)} />
            <Metric label="Brightness" value={formatNumber(metrics.mean_brightness, 1)} />
            <Metric label="Resolution" value={`${metrics.width}×${metrics.height}`} />
          </dl>
        </CardContent>
      )}
    </Card>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <dt className="text-[11px] text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 font-medium tabular-nums">{value}</dd>
    </div>
  );
}
