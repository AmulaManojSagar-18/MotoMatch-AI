// Single source of truth for the backend base URL.
// Configured via VITE_API_BASE_URL (see .env), with a sensible local default.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
