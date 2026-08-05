const trimTrailingSlash = (value) => value.replace(/\/+$/, "");

export const API_ORIGIN = trimTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
);

export const API_BASE_URL = API_ORIGIN.endsWith("/api/v1")
  ? API_ORIGIN
  : `${API_ORIGIN}/api/v1`;

export const apiUrl = (path = "") => {
  if (!path) return API_ORIGIN;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_ORIGIN}/${String(path).replace(/^\/+/, "")}`;
};
