// Enhanced AssetLibrary.jsx with Fixed Settings Panel
import React, { useState, useEffect } from 'react';
import { Search, Grid3X3, List, Filter, Upload, Download, Eye, X, Settings, Save, FolderOpen, Database, RefreshCw } from 'lucide-react';

const AssetLibrary = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [dbStatus, setDbStatus] = useState({ status: 'unknown', assets_count: 0 });

  // Preview modal state
  const [previewAsset, setPreviewAsset] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const [selectedFilters, setSelectedFilters] = useState({
    type: 'all',
    format: 'all',
    category: 'all',
    creator: 'all'
  });

  // Settings state
  const [settings, setSettings] = useState({
    rootFolder: 'C:\\Users\\alexh\\Desktop\\BlacksmithAtlas_Files\\AssetLibrary\\3D',
    jsonFilePath: 'C:\\Users\\alexh\\Desktop\\BlacksmithAtlas\\backend\\assetlibrary\\database\\3DAssets.json',
    apiEndpoint: 'http://localhost:8000/api/v1/assets',
    databaseEnabled: true,
    autoSync: true
  });

  const [tempSettings, setTempSettings] = useState(settings);

  useEffect(() => {
    loadAssets();
    checkDatabaseStatus();
  }, [settings.apiEndpoint]);

  const loadAssets = () => {
    setLoading(true);
    fetch(settings.apiEndpoint)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Loaded assets:', data);
        setAssets(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load assets:', err);
        setLoading(false);
        setAssets([]);
      });
  };

  const checkDatabaseStatus = () => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        setDbStatus({
          status: data.status || 'unknown',
          assets_count: data.database_assets || 0,
          database_type: data.database || 'unknown'
        });
      })
      .catch(err => {
        console.error('Failed to check database status:', err);
        setDbStatus({ status: 'error', assets_count: 0 });
      });
  };

  const syncDatabase = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/admin/sync', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Database sync result:', result);
        await loadAssets();
        await checkDatabaseStatus();
        alert('Database synced successfully!');
      } else {
        throw new Error('Sync failed');
      }
    } catch (error) {
      console.error('Database sync failed:', error);
      alert('Database sync failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  // Preview functions
  const openPreview = (asset) => {
    setPreviewAsset(asset);
    setShowPreview(true);
  };

  const closePreview = () => {
    setShowPreview(false);
    setPreviewAsset(null);
  };

  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (asset.description && asset.description.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = selectedFilters.type === 'all' ||
                       (selectedFilters.type === '2d' && ['texture', 'image', 'reference'].includes(asset.asset_type)) ||
                       (selectedFilters.type === '3d' && ['3D', 'geometry', 'material', 'light_rig'].includes(asset.asset_type));

    const matchesCategory = selectedFilters.category === 'all' || asset.category === selectedFilters.category;
    const matchesCreator = selectedFilters.creator === 'all' || asset.artist === selectedFilters.creator;

    return matchesSearch && matchesType && matchesCategory && matchesCreator;
  });

  const handleFilterChange = (filterType, value) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const clearFilters = () => {
    setSelectedFilters({
      type: 'all',
      format: 'all',
      category: 'all',
      creator: 'all'
    });
  };

  const saveSettings = async () => {
    try {
      // Update local settings
      setSettings(tempSettings);
      setShowSettingsPanel(false);

      // Save to localStorage
      localStorage.setItem('blacksmith-atlas-settings', JSON.stringify(tempSettings));
      console.log('Settings saved to localStorage');

      // Save to backend config
      try {
        const response = await fetch('http://localhost:8000/admin/save-config', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(tempSettings)
        });

        if (response.ok) {
          console.log('Settings saved to backend config');
          alert('Settings saved successfully! Restart the application to apply changes.');
        } else {
          console.log('Backend config save failed, but localStorage saved');
          alert('Settings saved locally. Backend save failed - this is normal if backend is not running.');
        }
      } catch (error) {
        console.log('Could not save to backend config (normal if backend not running)');
        alert('Settings saved locally. To apply fully, restart the application.');
      }

    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings. Please try again.');
    }
  };

  const resetSettings = () => {
    const defaultSettings = {
      rootFolder: 'C:\\Users\\alexh\\Desktop\\BlacksmithAtlas_Files\\AssetLibrary\\3D',
      jsonFilePath: 'C:\\Users\\alexh\\Desktop\\BlacksmithAtlas\\backend\\assetlibrary\\database\\3DAssets.json',
      apiEndpoint: 'http://localhost:8000/api/v1/assets',
      databaseEnabled: true,
      autoSync: true
    };
    setTempSettings(defaultSettings);
    alert('Settings reset to defaults. Click "Save Settings" to apply.');
  };

  const browseFolder = (fieldName) => {
    // Since we're in Electron, we could use the file dialog here
    // For now, just prompt for manual entry
    const newPath = prompt(`Enter new path for ${fieldName}:`, tempSettings[fieldName]);
    if (newPath !== null) {
      setTempSettings(prev => ({
        ...prev,
        [fieldName]: newPath
      }));
    }
  };

  const testConnection = async () => {
    try {
      setLoading(true);
      const response = await fetch(tempSettings.apiEndpoint);

      if (response.ok) {
        const data = await response.json();
        alert(`Connection successful! Found ${data.length || 0} assets.`);
      } else {
        alert(`Connection failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      alert(`Connection failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedSettings = localStorage.getItem('blacksmith-atlas-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
        setTempSettings(parsed);
        console.log('Loaded settings from localStorage:', parsed);
      } catch (e) {
        console.error('Error loading saved settings:', e);
      }
    }
  }, []);

  const categories = [...new Set(assets.map(asset => asset.category))];
  const creators = [...new Set(assets.map(asset => asset.artist).filter(Boolean))];

  return (
    <div className="min-h-screen bg-neutral-900 text-white">
      {/* Header */}
      <div className="bg-neutral-800 border-b border-neutral-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-blue-400">Asset Library</h1>

            <div className="flex items-center gap-2 px-3 py-1 rounded-full text-sm border">
              <Database size={16} />
              <span className={`${
                dbStatus.status === 'healthy' ? 'text-green-400 border-green-500' :
                dbStatus.status === 'error' ? 'text-red-400 border-red-500' :
                'text-yellow-400 border-yellow-500'
              }`}>
                {dbStatus.status === 'healthy' ? 'ArangoDB Ready' :
                 dbStatus.status === 'error' ? 'DB Error' :
                 'DB Unknown'}
              </span>
              {dbStatus.assets_count > 0 && (
                <span className="text-neutral-400">({dbStatus.assets_count})</span>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={syncDatabase}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-neutral-600 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
              Sync DB
            </button>
            <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors">
              <Upload size={20} />
              Upload Asset
            </button>
            <button
              onClick={() => setShowSettingsPanel(true)}
              className="bg-neutral-700 hover:bg-neutral-600 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Settings size={20} />
              Settings
            </button>
          </div>
        </div>

        {/* Search and Controls */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" size={20} />
            <input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-neutral-700 border border-neutral-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 bg-neutral-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition-colors ${viewMode === 'grid' ? 'bg-blue-600' : 'hover:bg-neutral-600'}`}
            >
              <Grid3X3 size={18} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition-colors ${viewMode === 'list' ? 'bg-blue-600' : 'hover:bg-neutral-600'}`}
            >
              <List size={18} />
            </button>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowFilterMenu(!showFilterMenu)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                showFilterMenu ? 'bg-blue-600' : 'bg-neutral-700 hover:bg-neutral-600'
              }`}
            >
              <Filter size={18} />
              Filter
              {(selectedFilters.type !== 'all' || selectedFilters.category !== 'all' || selectedFilters.creator !== 'all') && (
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              )}
            </button>

            {showFilterMenu && (
              <div className="absolute right-0 top-12 bg-neutral-800 border border-neutral-700 rounded-lg shadow-lg z-10 w-80">
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-white font-medium">Filters</h3>
                    <button
                      onClick={() => setShowFilterMenu(false)}
                      className="text-neutral-400 hover:text-white"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-neutral-300 mb-2">Asset Type</label>
                    <div className="space-y-2">
                      {[
                        { value: 'all', label: 'All Assets' },
                        { value: '2d', label: '2D Assets' },
                        { value: '3d', label: '3D Assets' }
                      ].map(option => (
                        <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="assetType"
                            value={option.value}
                            checked={selectedFilters.type === option.value}
                            onChange={(e) => handleFilterChange('type', e.target.value)}
                            className="text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-neutral-300 text-sm">{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-neutral-300 mb-2">Category</label>
                    <select
                      value={selectedFilters.category}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      className="w-full bg-neutral-700 border border-neutral-600 rounded px-3 py-2 text-white text-sm"
                    >
                      <option value="all">All Categories</option>
                      {categories.map(category => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-neutral-300 mb-2">Creator</label>
                    <select
                      value={selectedFilters.creator}
                      onChange={(e) => handleFilterChange('creator', e.target.value)}
                      className="w-full bg-neutral-700 border border-neutral-600 rounded px-3 py-2 text-white text-sm"
                    >
                      <option value="all">All Creators</option>
                      {creators.map(creator => (
                        <option key={creator} value={creator}>{creator}</option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={clearFilters}
                    className="w-full bg-neutral-700 hover:bg-neutral-600 text-white py-2 rounded text-sm transition-colors"
                  >
                    Clear All Filters
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettingsPanel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Asset Library Settings</h2>
              <button
                onClick={() => setShowSettingsPanel(false)}
                className="text-neutral-400 hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            <div className="space-y-6">
              {/* Root Folder Setting */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Asset Library Root Folder
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tempSettings.rootFolder}
                    onChange={(e) => setTempSettings(prev => ({ ...prev, rootFolder: e.target.value }))}
                    className="flex-1 bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white"
                    placeholder="C:\Path\To\AssetLibrary\3D"
                  />
                  <button
                    onClick={() => browseFolder('rootFolder')}
                    className="bg-neutral-700 hover:bg-neutral-600 px-3 py-2 rounded-lg flex items-center gap-2"
                  >
                    <FolderOpen size={16} />
                    Browse
                  </button>
                </div>
                <p className="text-xs text-neutral-400 mt-1">
                  The main folder containing your 3D assets
                </p>
              </div>

              {/* JSON File Path Setting */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  JSON Database File
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tempSettings.jsonFilePath}
                    onChange={(e) => setTempSettings(prev => ({ ...prev, jsonFilePath: e.target.value }))}
                    className="flex-1 bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white"
                    placeholder="C:\Path\To\3DAssets.json"
                  />
                  <button
                    onClick={() => browseFolder('jsonFilePath')}
                    className="bg-neutral-700 hover:bg-neutral-600 px-3 py-2 rounded-lg flex items-center gap-2"
                  >
                    <FolderOpen size={16} />
                    Browse
                  </button>
                </div>
                <p className="text-xs text-neutral-400 mt-1">
                  The JSON file containing asset metadata
                </p>
              </div>

              {/* API Endpoint Setting */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  API Endpoint
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={tempSettings.apiEndpoint}
                    onChange={(e) => setTempSettings(prev => ({ ...prev, apiEndpoint: e.target.value }))}
                    className="flex-1 bg-neutral-700 border border-neutral-600 rounded-lg px-3 py-2 text-white"
                    placeholder="http://localhost:8000/api/v1/assets"
                  />
                  <button
                    onClick={testConnection}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-600 px-3 py-2 rounded-lg flex items-center gap-2"
                  >
                    {loading ? (
                      <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                    ) : (
                      <Database size={16} />
                    )}
                    Test
                  </button>
                </div>
                <p className="text-xs text-neutral-400 mt-1">
                  The backend API endpoint for asset data
                </p>
              </div>

              {/* Database Options */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-3">
                  Database Options
                </label>
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={tempSettings.databaseEnabled}
                      onChange={(e) => setTempSettings(prev => ({ ...prev, databaseEnabled: e.target.checked }))}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-neutral-300 text-sm">Enable Database Connection</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={tempSettings.autoSync}
                      onChange={(e) => setTempSettings(prev => ({ ...prev, autoSync: e.target.checked }))}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-neutral-300 text-sm">Auto-sync on startup</span>
                  </label>
                </div>
              </div>

              {/* Current Status */}
              <div className="bg-neutral-700 rounded-lg p-4">
                <h3 className="text-white font-medium mb-3">Current Status</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-neutral-400">Database:</span>
                    <div className={`font-medium ${
                      dbStatus.status === 'healthy' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {dbStatus.status === 'healthy' ? 'Connected' : 'Disconnected'}
                    </div>
                  </div>
                  <div>
                    <span className="text-neutral-400">Assets:</span>
                    <div className="text-blue-400 font-medium">{dbStatus.assets_count}</div>
                  </div>
                  <div>
                    <span className="text-neutral-400">Type:</span>
                    <div className="text-purple-400 font-medium">{dbStatus.database_type || 'Unknown'}</div>
                  </div>
                  <div>
                    <span className="text-neutral-400">API:</span>
                    <div className="text-green-400 font-medium">
                      {settings.apiEndpoint.includes('localhost') ? 'Local' : 'Remote'}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6 pt-6 border-t border-neutral-700">
              <button
                onClick={saveSettings}
                className="bg-green-600 hover:bg-green-700 text-white py-2 px-6 rounded-lg flex items-center gap-2 transition-colors"
              >
                <Save size={16} />
                Save Settings
              </button>
              <button
                onClick={resetSettings}
                className="bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Reset to Defaults
              </button>
              <button
                onClick={() => setShowSettingsPanel(false)}
                className="bg-neutral-700 hover:bg-neutral-600 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && previewAsset && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-700">
              <div>
                <h2 className="text-xl font-semibold text-white">{previewAsset.name}</h2>
                <p className="text-neutral-400 text-sm">{previewAsset.category} • {previewAsset.artist || 'Unknown Artist'}</p>
              </div>
              <button
                onClick={closePreview}
                className="text-neutral-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Large Preview Image */}
                <div className="aspect-square bg-neutral-700 rounded-lg overflow-hidden flex items-center justify-center">
                  {previewAsset.thumbnail_path && previewAsset.thumbnail_path !== 'null' ? (
                    <img
                      src={previewAsset.thumbnail_path}
                      alt={previewAsset.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div
                    className="text-neutral-500 text-6xl flex items-center justify-center w-full h-full"
                    style={{ display: (previewAsset.thumbnail_path && previewAsset.thumbnail_path !== 'null') ? 'none' : 'flex' }}
                  >
                    {previewAsset.category === 'Characters' ? '🎭' :
                     previewAsset.category === 'Props' ? '📦' :
                     previewAsset.category === 'Environments' ? '🏞️' :
                     previewAsset.category === 'Vehicles' ? '🚗' :
                     previewAsset.category === 'Effects' ? '✨' :
                     '🎨'}
                  </div>
                </div>

                {/* Asset Details */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white mb-2">Asset Information</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-400">ID:</span>
                        <span className="text-white font-mono">{previewAsset.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Category:</span>
                        <span className="text-blue-400">{previewAsset.category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Artist:</span>
                        <span className="text-green-400">{previewAsset.artist || 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Format:</span>
                        <span className="text-purple-400">{previewAsset.file_format || 'USD'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Size:</span>
                        <span className="text-neutral-300">
                          {Math.round(Object.values(previewAsset.file_sizes || {}).reduce((sum, size) => sum + (typeof size === 'number' ? size : 0), 0) / 1024)} KB
                        </span>
                      </div>
                    </div>
                  </div>

                  {previewAsset.description && (
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">Description</h3>
                      <p className="text-neutral-300 text-sm">{previewAsset.description}</p>
                    </div>
                  )}

                  {previewAsset.metadata && (
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">Technical Details</h3>
                      <div className="space-y-1 text-sm">
                        {previewAsset.metadata.houdini_version && (
                          <div className="flex justify-between">
                            <span className="text-neutral-400">Houdini Version:</span>
                            <span className="text-neutral-300">{previewAsset.metadata.houdini_version}</span>
                          </div>
                        )}
                        {previewAsset.metadata.export_time && (
                          <div className="flex justify-between">
                            <span className="text-neutral-400">Export Time:</span>
                            <span className="text-neutral-300">{new Date(previewAsset.metadata.export_time).toLocaleString()}</span>
                          </div>
                        )}
                        {previewAsset.created_at && (
                          <div className="flex justify-between">
                            <span className="text-neutral-400">Created:</span>
                            <span className="text-neutral-300">{new Date(previewAsset.created_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-4">
                    <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors">
                      Import to Scene
                    </button>
                    <button className="bg-neutral-700 hover:bg-neutral-600 text-white py-2 px-4 rounded-lg transition-colors">
                      <Download size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content (Asset Grid/List) */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-neutral-400 text-lg">Loading assets...</div>
          </div>
        ) : (
          <>
            <div className="bg-neutral-800 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-8 text-sm text-neutral-400">
                <span>{filteredAssets.length} assets found</span>
                <span>Total size: {Math.round(filteredAssets.reduce((sum, asset) => {
                  const sizes = Object.values(asset.file_sizes || {});
                  return sum + sizes.reduce((total, size) => total + (typeof size === 'number' ? size : 0), 0);
                }, 0) / 1024 / 1024)} MB</span>
                <span>Categories: {categories.join(', ')}</span>
                <span>Database: {dbStatus.database_type || 'JSON'}</span>
                {(selectedFilters.type !== 'all' || selectedFilters.category !== 'all' || selectedFilters.creator !== 'all') && (
                  <span className="text-blue-400">Filtered</span>
                )}
              </div>
            </div>

            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                {filteredAssets.map(asset => (
                  <div key={asset.id} className="group relative">
                    <div className="bg-neutral-800 rounded-lg overflow-hidden border border-neutral-700 hover:border-blue-500 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10 cursor-pointer">
                      <div className="aspect-square bg-neutral-700 flex items-center justify-center relative overflow-hidden">
                        {asset.thumbnail_path && asset.thumbnail_path !== 'null' ? (
                          <img
                            src={asset.thumbnail_path}
                            alt={asset.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                        ) : null}
                        <div className="text-neutral-500 text-3xl flex items-center justify-center w-full h-full"
                             style={{ display: (asset.thumbnail_path && asset.thumbnail_path !== 'null') ? 'none' : 'flex' }}>
                          {asset.category === 'Characters' ? '🎭' :
                           asset.category === 'Props' ? '📦' :
                           asset.category === 'Environments' ? '🏞️' :
                           asset.category === 'Vehicles' ? '🚗' :
                           asset.category === 'Effects' ? '✨' :
                           '🎨'}
                        </div>

                        <div className="absolute top-2 right-2">
                          <span className="px-2 py-1 text-xs rounded-full font-medium bg-blue-600/80 text-blue-100">
                            3D
                          </span>
                        </div>

                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openPreview(asset)}
                              className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors"
                            >
                              <Eye size={16} />
                            </button>
                            <button className="bg-neutral-700 hover:bg-neutral-600 text-white p-2 rounded-lg transition-colors">
                              <Download size={16} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="absolute top-full left-0 right-0 mt-2 bg-neutral-800 border border-neutral-700 rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-all duration-200 z-10 shadow-lg">
                      <h3 className="text-white font-semibold text-sm mb-1 truncate">{asset.name}</h3>
                      <p className="text-neutral-400 text-xs mb-2 line-clamp-2">{asset.description || 'No description available'}</p>

                      <div className="grid grid-cols-2 gap-2 text-xs text-neutral-500">
                        <div>
                          <span className="text-neutral-400">Category:</span>
                          <div className="text-blue-400 font-medium">{asset.category}</div>
                        </div>
                        <div>
                          <span className="text-neutral-400">Size:</span>
                          <div className="text-neutral-300">
                            {Math.round(Object.values(asset.file_sizes || {}).reduce((sum, size) => sum + (typeof size === 'number' ? size : 0), 0) / 1024)} KB
                          </div>
                        </div>
                        <div>
                          <span className="text-neutral-400">Artist:</span>
                          <div className="text-green-400 font-medium truncate">{asset.artist || 'Unknown'}</div>
                        </div>
                        <div>
                          <span className="text-neutral-400">Format:</span>
                          <div className="text-purple-400 font-medium">{asset.file_format}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-neutral-800 rounded-lg overflow-hidden">
                <div className="grid grid-cols-12 gap-4 p-4 border-b border-neutral-700 text-sm font-medium text-neutral-400">
                  <div className="col-span-4">Name</div>
                  <div className="col-span-2">Category</div>
                  <div className="col-span-2">Artist</div>
                  <div className="col-span-2">Size</div>
                  <div className="col-span-2">Actions</div>
                </div>
                {filteredAssets.map(asset => (
                  <div key={asset.id} className="grid grid-cols-12 gap-4 p-4 border-b border-neutral-700 hover:bg-neutral-750 transition-colors">
                    <div className="col-span-4">
                      <div className="font-medium text-white">{asset.name}</div>
                      <div className="text-sm text-neutral-400 truncate">{asset.description || 'No description'}</div>
                    </div>
                    <div className="col-span-2 text-blue-400">{asset.category}</div>
                    <div className="col-span-2 text-green-400">{asset.artist || 'Unknown'}</div>
                    <div className="col-span-2 text-neutral-300">
                      {Math.round(Object.values(asset.file_sizes || {}).reduce((sum, size) => sum + (typeof size === 'number' ? size : 0), 0) / 1024)} KB
                    </div>
                    <div className="col-span-2 flex gap-2">
                      <button
                        onClick={() => openPreview(asset)}
                        className="bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded text-sm transition-colors"
                      >
                        Preview
                      </button>
                      <button className="bg-neutral-700 hover:bg-neutral-600 text-white py-1 px-3 rounded text-sm transition-colors">
                        <Download size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {filteredAssets.length === 0 && !loading && (
              <div className="text-center py-12">
                <div className="text-neutral-400 text-lg mb-2">No assets found</div>
                <div className="text-neutral-500">
                  Try adjusting your filters or sync the database
                </div>
              </div>
            )}

            <div className="mt-8 pt-4 border-t border-neutral-700">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm text-neutral-400">
                <div>
                  <span className="block">Total Files:</span>
                  <span className="text-white font-medium">{filteredAssets.length}</span>
                </div>
                <div>
                  <span className="block">Total Size:</span>
                  <span className="text-white font-medium">
                    {Math.round(filteredAssets.reduce((sum, asset) => {
                      const sizes = Object.values(asset.file_sizes || {});
                      return sum + sizes.reduce((total, size) => total + (typeof size === 'number' ? size : 0), 0);
                    }, 0) / 1024 / 1024)} MB
                  </span>
                </div>
                <div>
                  <span className="block">Categories:</span>
                  <span className="text-white font-medium">{categories.length}</span>
                </div>
                <div>
                  <span className="block">Creators:</span>
                  <span className="text-white font-medium">{creators.length}</span>
                </div>
                <div>
                  <span className="block">Database:</span>
                  <span className={`font-medium ${
                    dbStatus.status === 'healthy' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {dbStatus.database_type || 'JSON'}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AssetLibrary;