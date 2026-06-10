import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FolderOpen, 
  Map, 
  Cpu, 
  Activity,
  Settings,
  ChevronLeft
} from 'lucide-react';
import { useUIStore } from '@stores/uiStore';
import { useProjectStore } from '@stores/projectStore';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: FolderOpen, label: 'Projects', path: '/projects' },
  { icon: Map, label: 'Maps', path: '/maps' },
  { icon: Cpu, label: 'ECU', path: '/ecu' },
  { icon: Activity, label: 'Simulation', path: '/simulation' }
];

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { currentProject } = useProjectStore();
  const location = useLocation();

  return (
    <aside
      className={`${
        sidebarOpen ? 'w-64' : 'w-16'
      } bg-cyber-surface border-r border-cyber-border transition-all duration-300 flex flex-col`}
    >
      {/* Toggle button */}
      <button
        onClick={toggleSidebar}
        className="p-3 hover:bg-cyber-border/50 transition-colors flex justify-end"
      >
        <ChevronLeft
          className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${
            !sidebarOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30'
                  : 'text-gray-400 hover:text-white hover:bg-cyber-border/30'
              }`}
            >
              <item.icon className={`w-5 h-5 ${isActive ? 'text-cyber-primary' : ''}`} />
              {sidebarOpen && (
                <span className="font-mono text-sm">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Current project info */}
      {sidebarOpen && currentProject && (
        <div className="p-4 border-t border-cyber-border">
          <div className="text-xs text-gray-500 font-mono mb-1">CURRENT PROJECT</div>
          <div className="text-sm text-cyber-primary font-mono truncate">
            {currentProject.name}
          </div>
          <div className="text-xs text-gray-600 font-mono mt-1">
            {currentProject.ecuType || 'Unknown ECU'}
          </div>
        </div>
      )}

      {/* Settings */}
      <Link
        to="/settings"
        className="flex items-center gap-3 px-4 py-3 mx-2 mb-4 text-gray-400 hover:text-white hover:bg-cyber-border/30 rounded-lg transition-all"
      >
        <Settings className="w-5 h-5" />
        {sidebarOpen && <span className="font-mono text-sm">Settings</span>}
      </Link>
    </aside>
  );
}