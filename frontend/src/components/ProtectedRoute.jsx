import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ requireOnboarded = false }) {
  const { profile, loading } = useAuth();

  if (loading) return <div className="page-loading">Loading…</div>;
  if (!profile) return <Navigate to="/login" replace />;
  if (requireOnboarded && !profile.onboarding_complete) {
    return <Navigate to="/onboarding" replace />;
  }
  return <Outlet />;
}
