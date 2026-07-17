const http = require("http");
const https = require("https");
const { URL } = require("url");

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

const RETRYABLE_PROXY_CODES = new Set([
  "ECONNREFUSED",
  "ECONNRESET",
  "EHOSTUNREACH",
  "ENOTFOUND",
  "EAI_AGAIN",
  "ETIMEDOUT",
  "EPIPE",
]);

const ZEABUR_API_HOSTS = [
  "training-platform.zeabur.internal",
  "backend.zeabur.internal",
  "training-platform-beling.zeabur.internal",
];

const normalizeBackendOrigin = (rawUrl) => {
  const trimmed = (rawUrl || "http://localhost:8001").trim().replace(/\/$/, "");
  return new URL(trimmed);
};

const isBrowserFacingBackendUrl = (rawUrl = "") => {
  const trimmed = (rawUrl || "").trim();
  if (!trimmed) return false;
  try {
    const parsed = new URL(trimmed);
    // HTTPS origins are almost always public browser-facing API URLs.
    if (parsed.protocol === "https:") return true;
    const host = parsed.hostname.toLowerCase();
    // Container-local / private targets are valid proxy backends.
    if (
      host === "localhost" ||
      host === "127.0.0.1" ||
      host.endsWith(".internal") ||
      host.endsWith(".local") ||
      !host.includes(".") ||
      /^\d{1,3}(?:\.\d{1,3}){3}$/.test(host)
    ) {
      return false;
    }
    // Any other hostname (e.g. *.zeabur.app) is treated as browser-facing.
    return true;
  } catch {
    return false;
  }
};

const toHttpOrigin = (hostOrUrl, port = "8080") => {
  const trimmed = (hostOrUrl || "").trim().replace(/\/$/, "");
  if (!trimmed) return "";
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `http://${trimmed}:${port}`;
};

const expandHostnameVariants = (rawUrl) => {
  const origin = normalizeBackendOrigin(rawUrl);
  const variants = [origin.origin];
  const hostname = origin.hostname;
  const port = origin.port || (origin.protocol === "https:" ? "443" : "80");
  const protocol = origin.protocol;

  // Short Docker/K8s names often work, but Zeabur private DNS uses *.zeabur.internal.
  if (hostname && !hostname.includes(".") && hostname !== "localhost") {
    variants.push(`${protocol}//${hostname}.zeabur.internal:${port}`);
  }

  if (hostname.endsWith(".zeabur.internal")) {
    const shortName = hostname.replace(/\.zeabur\.internal$/, "");
    if (shortName && !shortName.includes(".")) {
      variants.push(`${protocol}//${shortName}:${port}`);
    }
  }

  return [...new Set(variants)];
};

const DEFAULT_PRIVATE_PORT = "8080";

const resolveProxyPort = (env = process.env) => {
  for (const key of [
    "BACKEND_PROXY_PORT",
    "TRAINING_PLATFORM_PORT",
    "BACKEND_PORT",
    "API_PORT",
    "WEB_PORT",
  ]) {
    const raw = (env[key] || "").trim();
    if (!raw) continue;
    const port = Number.parseInt(raw, 10);
    if (Number.isInteger(port) && port > 0 && port < 65536) {
      return String(port);
    }
  }
  return DEFAULT_PRIVATE_PORT;
};

const isLikelyDatabaseHostKey = (key = "") =>
  /^(MONGO|MONGODB|POSTGRES|MYSQL|REDIS|MARIA|DB)_/i.test(key);

/**
 * Build ordered backend proxy candidates from environment.
 *
 * Prefer an explicit BACKEND_PROXY_URL. Expand short hostnames to
 * *.zeabur.internal (and back) so either Zeabur or docker-compose style
 * targets work. Private hosts are tried first; browser-facing public API
 * URLs are kept as a last resort so login can still work when private
 * networking is misconfigured but the API public domain is healthy.
 */
const resolveBackendProxyCandidates = (env = process.env) => {
  const candidates = [];
  const publicCandidates = [];
  const port = resolveProxyPort(env);

  const push = (value, { allowPublic = false } = {}) => {
    const normalized = (value || "").trim().replace(/\/$/, "");
    if (!normalized) return;
    if (isBrowserFacingBackendUrl(normalized)) {
      if (allowPublic && !publicCandidates.includes(normalized)) {
        publicCandidates.push(normalized);
      }
      return;
    }
    for (const variant of expandHostnameVariants(normalized)) {
      if (!candidates.includes(variant)) candidates.push(variant);
    }
  };

  push(env.BACKEND_PROXY_URL);

  for (const key of [
    "TRAINING_PLATFORM_HOST",
    "BACKEND_HOST",
    "TRAINING_PLATFORM_BELING_HOST",
    "API_HOST",
  ]) {
    push(toHttpOrigin(env[key], port));
  }

  // Auto-discover Zeabur-injected sibling service hosts (NAME_HOST).
  for (const [key, value] of Object.entries(env)) {
    if (!key.endsWith("_HOST") || isLikelyDatabaseHostKey(key)) continue;
    if (key === "CONTAINER_HOSTNAME") continue;
    const host = (value || "").trim();
    if (!host) continue;
    // Prefer private DNS / short names; skip the frontend's own hostname.
    if (
      host === env.CONTAINER_HOSTNAME ||
      host === `${(env.CONTAINER_HOSTNAME || "").replace(/\.zeabur\.internal$/, "")}`
    ) {
      continue;
    }
    push(toHttpOrigin(host, port));
  }

  // On Zeabur, try conventional private API hostnames when nothing explicit worked.
  if (candidates.length === 0 && (env.ZEABUR || env.CONTAINER_HOSTNAME)) {
    for (const host of ZEABUR_API_HOSTS) {
      push(toHttpOrigin(host, port));
    }
  }

  // Private (non-browser) REACT_APP_BACKEND_URL values.
  push(env.REACT_APP_BACKEND_URL);

  // Public API URLs last — server-side proxy can still reach them, and the
  // browser keeps same-origin /api cookies on the frontend domain.
  // Do not use ZEABUR_WEB_URL here: on the frontend service that is this app.
  for (const key of [
    "REACT_APP_BACKEND_URL",
    "TRAINING_PLATFORM_URL",
    "BACKEND_URL",
    "API_URL",
  ]) {
    push(env[key], { allowPublic: true });
  }

  if (candidates.length === 0 && publicCandidates.length === 0) {
    push("http://localhost:8001");
  }

  return [...candidates, ...publicCandidates];
};

const buildProxyRequestOptions = (req, backendOrigin) => {
  const headers = { ...req.headers, host: backendOrigin.host };
  for (const header of HOP_BY_HOP_HEADERS) {
    delete headers[header];
  }

  return {
    hostname: backendOrigin.hostname,
    port:
      backendOrigin.port ||
      (backendOrigin.protocol === "https:" ? 443 : 80),
    path: req.url,
    method: req.method,
    headers,
    // Prefer IPv4; Zeabur/K8s private networking is IPv4 ClusterIP based.
    family: 4,
  };
};

const readRequestBody = (req) =>
  new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });

const formatProxyError = (error, attemptedOrigins) => {
  const attempted = attemptedOrigins.map((origin) => origin.origin).join(", ");
  return (
    `API proxy error: ${error.message}. ` +
    `Tried: ${attempted}. ` +
    "Set BACKEND_PROXY_URL on the frontend service to the API private hostname " +
    "(e.g. http://training-platform.zeabur.internal:8080) and ensure the API is running."
  );
};

const proxyOnce = (req, res, backendOrigin, body) =>
  new Promise((resolve, reject) => {
    const client = backendOrigin.protocol === "https:" ? https : http;
    const options = buildProxyRequestOptions(req, backendOrigin);

    const proxyReq = client.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
      proxyRes.pipe(res);
      proxyRes.on("end", () => resolve());
      proxyRes.on("error", reject);
    });

    proxyReq.on("error", reject);

    if (body && body.length > 0) {
      proxyReq.end(body);
    } else {
      proxyReq.end();
    }
  });

const proxyHttpRequest = async (req, res, backendOrigins) => {
  const origins = (
    Array.isArray(backendOrigins) ? backendOrigins : [backendOrigins]
  ).map((value) =>
    typeof value === "string" ? normalizeBackendOrigin(value) : value
  );

  let body;
  try {
    body = await readRequestBody(req);
  } catch (error) {
    if (!res.headersSent) {
      res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
      res.end(JSON.stringify({ detail: `API proxy error: ${error.message}` }));
    }
    return;
  }

  let lastError = null;
  const attempted = [];

  for (const origin of origins) {
    attempted.push(origin);
    try {
      await proxyOnce(req, res, origin, body);
      return;
    } catch (error) {
      lastError = error;
      if (!RETRYABLE_PROXY_CODES.has(error.code) || res.headersSent) {
        break;
      }
    }
  }

  if (!res.headersSent) {
    res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
    res.end(
      JSON.stringify({
        detail: formatProxyError(
          lastError || new Error("Unable to reach API"),
          attempted
        ),
      })
    );
  }
};

const shouldProxyApiRequest = (url = "") => url === "/api" || url.startsWith("/api/");

/**
 * Re-write a JSON body that was already consumed by upstream Express middleware
 * (notably @emergentbase/visual-edits in CRACO dev) onto the outgoing proxy
 * request. Without this, http-proxy-middleware waits forever for Content-Length
 * bytes that will never arrive — login/refresh POSTs hang with a spinner.
 *
 * Safe no-op when req.body was never parsed (stream still intact).
 */
const rewriteParsedJsonBody = (proxyReq, req) => {
  if (req == null || req.body === undefined) return false;

  const contentType = String(
    (req.headers && (req.headers["content-type"] || req.headers["Content-Type"])) ||
      ""
  ).toLowerCase();
  if (!contentType.includes("application/json")) return false;

  const bodyData =
    typeof req.body === "string" || Buffer.isBuffer(req.body)
      ? req.body
      : JSON.stringify(req.body);

  const length = Buffer.byteLength(bodyData);
  proxyReq.setHeader("Content-Type", "application/json");
  proxyReq.setHeader("Content-Length", length);
  if (length > 0) {
    proxyReq.write(bodyData);
  }
  return true;
};

module.exports = {
  buildProxyRequestOptions,
  expandHostnameVariants,
  formatProxyError,
  isBrowserFacingBackendUrl,
  normalizeBackendOrigin,
  proxyHttpRequest,
  resolveBackendProxyCandidates,
  rewriteParsedJsonBody,
  shouldProxyApiRequest,
};
