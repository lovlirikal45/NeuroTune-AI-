import { useEffect, useState } from 'react';
import { Wifi, Cpu, HardDrive, Clock } from 'lucide-react';

export default function StatusBar() {
  const [time, setTime] = useState(new Date());
  const [status, setStatus] = useState<'connected' | 'disconnected'>('connected');

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <footer className="h-7 bg-cyber-surface border-t border-cyber-border flex items-center justify-between px-4 text-xs font-mono shrink-0">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <Wifi className={`w-3 h-3 ${status === 'connected' ? 'text-cyber-accent' : 'text-cyber-danger'}`} />
          <span className={status === 'connected' ? 'text-cyber-accent' : 'text-cyber-danger'}>
            {status.toUpperCase()}
          </span>
        </div>
        
        <div className="flex items-center gap-1 text-gray-500">
          <Cpu className="w-3 h-3" />
          <span>AI ENGINE: ONLINE</span>
        </div>
        
        <div className="flex items-center gap-1 text-gray-500">
          <HardDrive className="w-3 h-3" />
          <span>DB: 45ms</span>
        </div>
      </div>

      <div className="flex items-center gap-4 text-gray-500">
        <span>ENCRYPTED • AES-256</span>
        <span>|</span>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{time.toLocaleTimeString()}</span>
        </div>
      </div>
    </footer>
  );
}