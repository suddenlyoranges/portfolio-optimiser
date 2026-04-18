import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import Layout from "./components/common/Layout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import PortfolioPage from "./pages/PortfolioPage";
import OptimisationPage from "./pages/OptimisationPage";
import BacktestPage from "./pages/BacktestPage";
import HedgingPage from "./pages/HedgingPage";
import ComparePage from "./pages/ComparePage";
import ProtectedRoute from "./components/auth/ProtectedRoute";

export default function App() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" /> : <LoginPage />}
      />
      <Route
        path="/register"
        element={user ? <Navigate to="/" /> : <RegisterPage />}
      />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/portfolio/:id" element={<PortfolioPage />} />
          <Route
            path="/portfolio/:id/optimise"
            element={<OptimisationPage />}
          />
          <Route path="/portfolio/:id/backtest" element={<BacktestPage />} />
          <Route path="/portfolio/:id/hedge" element={<HedgingPage />} />
          <Route path="/compare" element={<ComparePage />} />
        </Route>
      </Route>
    </Routes>
  );
}
