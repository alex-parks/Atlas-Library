// frontend/src/App.jsx - SIMPLE VERSION
import React, { useState, useEffect } from 'react';
import { Library, Briefcase, Bot, Package } from 'lucide-react';
import AssetLibrary from './components/AssetLibrary';
import ProducerTools from './components/ProducerTools';
import AITools from './components/AITools';
import DeliveryTool from './components/DeliveryTool';

const App = () => {
  const [activeTab, setActiveTab] = useState('delivery-tool'); // Start with delivery tool
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [apiStatus, setApiStatus] = useState('connected'); // Assume it's working

  // Simple API check - just once
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.ok ? setApiStatus('connected') : setApiStatus('disconnected'))
      .catch(() => setApiStatus('disconnected'));
  }, []);

  const tabs = [
    {
      id: 'delivery-tool',
      name: 'Delivery Tool',
      icon: Package,
      component: DeliveryTool
    },
    {
      id: 'asset-library',
      name: 'Asset Library',
      icon: Library,
      component: AssetLibrary
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

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || DeliveryTool;

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
              <h2 className="text-xl font-semibold text-white">
                {tabs.find(tab => tab.id === activeTab)?.name}
              </h2>
              <div className="text-sm text-neutral-400">
                Blacksmith VFX Company
              </div>
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
          <ActiveComponent />
        </div>
      </div>
    </div>
  );
};

export default App;