const {
  buildProxyRequestOptions,
  normalizeBackendOrigin,
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
  });
});
