/**
 * Resolve the browser-facing API base URL.
 *
 * Prefer same-origin `/api` (proxied by the dev server or static-server) so
 * HTTP-only auth cookies are first-party and survive login. Set
 * REACT_APP_BACKEND_URL only for legacy direct cross-origin API access.
 */
export const resolveApiBaseUrl = (backendUrl = process.env.REACT_APP_BACKEND_URL) => {
  const trimmed = (backendUrl || "").trim().replace(/\/$/, "");
  return trimmed ? `${trimmed}/api` : "/api";
};

export const resolveBackendOrigin = (
  backendUrl = process.env.REACT_APP_BACKEND_URL,
  proxyUrl = process.env.BACKEND_PROXY_URL
) => {
  const candidate = (proxyUrl || backendUrl || "http://localhost:8001").trim();
  return candidate.replace(/\/$/, "");
};

/**
 * Resolve a stored upload URL for use in <img src>.
 *
 * Uploaded assets are stored as `/api/uploads/...`. When the app talks to the
 * backend directly via REACT_APP_BACKEND_URL, image tags must use the same
 * origin instead of the frontend host.
 */
export const resolveUploadUrl = (
  url,
  backendUrl = process.env.REACT_APP_BACKEND_URL
) => {
  const trimmed = (url || "").trim();
  if (!trimmed) return "";

  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }

  if (trimmed.startsWith("/api/")) {
    const backend = (backendUrl || "").trim().replace(/\/$/, "");
    return backend ? `${backend}${trimmed}` : trimmed;
  }

  return trimmed;
};
