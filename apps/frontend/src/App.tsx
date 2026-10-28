import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { TelemetryPage } from './pages/TelemetryPage';
import { CartesianPage } from './pages/CartesianPage';
import { TrajectoryPage } from './pages/TrajectoryPage';
import { MathLabPage } from './pages/MathLabPage';

export default function App() {
  return <Routes>
    <Route element={<Layout />}>
      <Route index element={<DashboardPage />} />
      <Route path="telemetry" element={<TelemetryPage />} />
      <Route path="cartesian" element={<CartesianPage />} />
      <Route path="trajectory" element={<TrajectoryPage />} />
      <Route path="math" element={<MathLabPage />} />
      <Route path="visao-publica">
        <Route index element={<DashboardPage />} />
        <Route path="telemetry" element={<TelemetryPage />} />
        <Route path="cartesian" element={<CartesianPage />} />
        <Route path="trajectory" element={<TrajectoryPage />} />
        <Route path="math" element={<MathLabPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route>
  </Routes>;
}
