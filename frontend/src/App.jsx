import { useCallback, useEffect, useMemo, useRef, useState, lazy, Suspense } from "react";
import { Plus, ScanSearch, Target, TowerControl } from "lucide-react";

import { AppSidebar } from "./components/layout/AppSidebar";
import { Topbar } from "./components/layout/Topbar";
import { StatCard } from "./components/dashboard/StatCard";
import { UploadPanel } from "./components/dashboard/UploadPanel";
import { QualityGate } from "./components/dashboard/QualityGate";
import { DetectionResults } from "./components/dashboard/DetectionResults";
import { RecentInspections } from "./components/dashboard/RecentInspections";
import { Button } from "./components/ui/button";
import { Skeleton } from "./components/ui/skeleton";
import {
  detectTower,
  getVisualizationUrl,
  validateImageFile,
} from "./lib/api";

const AnalyticsPanel = lazy(() =>
  import("./components/dashboard/AnalyticsPanel").then((module) => ({
    default: module.AnalyticsPanel,
  }))
);

const INITIAL_STATE = { status: "idle", message: "", data: null };

function deriveQualityState(status, data) {
  if (status === "rejected") return "failed";
  if (status === "success" && data?.quality?.passed !== false) return "passed";
  if (status === "processing") return "ready";
  return "ready";
}

import { usePathname } from "./lib/router";
import Landing from "./pages/Landing";

export default function App() {
  const pathname = usePathname();
  const isDashboard = pathname.startsWith("/app") || pathname.startsWith("/dashboard");

  if (!isDashboard) return <Landing />;

  return <Dashboard />;
}

function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState(INITIAL_STATE);
  const [inspections, setInspections] = useState([]);

  const fileRef = useRef(null);

  const isProcessing = result.status === "processing";
  const data = result.data;
  const detection = data?.detection?.results ?? null;
  const quality = data?.quality ?? null;
  const visualizationUrl = getVisualizationUrl(data?.visualization?.url_path);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFile = useCallback(
    (nextFile) => {
      const validationError = validateImageFile(nextFile);
      if (validationError) {
        setResult({ status: "error", message: validationError, data: null });
        return;
      }

      if (previewUrl) URL.revokeObjectURL(previewUrl);

      setFile(nextFile);
      setPreviewUrl(URL.createObjectURL(nextFile));
      setResult(INITIAL_STATE);
    },
    [previewUrl]
  );

  const clearImage = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl("");
    setResult(INITIAL_STATE);
    if (fileRef.current) fileRef.current.value = "";
  }, [previewUrl]);

  const runDetection = useCallback(async () => {
    if (!file) return;

    setResult({ status: "processing", message: "Running detection…", data: null });

    try {
      const body = await detectTower(file);
      const rejected = body.pipeline?.status === "REJECTED";

      setResult({
        status: rejected ? "rejected" : "success",
        message: rejected ? "Image rejected by the quality gate." : "Image analyzed successfully.",
        data: body,
      });

      setInspections((previous) => [
        {
          id: `${Date.now()}-${file.name}`,
          name: file.name,
          previewUrl: URL.createObjectURL(file),
          totalDetections: body?.detection?.results?.total_detections ?? 0,
          type: detectPrimaryType(body),
          averageConfidence: body?.detection?.results?.average_confidence ?? null,
          status: rejected ? "rejected" : "passed",
          createdAt: new Date().toISOString(),
        },
        ...previous,
      ]);
    } catch (error) {
      setResult({
        status: "error",
        message: error?.message || "Unable to connect to the Tower Vision AI backend.",
        data: null,
      });
    }
  }, [file]);

  const stats = useMemo(
    () => [
      {
        label: "Total detections",
        value: detection ? detection.total_detections : "—",
        icon: ScanSearch,
        hint: detection ? "Above 0.25 confidence" : "Awaiting detection",
      },
      {
        label: "Supporting towers",
        value: detection ? detection.class_counts?.supporting_tower ?? 0 : "—",
        icon: TowerControl,
        hint: "Lattice structures",
      },
      {
        label: "Monopole towers",
        value: detection ? detection.class_counts?.monopole_tower ?? 0 : "—",
        icon: Target,
        hint: "Single-pole structures",
      },
      {
        label: "Average confidence",
        value: detection ? `${(detection.average_confidence * 100).toFixed(1)}%` : "—",
        icon: ScanSearch,
        hint: "Mean across detections",
      },
    ],
    [detection]
  );

  return (
    <div className="min-h-screen bg-background">
      <AppSidebar open={sidebarOpen} onOpenChange={setSidebarOpen} />

      <div className="lg:pl-60">
        <Topbar
          title="Tower Detection"
          context="YOLO11n · confidence threshold 0.25"
          status={{ label: isProcessing ? "Processing" : "System online" }}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        <main className="mx-auto w-full max-w-6xl space-y-5 px-4 py-6 lg:px-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-1">
              <h1 className="text-xl font-semibold tracking-tight">Tower Detection</h1>
              <p className="max-w-2xl text-sm text-muted-foreground">
                Analyze telecom tower images using AI-powered visual inspection.
              </p>
            </div>

            <Button
              variant="outline"
              onClick={() => {
                clearImage();
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              New Inspection
            </Button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <StatCard key={stat.label} {...stat} />
            ))}
          </div>

          <div className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)] lg:items-start">
            <div className="space-y-5">
              <UploadPanel
                file={file}
                previewUrl={previewUrl}
                isDragging={isDragging}
                isProcessing={isProcessing}
                error={result.status === "error" ? result.message : ""}
                onFile={handleFile}
                onDragState={setIsDragging}
                onRun={runDetection}
                onClear={clearImage}
              />

              <QualityGate
                state={deriveQualityState(result.status, data)}
                metrics={quality?.metrics}
                reasons={quality?.reasons || []}
              />
            </div>

            <div className="space-y-5">
              <DetectionResults
                status={result.status}
                detection={detection}
                previewUrl={previewUrl}
                visualizationUrl={visualizationUrl}
                fileName={file?.name}
              />

              <Suspense fallback={<Skeleton className="h-64 w-full" />}>
                <AnalyticsPanel inspections={inspections} />
              </Suspense>
            </div>
          </div>

          <RecentInspections inspections={inspections} />
        </main>
      </div>
    </div>
  );
}

function detectPrimaryType(body) {
  const counts = body?.detection?.results?.class_counts;
  if (!counts) return null;

  const supporting = counts.supporting_tower || 0;
  const monopole = counts.monopole_tower || 0;

  if (supporting === 0 && monopole === 0) return null;
  return supporting >= monopole ? "supporting_tower" : "monopole_tower";
}
