// frontend/src/App.jsx - SIMPLE VERSION
import React, { useState, useEffect } from 'react';
import { Library, Briefcase, Bot, Package, Settings } from 'lucide-react';
import AssetLibrary from './components/AssetLibrary';
import ProducerTools from './components/ProducerTools';
import AITools from './components/AITools';
import DeliveryTool from './components/DeliveryTool/DeliveryTool.jsx';
import SettingsComponent from './components/Settings';

const App = () => {
  const [activeTab, setActiveTab] = useState('delivery-tool'); // Start with delivery tool
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [apiStatus, setApiStatus] = useState('connected'); // Assume it's working

  // Initialize theme and settings on app startup
  useEffect(() => {
    // Always start with dark mode
    document.documentElement.classList.add('dark');
    document.documentElement.classList.remove('light');
    
    // Load saved accent color
    const savedAccentColor = localStorage.getItem('accentColor');
    
    // Apply accent color
    if (savedAccentColor) {
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
      root.style.setProperty('--accent-primary', colors[savedAccentColor].primary);
      root.style.setProperty('--accent-hover', colors[savedAccentColor].hover);
    }
  }, []);

  // Simple API check - just once
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.ok ? setApiStatus('connected') : setApiStatus('disconnected'))
      .catch(() => setApiStatus('disconnected'));
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
    // {
    //   id: 'producer-tools',
    //   name: 'Producer Tools',
    //   icon: Briefcase,
    //   component: ProducerTools
    // },
    {
      id: 'ai-tools',
      name: 'AI Tools',
      icon: Bot,
      component: AITools
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: Settings,
      component: SettingsComponent
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