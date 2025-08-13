// New Asset Library with Navigation Structure
import React, { useState, useEffect } from 'react';
import { Search, Grid3X3, List, Filter, Upload, Copy, Eye, X, Settings, Save, FolderOpen, Database, RefreshCw, ArrowLeft, Folder, ExternalLink } from 'lucide-react';

const AssetLibrary = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [dbStatus, setDbStatus] = useState({ status: 'unknown', assets_count: 0 });

  // Navigation state
  const [currentView, setCurrentView] = useState('dimension'); // 'dimension', 'category', 'subcategory', 'assets'
  const [selectedDimension, setSelectedDimension] = useState(null); // '2D' or '3D'
  const [selectedCategory, setSelectedCategory] = useState(null); // 'Assets', 'FX', etc.
  const [selectedSubcategory, setSelectedSubcategory] = useState(null); // 'Blacksmith Asset', 'Megascans', etc.
  
  // Define the folder structure based on your specifications
  const dimensions = [
    { id: '2D', name: '2D', icon: '🎨', description: '2D Assets and Textures' },
    { id: '3D', name: '3D', icon: '🧊', description: '3D Models and Scenes' }
  ];

  const categories = {
    '2D': [
      { id: 'Textures', name: 'Textures', icon: '🖼️', description: 'Surface textures and materials' },
      { id: 'References', name: 'References', icon: '📸', description: 'Reference images and concepts' },
      { id: 'UI', name: 'UI Elements', icon: '🎯', description: 'User interface components' }
    ],
    '3D': [
      { id: 'Assets', name: 'Assets', icon: '🏺', description: '3D models and objects' },
      { id: 'FX', name: 'FX', icon: '✨', description: 'Visual effects and simulations' },
      { id: 'Materials', name: 'Materials', icon: '🎭', description: 'Shaders and materials' },
      { id: 'Textures', name: 'Textures', icon: '🖼️', description: 'Texture maps and images' },
      { id: 'HDRI', name: 'HDRI', icon: '🌅', description: 'HDR environment maps' },
      { id: 'HDAs', name: 'HDAs', icon: '⚡', description: 'Houdini Digital Assets' }
    ]
  };

  // Subcategories matching Houdini subnet structure and ArangoDB data
  const subcategories = {
    'Assets': [
      { id: 'Blacksmith Asset', name: 'Blacksmith Asset', icon: '🔥', description: 'Original Blacksmith VFX assets' },
      { id: 'Megascans', name: 'Megascans', icon: '🏔️', description: 'Quixel Megascans library assets' },
      { id: 'Kitbash', name: 'Kitbash', icon: '🔧', description: 'Kitbash3D modular assets' }
    ],
    'FX': [
      { id: 'Blacksmith FX', name: 'Blacksmith FX', icon: '🌟', description: 'Custom VFX elements' },
      { id: 'Atmosphere', name: 'Atmosphere', icon: '☁️', description: 'Atmospheric and environmental effects' },
      { id: 'FLIP', name: 'FLIP', icon: '🌊', description: 'Fluid simulation effects' },
      { id: 'Pyro', name: 'Pyro', icon: '🔥', description: 'Fire, smoke, and explosion effects' }
    ],
    'Materials': [
      { id: 'Blacksmith Materials', name: 'Blacksmith Materials', icon: '🎨', description: 'Custom material library' },
      { id: 'Redshift', name: 'Redshift', icon: '🔴', description: 'Redshift renderer materials' },
      { id: 'Karma', name: 'Karma', icon: '🟡', description: 'Karma renderer materials' }
    ],
    'HDAs': [
      { id: 'Blacksmith HDAs', name: 'Blacksmith HDAs', icon: '⚡', description: 'Custom Houdini Digital Assets' }
    ],
    // 2D and other categories can have subcategories too, but focusing on 3D for now
    'Textures': [],
    'HDRI': []
  };

  // Preview modal state
  const [previewAsset, setPreviewAsset] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const [selectedFilters, setSelectedFilters] = useState({
    type: 'all',
    format: 'all',
    category: 'all',
    creator: 'all'
  });

  // Active navigation filters (from square button navigation)
  const [activeFilters, setActiveFilters] = useState([]);

  // Settings state
  const [settings, setSettings] = useState({
    rootFolder: '/net/library/atlaslib/3D',
    jsonFilePath: '/net/library/atlaslib/database/3DAssets.json',
    apiEndpoint: 'http://localhost:8000/api/v1/assets',
    databaseEnabled: true,
    autoSync: true
  });

  const [tempSettings, setTempSettings] = useState(settings);

  useEffect(() => {
    // Always load assets on component mount and when API endpoint changes
    loadAssets();
    checkDatabaseStatus();
  }, [settings.apiEndpoint]);

  useEffect(() => {
    // Check database status when navigation changes
    checkDatabaseStatus();
  }, [selectedDimension, selectedCategory, selectedSubcategory, currentView]);

  // Navigation functions
  const handleDimensionSelect = (dimension) => {
    setSelectedDimension(dimension);
    setCurrentView('category');
    setSelectedCategory(null);
    setSelectedSubcategory(null);
    // Add dimension filter
    addDimensionFilter(dimension);
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    // Check if this category has subcategories
    const hasSubcategories = subcategories[category] && subcategories[category].length > 0;
    if (hasSubcategories) {
      setCurrentView('subcategory');
    } else {
      setCurrentView('assets');
    }
    setSelectedSubcategory(null);
    // Add category filter
    addCategoryFilter(category);
  };

  const handleSubcategorySelect = (subcategory) => {
    setSelectedSubcategory(subcategory);
    setCurrentView('assets');
    // Add subcategory filter
    addSubcategoryFilter(subcategory);
  };

  // Add individual filter functions
  const addDimensionFilter = (dimension) => {
    const newFilter = {
      id: `dimension-${dimension}`,
      type: 'dimension',
      value: dimension,
      label: dimension
    };
    
    setActiveFilters(prev => {
      const filtered = prev.filter(f => f.type !== 'dimension');
      return [...filtered, newFilter];
    });
  };

  const addCategoryFilter = (category) => {
    const newFilter = {
      id: `category-${category}`,
      type: 'category', 
      value: category,
      label: category
    };
    
    setActiveFilters(prev => {
      const filtered = prev.filter(f => f.type !== 'category');
      return [...filtered, newFilter];
    });
  };

  const addSubcategoryFilter = (subcategory) => {
    const newFilter = {
      id: `subcategory-${subcategory}`,
      type: 'subcategory',
      value: subcategory, 
      label: subcategory
    };
    
    setActiveFilters(prev => {
      const filtered = prev.filter(f => f.type !== 'subcategory');
      return [...filtered, newFilter];
    });
  };

  // Remove a specific navigation filter
  const removeNavigationFilter = (filterId, filterType) => {
    setActiveFilters(prev => prev.filter(f => f.id !== filterId));
    
    // Reset navigation state when removing filters
    if (filterType === 'dimension') {
      setSelectedDimension(null);
      setSelectedCategory(null);
      setSelectedSubcategory(null);
      setCurrentView('dimension');
    } else if (filterType === 'category') {
      setSelectedCategory(null);
      setSelectedSubcategory(null); 
      setCurrentView('category');
    } else if (filterType === 'subcategory') {
      setSelectedSubcategory(null);
      setCurrentView('subcategory');
    }
  };


  const handleBackToDimensions = () => {
    setCurrentView('dimension');
    setSelectedDimension(null);
    setSelectedCategory(null);
    setSelectedSubcategory(null);
    setAssets([]);
  };

  const handleBackToCategories = () => {
    setCurrentView('category');
    setSelectedCategory(null);
    setSelectedSubcategory(null);
    setAssets([]);
  };

  const handleBackToSubcategories = () => {
    setCurrentView('subcategory');
    setSelectedSubcategory(null);
    setAssets([]);
  };

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
        console.log('Loaded assets from API:', data);
        console.log('Number of assets loaded:', data.length);
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
      console.log('🔄 Refreshing assets from ArangoDB Atlas_Library collection...');
      
      // Simply reload assets from the database (no filesystem scanning)
      await loadAssets();
      await checkDatabaseStatus();
      
      console.log('✅ Assets refreshed from database');
      alert(`✅ Database Sync Complete!\n\nRefreshed asset list from ArangoDB Atlas_Library collection.`);
      
    } catch (error) {
      console.error('❌ Database refresh failed:', error);
      alert(`❌ Database refresh failed: ${error.message}\n\nCheck console for details.`);
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

  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (asset.description && asset.description.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = selectedFilters.type === 'all' ||
                       (selectedFilters.type === '2d' && ['texture', 'image', 'reference'].includes(asset.asset_type)) ||
                       (selectedFilters.type === '3d' && ['3D', 'Assets', 'FX', 'Materials', 'HDAs'].includes(asset.asset_type));

    const matchesCategory = selectedFilters.category === 'all' || asset.category === selectedFilters.category;
    const matchesCreator = selectedFilters.creator === 'all' || asset.artist === selectedFilters.creator;

    // Apply navigation filters based on current navigation state and ArangoDB data structure
    let matchesNavigation = true;
    
    // Only apply navigation filtering when we're in the assets view
    if (currentView === 'assets') {
      // Check dimension filter (should always be 3D for our current assets)
      if (selectedDimension) {
        const assetDimension = asset.dimension || asset.hierarchy?.dimension || '3D';
        matchesNavigation = matchesNavigation && (assetDimension === selectedDimension);
      }
      
      // Check category filter (Assets, FX, etc.)
      if (selectedCategory) {
        const assetCategory = asset.asset_type || asset.hierarchy?.asset_type;
        matchesNavigation = matchesNavigation && (assetCategory === selectedCategory);
      }
      
      // Check subcategory filter (Blacksmith Asset, FLIP, etc.)
      if (selectedSubcategory) {
        const assetSubcategory = asset.subcategory || asset.category || asset.hierarchy?.subcategory;
        matchesNavigation = matchesNavigation && (assetSubcategory === selectedSubcategory);
      }
    }

    // Apply active filters from filter buttons (secondary filtering system)
    const matchesActiveFilters = activeFilters.length === 0 || activeFilters.every(filter => {
      const assetDimension = asset.dimension || asset.hierarchy?.dimension || '3D';
      const assetCategory = asset.asset_type || asset.hierarchy?.asset_type;
      const assetSubcategory = asset.subcategory || asset.category || asset.hierarchy?.subcategory;
      
      if (filter.type === 'dimension') {
        return assetDimension === filter.value;
      } else if (filter.type === 'category') {
        return assetCategory === filter.value;
      } else if (filter.type === 'subcategory') {
        return assetSubcategory === filter.value;
      }
      
      return true;
    });

    return matchesSearch && matchesType && matchesCategory && matchesCreator && matchesNavigation && matchesActiveFilters;
  });

  // Debug logging for filtering
  React.useEffect(() => {
    console.log('=== FILTERING DEBUG ===');
    console.log('Total assets:', assets.length);
    console.log('Filtered assets:', filteredAssets.length);
    console.log('Current view:', currentView);
    console.log('Selected dimension:', selectedDimension);
    console.log('Selected category:', selectedCategory);
    console.log('Selected subcategory:', selectedSubcategory);
    console.log('Active filters:', activeFilters);
    if (assets.length > 0) {
      console.log('Sample asset structure:', assets[0]);
    }
    console.log('=======================');
  }, [assets, filteredAssets, currentView, selectedDimension, selectedCategory, selectedSubcategory, activeFilters]);

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
      rootFolder: '/net/library/atlaslib/3D',
      jsonFilePath: '/net/library/atlaslib/database/3DAssets.json',
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

  const copyAssetToClipboard = async (asset) => {
    try {
      // Create comprehensive asset data for Houdini clipboard
      const assetClipboardData = {
        // Core asset information
        atlas_asset_id: asset.id,
        asset_name: asset.name,
        asset_type: asset.metadata?.asset_type || asset.category,
        subcategory: asset.metadata?.subcategory || 'General',
        render_engine: asset.metadata?.render_engine || 'Redshift',
        
        // File paths (Docker-mounted paths for Houdini access)  
        asset_folder: asset.asset_folder || `/net/library/atlaslib/3D/${asset.metadata?.asset_type || 'Assets'}/${asset.metadata?.subcategory?.replace(/\s/g, '') || 'General'}/${asset.id}_${asset.name}`,
        template_file: `${asset.id}_${asset.name}.hip`,
        usd_file: asset.paths?.usd || `${asset.id}_${asset.name}.usd`,
        
        // Metadata for smart pasting
        metadata: {
          dimension: asset.metadata?.dimension || '3D',
          export_context: asset.metadata?.export_context || 'houdini',
          houdini_version: asset.metadata?.houdini_version || '20.0',
          tags: asset.metadata?.tags || [],
          description: asset.description || '',
          artist: asset.artist || 'Unknown'
        },
        
        // Instructions for Houdini
        paste_instructions: {
          method: 'template_load',
          load_command: 'hou.hipFile.load("TEMPLATE_PATH", suppress_save_prompt=True)',
          copy_nodes_command: 'atlas_clipboard_paste',
          notes: 'Asset exported from Blacksmith Atlas - use Atlas clipboard system for pasting'
        },
        
        // Timestamp
        copied_at: new Date().toISOString(),
        copy_source: 'blacksmith_atlas_web'
      };

      // Create formatted text for clipboard that includes both JSON data and human-readable info
      const clipboardText = `# Blacksmith Atlas Asset Copy
# Asset: ${asset.name}
# Type: ${asset.metadata?.dimension || '3D'} → ${asset.metadata?.asset_type || 'Assets'} → ${asset.metadata?.subcategory || 'General'}
# Render Engine: ${asset.metadata?.render_engine || 'Redshift'}
# Artist: ${asset.artist || 'Unknown'}
# Copied: ${new Date().toLocaleString()}

# JSON Data for Houdini Integration:
${JSON.stringify(assetClipboardData, null, 2)}

# To paste in Houdini:
# 1. Use Atlas Clipboard System: Ctrl+V or Atlas Paste shelf button
# 2. Or manually load template: ${assetClipboardData.asset_folder}/${assetClipboardData.template_file}`;

      // Copy to clipboard
      await navigator.clipboard.writeText(clipboardText);
      
      // Show success feedback
      console.log('Asset copied to clipboard:', assetClipboardData);
      
      // Optional: Show a more prominent notification
      alert(`✅ Asset "${asset.name}" copied to clipboard!\n\nYou can now paste it in Houdini using:\n• Ctrl+V (Atlas Clipboard System)\n• Atlas Paste shelf button\n• Or manually load the template file`);
      
    } catch (error) {
      console.error('Failed to copy asset to clipboard:', error);
      alert('❌ Failed to copy asset to clipboard. Please try again.');
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

  const assetCategories = [...new Set(assets.map(asset => asset.category))];
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

        {/* Search and Controls - Only show in assets view */}
        {currentView === 'assets' && (
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
                        {assetCategories.map(category => (
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

            {/* Active Navigation Filters - positioned right after Filter button */}
            {activeFilters.length > 0 && (
              <div className="flex items-center gap-2">
                {activeFilters.map(filter => (
                  <div key={filter.id} className="flex items-center gap-1 bg-blue-600/20 border border-blue-500 rounded-lg px-3 py-1 text-sm">
                    <span className="text-blue-200">{filter.label}</span>
                    <button
                      onClick={() => removeNavigationFilter(filter.id, filter.type)}
                      className="text-blue-300 hover:text-white transition-colors"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Breadcrumb Navigation */}
        {currentView !== 'dimension' && (
          <div className="flex items-center gap-2 text-sm text-neutral-400 mt-4">
            <button
              onClick={handleBackToDimensions}
              className="hover:text-white transition-colors"
            >
              Asset Library
            </button>
            {selectedDimension && (
              <>
                <span>/</span>
                <button
                  onClick={currentView === 'category' ? undefined : handleBackToCategories}
                  className={currentView === 'category' ? "text-blue-400" : "hover:text-white transition-colors"}
                >
                  {selectedDimension}
                </button>
              </>
            )}
            {selectedCategory && (
              <>
                <span>/</span>
                <button
                  onClick={currentView === 'subcategory' ? undefined : handleBackToSubcategories}
                  className={currentView === 'subcategory' ? "text-blue-400" : "hover:text-white transition-colors"}
                >
                  {selectedCategory}
                </button>
              </>
            )}
            {selectedSubcategory && (
              <>
                <span>/</span>
                <span className="text-blue-400">{selectedSubcategory}</span>
              </>
            )}
          </div>
        )}
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
                    placeholder="/net/library/atlaslib/3D"
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
                    placeholder="/net/library/atlaslib/database/3DAssets.json"
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
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 transition-all duration-300 ease-in-out">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg max-w-7xl w-full max-h-[95vh] overflow-auto transform transition-all duration-300 ease-in-out scale-100">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-700">
              <div>
                <h2 className="text-xl font-semibold text-white">{previewAsset.name}</h2>
                <div className="flex items-center gap-4 mt-2">
                  {/* Hierarchy Path */}
                  <div className="flex items-center gap-2 text-sm">
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded">{previewAsset.metadata?.dimension || '3D'}</span>
                    <span className="text-neutral-400">→</span>
                    <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded">{previewAsset.metadata?.asset_type || previewAsset.category}</span>
                    <span className="text-neutral-400">→</span>
                    <span className="px-2 py-1 bg-green-600/20 text-green-300 rounded">{previewAsset.metadata?.subcategory || 'General'}</span>
                  </div>
                  <div className="text-neutral-400 text-sm">•</div>
                  <div className="text-neutral-400 text-sm">{previewAsset.artist || 'Unknown Artist'}</div>
                </div>
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
                        <span className="text-neutral-400">Render Engine:</span>
                        <span className="text-orange-400">{previewAsset.metadata?.render_engine || 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Size:</span>
                        <span className="text-neutral-300">
                          {(() => {
                            const totalBytes = previewAsset.file_sizes?.total_folder_size || 0;
                            if (totalBytes === 0) return 'Calculating...';
                            if (totalBytes < 1024 * 1024) return `${Math.round(totalBytes / 1024)} KB`;
                            else if (totalBytes < 1024 * 1024 * 1024) return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                            else return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                          })()}
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
                  <div className="space-y-3 pt-4">
                    <button 
                      onClick={() => copyAssetToClipboard(previewAsset)}
                      className="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                    >
                      <Copy size={20} />
                      Copy Atlas Asset
                    </button>
                    <button 
                      onClick={async () => {
                        try {
                          const response = await fetch(`http://localhost:8000/api/v1/assets/${previewAsset.id}/open-folder`, {
                            method: 'POST'
                          });
                          
                          if (response.ok) {
                            const result = await response.json();
                            alert(`✅ ${result.message}`);
                          } else {
                            const error = await response.json();
                            alert(`❌ Failed to open folder: ${error.detail}`);
                          }
                        } catch (error) {
                          console.error('Error opening folder:', error);
                          alert('❌ Failed to open folder. Please check console for details.');
                        }
                      }}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                    >
                      <FolderOpen size={20} />
                      Open Asset Folder
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="p-6">
        {/* Dimension Selection View */}
        {currentView === 'dimension' && (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-white mb-4">Choose Asset Type</h2>
              <p className="text-neutral-400 text-lg">Select the type of assets you want to browse</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {dimensions.map(dimension => (
                <button
                  key={dimension.id}
                  onClick={() => handleDimensionSelect(dimension.id)}
                  className="group bg-neutral-800 hover:bg-neutral-750 border border-neutral-700 hover:border-blue-500 rounded-xl p-8 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-105"
                >
                  <div className="text-8xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    {dimension.icon}
                  </div>
                  <h3 className="text-3xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">
                    {dimension.name}
                  </h3>
                  <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors">
                    {dimension.description}
                  </p>
                  <div className="mt-6 inline-flex items-center gap-2 text-blue-400 group-hover:text-blue-300 transition-colors">
                    <span>Browse {dimension.name} Assets</span>
                    <ArrowLeft className="rotate-180" size={20} />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Category Selection View */}
        {currentView === 'category' && selectedDimension && (
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-white mb-4">{selectedDimension} Categories</h2>
              <p className="text-neutral-400 text-lg">Choose a category to browse {selectedDimension} assets</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categories[selectedDimension]?.map(category => (
                <button
                  key={category.id}
                  onClick={() => handleCategorySelect(category.id)}
                  className="group bg-neutral-800 hover:bg-neutral-750 border border-neutral-700 hover:border-blue-500 rounded-xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-105"
                >
                  <div className="text-6xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    {category.icon}
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                    {category.name}
                  </h3>
                  <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors text-sm">
                    {category.description}
                  </p>
                  <div className="mt-4 inline-flex items-center gap-2 text-blue-400 group-hover:text-blue-300 transition-colors">
                    <Folder size={16} />
                    <span>Browse</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Subcategory Selection View */}
        {currentView === 'subcategory' && selectedCategory && (
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-white mb-4">{selectedCategory} Subcategories</h2>
              <p className="text-neutral-400 text-lg">Choose a subcategory from {selectedCategory}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {subcategories[selectedCategory]?.map(subcategory => (
                <button
                  key={subcategory.id}
                  onClick={() => handleSubcategorySelect(subcategory.name)}
                  className="group bg-neutral-800 hover:bg-neutral-750 border border-neutral-700 hover:border-blue-500 rounded-xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-105"
                >
                  <div className="text-5xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    {subcategory.icon}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                    {subcategory.name}
                  </h3>
                  <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors text-sm">
                    {subcategory.description}
                  </p>
                  <div className="mt-4 inline-flex items-center gap-2 text-blue-400 group-hover:text-blue-300 transition-colors">
                    <Folder size={14} />
                    <span className="text-sm">Browse</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Assets View */}
        {currentView === 'assets' && (
          <>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-neutral-400 text-lg">Loading assets...</div>
              </div>
            ) : (
              <>
                <div className="bg-neutral-800 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-8 text-sm text-neutral-400">
                    <span>{filteredAssets.length} assets found</span>
                    <span>Path: /net/library/atlaslib/{selectedDimension}/{selectedCategory}{selectedSubcategory ? `/${selectedSubcategory}` : ''}</span>
                    <span>Database: {dbStatus.database_type || 'JSON'}</span>
                    {(selectedFilters.type !== 'all' || selectedFilters.category !== 'all' || selectedFilters.creator !== 'all') && (
                      <span className="text-blue-400">Filtered</span>
                    )}
                  </div>
                </div>

                {viewMode === 'grid' ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                    {filteredAssets.map(asset => (
                      <div key={asset.id} className="group relative overflow-hidden">
                        <div 
                          className="bg-neutral-800 rounded-lg overflow-hidden border border-neutral-700 hover:border-blue-500 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10 cursor-pointer"
                          onClick={() => openPreview(asset)}
                        >
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
                                {selectedDimension}
                              </span>
                            </div>

                            {/* Render Engine Tags - Bottom Right */}
                            <div className="absolute bottom-2 right-2 flex flex-col gap-1 items-end">
                              {(asset.metadata?.render_engine === 'Redshift' || asset.metadata?.render_engine?.includes('Redshift')) && (
                                <span className="px-2 py-1 text-xs rounded font-medium bg-red-500/20 text-red-300 backdrop-blur-sm">
                                  Redshift
                                </span>
                              )}
                              {(asset.metadata?.render_engine === 'Karma' || asset.metadata?.render_engine?.includes('Karma')) && (
                                <span className="px-2 py-1 text-xs rounded font-medium bg-gray-500/20 text-gray-300 backdrop-blur-sm">
                                  Karma
                                </span>
                              )}
                              {/* If asset has multiple exports with different engines, check tags */}
                              {asset.metadata?.tags?.includes('redshift') && !asset.metadata?.render_engine?.includes('Redshift') && (
                                <span className="px-2 py-1 text-xs rounded font-medium bg-red-500/20 text-red-300 backdrop-blur-sm">
                                  Redshift
                                </span>
                              )}
                              {asset.metadata?.tags?.includes('karma') && !asset.metadata?.render_engine?.includes('Karma') && (
                                <span className="px-2 py-1 text-xs rounded font-medium bg-gray-500/20 text-gray-300 backdrop-blur-sm">
                                  Karma
                                </span>
                              )}
                            </div>

                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                              <div className="flex gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openPreview(asset);
                                  }}
                                  className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors"
                                >
                                  <Eye size={16} />
                                </button>
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyAssetToClipboard(asset);
                                  }}
                                  className="bg-green-700 hover:bg-green-600 text-white p-2 rounded-lg transition-colors"
                                  title="Copy to Houdini"
                                >
                                  <Copy size={16} />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="absolute bottom-0 left-0 right-0 bg-neutral-800 border border-neutral-700 rounded-b-lg p-3 transform translate-y-full group-hover:translate-y-0 transition-transform duration-200 z-10 shadow-lg">
                          <h3 className="text-white font-semibold text-sm mb-1 truncate">{asset.name}</h3>
                          <p className="text-neutral-400 text-xs mb-2 line-clamp-2">{asset.description || 'No description available'}</p>

                          {/* Technical Details Grid - Simplified */}
                          <div className="grid grid-cols-2 gap-2 text-xs text-neutral-500">
                            <div>
                              <span className="text-neutral-400">Render Engine:</span>
                              <div className="text-orange-400 font-medium">{asset.metadata?.render_engine || 'Unknown'}</div>
                            </div>
                            <div>
                              <span className="text-neutral-400">Size:</span>
                              <div className="text-neutral-300">
                                {(() => {
                                  // Use total_folder_size which includes all assets and textures
                                  const totalBytes = asset.file_sizes?.total_folder_size || 0;
                                  
                                  if (totalBytes === 0) {
                                    // If no size data, show placeholder
                                    return <span className="text-neutral-500">Calculating...</span>;
                                  }
                                  
                                  // Convert to appropriate unit
                                  if (totalBytes < 1024 * 1024) {
                                    return `${Math.round(totalBytes / 1024)} KB`;
                                  } else if (totalBytes < 1024 * 1024 * 1024) {
                                    return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                                  } else {
                                    return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                                  }
                                })()}
                              </div>
                            </div>
                            <div>
                              <span className="text-neutral-400">Artist:</span>
                              <div className="text-green-400 font-medium truncate">{asset.artist || 'Unknown'}</div>
                            </div>
                            <div>
                              <span className="text-neutral-400">Version:</span>
                              <div className="text-blue-300 font-medium">{asset.metadata?.houdini_version || 'Unknown'}</div>
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
                          <button 
                            onClick={() => copyAssetToClipboard(asset)}
                            className="bg-green-700 hover:bg-green-600 text-white py-1 px-3 rounded text-sm transition-colors"
                            title="Copy to Houdini"
                          >
                            <Copy size={14} />
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
                      <span className="text-white font-medium">{assetCategories.length}</span>
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
          </>
        )}
      </div>
    </div>
  );
};

export default AssetLibrary;