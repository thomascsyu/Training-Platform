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

const normalizeBackendOrigin = (rawUrl) => {
  const trimmed = (rawUrl || "http://localhost:8001").trim().replace(/\/$/, "");
  return new URL(trimmed);
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
  };
};

const proxyHttpRequest = (req, res, backendOrigin) => {
  const client = backendOrigin.protocol === "https:" ? https : http;
  const options = buildProxyRequestOptions(req, backendOrigin);

  const proxyReq = client.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on("error", (error) => {
    if (!res.headersSent) {
      res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
      res.end(
        JSON.stringify({
          detail: `API proxy error: ${error.message}`,
        })
      );
      return;
    }
    res.end();
  });

  req.pipe(proxyReq);
};

const shouldProxyApiRequest = (url = "") => url === "/api" || url.startsWith("/api/");

module.exports = {
  buildProxyRequestOptions,
  normalizeBackendOrigin,
  proxyHttpRequest,
  shouldProxyApiRequest,
};
