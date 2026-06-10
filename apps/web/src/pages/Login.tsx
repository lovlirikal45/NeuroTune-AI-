import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cpu, Lock, Mail } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement login
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyber-primary/10 border border-cyber-primary/30 mb-4">
            <Cpu className="w-8 h-8 text-cyber-primary" />
          </div>
          <h1 className="text-3xl font-bold font-mono glow-text">NEUROTUNE AI</h1>
          <p className="text-gray-500 text-sm mt-2">Professional ECU Calibration Platform</p>
        </div>

        {/* Login form */}
        <div className="card-cyber">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-gray-400 mb-1">
                EMAIL
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-600 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-cyber pl-9 w-full"
                  placeholder="tuner@workshop.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-gray-400 mb-1">
                PASSWORD
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-600 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-cyber pl-9 w-full"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn-cyber w-full text-base py-3">
              AUTHENTICATE
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-cyber-border text-center">
            <p className="text-xs text-gray-600">
              Secured with AES-256-GCM • End-to-end encryption
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}