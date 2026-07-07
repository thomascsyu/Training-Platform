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
 * Uploaded assets are stored as `/api/uploads/...`. Thumbnail GET requests are
 * always served through the same-origin `/api` proxy (dev server or static
 * server) so they keep working when JSON API calls use REACT_APP_BACKEND_URL
 * for direct cross-origin access.
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

  if (trimmed.startsWith("/api/uploads/thumbnails/")) {
    const backend = (backendUrl || "").trim().replace(/\/$/, "");
    return backend ? `${backend}${trimmed}` : trimmed;
  }

  if (trimmed.startsWith("/api/")) {
    const backend = (backendUrl || "").trim().replace(/\/$/, "");
    return backend ? `${backend}${trimmed}` : trimmed;
  }

  return trimmed;
};

/**
 * Secondary URL for thumbnail image requests.
 *
 * When a backend origin is configured, the primary URL is cross-origin
 * (`${REACT_APP_BACKEND_URL}/api/uploads/thumbnails/...`). This helper returns
 * a same-origin `/api/...` fallback for environments where a frontend proxy is
 * available and direct backend image requests fail.
 */
export const resolveUploadFallbackUrl = (
  url,
  backendUrl = process.env.REACT_APP_BACKEND_URL
) => {
  const trimmed = (url || "").trim();
  if (!trimmed) return "";
  if (/^https?:\/\//i.test(trimmed)) return "";
  if (!trimmed.startsWith("/api/uploads/thumbnails/")) return "";

  const backend = (backendUrl || "").trim().replace(/\/$/, "");
  return backend ? trimmed : "";
};
