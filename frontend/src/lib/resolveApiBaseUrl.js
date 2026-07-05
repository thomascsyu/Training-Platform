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
