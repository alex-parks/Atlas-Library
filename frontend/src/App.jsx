// frontend/src/App.jsx
import React, { useState } from 'react';
import { Library, Briefcase, Bot, ChevronRight } from 'lucide-react';
import AssetLibrary from './components/AssetLibrary';
import ProducerTools from './components/ProducerTools';
import AITools from './components/AITools';

const App = () => {
  const [activeTab, setActiveTab] = useState('asset-library');
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  const tabs = [
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

  const activeComponent = tabs.find(tab => tab.id === activeTab)?.component || AssetLibrary;
  const ActiveComponent = activeComponent;

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
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-neutral-400">Connected</span>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          <ActiveComponent />
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