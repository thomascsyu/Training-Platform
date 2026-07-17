const {
  buildProxyRequestOptions,
  expandHostnameVariants,
  isBrowserFacingBackendUrl,
  normalizeBackendOrigin,
  resolveBackendProxyCandidates,
  shouldProxyApiRequest,
} = require("../../proxy-utils");

describe("api proxy helpers", () => {
  it("normalizes backend origins", () => {
    expect(normalizeBackendOrigin("http://api:8080/").origin).toBe(
      "http://api:8080"
    );
  });

  it("matches /api routes only", () => {
    expect(shouldProxyApiRequest("/api/auth/login")).toBe(true);
    expect(shouldProxyApiRequest("/api")).toBe(true);
    expect(shouldProxyApiRequest("/health")).toBe(false);
    expect(shouldProxyApiRequest("/dashboard")).toBe(false);
  });

  it("forwards cookies and rewrites the host header", () => {
    const backendOrigin = normalizeBackendOrigin("http://api:8080");
    const options = buildProxyRequestOptions(
      {
        url: "/api/auth/me",
        method: "GET",
        headers: {
          cookie: "access_token=abc",
          connection: "keep-alive",
          host: "localhost:3000",
        },
      },
      backendOrigin
    );

    expect(options.path).toBe("/api/auth/me");
    expect(options.hostname).toBe("api");
    expect(options.port).toBe("8080");
    expect(options.headers.host).toBe("api:8080");
    expect(options.headers.cookie).toBe("access_token=abc");
    expect(options.headers.connection).toBeUndefined();
    expect(options.family).toBe(4);
  });

  it("expands short hosts to Zeabur private DNS and back", () => {
    expect(expandHostnameVariants("http://training-platform:8080")).toEqual([
      "http://training-platform:8080",
      "http://training-platform.zeabur.internal:8080",
    ]);
    expect(
      expandHostnameVariants("http://training-platform.zeabur.internal:8080")
    ).toEqual([
      "http://training-platform.zeabur.internal:8080",
      "http://training-platform:8080",
    ]);
  });

  it("detects browser-facing backend URLs", () => {
    expect(isBrowserFacingBackendUrl("https://api.example.zeabur.app")).toBe(
      true
    );
    expect(isBrowserFacingBackendUrl("http://api:8080")).toBe(false);
    expect(
      isBrowserFacingBackendUrl("http://training-platform.zeabur.internal:8080")
    ).toBe(false);
    expect(isBrowserFacingBackendUrl("http://localhost:8001")).toBe(false);
  });

  it("resolves proxy candidates from BACKEND_PROXY_URL first", () => {
    expect(
      resolveBackendProxyCandidates({
        BACKEND_PROXY_URL: "http://training-platform:8080",
        REACT_APP_BACKEND_URL: "https://api.example.zeabur.app",
      })
    ).toEqual([
      "http://training-platform:8080",
      "http://training-platform.zeabur.internal:8080",
      "https://api.example.zeabur.app",
    ]);
  });

  it("falls back to Zeabur private hostnames when unset on Zeabur", () => {
    const candidates = resolveBackendProxyCandidates({
      ZEABUR: "1",
      CONTAINER_HOSTNAME: "frontend.zeabur.internal",
    });
    expect(candidates[0]).toBe("http://training-platform.zeabur.internal:8080");
    expect(candidates).toContain("http://backend.zeabur.internal:8080");
  });

  it("auto-discovers Zeabur *_HOST siblings and skips databases", () => {
    const candidates = resolveBackendProxyCandidates({
      CONTAINER_HOSTNAME: "frontend.zeabur.internal",
      SERVICE_6A492B_HOST: "service-6a492b065b59c97aa607005d.zeabur.internal",
      MONGO_HOST: "mongo.zeabur.internal",
      BACKEND_PROXY_PORT: "8080",
    });
    expect(candidates).toContain(
      "http://service-6a492b065b59c97aa607005d.zeabur.internal:8080"
    );
    expect(candidates).toContain("http://service-6a492b065b59c97aa607005d:8080");
    expect(candidates.join(" ")).not.toContain("mongo.zeabur.internal");
  });

  it("appends public API URL as last-resort candidate", () => {
    const candidates = resolveBackendProxyCandidates({
      BACKEND_PROXY_URL: "http://training-platform.zeabur.internal:8080",
      TRAINING_PLATFORM_URL: "https://api.example.zeabur.app",
    });
    expect(candidates[candidates.length - 1]).toBe(
      "https://api.example.zeabur.app"
    );
  });

  it("defaults to localhost outside Zeabur when unset", () => {
    expect(resolveBackendProxyCandidates({})).toEqual([
      "http://localhost:8001",
    ]);
  });
});
