import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import api from "../api/client";
import type { TokenResponse } from "../types";

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("scoutlens_token")
  );

  const handleAuth = useCallback(async (endpoint: string, email: string, password: string) => {
    const { data } = await api.post<TokenResponse>(endpoint, { email, password });
    localStorage.setItem("scoutlens_token", data.access_token);
    setToken(data.access_token);
  }, []);

  const login = useCallback(
    (email: string, password: string) => handleAuth("/auth/login", email, password),
    [handleAuth]
  );

  const register = useCallback(
    (email: string, password: string) => handleAuth("/auth/register", email, password),
    [handleAuth]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("scoutlens_token");
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
