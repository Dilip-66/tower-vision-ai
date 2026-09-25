const STATUS_STYLES: Record<string, string> = {
  Active: "bg-statusActive text-onstatusActive",
  Funded: "bg-statusFunded text-onstatusFunded",
  Expired: "bg-statusExpired text-onstatusExpired",
  Cancelled: "bg-statusCancelled text-onstatusCancelled",
  "Needs Verification": "bg-statusNeedsVerification text-onstatusNeedsVerification",
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

export function PanelPill({ panel }: { panel: string }) {
  return (
    <span className="inline-block rounded-full bg-surface2 px-2.5 py-0.5 text-xs font-semibold text-onbackground">
      {panel}
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
