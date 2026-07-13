import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add interceptor to inject JWT token into header
if (typeof window !== "undefined") {
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
}

export function formatError(err: any, fallback: string): string {
  const detail = err.response?.data?.detail;
  if (!detail) return fallback;
  if (Array.isArray(detail)) {
    return detail.map((e: any) => {
      const field = e.loc ? e.loc.filter((segment: any) => segment !== "body").join(".") : "";
      return field ? `${field}: ${e.msg}` : e.msg;
    }).join(", ");
  }
  if (typeof detail === "string") return detail;
  return fallback;
}
