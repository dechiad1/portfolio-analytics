import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './shared/components/Layout';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { HoldingsPage } from './pages/holdings/HoldingsPage';

/**
 * App is the root component that sets up routing.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="holdings" element={<HoldingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
