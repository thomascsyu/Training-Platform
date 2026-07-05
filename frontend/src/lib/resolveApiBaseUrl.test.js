import { resolveApiBaseUrl, resolveBackendOrigin } from "@/lib/resolveApiBaseUrl";

describe("resolveApiBaseUrl", () => {
  it("defaults to same-origin /api when unset", () => {
    expect(resolveApiBaseUrl("")).toBe("/api");
    expect(resolveApiBaseUrl(undefined)).toBe("/api");
    expect(resolveApiBaseUrl("   ")).toBe("/api");
  });

  it("builds an absolute API URL when a backend origin is provided", () => {
    expect(resolveApiBaseUrl("http://localhost:8001")).toBe(
      "http://localhost:8001/api"
    );
    expect(resolveApiBaseUrl("http://localhost:8001/")).toBe(
      "http://localhost:8001/api"
    );
  });
});

describe("resolveBackendOrigin", () => {
  it("prefers BACKEND_PROXY_URL over REACT_APP_BACKEND_URL", () => {
    expect(
      resolveBackendOrigin("http://public-api.example.com", "http://api:8080")
    ).toBe("http://api:8080");
  });

  it("falls back to localhost when nothing is configured", () => {
    expect(resolveBackendOrigin("", "")).toBe("http://localhost:8001");
  });
});
