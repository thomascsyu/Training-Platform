import {
  resolveApiBaseUrl,
  resolveBackendOrigin,
  resolveUploadUrl,
  resolveUploadFallbackUrl,
} from "@/lib/resolveApiBaseUrl";

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

describe("resolveUploadUrl", () => {
  it("returns an empty string for missing values", () => {
    expect(resolveUploadUrl("")).toBe("");
    expect(resolveUploadUrl(undefined)).toBe("");
    expect(resolveUploadUrl("   ")).toBe("");
  });

  it("prefixes thumbnail upload paths with backend origin when configured", () => {
    expect(resolveUploadUrl("/api/uploads/thumbnails/example.jpg", "")).toBe(
      "/api/uploads/thumbnails/example.jpg"
    );
    expect(
      resolveUploadUrl(
        "/api/uploads/thumbnails/example.jpg",
        "http://localhost:8001"
      )
    ).toBe("http://localhost:8001/api/uploads/thumbnails/example.jpg");
  });

  it("prefixes other /api paths with the backend origin when configured", () => {
    expect(
      resolveUploadUrl("/api/files/example.jpg", "http://localhost:8001")
    ).toBe("http://localhost:8001/api/files/example.jpg");
  });

  it("leaves absolute URLs unchanged", () => {
    expect(resolveUploadUrl("https://cdn.example.com/thumb.jpg")).toBe(
      "https://cdn.example.com/thumb.jpg"
    );
  });
});

describe("resolveUploadFallbackUrl", () => {
  it("returns same-origin thumbnail URL as fallback when backend is configured", () => {
    expect(
      resolveUploadFallbackUrl(
        "/api/uploads/thumbnails/example.jpg",
        "http://localhost:8001"
      )
    ).toBe("/api/uploads/thumbnails/example.jpg");
  });

  it("returns empty fallback when backend is not configured", () => {
    expect(resolveUploadFallbackUrl("/api/uploads/thumbnails/example.jpg", "")).toBe(
      ""
    );
  });
});
