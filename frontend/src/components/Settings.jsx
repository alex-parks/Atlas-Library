import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Monitor, Sun, Moon, Palette, Database, Activity, ExternalLink } from 'lucide-react';

const Settings = () => {
  const [darkMode, setDarkMode] = useState(true);
  const [accentColor, setAccentColor] = useState('blue');
  const [databaseStatus, setDatabaseStatus] = useState('checking');

  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode');
    const savedAccentColor = localStorage.getItem('accentColor');
    
    if (savedDarkMode !== null) {
      setDarkMode(JSON.parse(savedDarkMode));
    }
    if (savedAccentColor) {
      setAccentColor(savedAccentColor);
    }

    // Check database status
    checkDatabaseStatus();
  }, []);

  const checkDatabaseStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        const data = await response.json();
        setDatabaseStatus(data.status === 'healthy' ? 'connected' : 'error');
      } else {
        setDatabaseStatus('error');
      }
    } catch (error) {
      setDatabaseStatus('error');
    }
  };

  const openDatabaseHealth = () => {
    // Open database health dashboard in a new tab
    const healthUrl = window.location.origin + '/database-health';
    const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
    
    if (newWindow) {
      newWindow.document.write(`
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Database Health - Blacksmith Atlas</title>
          <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
          <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
          <script src="https://cdn.tailwindcss.com"></script>
          <script>
            tailwind.config = {
              darkMode: 'class',
              theme: {
                extend: {
                  colors: {
                    neutral: {
                      800: '#262626',
                      900: '#171717'
                    }
                  }
                }
              }
            }
          </script>
          <style>
            body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }
          </style>
        </head>
        <body>
          <div id="database-health-root"></div>
          <script>
            // Simple database health dashboard
            const { createElement: h, useState, useEffect } = React;
            
            function DatabaseHealth() {
              const [healthData, setHealthData] = useState(null);
              const [loading, setLoading] = useState(true);
              const [lastUpdate, setLastUpdate] = useState(new Date());
              
              const fetchHealthData = async () => {
                setLoading(true);
                try {
                  const healthRes = await fetch('http://localhost:8000/health');
                  const statsRes = await fetch('http://localhost:8000/api/v1/assets/stats/summary').catch(() => null);
                  
                  const health = healthRes.ok ? await healthRes.json() : { status: 'unhealthy' };
                  const stats = statsRes?.ok ? await statsRes.json() : { total_assets: 0 };
                  
                  setHealthData({ health, stats });
                  setLastUpdate(new Date());
                } catch (error) {
                  setHealthData({ 
                    health: { status: 'unhealthy', error: error.message },
                    stats: { total_assets: 0 }
                  });
                } finally {
                  setLoading(false);
                }
              };
              
              useEffect(() => {
                fetchHealthData();
                const interval = setInterval(fetchHealthData, 30000);
                return () => clearInterval(interval);
              }, []);
              
              if (loading && !healthData) {
                return h('div', { className: 'min-h-screen bg-neutral-900 flex items-center justify-center' },
                  h('div', { className: 'text-white' }, 'Loading database health...')
                );
              }
              
              const health = healthData?.health || {};
              const stats = healthData?.stats || {};
              
              return h('div', { className: 'min-h-screen bg-neutral-900 text-white p-6' }, [
                h('div', { key: 'header', className: 'max-w-7xl mx-auto mb-8' }, [
                  h('h1', { key: 'title', className: 'text-3xl font-bold mb-2' }, 'Database Health Dashboard'),
                  h('p', { key: 'subtitle', className: 'text-neutral-400 mb-4' }, 'Monitor the status and performance of your Atlas database'),
                  h('button', {
                    key: 'refresh',
                    onClick: fetchHealthData,
                    className: 'px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium'
                  }, loading ? 'Refreshing...' : 'Refresh')
                ]),
                h('div', { key: 'grid', className: 'max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' }, [
                  h('div', { key: 'api', className: 'bg-neutral-800 rounded-lg border border-neutral-700 p-6' }, [
                    h('h3', { key: 'title', className: 'font-medium text-white mb-2' }, 'API Server'),
                    h('div', { 
                      key: 'status',
                      className: \`px-3 py-1 rounded-full text-sm \${health.status === 'healthy' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}\`
                    }, health.status || 'Unknown'),
                    h('p', { key: 'service', className: 'text-sm text-neutral-400 mt-2' }, health.service || 'Backend API')
                  ]),
                  h('div', { key: 'db', className: 'bg-neutral-800 rounded-lg border border-neutral-700 p-6' }, [
                    h('h3', { key: 'title', className: 'font-medium text-white mb-2' }, 'ArangoDB'),
                    h('div', { 
                      key: 'status',
                      className: \`px-3 py-1 rounded-full text-sm \${health.database ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}\`
                    }, health.database || 'Disconnected'),
                    h('p', { key: 'info', className: 'text-sm text-neutral-400 mt-2' }, 'Database connectivity')
                  ]),
                  h('div', { key: 'assets', className: 'bg-neutral-800 rounded-lg border border-neutral-700 p-6' }, [
                    h('h3', { key: 'title', className: 'font-medium text-white mb-2' }, 'Asset Library'),
                    h('div', { key: 'count', className: 'text-2xl font-bold text-white' }, stats.total_assets || 0),
                    h('p', { key: 'label', className: 'text-sm text-neutral-400' }, 'Total assets')
                  ])
                ]),
                h('div', { key: 'details', className: 'max-w-7xl mx-auto mt-8 bg-neutral-800 rounded-lg border border-neutral-700 p-6' }, [
                  h('h2', { key: 'title', className: 'text-lg font-semibold text-white mb-4' }, 'System Information'),
                  h('div', { key: 'info', className: 'grid grid-cols-1 md:grid-cols-2 gap-4 text-sm' }, [
                    h('div', { key: 'timestamp' }, [
                      h('p', { key: 'label', className: 'text-neutral-400' }, 'Last Updated'),
                      h('p', { key: 'value', className: 'text-white' }, lastUpdate.toLocaleString())
                    ]),
                    h('div', { key: 'env' }, [
                      h('p', { key: 'label', className: 'text-neutral-400' }, 'Environment'),
                      h('p', { key: 'value', className: 'text-white' }, 'Development')
                    ]),
                    h('div', { key: 'endpoint' }, [
                      h('p', { key: 'label', className: 'text-neutral-400' }, 'API Endpoint'),
                      h('p', { key: 'value', className: 'text-white' }, 'http://localhost:8000')
                    ]),
                    h('div', { key: 'db-name' }, [
                      h('p', { key: 'label', className: 'text-neutral-400' }, 'Database'),
                      h('p', { key: 'value', className: 'text-white' }, 'blacksmith_atlas')
                    ])
                  ])
                ])
              ]);
            }
            
            ReactDOM.render(h(DatabaseHealth), document.getElementById('database-health-root'));
          </script>
        </body>
        </html>
      `);
      newWindow.document.close();
    }
  };

  // Save settings to localStorage and apply theme
  const handleDarkModeToggle = (newDarkMode) => {
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', JSON.stringify(newDarkMode));
    
    // Apply theme to document
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  };

  const handleAccentColorChange = (color) => {
    setAccentColor(color);
    localStorage.setItem('accentColor', color);
    
    // Apply accent color CSS variables
    const root = document.documentElement;
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
    
    root.style.setProperty('--accent-primary', colors[color].primary);
    root.style.setProperty('--accent-hover', colors[color].hover);
  };

  const accentColors = [
    { name: 'Blue', value: 'blue', color: '#3b82f6' },
    { name: 'Purple', value: 'purple', color: '#8b5cf6' },
    { name: 'Green', value: 'green', color: '#10b981' },
    { name: 'Orange', value: 'orange', color: '#f59e0b' },
    { name: 'Red', value: 'red', color: '#ef4444' },
    { name: 'White', value: 'white', color: '#ffffff' },
    { name: 'Light Gray', value: 'lightgray', color: '#9ca3af' },
    { name: 'Dark Gray', value: 'darkgray', color: '#4b5563' }
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <SettingsIcon className="w-6 h-6 text-blue-500" />
          <h1 className="text-2xl font-bold text-white">Settings</h1>
        </div>
        <p className="text-neutral-400">Customize your Blacksmith Atlas experience</p>
      </div>

      {/* Settings Sections */}
      <div className="space-y-8">
        {/* Interface Section */}
        <div className="bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="p-6 border-b border-neutral-700">
            <div className="flex items-center gap-3 mb-2">
              <Monitor className="w-5 h-5 text-blue-500" />
              <h2 className="text-lg font-semibold text-white">Interface</h2>
            </div>
            <p className="text-sm text-neutral-400">Customize the appearance and behavior of the interface</p>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Theme Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
                  {darkMode ? (
                    <Moon className="w-5 h-5 text-blue-500" />
                  ) : (
                    <Sun className="w-5 h-5 text-yellow-500" />
                  )}
                </div>
                <div>
                  <h3 className="font-medium text-white">Theme</h3>
                  <p className="text-sm text-neutral-400">
                    {darkMode ? 'Dark mode for low-light environments' : 'Light mode for bright environments'}
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => handleDarkModeToggle(!darkMode)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  darkMode ? 'bg-blue-600' : 'bg-neutral-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    darkMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Accent Color */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
                  <Palette className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Accent Color</h3>
                  <p className="text-sm text-neutral-400">Choose your preferred accent color</p>
                </div>
              </div>
              
              <div className="flex gap-2 flex-wrap">
                {accentColors.map((colorOption) => (
                  <button
                    key={colorOption.value}
                    onClick={() => handleAccentColorChange(colorOption.value)}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      accentColor === colorOption.value
                        ? 'border-white scale-110'
                        : 'border-neutral-600 hover:border-neutral-500'
                    }`}
                    style={{ backgroundColor: colorOption.color }}
                    title={colorOption.name}
                  />
                ))}
              </div>
            </div>

            {/* Additional Interface Settings */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
                  <Monitor className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Compact Mode</h3>
                  <p className="text-sm text-neutral-400">Reduce spacing for more content</p>
                </div>
              </div>
              
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-neutral-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
              </button>
            </div>
          </div>
        </div>

        {/* Database Section */}
        <div className="bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="p-6 border-b border-neutral-700">
            <div className="flex items-center gap-3 mb-2">
              <Database className="w-5 h-5 text-blue-500" />
              <h2 className="text-lg font-semibold text-white">Database</h2>
            </div>
            <p className="text-sm text-neutral-400">Monitor and manage database connections and health</p>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Database Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Database Status</h3>
                  <p className="text-sm text-neutral-400">
                    {databaseStatus === 'connected' ? 'ArangoDB connected and healthy' : 
                     databaseStatus === 'error' ? 'Database connection error' : 
                     'Checking connection...'}
                  </p>
                </div>
              </div>
              
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${
                databaseStatus === 'connected' ? 'bg-green-500/10 border-green-500/20 text-green-500' :
                databaseStatus === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-500' :
                'bg-yellow-500/10 border-yellow-500/20 text-yellow-500'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  databaseStatus === 'connected' ? 'bg-green-500' :
                  databaseStatus === 'error' ? 'bg-red-500' :
                  'bg-yellow-500'
                }`}></div>
                <span className="text-sm font-medium capitalize">{databaseStatus}</span>
              </div>
            </div>

            {/* Sync Database Button */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Database Health Dashboard</h3>
                  <p className="text-sm text-neutral-400">View detailed database status and performance metrics</p>
                </div>
              </div>
              
              <button
                onClick={openDatabaseHealth}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Open Dashboard
              </button>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Quick Health Check</h3>
                  <p className="text-sm text-neutral-400">Test database connectivity and refresh status</p>
                </div>
              </div>
              
              <button
                onClick={checkDatabaseStatus}
                className="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 rounded-lg text-sm font-medium transition-colors"
              >
                Refresh Status
              </button>
            </div>
          </div>
        </div>

        {/* Future Settings Sections */}
        <div className="bg-neutral-800 rounded-lg border border-neutral-700 opacity-50">
          <div className="p-6 border-b border-neutral-700">
            <h2 className="text-lg font-semibold text-white">Account</h2>
            <p className="text-sm text-neutral-400">Manage your account settings and preferences</p>
          </div>
          <div className="p-6">
            <p className="text-sm text-neutral-400">Coming soon...</p>
          </div>
        </div>

        <div className="bg-neutral-800 rounded-lg border border-neutral-700 opacity-50">
          <div className="p-6 border-b border-neutral-700">
            <h2 className="text-lg font-semibold text-white">Notifications</h2>
            <p className="text-sm text-neutral-400">Configure notification preferences</p>
          </div>
          <div className="p-6">
            <p className="text-sm text-neutral-400">Coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings; 