import { createContext, useContext, useEffect, useState } from "react";
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

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      const { data } = await API.get("/auth/me");
      setUser(data);
    } catch {
      setUser(false);
    } finally {
      setLoading(false);
    }
  };

  const _verifySession = async (user) => {
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
          "This usually means cookies are blocked by CORS, HTTPS, or browser settings."
      );
      sessionError.cause = err;
      throw sessionError;
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    try {
      const { data } = await API.post("/auth/login", { email, password });
      setUser(data);
      const me = await _verifySession(data);
      setUser(me);
      return me;
    } catch (err) {
      setUser(false);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password, name) => {
    setLoading(true);
    try {
      const { data } = await API.post("/auth/register", {
        email,
        password,
        name,
        role: "student",
      });
      setUser(data);
      const me = await _verifySession(data);
      setUser(me);
      return me;
    } catch (err) {
      setUser(false);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await API.post("/auth/logout");
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
