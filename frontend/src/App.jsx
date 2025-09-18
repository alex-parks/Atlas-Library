// frontend/src/App.jsx - SIMPLE VERSION
import React, { useState, useEffect } from 'react';
import { Library } from 'lucide-react';
import AssetLibrary from './components/AssetLibrary';

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.props.setHasError(true);
    this.props.setErrorMessage(error.message || 'An unexpected error occurred');
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center p-8">
            <h2 className="text-xl font-bold text-red-400 mb-4">Component Error</h2>
            <p className="text-neutral-300">This component encountered an error.</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const App = () => {
  // Set the default active tab to something other than delivery-tool
  const [activeTab, setActiveTab] = useState('asset-library'); // Start with asset library
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [apiStatus, setApiStatus] = useState('connected'); // Assume it's working
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Theme state for sharing with AssetLibrary
  const [darkMode, setDarkMode] = useState(true);
  const [accentColor, setAccentColor] = useState('blue');
  
  // Database status for Asset Library
  const [dbStatus, setDbStatus] = useState({
    status: 'loading',
    assets_count: 0
  });

  // Initialize theme and settings on app startup
  useEffect(() => {
    // Load saved theme settings
    const savedDarkMode = localStorage.getItem('darkMode');
    const savedAccentColor = localStorage.getItem('accentColor');
    
    if (savedDarkMode !== null) {
      setDarkMode(JSON.parse(savedDarkMode));
    }
    if (savedAccentColor) {
      setAccentColor(savedAccentColor);
    }
  }, []);
  
  // Apply theme changes
  useEffect(() => {
    // Apply dark mode
    if (darkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
    
    // Apply accent color
    const colors = {
      blue: { primary: '#3b82f6', hover: '#2563eb' },
      purple: { primary: '#8b5cf6', hover: '#7c3aed' },
      green: { primary: '#10b981', hover: '#059669' },
      orange: { primary: '#f59e0b', hover: '#d97706' },
      red: { primary: '#ef4444', hover: '#dc2626' },
      white: { primary: '#ffffff', hover: '#f3f4f6' },
      lightgray: { primary: '#9ca3af', hover: '#6b7280' },
      darkgray: { primary: '#4b5563', hover: '#374151' }
    };
    
    const root = document.documentElement;
    root.style.setProperty('--accent-primary', colors[accentColor].primary);
    root.style.setProperty('--accent-hover', colors[accentColor].hover);
  }, [darkMode, accentColor]);

  // Simple API check - just once
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.ok ? setApiStatus('connected') : setApiStatus('disconnected'))
      .catch((error) => {
        console.error('API health check failed:', error);
        setApiStatus('disconnected');
      });
  }, []);

  const tabs = [
    {
      id: 'asset-library',
      name: 'Asset Library',
      icon: Library,
      component: AssetLibrary
    },
    // {
    //   id: 'delivery-tool',
    //   name: 'Delivery Tool',
    //   icon: Package,
    //   component: DeliveryTool
    // },
    // {
    //   id: 'producer-tools',
    //   name: 'Producer Tools',
    //   icon: Briefcase,
    //   component: ProducerTools
    // },
  ];

  // Theme handler functions
  const handleDarkModeToggle = (newDarkMode) => {
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', JSON.stringify(newDarkMode));
  };

  const handleAccentColorChange = (color) => {
    setAccentColor(color);
    localStorage.setItem('accentColor', color);
  };

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || AssetLibrary;

  // Error boundary fallback
  if (hasError) {
    return (
      <div className="flex h-screen bg-neutral-900 text-white items-center justify-center">
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Application Error</h1>
          <p className="text-neutral-300 mb-4">{errorMessage}</p>
          <button 
            onClick={() => {
              setHasError(false);
              setErrorMessage('');
              window.location.reload();
            }}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
          >
            Reload Application
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-neutral-900 text-white overflow-hidden">
      {/* Sidebar */}
      <div
        className={`bg-neutral-800 border-r border-neutral-700 transition-all duration-300 ease-in-out ${
          sidebarExpanded ? 'w-64' : 'w-16'
        } flex flex-col`}
        onMouseEnter={() => setSidebarExpanded(true)}
        onMouseLeave={() => setSidebarExpanded(false)}
      >
        {/* Logo/Header */}
        <div className="p-4 border-b border-neutral-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 flex items-center justify-center overflow-hidden">
              <img
                src="/Blacksmith_TopLeft.png"
                alt="Blacksmith"
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback to the original "BA" text if image fails to load
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <span className="text-white font-bold text-sm hidden">BA</span>
            </div>
            {sidebarExpanded && (
              <div>
                <h1 className="text-lg font-bold text-white">Blacksmith</h1>
                <p className="text-xs text-neutral-400">Atlas</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2">
          <ul className="space-y-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <li key={tab.id}>
                  <button
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'text-neutral-400 hover:bg-neutral-700 hover:text-white'
                    }`}
                  >
                    <Icon size={20} className="flex-shrink-0" />
                    {sidebarExpanded && (
                      <span className="text-sm font-medium truncate">{tab.name}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-neutral-800 border-b border-neutral-700 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-200 to-gray-400 bg-clip-text text-transparent">
                {tabs.find(tab => tab.id === activeTab)?.name}
              </h1>
              
              {/* ArangoDB Status - only show in Asset Library */}
              {activeTab === 'asset-library' && (
                <div className="flex items-center gap-2 px-4 py-2 rounded-full text-sm bg-gray-700/50 border border-gray-600/30 backdrop-blur-sm shadow-sm">
                  <div className={`w-3 h-3 rounded-full ${
                    dbStatus.status === 'healthy' ? 'bg-emerald-400' :
                    dbStatus.status === 'error' ? 'bg-rose-400' :
                    'bg-amber-400'
                  }`}></div>
                  <span className={`font-medium ${
                    dbStatus.status === 'healthy' ? 'text-emerald-400' :
                    dbStatus.status === 'error' ? 'text-rose-400' :
                    'text-amber-400'
                  }`}>
                    {dbStatus.status === 'healthy' ? 'ArangoDB Ready' :
                     dbStatus.status === 'error' ? 'DB Error' :
                     'DB Unknown'}
                  </span>
                  {dbStatus.assets_count > 0 && (
                    <span className="text-gray-400">({dbStatus.assets_count})</span>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-neutral-400">
                {apiStatus === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          <ErrorBoundary setHasError={setHasError} setErrorMessage={setErrorMessage}>
            <ActiveComponent 
              darkMode={darkMode}
              accentColor={accentColor}
              handleDarkModeToggle={handleDarkModeToggle}
              handleAccentColorChange={handleAccentColorChange}
              onDbStatusChange={setDbStatus}
            />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
};

export default App;