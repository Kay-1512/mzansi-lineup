import { createContext, useContext, useEffect, useState } from "react";
import * as authApi from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refreshProfile() {
    try {
      const data = await authApi.getProfile();
      setProfile(data);
      return data;
    } catch {
      setProfile(null);
      return null;
    }
  }

  useEffect(() => {
    const hasToken = Boolean(localStorage.getItem("access_token"));
    if (!hasToken) {
      setLoading(false);
      return;
    }
    refreshProfile().finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    await authApi.login(email, password);
    return refreshProfile();
  }

  async function register(email, password) {
    await authApi.register(email, password);
    return login(email, password);
  }

  function logout() {
    authApi.logout();
    setProfile(null);
  }

  const value = { profile, loading, login, register, logout, refreshProfile };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
