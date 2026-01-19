import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './shared/contexts/AuthContext';
import { Layout } from './shared/components/Layout';
import { ProtectedRoute } from './shared/components/ProtectedRoute';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { HoldingsPage } from './pages/holdings/HoldingsPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { PortfolioListPage } from './pages/portfolios/PortfolioListPage';
import { PortfolioDetailPage } from './pages/portfolios/PortfolioDetailPage';

/**
 * App is the root component that sets up routing and auth context.
 */
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes with layout */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/portfolios" replace />} />
            <Route path="portfolios" element={<PortfolioListPage />} />
            <Route path="portfolios/:id" element={<PortfolioDetailPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="holdings" element={<HoldingsPage />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/portfolios" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
