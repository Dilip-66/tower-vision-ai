export function formatPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatNumber(value, decimals = 1) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(decimals);
}

export function formatLabel(value) {
  if (!value) return "—";
  return String(value).replaceAll("_", " ");
}

export function formatFileSize(bytes) {
  if (typeof bytes !== "number") return "—";
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export function formatTime(isoString) {
  if (!isoString) return "—";
  try {
    return new Date(isoString).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}
