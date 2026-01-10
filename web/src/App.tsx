import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './shared/components/Layout';
import { LoadingSpinner } from './shared/components/LoadingSpinner';
import { ErrorMessage } from './shared/components/ErrorMessage';
import { useSessionProvider, SessionProvider } from './shared/hooks/useSession';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { HoldingsPage } from './pages/holdings/HoldingsPage';

/**
 * SessionWrapper provides session context to the entire application.
 */
function SessionWrapper({ children }: { children: React.ReactNode }) {
  const sessionState = useSessionProvider();

  if (sessionState.isLoading) {
    return (
      <div className="app-loading">
        <LoadingSpinner size="large" message="Initializing session..." />
      </div>
    );
  }

  if (sessionState.error) {
    return (
      <div className="app-error">
        <ErrorMessage
          title="Session Error"
          message={sessionState.error}
          onRetry={sessionState.refreshSession}
        />
      </div>
    );
  }

  return (
    <SessionProvider value={sessionState}>{children}</SessionProvider>
  );
}

/**
 * App is the root component that sets up routing and session management.
 */
function App() {
  return (
    <BrowserRouter>
      <SessionWrapper>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="holdings" element={<HoldingsPage />} />
          </Route>
        </Routes>
      </SessionWrapper>
    </BrowserRouter>
  );
}

export default App;
