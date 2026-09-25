import { CLASS_DESCRIPTIONS } from "@/lib/data";

/** Reuses the existing status colour tokens — only the label is new. */
const STATUS_STYLES: Record<string, string> = {
  Detected: "bg-statusFunded text-onstatusFunded",
  "No Detection": "bg-statusCancelled text-onstatusCancelled",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={`inline-block whitespace-nowrap px-2.5 py-0.5 rounded-full text-xs font-semibold ${
        STATUS_STYLES[status] ?? ""
      }`}
    >
      {status}
    </span>
  );
}

export function PanelPill({ category }: { category: string }) {
  return (
    <span
      className="inline-block rounded-full bg-surface2 px-2.5 py-0.5 text-xs font-semibold text-onbackground"
      title={CLASS_DESCRIPTIONS[category as keyof typeof CLASS_DESCRIPTIONS]}
    >
      {category}
    </span>
  );
}

export function DetectedPill({ label }: { label: string }) {
  return (
    <span className="inline-block rounded-full bg-surfaceNegative px-2.5 py-0.5 text-xs font-medium text-ctaNegative">
      {label}
    </span>
  );
}
