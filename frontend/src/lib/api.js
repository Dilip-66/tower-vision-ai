// API layer — preserves the existing upload → inference → result flow.
// Endpoint and validation rules mirror backend/app/api/routes/detection.py.

export const API_BASE_URL = "http://127.0.0.1:8000";

export const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/bmp"];

export const MAX_FILE_SIZE = 15 * 1024 * 1024;

export function validateImageFile(file) {
  if (!file) return "No file selected.";
  if (!ALLOWED_TYPES.includes(file.type)) {
    return "Please select a JPG, PNG, WEBP, or BMP image.";
  }
  if (file.size > MAX_FILE_SIZE) {
    return "Image must be smaller than 15 MB.";
  }
  return null;
}

export async function detectTower(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/detect`, {
    method: "POST",
    body: formData,
  });

  const body = await response.json();

  if (!response.ok) {
    throw new Error(body?.detail?.message || body?.detail || "Image processing failed.");
  }

  return body;
}

export function getVisualizationUrl(path) {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE_URL}${path}`;
}
