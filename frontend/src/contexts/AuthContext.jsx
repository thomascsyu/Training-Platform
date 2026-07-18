import { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
import { API, setSessionExpiredHandler } from "@/lib/api";

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(false));
    return () => setSessionExpiredHandler(null);
  }, []);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await API.get("/auth/me");
      setUser(data);
    } catch {
      setUser(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const _verifySession = useCallback(async () => {
    // The login/register endpoints return the user object in the JSON body, but
    // real session persistence depends on HTTP-only cookies. Re-fetch /me so
    // we fail fast here if the browser didn't store/send cookies, instead of
    // navigating to a protected route and immediately being bounced back.
    try {
      const { data } = await API.get("/auth/me");
      return data;
    } catch (err) {
      // Replace the low-level API error with a clear message so the UI doesn't
      // just flash "Not authenticated" after a successful login.
      const sessionError = new Error(
        "Login succeeded, but the browser could not establish a session. " +
          "Ensure the frontend proxies /api to the backend (BACKEND_PROXY_URL) " +
          "or configure CORS, COOKIE_SAMESITE=none, and COOKIE_SECURE=true for cross-origin API access."
      );
      sessionError.cause = err;
      throw sessionError;
    }
  }, []);

  const login = useCallback(
    async (email, password) => {
      setLoading(true);
      try {
        const { data } = await API.post("/auth/login", { email, password });
        setUser(data);
        const me = await _verifySession();
        setUser(me);
        return me;
      } catch (err) {
        setUser(false);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [_verifySession]
  );

  const register = useCallback(
    async (email, password, name) => {
      setLoading(true);
      try {
        const { data } = await API.post("/auth/register", {
          email,
          password,
          name,
          role: "student",
        });
        setUser(data);
        const me = await _verifySession();
        setUser(me);
        return me;
      } catch (err) {
        setUser(false);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [_verifySession]
  );

  const logout = useCallback(async () => {
    await API.post("/auth/logout");
    setUser(false);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, checkAuth }),
    [user, loading, login, register, logout, checkAuth]
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};
