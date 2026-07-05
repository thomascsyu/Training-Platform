const http = require("http");
const fs = require("fs");
const path = require("path");
const {
  normalizeBackendOrigin,
  proxyHttpRequest,
  shouldProxyApiRequest,
} = require("./proxy-utils");

const buildDir = path.join(__dirname, "build");
const backendOrigin = normalizeBackendOrigin(
  process.env.BACKEND_PROXY_URL || process.env.REACT_APP_BACKEND_URL
);

function parsePort(rawPort) {
  const port = Number.parseInt(rawPort || "8080", 10);

  if (!Number.isInteger(port) || port <= 0 || port >= 65536) {
    console.warn(`Invalid PORT value ${JSON.stringify(rawPort)}; falling back to 8080`);
    return 8080;
  }

  return port;
}

const port = parsePort(process.env.PORT);
const host = process.env.HOST || "0.0.0.0";

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
};

function safeResolve(urlPath) {
  const decodedPath = decodeURIComponent(urlPath.split("?")[0]);
  const normalizedPath = path.normalize(decodedPath).replace(/^([.][.][/\\])+/, "");
  const filePath = path.join(buildDir, normalizedPath === "/" ? "index.html" : normalizedPath);
  return filePath.startsWith(buildDir) ? filePath : path.join(buildDir, "index.html");
}

function sendFile(res, filePath) {
  fs.readFile(filePath, (error, data) => {
    if (error) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Internal Server Error");
      return;
    }

    res.writeHead(200, {
      "Content-Type": contentTypes[path.extname(filePath)] || "application/octet-stream",
      "Cache-Control": filePath.endsWith("index.html") ? "no-cache" : "public, max-age=31536000, immutable",
    });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  const requestUrl = req.url || "/";

  if (requestUrl === "/health") {
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ status: "ok" }));
    return;
  }

  if (shouldProxyApiRequest(requestUrl)) {
    proxyHttpRequest(req, res, backendOrigin);
    return;
  }

  const requestedPath = safeResolve(requestUrl);
  fs.stat(requestedPath, (error, stats) => {
    if (!error && stats.isFile()) {
      sendFile(res, requestedPath);
      return;
    }

    sendFile(res, path.join(buildDir, "index.html"));
  });
});

server.listen(port, host, () => {
  console.log(`Static server listening on http://${host}:${port}`);
  console.log(`Proxying /api/* to ${backendOrigin.origin}`);
});
