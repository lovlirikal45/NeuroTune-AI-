import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import StatusBar from './StatusBar';

export default function DashboardLayout() {
  return (
    <div className="h-screen flex flex-col bg-cyber-bg overflow-hidden">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto hex-grid">
          <Outlet />
        </main>
      </div>
      <StatusBar />
    </div>
  );
}