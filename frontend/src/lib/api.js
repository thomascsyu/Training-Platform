import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const API = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true,
});

export const formatError = (error) => {
  const detail = error.response?.data?.detail;
  if (!detail) return error.message || "Something went wrong";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => e.msg || JSON.stringify(e)).join(" ");
  }
  return String(detail);
};
