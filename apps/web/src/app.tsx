import { Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';

// Layouts
import DashboardLayout from '@components/layout/DashboardLayout';

// Pages (lazy loaded)
const Dashboard = lazy(() => import('@pages/Dashboard'));
const ProjectView = lazy(() => import('@pages/ProjectView'));
const MapEditor = lazy(() => import('@pages/MapEditor'));
const HexEditor = lazy(() => import('@pages/HexEditor'));
const SimulationView = lazy(() => import('@pages/SimulationView'));
const Settings = lazy(() => import('@pages/Settings'));
const Login = lazy(() => import('@pages/Login'));

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-screen bg-cyber-bg">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-2 border-cyber-primary/30 border-t-cyber-primary rounded-full animate-spin" />
        <p className="text-cyber-primary font-mono text-sm animate-pulse-glow">
          LOADING...
        </p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/:id" element={<ProjectView />} />
          <Route path="/project/:id/map/:mapId" element={<MapEditor />} />
          <Route path="/project/:id/hex" element={<HexEditor />} />
          <Route path="/project/:id/simulation" element={<SimulationView />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </Suspense>
  );
}