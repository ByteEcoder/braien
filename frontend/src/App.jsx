import React, { useState, useEffect, useRef } from 'react';
import { Monitor, X, Loader, AlertCircle, Globe, Zap, Layers, Code, Shield, Cpu, HardDrive, Eye, ExternalLink, Activity, Server, Network } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// Utility Components
const StatCard = ({ icon: Icon, label, value, unit, gradient, isLoading = false }) => (
  <div className={`relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br ${gradient} border border-white/20 backdrop-blur-sm hover:border-white/30 transition-all duration-300`}>
    <div className="relative z-10 flex items-center justify-between">
      <div>
        <p className="text-white/80 text-sm font-medium">{label}</p>
        <div className="flex items-baseline mt-1">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <Loader className="w-5 h-5 text-white animate-spin" />
              <span className="text-white/60">Loading...</span>
            </div>
          ) : (
            <>
              <span className="text-3xl font-bold text-white">
                {typeof value === 'number' ? Math.round(value) : value}
              </span>
              {unit && <span className="text-lg font-normal text-white/80 ml-1">{unit}</span>}
            </>
          )}
        </div>
      </div>
      <div className="p-3 rounded-xl bg-white/20 backdrop-blur-sm">
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
    <div className="absolute inset-0 bg-gradient-to-r from-white/5 to-transparent opacity-50"></div>
  </div>
);

const BrowserOption = ({ 
  name, 
  icon: Icon, 
  available, 
  onClick, 
  description, 
  gradient, 
  isLaunching = false 
}) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <div 
      className={`group relative overflow-hidden rounded-2xl cursor-pointer transition-all duration-500 transform hover:scale-105 ${
        available 
          ? 'hover:shadow-2xl' 
          : 'cursor-not-allowed opacity-60'
      } ${isLaunching ? 'animate-pulse' : ''}`}
      onClick={available && !isLaunching ? onClick : undefined}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-90 group-hover:opacity-100 transition-opacity duration-300`}></div>
      <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors duration-300"></div>
      
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-4 -right-4 w-24 h-24 bg-white/10 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute -bottom-6 -left-6 w-32 h-32 bg-white/5 rounded-full blur-2xl animate-pulse delay-1000"></div>
      </div>
      
      <div className="relative z-10 p-8 h-full flex flex-col items-center justify-center space-y-4 text-center">
        <div className="p-4 rounded-2xl bg-white/20 backdrop-blur-sm group-hover:bg-white/30 transition-colors duration-300">
          {isLaunching ? (
            <Loader className="animate-spin text-white" size={48} />
          ) : (
            <Icon size={48} className="text-white" />
          )}
        </div>
        <div>
          <h3 className="font-bold text-xl text-white mb-2">{name}</h3>
          <p className="text-white/80 text-sm mb-3">{description}</p>
          {isLaunching ? (
            <div className="flex items-center justify-center space-x-2 px-4 py-2 bg-blue-500/30 rounded-full backdrop-blur-sm">
              <Loader className="w-4 h-4 text-white animate-spin" />
              <span className="text-white font-medium text-sm">Launching...</span>
            </div>
          ) : available ? (
            <div className="flex items-center justify-center space-x-2 px-4 py-2 bg-white/20 rounded-full backdrop-blur-sm group-hover:bg-white/30 transition-colors duration-300">
              <Zap className="w-4 h-4 text-white" />
              <span className="text-white font-medium text-sm">Launch Now</span>
            </div>
          ) : (
            <div className="px-4 py-2 bg-white/10 rounded-full backdrop-blur-sm">
              <span className="text-white/60 font-medium text-sm">Coming Soon</span>
            </div>
          )}
        </div>
      </div>
      
      {isHovered && available && !isLaunching && (
        <div className="absolute inset-0 ring-2 ring-white/50 rounded-2xl animate-pulse"></div>
      )}
    </div>
  );
};

const BrowserSession = ({ session, onClose }) => {
  const [timeActive, setTimeActive] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeActive(Math.floor((new Date() - session.createdAt) / 1000 / 60));
    }, 60000);
    
    // Initial calculation
    setTimeActive(Math.floor((new Date() - session.createdAt) / 1000 / 60));
    
    return () => clearInterval(interval);
  }, [session.createdAt]);
  
  const getBrowserConfig = (browser) => {
    const configs = {
      firefox: {
        icon: Globe,
        name: 'Firefox',
        gradient: 'from-orange-500 to-red-500',
        color: 'orange'
      },
      tor: {
        icon: Eye,
        name: 'Tor Browser',
        gradient: 'from-purple-600 to-indigo-600',
        color: 'purple'
      },
      'tor-browser': {
        icon: Eye,
        name: 'Tor Browser',
        gradient: 'from-purple-600 to-indigo-600',
        color: 'purple'
      }
    };
    
    return configs[browser.toLowerCase()] || {
      icon: Globe,
      name: browser.charAt(0).toUpperCase() + browser.slice(1),
      gradient: 'from-blue-500 to-purple-500',
      color: 'blue'
    };
  };

  const openInNewTab = () => {
    window.open(session.url, '_blank', 'noopener,noreferrer');
  };

  const config = getBrowserConfig(session.browser);
  const BrowserIcon = config.icon;
  
  return (
    <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-700/50 backdrop-blur-sm hover:border-slate-600/50 transition-all duration-500">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-purple-600/5"></div>
      
      <div className="relative z-10 p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg bg-gradient-to-r ${config.gradient}`}>
              <BrowserIcon className="text-white" size={20} />
            </div>
            <div>
              <span className="font-bold text-white text-lg">{config.name}</span>
              <p className="text-slate-400 text-sm">Active for {timeActive}m</p>
            </div>
            <div className="flex items-center space-x-2 px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full backdrop-blur-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-300 text-xs font-medium uppercase tracking-wide">{session.status}</span>
            </div>
          </div>
          <button
            onClick={() => onClose(session.id)}
            className="p-2 hover:bg-red-500/20 rounded-lg text-slate-400 hover:text-red-400 transition-colors duration-200 backdrop-blur-sm"
            title="Close Session"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* Session Info */}
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-slate-300 font-medium">Browser Ready</span>
              {session.port && (
                <span className="text-slate-400 text-xs bg-slate-700/50 px-2 py-1 rounded">
                  Port: {session.port}
                </span>
              )}
            </div>
            <span className="text-slate-400 text-sm font-mono">{session.id.substring(0, 8)}...</span>
          </div>
          
          {/* Launch Button */}
          <button
            onClick={openInNewTab}
            className="w-full p-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-xl text-white font-semibold transition-all duration-300 transform hover:scale-[1.02] hover:shadow-lg flex items-center justify-center space-x-3"
          >
            <BrowserIcon className="w-5 h-5" />
            <span>Open Browser</span>
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

const ErrorAlert = ({ error, onDismiss }) => (
  <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 mb-8 backdrop-blur-sm">
    <div className="flex items-start justify-between">
      <div className="flex items-center space-x-3">
        <AlertCircle className="text-red-400 flex-shrink-0" size={24} />
        <div>
          <span className="text-red-300 text-lg font-medium block">Launch Error</span>
          <p className="text-red-200 text-sm mt-1">{error}</p>
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-400 hover:text-red-300 transition-colors p-1"
        >
          <X size={16} />
        </button>
      )}
    </div>
  </div>
);

const LoadingIndicator = ({ browserName }) => (
  <div className="flex items-center justify-center mt-8 p-6 bg-blue-500/10 border border-blue-500/20 rounded-2xl backdrop-blur-sm">
    <Loader className="animate-spin text-blue-400 mr-3" size={24} />
    <div className="text-center">
      <span className="text-blue-300 text-lg font-medium block">
        Initializing {browserName} container...
      </span>
      <span className="text-blue-200 text-sm">This may take 30-60 seconds</span>
    </div>
  </div>
);

const SystemStats = ({ sessions }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
      <StatCard
        icon={Server}
        label="Active Sessions"
        value={sessions.length}
        unit={sessions.length === 1 ? "container" : "containers"}
        gradient="from-blue-600 to-blue-800"
      />
      <StatCard
        icon={Network}
        label="System Status"
        value="Online"
        gradient="from-green-600 to-green-800"
      />
      <StatCard
        icon={Activity}
        label="Uptime"
        value="99.9"
        unit="%"
        gradient="from-purple-600 to-purple-800"
      />
    </div>
  );
};

// Main App Component
const App = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [launchingBrowser, setLaunchingBrowser] = useState(null);
  const sessionsRef = useRef(new Set());

  // Cleanup function
  const cleanupSession = async (sessionId) => {
    try {
      await fetch(`${API_BASE}/cleanup/${sessionId}`, {
        method: 'DELETE'
      });
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      sessionsRef.current.delete(sessionId);
    } catch (err) {
      console.error('Cleanup error:', err);
    }
  };

  // Handle tab close - cleanup all sessions
  useEffect(() => {
    const handleBeforeUnload = async () => {
      const cleanupPromises = Array.from(sessionsRef.current).map(sessionId => 
        fetch(`${API_BASE}/cleanup/${sessionId}`, { method: 'DELETE' })
      );
      
      try {
        await Promise.all(cleanupPromises);
      } catch (err) {
        console.error('Error during cleanup:', err);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('unload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('unload', handleBeforeUnload);
      handleBeforeUnload();
    };
  }, []);

  const launchBrowser = async (browserType) => {
    setLoading(true);
    setLaunchingBrowser(browserType);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE}/launch-browser`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ browser: browserType })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to launch browser');
      }
      
      const data = await response.json();
      
      const newSession = {
        id: data.session_id,
        browser: browserType,
        url: data.vnc_url,
        status: data.status,
        port: data.port,
        createdAt: new Date()
      };
      
      setSessions(prev => [...prev, newSession]);
      sessionsRef.current.add(data.session_id);
      
    } catch (err) {
      console.error('Error launching browser:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setLaunchingBrowser(null);
    }
  };

  const browserOptions = [
    {
      name: "Firefox",
      icon: Globe,
      available: true,
      description: "Secure, privacy-focused browsing with advanced container isolation",
      gradient: "from-orange-600 to-red-600",
      onClick: () => launchBrowser('firefox')
    },
    {
      name: "Tor",
      icon: Eye,
      available: true,
      description: "Anonymous browsing through the Tor network with maximum privacy",
      gradient: "from-purple-600 to-indigo-600",
      onClick: () => launchBrowser('tor')
    },
    {
      name: "Brave",
      icon: Shield,
      available: false,
      description: "Privacy-first browser with built-in ad blocking",
      gradient: "from-emerald-600 to-teal-600"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>
      
      <div className="relative z-10 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600">
                <Layers className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
                Braien
              </h1>
            </div>
            <p className="text-xl text-slate-300 font-medium">
              Next-Gen Cloud Browser Orchestration Platform
            </p>
            <p className="text-slate-400 mt-2">
              Deploy isolated browser containers with enterprise-grade security
            </p>
          </div>

          {/* System Stats */}
          <SystemStats sessions={sessions} />

          {/* Error Display */}
          {error && (
            <ErrorAlert 
              error={error} 
              onDismiss={() => setError('')} 
            />
          )}

          {/* Browser Selection */}
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 mb-12">
            <div className="flex items-center space-x-3 mb-8">
              <Code className="text-blue-400" size={28} />
              <h2 className="text-3xl font-bold text-white">Launch Browser Environment</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {browserOptions.map((browser) => (
                <BrowserOption
                  key={browser.name}
                  {...browser}
                  isLaunching={launchingBrowser === browser.name.toLowerCase()}
                />
              ))}
            </div>
            
            {loading && (
              <LoadingIndicator browserName={launchingBrowser} />
            )}
          </div>

          {/* Active Sessions */}
          {sessions.length > 0 && (
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8">
              <div className="flex items-center space-x-3 mb-8">
                <Monitor className="text-green-400" size={28} />
                <h2 className="text-3xl font-bold text-white">Active Browser Sessions</h2>
                <div className="flex items-center space-x-2 px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-green-300 text-sm font-medium">{sessions.length} Running</span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {sessions.map(session => (
                  <BrowserSession 
                    key={session.id} 
                    session={session} 
                    onClose={cleanupSession}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Footer Info */}
          <div className="mt-12 text-center space-y-3">
            <div className="flex items-center justify-center space-x-6 text-slate-400">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4" />
                <span className="text-sm">Auto-cleanup on tab close</span>
              </div>
              <div className="flex items-center space-x-2">
                <Eye className="w-4 h-4" />
                <span className="text-sm">Anonymous browsing support</span>
              </div>
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4" />
                <span className="text-sm">Instant container deployment</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;