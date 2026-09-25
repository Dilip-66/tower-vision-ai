import { History, ScanSearch } from "lucide-react";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { formatLabel, formatPercent, formatTime } from "../../lib/format";

/**
 * Recent inspections rendered from real detections only.
 * No fabricated rows — an empty state is shown when there is no data.
 */
export function RecentInspections({ inspections = [] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent inspections</CardTitle>
        <CardDescription>Completed detection runs in this session.</CardDescription>
      </CardHeader>

      <CardContent>
        {inspections.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-input px-4 py-10 text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
              <History className="h-4 w-4" aria-hidden="true" />
            </span>
            <p className="text-sm font-medium">No inspections yet</p>
            <p className="max-w-sm text-xs text-muted-foreground">
              Completed detection runs will be listed here with their classification and confidence.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Image</TableHead>
                <TableHead>Detections</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden sm:table-cell">Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {inspections.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {item.previewUrl ? (
                        <img
                          src={item.previewUrl}
                          alt=""
                          className="h-8 w-8 shrink-0 rounded border border-border object-cover"
                        />
                      ) : (
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-border bg-muted text-muted-foreground">
                          <ScanSearch className="h-3.5 w-3.5" aria-hidden="true" />
                        </span>
                      )}
                      <span className="max-w-[140px] truncate text-xs font-medium">{item.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="tabular-nums">{item.totalDetections}</TableCell>
                  <TableCell className="text-xs capitalize">{formatLabel(item.type)}</TableCell>
                  <TableCell className="tabular-nums">{formatPercent(item.averageConfidence)}</TableCell>
                  <TableCell>
                    <Badge variant={item.status === "passed" ? "success" : "destructive"}>
                      {item.status === "passed" ? "Passed" : "Rejected"}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden whitespace-nowrap text-xs text-muted-foreground sm:table-cell">
                    {formatTime(item.createdAt)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
