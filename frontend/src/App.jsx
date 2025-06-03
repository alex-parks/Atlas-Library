// frontend/src/App.jsx - TEMPORARY DEBUG VERSION
import React, { useState, useEffect } from 'react';
import { Library, Briefcase, Bot, Package, ChevronRight } from 'lucide-react';
import AssetLibrary from './components/AssetLibrary';
import ProducerTools from './components/ProducerTools';
import AITools from './components/AITools';
import DeliveryTool from './components/DeliveryTool';

const App = () => {
  const [activeTab, setActiveTab] = useState('asset-library');
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');

  // Test API connection on startup
  useEffect(() => {
    const testAPI = async () => {
      try {
        console.log('Testing API connection...');
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
          const data = await response.json();
          console.log('API response:', data);
          setApiStatus('connected');
        } else {
          console.error('API responded with error:', response.status);
          setApiStatus('error');
        }
      } catch (error) {
        console.error('API connection failed:', error);
        setApiStatus('disconnected');
      }
    };

    testAPI();
  }, []);

  const tabs = [
    {
      id: 'asset-library',
      name: 'Asset Library',
      icon: Library,
      component: AssetLibrary
    },
    {
      id: 'delivery-tool',
      name: 'Delivery Tool',
      icon: Package,
      component: DeliveryTool
    },
    {
      id: 'producer-tools',
      name: 'Producer Tools',
      icon: Briefcase,
      component: ProducerTools
    },
    {
      id: 'ai-tools',
      name: 'AI Tools',
      icon: Bot,
      component: AITools
    }
  ];

  const activeComponent = tabs.find(tab => tab.id === activeTab)?.component || AssetLibrary;
  const ActiveComponent = activeComponent;

  return (
    <div className="flex h-screen bg-neutral-900 text-white overflow-hidden">
      {/* Debug Panel - Remove this after fixing */}
      <div className="absolute top-0 right-0 z-50 bg-red-900 text-white p-2 m-2 rounded text-xs">
        <div>App Status: Running</div>
        <div>API Status: {apiStatus}</div>
        <div>React: OK</div>
        <div>Port: 3000</div>
      </div>

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
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">BA</span>
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
                    {!sidebarExpanded && isActive && (
                      <div className="absolute left-14 bg-neutral-800 text-white px-2 py-1 rounded text-xs whitespace-nowrap border border-neutral-600 shadow-lg">
                        {tab.name}
                      </div>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-neutral-600 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">U</span>
            </div>
            {sidebarExpanded && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">User</p>
                <p className="text-xs text-neutral-400 truncate">user@blacksmith.com</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-neutral-800 border-b border-neutral-700 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-white">
                {tabs.find(tab => tab.id === activeTab)?.name}
              </h2>
              <div className="text-sm text-neutral-400">
                Blacksmith VFX Company
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'connected' ? 'bg-green-500' : 
                apiStatus === 'disconnected' ? 'bg-red-500' : 
                'bg-yellow-500'
              }`}></div>
              <span className="text-sm text-neutral-400">
                {apiStatus === 'connected' ? 'Connected' :
                 apiStatus === 'disconnected' ? 'Disconnected' :
                 'Checking...'}
              </span>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          {apiStatus === 'checking' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-neutral-400">Connecting to backend...</p>
              </div>
            </div>
          )}
          {apiStatus === 'disconnected' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="text-red-500 text-6xl mb-4">⚠️</div>
                <h3 className="text-xl font-semibold text-white mb-2">Backend Disconnected</h3>
                <p className="text-neutral-400 mb-4">
                  Cannot connect to the backend API at http://localhost:8000
                </p>
                <p className="text-sm text-neutral-500">
                  Make sure your backend is running with: <code>cd backend && python -m uvicorn main:app --reload --port 8000</code>
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-4 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          )}
          {apiStatus === 'connected' && <ActiveComponent />}
        </div>
      </div>

      {/* Hover Trigger Area */}
      <div
        className="absolute left-0 top-0 w-4 h-full z-10"
        onMouseEnter={() => setSidebarExpanded(true)}
      />
    </div>
  );
};

export default App;