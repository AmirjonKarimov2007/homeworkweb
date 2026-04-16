import axios from "axios";
import { getAccessToken, logout } from "@/lib/auth";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api",
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== "undefined" && error?.response?.status === 401) {
      const url = String(error?.config?.url || "");
      if (!url.includes("/auth/login")) {
        logout();
        window.location.replace("/login");
      }
    }
    return Promise.reject(error);
  }
);

export default api;
