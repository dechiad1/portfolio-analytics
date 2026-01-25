import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './shared/contexts/AuthContext';
import { Layout } from './shared/components/Layout';
import { ProtectedRoute } from './shared/components/ProtectedRoute';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { LoginPage } from './pages/auth/LoginPage';
import { PortfolioListPage } from './pages/portfolios/PortfolioListPage';
import { PortfolioDetailPage } from './pages/portfolios/PortfolioDetailPage';
import { SecuritiesPage } from './pages/securities/SecuritiesPage';
import { SimulationDetailPage } from './pages/simulations/SimulationDetailPage';

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
            <Route path="portfolios/:portfolioId/simulations/:simulationId" element={<SimulationDetailPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="securities" element={<SecuritiesPage />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/portfolios" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
