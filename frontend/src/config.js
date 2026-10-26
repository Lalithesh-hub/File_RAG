export const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

// Keep these two in sync with the backend (parsers/router.py and config.py)
export const MAX_UPLOAD_MB = 50;
export const ACCEPTED_EXTENSIONS = [
  ".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".html", ".htm",
  ".txt", ".md", ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
];
export const MAX_QUESTION_CHARS = 1000;

/** Returns an error message, or null if the file is acceptable. */
export function validateFile(file) {
  const dot = file.name.lastIndexOf(".");
  const ext = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    return `${ext || "This"} files aren't supported. Try ${ACCEPTED_EXTENSIONS.slice(0, 5).join(", ")} or another listed format.`;
  }
  if (file.size === 0) return "This file is empty.";
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `This file is larger than ${MAX_UPLOAD_MB} MB.`;
  }
  return null;
}
