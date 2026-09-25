import { BarChart3 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { formatPercent } from "../../lib/format";

/**
 * Confidence distribution across completed inspections.
 * Rendered only when real detection data exists.
 */
export function AnalyticsPanel({ inspections = [] }) {
  const completed = inspections.filter((item) => item.status === "passed" && item.totalDetections > 0);

  if (completed.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Detection analytics</CardTitle>
          <CardDescription>Confidence distribution across completed inspections.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-input px-4 py-10 text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
              <BarChart3 className="h-4 w-4" aria-hidden="true" />
            </span>
            <p className="text-sm font-medium">Not enough data</p>
            <p className="max-w-sm text-xs text-muted-foreground">
              Run at least one successful detection to populate analytics.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const data = completed.slice(-8).map((item) => ({
    name: item.name.length > 14 ? `${item.name.slice(0, 12)}…` : item.name,
    confidence: Number((item.averageConfidence * 100).toFixed(1)),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Detection analytics</CardTitle>
        <CardDescription>Average confidence per inspection (last {data.length}).</CardDescription>
      </CardHeader>

      <CardContent>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="hsl(240 5.9% 90%)" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10, fill: "hsl(240 3.8% 46.1%)" }}
                tickLine={false}
                axisLine={false}
                interval={0}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: "hsl(240 3.8% 46.1%)" }}
                tickLine={false}
                axisLine={false}
              />
              <RechartsTooltip
                cursor={{ fill: "hsl(240 4.8% 95.9%)" }}
                contentStyle={{
                  borderRadius: 6,
                  border: "1px solid hsl(240 5.9% 90%)",
                  fontSize: 12,
                  boxShadow: "none",
                }}
                formatter={(value) => [`${value}%`, "Confidence"]}
              />
              <Bar dataKey="confidence" radius={[4, 4, 0, 0]} maxBarSize={36}>
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.confidence >= 75 ? "hsl(240 5.9% 10%)" : "hsl(240 5% 62%)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <p className="mt-3 text-[11px] text-muted-foreground">
          Average of all detections in each run ({formatPercent(completed[0].averageConfidence)} in the most
          recent).
        </p>
      </CardContent>
    </Card>
  );
}
