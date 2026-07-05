import { useState } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { API } from "@/lib/api";

jest.mock("@/lib/api", () => {
  const actual = jest.requireActual("@/lib/api");
  return {
    ...actual,
    API: {
      get: jest.fn(),
      post: jest.fn(),
      interceptors: { response: { use: jest.fn() } },
    },
    setSessionExpiredHandler: jest.fn(),
  };
});

const TestComponent = () => {
  const { user, loading, login } = useAuth();
  const [error, setError] = useState(null);
  return (
    <div>
      <div data-testid="user">{user === null ? "null" : JSON.stringify(user)}</div>
      <div data-testid="loading">{loading ? "loading" : "not-loading"}</div>
      <div data-testid="error">{error ? error.message : "no-error"}</div>
      <button
        onClick={async () => {
          try {
            await login("a@b.com", "pass");
          } catch (err) {
            setError(err);
          }
        }}
      >
        Login
      </button>
    </div>
  );
};

const renderProvider = () =>
  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

describe("AuthProvider", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("runs an initial session check on mount", async () => {
    API.get.mockResolvedValueOnce({ data: { id: "1", role: "student" } });

    renderProvider();

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading")
    );
    expect(API.get).toHaveBeenCalledWith("/auth/me");
  });

  it("verifies the session via /auth/me after login", async () => {
    API.get.mockResolvedValueOnce({ data: null }); // initial checkAuth
    API.post.mockResolvedValueOnce({
      data: { id: "1", email: "a@b.com", role: "student" },
    });
    API.get.mockResolvedValueOnce({
      data: { id: "1", email: "a@b.com", role: "student" },
    });

    renderProvider();

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading")
    );

    await userEvent.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading")
    );

    expect(API.post).toHaveBeenCalledWith("/auth/login", {
      email: "a@b.com",
      password: "pass",
    });
    expect(API.get).toHaveBeenLastCalledWith("/auth/me");
    expect(screen.getByTestId("user")).toHaveTextContent("student");
  });

  it("fails login and clears user when the session cannot be verified", async () => {
    API.get.mockResolvedValueOnce({ data: null }); // initial checkAuth
    API.post.mockResolvedValueOnce({
      data: { id: "1", email: "a@b.com", role: "student" },
    });
    API.get.mockRejectedValueOnce(new Error("Not authenticated"));

    renderProvider();

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading")
    );

    await userEvent.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading")
    );

    expect(screen.getByTestId("user")).toHaveTextContent("false");
    expect(screen.getByTestId("error")).toHaveTextContent(
      "Login succeeded, but the browser could not establish a session"
    );
  });
});
