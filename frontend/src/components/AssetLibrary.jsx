// frontend/src/components/AssetLibrary.jsx - Fixed settings section
import React, { useState, useEffect, useCallback } from 'react';
import './AssetLibrary.css';

const AssetLibrary = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [syncStatus, setSyncStatus] = useState('');

  // Settings with your current default paths
  const [settings, setSettings] = useState({
    rootFolder: 'C:\\Users\\alexh\\Desktop\\BlacksmithAtlas_Files\\AssetLibrary\\3D',
    jsonFilePath: 'C:\\Users\\alexh\\Desktop\\BlacksmithAtlas\\backend\\assetlibrary\\database\\3DAssets.json',
    apiEndpoint: 'http://localhost:8000/api/v1/assets',
    autoRebuildOnChange: true // Auto-rebuild database when JSON path changes
  });

  // Temporary settings for editing (so changes aren't applied until saved)
  const [tempSettings, setTempSettings] = useState({ ...settings });

  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('assetLibrarySettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
        setTempSettings(parsed);
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    }
  }, []);

  // Handle settings changes
  const handleSettingChange = (key, value) => {
    setTempSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Save settings and rebuild database if JSON path changed
  const saveSettings = async () => {
    try {
      setLoading(true);
      setSyncStatus('Saving settings...');

      // Check if JSON path changed
      const jsonPathChanged = settings.jsonFilePath !== tempSettings.jsonFilePath;

      // Save to localStorage
      localStorage.setItem('assetLibrarySettings', JSON.stringify(tempSettings));

      // Send to backend
      const response = await fetch('http://localhost:8000/admin/save-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tempSettings)
      });

      if (response.ok) {
        setSettings({ ...tempSettings });
        setShowSettings(false);

        if (jsonPathChanged && tempSettings.autoRebuildOnChange) {
          setSyncStatus('Settings saved! Rebuilding database with new JSON file...');

          // Trigger database rebuild with new JSON
          await rebuildDatabase();
        } else {
          setSyncStatus('Settings saved successfully!');
          // Just refresh assets with current database
          await loadAssets();
        }

        setTimeout(() => setSyncStatus(''), 3000);
      } else {
        throw new Error('Failed to save settings to backend');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setSyncStatus('Error saving settings: ' + error.message);
      setTimeout(() => setSyncStatus(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  // Cancel settings changes
  const cancelSettings = () => {
    setTempSettings({ ...settings });
    setShowSettings(false);
  };

  // Browse for folder
  const browseFolder = async (type) => {
    try {
      if (window.electron && window.electron.dialog) {
        const result = await window.electron.dialog.showOpenDialog({
          properties: ['openDirectory'],
          title: type === 'root' ? 'Select Asset Library Root Folder' : 'Select JSON Database File',
          ...(type === 'json' && {
            properties: ['openFile'],
            filters: [{ name: 'JSON Files', extensions: ['json'] }]
          })
        });

        if (!result.canceled && result.filePaths.length > 0) {
          const path = result.filePaths[0];
          const key = type === 'root' ? 'rootFolder' : 'jsonFilePath';
          handleSettingChange(key, path);
        }
      } else {
        // Fallback for web version
        setSyncStatus('File browser not available in web version. Please type the path manually.');
        setTimeout(() => setSyncStatus(''), 3000);
      }
    } catch (error) {
      console.error('Error browsing for folder:', error);
      setSyncStatus('Error opening file browser: ' + error.message);
      setTimeout(() => setSyncStatus(''), 3000);
    }
  };

  // Load assets from API
  const loadAssets = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(settings.apiEndpoint);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setAssets(data || []);
    } catch (error) {
      console.error('Error loading assets:', error);
      setSyncStatus('Error loading assets: ' + error.message);
      setTimeout(() => setSyncStatus(''), 5000);
    } finally {
      setLoading(false);
    }
  }, [settings.apiEndpoint]);

  // Rebuild database from scratch with new JSON file
  const rebuildDatabase = async () => {
    try {
      setSyncStatus('Rebuilding database from new JSON file...');

      // First, sync the database with the new JSON file
      const syncResponse = await fetch('http://localhost:8000/admin/sync', {
        method: 'POST'
      });

      if (!syncResponse.ok) {
        throw new Error('Failed to sync database with new JSON file');
      }

      // Wait a moment for the sync to complete
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Then reload assets
      await loadAssets();

      setSyncStatus('Database rebuilt successfully with new JSON file!');

    } catch (error) {
      console.error('Error rebuilding database:', error);
      setSyncStatus('Error rebuilding database: ' + error.message);
      setTimeout(() => setSyncStatus(''), 5000);
    }
  };

  // Sync database
  const syncDatabase = async () => {
    try {
      setLoading(true);
      setSyncStatus('Syncing database...');

      const response = await fetch('http://localhost:8000/admin/sync', {
        method: 'POST'
      });

      if (response.ok) {
        setSyncStatus('Database synced successfully!');
        await loadAssets(); // Reload assets after sync
      } else {
        throw new Error('Sync failed');
      }

      setTimeout(() => setSyncStatus(''), 3000);
    } catch (error) {
      console.error('Error syncing database:', error);
      setSyncStatus('Sync error: ' + error.message);
      setTimeout(() => setSyncStatus(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  // Load assets on component mount and when settings change
  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  // Filter assets based on search and category
  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (asset.category && asset.category.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || asset.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = ['all', ...new Set(assets.map(asset => asset.category).filter(Boolean))];

  return (
    <div className="asset-library">
      {/* Header */}
      <div className="asset-library-header">
        <div className="header-left">
          <h2>Asset Library</h2>
          <div className="asset-count">
            {filteredAssets.length} assets {filteredAssets.length !== assets.length && `(${assets.length} total)`}
          </div>
        </div>

        <div className="header-controls">
          <button
            className="btn btn-secondary"
            onClick={() => setShowSettings(!showSettings)}
            disabled={loading}
          >
            ⚙️ Settings
          </button>

          <button
            className="btn btn-primary"
            onClick={syncDatabase}
            disabled={loading}
          >
            {loading ? '🔄 Syncing...' : '🔄 Sync DB'}
          </button>

          <button
            className="btn btn-secondary"
            onClick={loadAssets}
            disabled={loading}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {syncStatus && (
        <div className={`status-message ${syncStatus.includes('Error') || syncStatus.includes('error') ? 'error' : 'success'}`}>
          {syncStatus}
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel">
          <h3>Asset Library Settings</h3>

          <div className="setting-group">
            <label>Asset Library Root Folder:</label>
            <div className="path-input-group">
              <input
                type="text"
                value={tempSettings.rootFolder}
                onChange={(e) => handleSettingChange('rootFolder', e.target.value)}
                placeholder="C:\path\to\your\asset\library"
                className="path-input"
              />
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => browseFolder('root')}
              >
                📁 Browse
              </button>
            </div>
          </div>

          <div className="setting-group">
            <label>JSON Database File Path:</label>
            <div className="path-input-group">
              <input
                type="text"
                value={tempSettings.jsonFilePath}
                onChange={(e) => handleSettingChange('jsonFilePath', e.target.value)}
                placeholder="C:\path\to\3DAssets.json"
                className="path-input"
              />
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => browseFolder('json')}
              >
                📄 Browse
              </button>
            </div>
          </div>

          <div className="setting-group">
            <label>Auto-rebuild Database on JSON Change:</label>
            <div className="checkbox-group">
              <input
                type="checkbox"
                id="autoRebuild"
                checked={tempSettings.autoRebuildOnChange}
                onChange={(e) => handleSettingChange('autoRebuildOnChange', e.target.checked)}
              />
              <label htmlFor="autoRebuild">
                Automatically rebuild database when JSON file path changes
              </label>
            </div>
          </div>

          <div className="setting-group">
            <label>API Endpoint:</label>
            <input
              type="text"
              value={tempSettings.apiEndpoint}
              onChange={(e) => handleSettingChange('apiEndpoint', e.target.value)}
              placeholder="http://localhost:8000/api/v1/assets"
              className="path-input"
            />
          </div>

          <div className="settings-actions">
            <button
              className="btn btn-primary"
              onClick={saveSettings}
              disabled={loading}
            >
              💾 Save Settings
              {settings.jsonFilePath !== tempSettings.jsonFilePath && tempSettings.autoRebuildOnChange &&
                " & Rebuild DB"
              }
            </button>
            <button
              className="btn btn-secondary"
              onClick={cancelSettings}
              disabled={loading}
            >
              ❌ Cancel
            </button>
            <button
              className="btn btn-accent"
              onClick={rebuildDatabase}
              disabled={loading}
            >
              🔄 Force Rebuild DB
            </button>
          </div>
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="search-controls">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search assets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-controls">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="category-filter"
          >
            {categories.map(category => (
              <option key={category} value={category}>
                {category === 'all' ? 'All Categories' : category}
              </option>
            ))}
          </select>

          <div className="view-mode-toggle">
            <button
              className={`btn ${viewMode === 'grid' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('grid')}
            >
              🔲 Grid
            </button>
            <button
              className={`btn ${viewMode === 'list' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setViewMode('list')}
            >
              📋 List
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading assets...</p>
        </div>
      )}

      {/* Asset Grid/List */}
      {!loading && (
        <div className={`assets-container ${viewMode}`}>
          {filteredAssets.length === 0 ? (
            <div className="empty-state">
              <h3>No assets found</h3>
              <p>
                {assets.length === 0
                  ? "No assets are available. Try syncing the database or check your settings."
                  : "No assets match your search criteria."
                }
              </p>
            </div>
          ) : (
            filteredAssets.map(asset => (
              <div
                key={asset.id}
                className="asset-item"
                onClick={() => setSelectedAsset(asset)}
              >
                <div className="asset-thumbnail">
                  {asset.paths?.thumbnail ? (
                    <img
                      src={`http://localhost:8000/thumbnails/${asset.id}`}
                      alt={asset.name}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div className="thumbnail-placeholder" style={{display: asset.paths?.thumbnail ? 'none' : 'flex'}}>
                    📦
                  </div>
                </div>

                <div className="asset-info">
                  <h4 className="asset-name">{asset.name}</h4>
                  <p className="asset-category">{asset.category}</p>
                  {asset.metadata?.created_by && (
                    <p className="asset-creator">by {asset.metadata.created_by}</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Asset Detail Modal */}
      {selectedAsset && (
        <div className="modal-overlay" onClick={() => setSelectedAsset(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedAsset.name}</h3>
              <button
                className="modal-close"
                onClick={() => setSelectedAsset(null)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="asset-preview">
                {selectedAsset.paths?.thumbnail ? (
                  <img
                    src={`http://localhost:8000/thumbnails/${selectedAsset.id}`}
                    alt={selectedAsset.name}
                  />
                ) : (
                  <div className="preview-placeholder">📦</div>
                )}
              </div>

              <div className="asset-details">
                <div className="detail-group">
                  <label>Category:</label>
                  <span>{selectedAsset.category}</span>
                </div>

                {selectedAsset.metadata?.created_by && (
                  <div className="detail-group">
                    <label>Created by:</label>
                    <span>{selectedAsset.metadata.created_by}</span>
                  </div>
                )}

                {selectedAsset.metadata?.houdini_version && (
                  <div className="detail-group">
                    <label>Houdini Version:</label>
                    <span>{selectedAsset.metadata.houdini_version}</span>
                  </div>
                )}

                <div className="detail-group">
                  <label>File Paths:</label>
                  <div className="file-paths">
                    {selectedAsset.paths?.usd && (
                      <div className="file-path">
                        <strong>USD:</strong> {selectedAsset.paths.usd}
                      </div>
                    )}
                    {selectedAsset.paths?.fbx && (
                      <div className="file-path">
                        <strong>FBX:</strong> {selectedAsset.paths.fbx}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-primary"
                onClick={() => {
                  // TODO: Add import functionality
                  console.log('Import asset:', selectedAsset);
                }}
              >
                📥 Import to Scene
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetLibrary;