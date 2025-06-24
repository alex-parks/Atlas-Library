import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Monitor, Sun, Moon, Palette } from 'lucide-react';

const Settings = () => {
  const [darkMode, setDarkMode] = useState(true);
  const [accentColor, setAccentColor] = useState('blue');

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
  }, []);

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