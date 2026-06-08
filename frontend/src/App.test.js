jest.mock("./contexts/AuthContext", () => ({
  useAuth: jest.fn(),
  AuthProvider: ({ children }) => children,
}));

jest.mock("./contexts/LanguageContext", () => ({
  useLanguage: () => ({ t: (k) => k, language: "en", setLanguage: jest.fn() }),
  LanguageProvider: ({ children }) => children,
}));

jest.mock("./lib/api", () => ({
  API: {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn(() => Promise.resolve({ data: {} })),
    interceptors: { response: { use: jest.fn() } },
  },
  setSessionExpiredHandler: jest.fn(),
  formatError: (e) => e?.message || "error",
  BACKEND_URL: "http://localhost:8001",
}));

import { render, screen } from "@testing-library/react";
import { ProtectedRoute } from "./components/ProtectedRoute";

const { useAuth } = require("./contexts/AuthContext");

describe("ProtectedRoute", () => {
  it("shows loading spinner while auth is loading", () => {
    useAuth.mockReturnValue({ user: null, loading: true });
    render(
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    );
    expect(screen.queryByText("Secret")).not.toBeInTheDocument();
  });

  it("redirects unauthenticated users away from protected content", () => {
    useAuth.mockReturnValue({ user: null, loading: false });
    render(
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    );
    expect(screen.queryByText("Secret")).not.toBeInTheDocument();
  });

  it("renders children for authenticated users", () => {
    useAuth.mockReturnValue({
      user: { id: "1", role: "student" },
      loading: false,
    });
    render(
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Secret")).toBeInTheDocument();
  });

  it("blocks users without required role", () => {
    useAuth.mockReturnValue({
      user: { id: "1", role: "student" },
      loading: false,
    });
    render(
      <ProtectedRoute roles={["admin"]}>
        <div>Admin only</div>
      </ProtectedRoute>
    );
    expect(screen.queryByText("Admin only")).not.toBeInTheDocument();
  });
});

describe("App", () => {
  it("loads the root App module", () => {
    const App = require("./App").default;
    expect(typeof App).toBe("function");
  });
});
