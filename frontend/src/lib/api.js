import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const API = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true,
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve();
  });
  failedQueue = [];
};

let onSessionExpired = null;

/** Register handler invoked when refresh fails (e.g. clear auth state). */
export const setSessionExpiredHandler = (handler) => {
  onSessionExpired = handler;
};

const AUTH_SKIP_REFRESH = [
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/auth/logout",
];

const shouldSkipRefresh = (url = "") =>
  AUTH_SKIP_REFRESH.some((path) => url.includes(path));

API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      !originalRequest ||
      error.response?.status !== 401 ||
      originalRequest._retry ||
      shouldSkipRefresh(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then(() => API(originalRequest));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      await API.post("/auth/refresh");
      processQueue(null);
      return API(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError);
      if (onSessionExpired) onSessionExpired();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export const formatError = (error) => {
  const detail = error.response?.data?.detail;
  if (!detail) return error.message || "Something went wrong";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => e.msg || JSON.stringify(e)).join(" ");
  }
  return String(detail);
};
