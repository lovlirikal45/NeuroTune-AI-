import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  Activity, 
  Zap, 
  Thermometer,
  Plus,
  FolderOpen
} from 'lucide-react';
import { useProjectStore } from '@stores/projectStore';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { projects, currentProject } = useProjectStore();

  const stats = [
    { icon: FolderOpen, label: 'Projects', value: projects.length, color: 'text-cyber-primary' },
    { icon: Activity, label: 'Active Maps', value: '24', color: 'text-cyber-accent' },
    { icon: Zap, label: 'Simulations', value: '156', color: 'text-cyber-secondary' },
    { icon: Thermometer, label: 'AI Score', value: '92%', color: 'text-cyber-warning' }
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-mono glow-text">DASHBOARD</h1>
          <p className="text-gray-500 text-sm mt-1">
            Welcome back, Tuner
          </p>
        </div>
        
        <button className="btn-cyber flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Project
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="card-cyber">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-xs font-mono">{stat.label}</p>
                <p className={`text-2xl font-bold font-mono mt-1 ${stat.color}`}>
                  {stat.value}
                </p>
              </div>
              <stat.icon className={`w-8 h-8 ${stat.color} opacity-50`} />
            </div>
          </div>
        ))}
      </div>

      {/* Recent Projects */}
      <div className="card-cyber">
        <h2 className="text-lg font-mono text-cyber-primary mb-4">
          RECENT PROJECTS
        </h2>
        
        {projects.length === 0 ? (
          <div className="text-center py-12">
            <FolderOpen className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 font-mono">No projects yet</p>
            <button className="btn-cyber mt-4 inline-flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Create First Project
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {projects.map((project) => (
              <Link
                key={project.id}
                to={`/project/${project.id}`}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-cyber-border/20 transition-colors border border-transparent hover:border-cyber-border"
              >
                <div>
                  <p className="font-mono text-sm text-white">{project.name}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {project.ecuType || 'Unknown'} • {project.status}
                  </p>
                </div>
                <div className="text-xs text-gray-600 font-mono">
                  {new Date(project.createdAt).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card-cyber">
          <h3 className="font-mono text-sm text-cyber-primary mb-3">AI ANALYSIS</h3>
          <p className="text-gray-500 text-sm">Run AI-powered map detection and optimization</p>
          <button className="btn-cyber mt-3 text-sm">Start Analysis</button>
        </div>
        
        <div className="card-cyber">
          <h3 className="font-mono text-sm text-cyber-primary mb-3">SIMULATION</h3>
          <p className="text-gray-500 text-sm">Test your calibration with the digital twin engine</p>
          <button className="btn-cyber mt-3 text-sm">Launch Simulator</button>
        </div>
      </div>
    </div>
  );
}