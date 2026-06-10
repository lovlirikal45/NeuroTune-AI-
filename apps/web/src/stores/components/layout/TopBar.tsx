import { Menu, Search, Bell, User } from 'lucide-react';
import { useUIStore } from '@stores/uiStore';

export default function TopBar() {
  const { toggleSidebar } = useUIStore();

  return (
    <header className="h-12 bg-cyber-surface border-b border-cyber-border flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-1 hover:bg-cyber-border/30 rounded transition-colors"
        >
          <Menu className="w-5 h-5 text-gray-400" />
        </button>
        
        <div className="flex items-center gap-2">
          <span className="text-cyber-primary font-bold text-lg font-mono tracking-wider">
            NEUROTUNE
          </span>
          <span className="text-xs text-gray-600 font-mono">AI v1.0</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search maps, projects..."
            className="input-cyber pl-9 w-64 text-xs"
          />
        </div>

        {/* Notifications */}
        <button className="p-2 hover:bg-cyber-border/30 rounded transition-colors relative">
          <Bell className="w-4 h-4 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-cyber-danger rounded-full" />
        </button>

        {/* User */}
        <button className="flex items-center gap-2 p-2 hover:bg-cyber-border/30 rounded transition-colors">
          <div className="w-7 h-7 rounded-full bg-cyber-primary/20 border border-cyber-primary/30 flex items-center justify-center">
            <User className="w-4 h-4 text-cyber-primary" />
          </div>
        </button>
      </div>
    </header>
  );
}