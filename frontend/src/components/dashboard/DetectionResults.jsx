import { useState } from "react";
import { Download, Eye, ScanSearch } from "lucide-react";
import { Alert } from "../ui/alert";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Dialog, DialogDescription, DialogHeader, DialogTitle } from "../ui/dialog";
import { Progress } from "../ui/progress";
import { Skeleton } from "../ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { formatLabel, formatPercent } from "../../lib/format";

export function DetectionResults({ status, detection, previewUrl, visualizationUrl, fileName }) {
  const [previewOpen, setPreviewOpen] = useState(false);

  if (status === "processing") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Detection results</CardTitle>
          <CardDescription>Running quality gate and YOLO inference.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-64 w-full" />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (status === "rejected") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Detection results</CardTitle>
          <CardDescription>Detection was skipped because the image failed the quality gate.</CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            The image did not meet the minimum quality requirements. Retake the photo in daylight, hold
            steady, and keep the tower in frame.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (status !== "success" || !detection) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Detection results</CardTitle>
          <CardDescription>Results appear here after a detection run.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-input px-4 py-14 text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
              <ScanSearch className="h-4 w-4" aria-hidden="true" />
            </span>
            <p className="text-sm font-medium">No results yet</p>
            <p className="max-w-sm text-xs text-muted-foreground">
              Upload a tower image and run detection to see classified components and confidence scores.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const classAverages = detection.class_average_confidence || {};
  const hasDetections = (detection.detections || []).length > 0;

  return (
    <>
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
          <div className="space-y-1">
            <CardTitle>Detection results</CardTitle>
            <CardDescription>
              {detection.total_detections} object{detection.total_detections === 1 ? "" : "s"} above the
              confidence threshold.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            {visualizationUrl && (
              <>
                <Button variant="outline" size="sm" onClick={() => setPreviewOpen(true)}>
                  <Eye className="h-4 w-4" aria-hidden="true" />
                  View
                </Button>
                <a
                  href={visualizationUrl}
                  download={`${fileName || "tower"}-detected.jpg`}
                  className="inline-flex h-8 items-center gap-2 rounded-md border border-input bg-background px-3 text-xs font-medium transition-colors hover:bg-accent"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Export
                </a>
              </>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <ResultTile
              label="Supporting tower"
              count={detection.class_counts?.supporting_tower ?? 0}
              confidence={formatPercent(classAverages.supporting_tower)}
            />
            <ResultTile
              label="Monopole tower"
              count={detection.class_counts?.monopole_tower ?? 0}
              confidence={formatPercent(classAverages.monopole_tower)}
            />
            <ResultTile
              label="Average confidence"
              count={null}
              confidence={formatPercent(detection.average_confidence)}
              emphasis
            />
          </div>

          {visualizationUrl && (
            <div className="overflow-hidden rounded-md border border-border">
              <img
                src={visualizationUrl}
                alt="Detected towers with bounding boxes"
                className="max-h-96 w-full bg-muted object-contain"
              />
            </div>
          )}

          {hasDetections ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>Component</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead className="hidden md:table-cell">Bounding box</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {detection.detections.map((detectionItem, index) => (
                  <TableRow key={`${detectionItem.class_name}-${index}`}>
                    <TableCell className="tabular-nums text-muted-foreground">{index + 1}</TableCell>
                    <TableCell>
                      <span className="font-medium capitalize">{formatLabel(detectionItem.class_name)}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={detectionItem.confidence * 100}
                          className="w-16"
                          aria-label={`Confidence ${formatPercent(detectionItem.confidence)}`}
                        />
                        <span className="tabular-nums text-xs">{formatPercent(detectionItem.confidence)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="hidden font-mono text-[11px] text-muted-foreground md:table-cell">
                      {Math.round(detectionItem.bounding_box.x1)}, {Math.round(detectionItem.bounding_box.y1)} ·{" "}
                      {Math.round(detectionItem.bounding_box.x2)}, {Math.round(detectionItem.bounding_box.y2)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <Alert variant="warning">
              The image passed the quality gate, but no tower component scored above the confidence
              threshold.
            </Alert>
          )}
        </CardContent>
      </Card>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogHeader>
          <DialogTitle>Annotated detection</DialogTitle>
          <DialogDescription>{fileName || "Uploaded image"}</DialogDescription>
        </DialogHeader>

        <div className="overflow-hidden rounded-md border border-border">
          <img
            src={visualizationUrl || previewUrl}
            alt="Annotated detection result"
            className="max-h-[70vh] w-full bg-muted object-contain"
          />
        </div>
      </Dialog>
    </>
  );
}

function ResultTile({ label, count, confidence, emphasis = false }) {
  return (
    <div className="rounded-md border border-border p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        {count !== null && count !== undefined && (
          <Badge variant={count > 0 ? "info" : "outline"}>{count}</Badge>
        )}
      </div>
      <p className={`mt-1.5 font-semibold tabular-nums ${emphasis ? "text-lg" : "text-base"}`}>
        {confidence}
      </p>
    </div>
  );
}
