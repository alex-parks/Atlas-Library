// New Asset Library with Navigation Structure
import React, { useState, useEffect } from 'react';
import { Search, Grid3X3, List, Filter, Upload, Copy, Eye, X, Settings, Save, FolderOpen, Database, RefreshCw, ArrowLeft, Folder, ExternalLink, MoreVertical, Edit, Trash2, Wrench, Moon, Sun, Palette } from 'lucide-react';
import SequenceThumbnail from './SequenceThumbnail';
import HoudiniAssetBadge from './badges/HoudiniAssetBadge';
import TextureBadge from './badges/TextureBadge';
import HDRIBadge from './badges/HDRIBadge';
import HoudiniAssetCard from './cards/HoudiniAssetCard';
import TextureCard from './cards/TextureCard';
import HDRICard from './cards/HDRICard';

// Asset Badge Factory - determines which badge component to use
const getAssetBadgeComponent = (asset) => {
  // Determine asset type from various sources
  let assetType = null;
  
  // Check asset_type field first (from uploads)
  if (asset.asset_type) {
    assetType = asset.asset_type;
  } else if (asset.category) {
    assetType = asset.category;
  } else {
    // Infer from file paths or other metadata
    if (asset.paths?.template_file) {
      const filename = asset.paths.template_file.toLowerCase();
      if (filename.includes('.hdr') || filename.includes('.hdri') || filename.includes('.exr')) {
        if (filename.includes('hdri') || asset.name?.toLowerCase().includes('hdri')) {
          assetType = 'HDRI';
        } else {
          assetType = 'Textures';
        }
      } else if (filename.includes('.jpg') || filename.includes('.png') || filename.includes('.tiff') || filename.includes('.tga')) {
        assetType = 'Textures';
      } else {
        assetType = 'Assets'; // Default to Houdini asset
      }
    } else {
      assetType = 'Assets'; // Default to Houdini asset
    }
  }
  
  // Return appropriate badge component
  switch (assetType) {
    case 'HDRI':
    case 'HDRIs':
      return HDRIBadge;
    case 'Textures':
    case 'Texture':
      return TextureBadge;
    default:
      // Default to Houdini Asset for anything else (Assets, FX, Materials, HDAs, etc.)
      return HoudiniAssetBadge;
  }
};

// Asset Card Factory - determines which card component to use for full card customization
const getAssetCardComponent = (asset) => {
  // Determine asset type from various sources
  let assetType = null;
  
  // Check asset_type field first (from uploads)
  if (asset.asset_type) {
    assetType = asset.asset_type;
  } else if (asset.category) {
    assetType = asset.category;
  } else {
    // Infer from file paths or other metadata
    if (asset.paths?.template_file) {
      const filename = asset.paths.template_file.toLowerCase();
      if (filename.includes('.hdr') || filename.includes('.hdri') || filename.includes('.exr')) {
        if (filename.includes('hdri') || asset.name?.toLowerCase().includes('hdri')) {
          assetType = 'HDRI';
        } else {
          assetType = 'Textures';
        }
      } else if (filename.includes('.jpg') || filename.includes('.png') || filename.includes('.tiff') || filename.includes('.tga')) {
        assetType = 'Textures';
      } else {
        assetType = 'Assets'; // Default to Houdini asset
      }
    } else {
      assetType = 'Assets'; // Default to Houdini asset
    }
  }
  
  // Return appropriate card component
  switch (assetType) {
    case 'HDRI':
    case 'HDRIs':
      return HDRICard;
    case 'Textures':
    case 'Texture':
      return TextureCard;
    default:
      // Default to Houdini Asset for anything else (Assets, FX, Materials, HDAs, etc.)
      return HoudiniAssetCard;
  }
};

const AssetLibrary = ({ 
  darkMode = true, 
  accentColor = 'blue', 
  handleDarkModeToggle, 
  handleAccentColorChange 
}) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [settingsTab, setSettingsTab] = useState('theme'); // 'theme' or 'database'
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
    'Textures': [
      { id: 'Uploaded', name: 'Uploaded', icon: '⬆️', description: 'Uploaded texture assets' }
    ],
    'HDRI': [
      { id: 'Uploaded', name: 'Uploaded', icon: '⬆️', description: 'Uploaded HDRI assets' }
    ]
  };

  // Preview modal state
  const [previewAsset, setPreviewAsset] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  
  // Dropdown menu state for asset actions
  const [activeDropdown, setActiveDropdown] = useState(null);
  
  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [newTagInput, setNewTagInput] = useState('');

  // Upload Asset modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadData, setUploadData] = useState({
    assetType: 'Textures', // 'Textures' or 'HDRI'
    name: '',
    filePath: '',
    description: ''
  });
  const [uploading, setUploading] = useState(false);

  const [selectedFilters, setSelectedFilters] = useState({
    showVariants: false,    // Show variants when checked (default unchecked = hide variants)
    showVersions: false,    // Show all versions when checked (default unchecked = show only latest)
    creator: 'all',
    showBranded: true       // Show branded assets when checked (default: on)
  });

  // Active navigation filters (from square button navigation)
  const [activeFilters, setActiveFilters] = useState([]);
  
  // Tag search functionality
  const [tagSearchTerm, setTagSearchTerm] = useState('');
  const [activeTagFilters, setActiveTagFilters] = useState([]);

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
    try {
      loadAssets(searchTerm, activeTagFilters);
      checkDatabaseStatus();
    } catch (error) {
      console.error('Error in AssetLibrary useEffect:', error);
      setLoading(false);
    }
  }, [settings.apiEndpoint]);

  // Debounced search effect - reload assets when search term changes
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (searchTerm !== '' || activeTagFilters.length > 0) {
        loadAssets(searchTerm, activeTagFilters);
      } else {
        loadAssets(); // Load all assets when search is empty and no tag filters
      }
    }, 300); // 300ms debounce delay

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]); // Only trigger when searchTerm changes, not activeTagFilters

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
    setActiveFilters([]); // Clear navigation filters when going back to dimensions
    // Don't clear assets - keep them loaded for filtering
  };

  const handleBackToCategories = () => {
    setCurrentView('category');
    setSelectedCategory(null);
    setSelectedSubcategory(null);
    // Remove category and subcategory filters but keep dimension filter
    setActiveFilters(prev => prev.filter(f => f.type === 'dimension'));
    // Don't clear assets - keep them loaded for filtering
  };

  const handleBackToSubcategories = () => {
    setCurrentView('subcategory');
    setSelectedSubcategory(null);
    // Remove subcategory filters but keep dimension and category filters
    setActiveFilters(prev => prev.filter(f => f.type === 'dimension' || f.type === 'category'));
    // Don't clear assets - keep them loaded for filtering
  };

  const handleJumpToLibrary = () => {
    setCurrentView('assets');
    
    // Set filters based on current navigation state
    let newFilters = [];
    
    if (selectedDimension) {
      newFilters.push({
        id: `dimension-${selectedDimension}`,
        type: 'dimension',
        value: selectedDimension,
        label: selectedDimension
      });
    }
    
    if (selectedCategory) {
      newFilters.push({
        id: `category-${selectedCategory}`,
        type: 'category', 
        value: selectedCategory,
        label: selectedCategory
      });
    }
    
    if (selectedSubcategory) {
      newFilters.push({
        id: `subcategory-${selectedSubcategory}`,
        type: 'subcategory',
        value: selectedSubcategory,
        label: selectedSubcategory
      });
    }
    
    setActiveFilters(newFilters);
  };

  const loadAssets = (searchFilter = null, tagFilters = null) => {
    setLoading(true);
    
    // Build query parameters
    const params = new URLSearchParams();
    if (searchFilter) params.set('search', searchFilter);
    if (tagFilters && tagFilters.length > 0) {
      tagFilters.forEach(tag => params.append('tags', tag));
    }
    
    const url = `${settings.apiEndpoint}${params.toString() ? '?' + params.toString() : ''}`;
    
    fetch(url)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('Loaded assets from API:', data);
        // API returns {items: [...], total: n, limit: n, offset: n}
        const assets = data.items || [];
        console.log(`Number of assets loaded: ${assets.length} ${tagFilters ? `(filtered by tags: ${tagFilters.join(', ')})` : ''}`);
        
        
        setAssets(Array.isArray(assets) ? assets : []);
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
          status: data.components?.database?.status || data.status || 'unknown',
          assets_count: data.components?.database?.assets_count || 0,
          database_type: data.components?.database?.type || 'unknown'
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
      showVariants: false,    // Reset to default OFF (hide variants)
      showVersions: false,    // Reset to default OFF (show only latest)
      creator: 'all',
      showBranded: true       // Reset to default ON (show branded assets)
    });
  };

  // Tag search functions
  const handleTagSearch = (e) => {
    if (e.key === 'Enter' && tagSearchTerm.trim()) {
      const newTag = tagSearchTerm.trim().toLowerCase();
      if (!activeTagFilters.includes(newTag)) {
        const newTagFilters = [...activeTagFilters, newTag];
        setActiveTagFilters(newTagFilters);
        // Reload assets with new tag filter
        loadAssets(searchTerm, newTagFilters);
      }
      setTagSearchTerm('');
    }
  };

  const removeTagFilter = (tagToRemove) => {
    const newTagFilters = activeTagFilters.filter(tag => tag !== tagToRemove);
    setActiveTagFilters(newTagFilters);
    // Reload assets without this tag filter
    loadAssets(searchTerm, newTagFilters);
  };

  const clearAllTagFilters = () => {
    setActiveTagFilters([]);
    // Reload assets without any tag filters
    loadAssets(searchTerm, []);
  };

  // Edit modal tag management functions
  const handleAddTag = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent form submission
      if (newTagInput.trim()) {
        const newTag = newTagInput.trim().toLowerCase();
        if (!editFormData.tags.includes(newTag)) {
          setEditFormData({
            ...editFormData,
            tags: [...editFormData.tags, newTag]
          });
        }
        setNewTagInput('');
      }
    }
  };

  const removeEditTag = (tagToRemove) => {
    setEditFormData({
      ...editFormData,
      tags: editFormData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  // Format asset name to show "{Original Name} - {Variant Name}" for variants
  const formatAssetName = (asset) => {
    // Check if this is a variant (variant_id is not "AA" - the original)
    const variantId = asset.variant_id || (asset.id && asset.id.length >= 13 ? asset.id.substring(11, 13) : 'AA');
    const variantName = asset.variant_name || asset.metadata?.variant_name;
    
    // If it's the original (AA variant) or no variant name, just show the original name
    if (variantId === 'AA' || !variantName || variantName === 'default') {
      return asset.name;
    }
    
    // For variants, show "Original Name - Variant Name"
    return `${asset.name} - ${variantName}`;
  };

  // Format asset name with JSX styling for hover cards (variant name darker)
  const formatAssetNameJSX = (asset) => {
    const variantId = asset.variant_id || (asset.id && asset.id.length >= 13 ? asset.id.substring(11, 13) : 'AA');
    const variantName = asset.variant_name || asset.metadata?.variant_name;
    
    // If it's the original (AA variant) or no variant name, just show the original name
    if (variantId === 'AA' || !variantName || variantName === 'default') {
      return <span>{asset.name}</span>;
    }
    
    // For variants, show "Original Name" in white and "- Variant Name" in darker gray
    return (
      <span>
        {asset.name} <span className="text-neutral-400">- {variantName}</span>
      </span>
    );
  };

  const filteredAssets = assets.filter(asset => {
    // Note: Search and tag filtering is now handled server-side via API
    // Only client-side filtering for creator, variants, versions, branded, and navigation
    
    const matchesCreator = selectedFilters.creator === 'all' || asset.artist === selectedFilters.creator;

    // Branded filtering logic
    const matchesBrandedFilter = selectedFilters.showBranded ? true : !(asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded);

    // Variant filtering logic
    let matchesVariantFilter = true;
    if (!selectedFilters.showVariants) {
      // When showVariants is OFF (unchecked): Only show assets where variant_id is 'AA' (original assets)
      // Check for variant_id in multiple possible locations
      const variantId = asset.metadata?.variant_id || asset.variant_id || 
                       (asset.metadata?.hierarchy?.variant_id) || 
                       // If no explicit variant_id, derive from asset ID (characters 10-11)
                       (asset.id && asset.id.length >= 11 ? asset.id.substring(9, 11) : 'AA');
      matchesVariantFilter = variantId === 'AA';
    }
    // When showVariants is ON (checked), matchesVariantFilter stays true (show all variants)

    // Version filtering logic  
    let matchesVersionFilter = true;
    if (!selectedFilters.showVersions) {
      // When showVersions is OFF (unchecked): Only show the highest version for each base ID
      // For version filtering, we need to group assets by their base ID (first 13 characters: 11-char base + 2-char variant)
      // and only show the highest version (last 3 digits) for each base ID
      
      // Extract the asset ID structure: XXXXXXXXXXX[AA]001
      const assetId = asset.id || asset._key || '';
      if (assetId.length >= 16) {
        const baseId = assetId.substring(0, 13); // First 13 characters (11 base + 2 variant)
        const versionNum = parseInt(assetId.substring(13), 10) || 1; // Last 3 digits as version
        
        // Find the highest version for this base ID among all assets
        const sameBaseAssets = assets.filter(a => {
          const otherId = a.id || a._key || '';
          return otherId.length >= 16 && otherId.substring(0, 13) === baseId;
        });
        
        const highestVersion = Math.max(...sameBaseAssets.map(a => {
          const otherId = a.id || a._key || '';
          return parseInt(otherId.substring(13), 10) || 1;
        }));
        
        // Only show if this asset has the highest version for its base ID
        matchesVersionFilter = versionNum === highestVersion;
      }
    }
    // When showVersions is ON (checked), matchesVersionFilter stays true (show all versions)

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

    return matchesCreator && matchesBrandedFilter && matchesVariantFilter && matchesVersionFilter && matchesNavigation && matchesActiveFilters;
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
    console.log('Selected filters:', selectedFilters);
    console.log('Show Variants filter:', selectedFilters.showVariants, '(true = show all variants, false = hide non-AA)');
    console.log('Show Versions filter:', selectedFilters.showVersions, '(true = show all versions, false = show only latest)');
    
    if (assets.length > 0) {
      console.log('Sample asset structure:', assets[0]);
      
      // Show some examples of variant_id and asset ID structures
      const sampleAssets = assets.slice(0, 10);
      console.log('Sample asset IDs and variants:');
      sampleAssets.forEach(asset => {
        const assetId = asset.id || asset._key || '';
        const variantId = asset.metadata?.variant_id || asset.variant_id || 
                         (asset.metadata?.hierarchy?.variant_id) || 
                         (asset.id && asset.id.length >= 11 ? asset.id.substring(9, 11) : 'AA');
        const derivedVariantId = asset.id && asset.id.length >= 11 ? asset.id.substring(9, 11) : 'AA';
        console.log(`  ID: ${assetId}, variant_id: ${variantId}, derived: ${derivedVariantId}, name: ${formatAssetName(asset)}`);
      });
      
      // Show filtering results for a few assets
      if (selectedFilters.noVariants === false || selectedFilters.noVersions === false) {
        console.log('Filter is OFF - should show all assets');
      }
    }
    console.log('=======================');
  }, [assets, filteredAssets, currentView, selectedDimension, selectedCategory, selectedSubcategory, activeFilters, selectedFilters]);

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

  const testConnection = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        const data = await response.json();
        setDbStatus({
          status: data.status,
          assets_count: data.components?.database?.assets_count || 0,
          database_type: data.components?.database?.type || 'Unknown'
        });
        alert('✅ Connection successful!\n\nDatabase: ' + (data.components?.database?.type || 'Unknown') + '\nAssets: ' + (data.components?.database?.assets_count || 0));
      } else {
        alert(`❌ Connection failed: ${response.status} ${response.statusText}`);
        setDbStatus({ status: 'error', assets_count: 0, database_type: 'Unknown' });
      }
    } catch (error) {
      alert(`❌ Connection failed: ${error.message}`);
      setDbStatus({ status: 'error', assets_count: 0, database_type: 'Unknown' });
    }
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

  const copyAssetToClipboard = async (asset) => {
    try {
      // Copy the full Asset ID to clipboard
      const assetId = asset.id;
      
      await navigator.clipboard.writeText(assetId);
      
      // Show success feedback
      console.log('Asset ID copied to clipboard:', assetId);
      alert(`✅ Asset ID copied: ${assetId}`);
      
    } catch (error) {
      console.error('Failed to copy asset ID to clipboard:', error);
      alert('❌ Failed to copy asset ID to clipboard. Please try again.');
    }
  };

  const copyVersionId = async (asset) => {
    try {
      // Extract version ID (remove last 3 characters)
      // CBA8403F4AA001 -> CBA8403F4AA
      const versionId = asset.id.slice(0, -3);
      
      await navigator.clipboard.writeText(versionId);
      
      console.log('Version ID copied to clipboard:', versionId);
      alert(`✅ Version ID copied: ${versionId}`);
      
    } catch (error) {
      console.error('Failed to copy version ID to clipboard:', error);
      alert('❌ Failed to copy version ID to clipboard. Please try again.');
    }
  };

  const copyVariantId = async (asset) => {
    try {
      // Extract variant ID (remove last 5 characters)
      // CBA8403F4AA001 -> CBA8403F4
      const variantId = asset.id.slice(0, -5);
      
      await navigator.clipboard.writeText(variantId);
      
      console.log('Variant ID copied to clipboard:', variantId);
      alert(`✅ Variant ID copied: ${variantId}`);
      
    } catch (error) {
      console.error('Failed to copy variant ID to clipboard:', error);
      alert('❌ Failed to copy variant ID to clipboard. Please try again.');
    }
  };

  // Upload Asset functionality
  const handleUploadAsset = async () => {
    if (!uploadData.name.trim() || !uploadData.filePath.trim()) {
      alert('❌ Please fill in both Name and File Path fields');
      return;
    }

    setUploading(true);
    try {
      console.log('🔧 Uploading asset:', uploadData);

      const response = await fetch('http://localhost:8000/api/v1/assets/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          asset_type: uploadData.assetType,
          name: uploadData.name,
          file_path: uploadData.filePath,
          description: uploadData.description || '',
          dimension: '3D',
          created_by: 'web_uploader'
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Asset uploaded successfully:', result);
        alert(`✅ Asset "${uploadData.name}" uploaded successfully!\n\nAsset ID: ${result.id}`);
        
        // Reset form
        setUploadData({
          assetType: 'Textures',
          name: '',
          filePath: '',
          description: ''
        });
        setShowUploadModal(false);
        
        // Refresh asset list
        loadAssets();
      } else {
        const error = await response.json();
        console.error('❌ Upload failed:', error);
        alert(`❌ Upload failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('❌ Upload error:', error);
      alert(`❌ Upload error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAsset = async (asset) => {
    try {
      // Show single confirmation dialog
      const confirmMessage = `⚠️  MOVE TO TRASHBIN ⚠️\n\nAre you sure you want to move this asset to the TrashBin?\n\nAsset: "${formatAssetName(asset)}"\nID: ${asset.id}\nCategory: ${asset.category}\n\n🗑️ The asset will be moved to:\n/net/library/atlaslib/TrashBin/${asset.metadata?.dimension || '3D'}/\n\n✅ This is RECOVERABLE - the asset folder will be moved to TrashBin, not permanently deleted.\n\n❌ The database entry will be removed.`;
      
      if (!confirm(confirmMessage)) {
        return;
      }

      // Show loading state
      setLoading(true);
      console.log(`🗑️ Deleting asset: ${asset.id} (${formatAssetName(asset)})`);

      // Call delete API
      const response = await fetch(`${settings.apiEndpoint}/${asset.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Delete response:', result);
        
        // Show success message with details
        const successMessage = `✅ Asset Successfully Moved to TrashBin!\n\nAsset: "${result.deleted_name}"\nID: ${result.deleted_id}\nDimension: ${result.dimension}\n\n${result.folder_moved ? 
          `📁 Folder moved to: /net/library/atlaslib/TrashBin/${result.dimension}/\n✅ Asset can be recovered from TrashBin if needed.` : 
          '📝 Database entry removed (no folder found to move).'
        }`;
        
        alert(successMessage);
        
        // Reload assets to update the UI
        await loadAssets();
        await checkDatabaseStatus();
        
      } else {
        const error = await response.json();
        console.error('❌ Delete failed:', error);
        alert(`❌ Failed to delete asset:\n\n${error.detail || 'Unknown error occurred'}\n\nCheck console for details.`);
      }
      
    } catch (error) {
      console.error('❌ Error deleting asset:', error);
      alert(`❌ Error deleting asset:\n\n${error.message}\n\nCheck console for details.`);
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

  // Click outside handler for dropdown menus
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (activeDropdown && !event.target.closest('.asset-dropdown-menu')) {
        setActiveDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeDropdown]);

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
            <button 
              onClick={() => setShowUploadModal(true)}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
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
          <div className="space-y-4">
            {/* Main Controls Row */}
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

              {/* Filter Button moved to same row */}
              <div className="relative">
                <button
                onClick={() => setShowFilterMenu(!showFilterMenu)}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  showFilterMenu ? 'bg-blue-600' : 'bg-neutral-700 hover:bg-neutral-600'
                }`}
              >
                <Filter size={18} />
                Filter
                {(selectedFilters.creator !== 'all' || selectedFilters.showVariants || selectedFilters.showVersions || !selectedFilters.showBranded) && (
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                )}
              </button>

              {showFilterMenu && (
                <>
                  {/* Backdrop to block interaction with assets behind */}
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowFilterMenu(false)}
                  ></div>
                  <div className="absolute right-0 top-12 bg-neutral-800 border border-neutral-700 rounded-lg shadow-lg z-50 w-80 pointer-events-auto">
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
                      <label className="block text-sm font-medium text-neutral-300 mb-2">Display Options</label>
                      <div className="space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedFilters.showVariants}
                            onChange={(e) => handleFilterChange('showVariants', e.target.checked)}
                            className="text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-neutral-300 text-sm">Variants</span>
                          <span className="text-neutral-500 text-xs">(Show all variants)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedFilters.showVersions}
                            onChange={(e) => handleFilterChange('showVersions', e.target.checked)}
                            className="text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-neutral-300 text-sm">Versions</span>
                          <span className="text-neutral-500 text-xs">(Show all versions)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedFilters.showBranded}
                            onChange={(e) => handleFilterChange('showBranded', e.target.checked)}
                            className="text-yellow-600 focus:ring-yellow-500"
                          />
                          <span className="text-neutral-300 text-sm">Branded</span>
                          <span className="text-neutral-500 text-xs">(Show branded assets)</span>
                        </label>
                      </div>
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
                </>
              )}
              </div>
            </div>

            {/* Tag Search Input Row */}
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <input
                  type="text"
                  placeholder="Filter by tags (e.g., tree, human, redshift)..."
                  value={tagSearchTerm}
                  onChange={(e) => setTagSearchTerm(e.target.value)}
                  onKeyDown={handleTagSearch}
                  className="w-full bg-neutral-600/50 border border-neutral-500 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-green-400 focus:bg-neutral-600 transition-all text-sm"
                />
              </div>
              
              {/* Clear all tags button */}
              {activeTagFilters.length > 0 && (
                <button
                  onClick={clearAllTagFilters}
                  className="px-3 py-2 bg-neutral-600 hover:bg-neutral-500 border border-neutral-500 rounded-lg text-neutral-300 hover:text-white text-sm transition-colors"
                  title="Clear all tag filters"
                >
                  Clear Tags
                </button>
              )}
            </div>

            {/* Active Tag Filters - Tag Bubbles */}
            {activeTagFilters.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs text-neutral-400 font-medium">Active Tags:</span>
                {activeTagFilters.map((tag, index) => (
                  <div key={`${tag}-${index}`} className="flex items-center gap-1 bg-green-600/20 border border-green-500/60 rounded-full px-3 py-1 text-sm backdrop-blur-sm">
                    <span className="text-green-200 font-medium">{tag}</span>
                    <button
                      onClick={() => removeTagFilter(tag)}
                      className="text-green-300 hover:text-white transition-colors p-0.5 rounded-full hover:bg-green-500/20"
                      title={`Remove "${tag}" tag filter`}
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}

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
              <h2 className="text-xl font-semibold text-white">Settings</h2>
              <button
                onClick={() => setShowSettingsPanel(false)}
                className="text-neutral-400 hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-1 mb-6 bg-neutral-700 rounded-lg p-1">
              <button
                onClick={() => setSettingsTab('theme')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  settingsTab === 'theme'
                    ? 'bg-neutral-600 text-white'
                    : 'text-neutral-400 hover:text-white'
                }`}
              >
                <Palette size={16} className="inline mr-2" />
                Theme
              </button>
              <button
                onClick={() => setSettingsTab('database')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  settingsTab === 'database'
                    ? 'bg-neutral-600 text-white'
                    : 'text-neutral-400 hover:text-white'
                }`}
              >
                <Database size={16} className="inline mr-2" />
                Database Connection
              </button>
            </div>

            {/* Tab Content */}
            {settingsTab === 'theme' ? (
              <div className="space-y-6">
                {/* Dark Mode Toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-neutral-700">
                      {darkMode ? (
                        <Moon className="w-5 h-5 text-blue-500" />
                      ) : (
                        <Sun className="w-5 h-5 text-yellow-500" />
                      )}
                    </div>
                    <div>
                      <div className="text-neutral-300 font-medium">
                        {darkMode ? 'Dark Mode' : 'Light Mode'}
                      </div>
                      <p className="text-xs text-neutral-500">
                        {darkMode ? 'Dark mode for low-light environments' : 'Light mode for bright environments'}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => handleDarkModeToggle && handleDarkModeToggle(!darkMode)}
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

                {/* Accent Color Selection */}
                <div>
                  <div className="text-neutral-300 font-medium mb-3">Accent Color</div>
                  <div className="flex gap-2">
                    {[
                      { name: 'Blue', value: 'blue', color: '#3b82f6' },
                      { name: 'Purple', value: 'purple', color: '#8b5cf6' },
                      { name: 'Green', value: 'green', color: '#10b981' },
                      { name: 'Orange', value: 'orange', color: '#f59e0b' },
                      { name: 'Red', value: 'red', color: '#ef4444' },
                      { name: 'White', value: 'white', color: '#ffffff' },
                      { name: 'Light Gray', value: 'lightgray', color: '#9ca3af' },
                      { name: 'Dark Gray', value: 'darkgray', color: '#4b5563' }
                    ].map((colorOption) => (
                      <button
                        key={colorOption.value}
                        onClick={() => handleAccentColorChange && handleAccentColorChange(colorOption.value)}
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
              </div>
            ) : (
              <div className="space-y-6">
                {/* Current Status */}
                <div>
                  <h3 className="text-white font-medium mb-4">Current Status</h3>
                  <div className="bg-neutral-700 rounded-lg p-4">
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
                        <div className="text-purple-400 font-medium">{dbStatus.database_type || 'ArangoDB Community Edition'}</div>
                      </div>
                      <div>
                        <span className="text-neutral-400">API:</span>
                        <div className="text-green-400 font-medium">Local</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Test Connection Button */}
                <div className="flex justify-center">
                  <button
                    onClick={testConnection}
                    className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <Database size={16} />
                    Test Connection
                  </button>
                </div>
              </div>
            )}

            {/* Close Button */}
            <div className="flex justify-end mt-6 pt-6 border-t border-neutral-700">
              <button
                onClick={() => setShowSettingsPanel(false)}
                className="bg-neutral-700 hover:bg-neutral-600 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingAsset && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-700">
              <h2 className="text-xl font-semibold text-white">Edit Asset</h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingAsset(null);
                  setEditFormData({});
                  setNewTagInput('');
                }}
                className="text-neutral-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              <form onSubmit={async (e) => {
                e.preventDefault();
                
                try {
                  // Only update editable fields - category, subcategory, and render engine are not editable
                  const updateData = {
                    name: editFormData.name,
                    description: editFormData.description,
                    tags: editFormData.tags || [],
                    thumbnail_frame: editFormData.thumbnail_frame
                  };
                  
                  
                  // Send PATCH request to update asset
                  const response = await fetch(`${settings.apiEndpoint}/${editingAsset.id}`, {
                    method: 'PATCH',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(updateData)
                  });
                  
                  if (response.ok) {
                    // Close modal
                    setShowEditModal(false);
                    setEditingAsset(null);
                    setEditFormData({});
                    setNewTagInput('');
                    
                    // Show success message
                    alert('✅ Asset updated successfully!');
                    
                    // Reload assets to ensure consistency
                    loadAssets();
                  } else {
                    const error = await response.json();
                    console.error('Backend error response:', error);
                    alert(`❌ Failed to update asset: ${error.detail || 'Unknown error'}`);
                  }
                } catch (error) {
                  console.error('Error updating asset:', error);
                  console.error('Full error object:', error);
                  alert(`❌ Error updating asset: ${error.message}`);
                }
              }} className="space-y-4">
                {/* Asset Name and Thumbnail Frame */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Asset Name
                    </label>
                    <input
                      type="text"
                      value={editFormData.name || ''}
                      onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
                      className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                      placeholder="Enter asset name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Thumbnail Frame
                    </label>
                    <input
                      type="number"
                      value={editFormData.thumbnail_frame || ''}
                      onChange={(e) => setEditFormData({...editFormData, thumbnail_frame: parseInt(e.target.value) || undefined})}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                        }
                      }}
                      className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-green-500"
                      placeholder="Default frame"
                      min="1001"
                      step="1"
                      title="Frame number to show when not hovering (e.g., 1001, 1015)"
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={editFormData.description || ''}
                    onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                    placeholder="Enter asset description"
                    rows={3}
                  />
                </div>


                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Tags
                  </label>
                  
                  {/* Current Tags as Bubbles */}
                  {editFormData.tags && editFormData.tags.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 mb-3 p-3 bg-neutral-700/50 border border-neutral-600 rounded-lg">
                      <span className="text-xs text-neutral-400 font-medium">Current Tags:</span>
                      {editFormData.tags.map((tag, index) => (
                        <div key={`${tag}-${index}`} className="flex items-center gap-1 bg-green-600/20 border border-green-500/60 rounded-full px-3 py-1 text-sm backdrop-blur-sm">
                          <span className="text-green-200 font-medium">{tag}</span>
                          <button
                            type="button"
                            onClick={() => removeEditTag(tag)}
                            className="text-green-300 hover:text-white transition-colors p-0.5 rounded-full hover:bg-green-500/20"
                            title={`Remove "${tag}" tag`}
                          >
                            <X size={12} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add New Tag Input */}
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={handleAddTag}
                    className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-green-400 focus:bg-neutral-600 transition-all"
                    placeholder="Type a tag and press Enter to add..."
                  />
                  <p className="text-xs text-neutral-400 mt-1">Press Enter to add tags. Click the X on existing tags to remove them.</p>
                </div>


                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <Save size={16} />
                    Save Changes
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingAsset(null);
                      setEditFormData({});
                      setNewTagInput('');
                    }}
                    className="bg-neutral-700 hover:bg-neutral-600 text-white py-2 px-4 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Upload Asset Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-neutral-700">
              <h2 className="text-xl font-semibold text-white">Upload Asset</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-neutral-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Asset Type Selection */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Asset Type <span className="text-red-400">*</span>
                </label>
                <select
                  value={uploadData.assetType}
                  onChange={(e) => setUploadData(prev => ({ ...prev, assetType: e.target.value }))}
                  className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="Textures">🖼️ Textures</option>
                  <option value="HDRI">🌅 HDRI</option>
                </select>
              </div>

              {/* Asset Name */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Asset Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={uploadData.name}
                  onChange={(e) => setUploadData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter asset name..."
                  className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* File Path */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  File Path <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={uploadData.filePath}
                  onChange={(e) => setUploadData(prev => ({ ...prev, filePath: e.target.value }))}
                  placeholder="/net/general/your/path/image.exr"
                  className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500 font-mono text-sm"
                />
                <p className="text-xs text-neutral-400 mt-1">
                  Full path to the image file (supports: .exr, .hdr, .jpg, .png, .tiff)<br/>
                  Available paths: /net/general/... or /app/assets/...<br/>
                  File will be copied to Asset/ folder with exact aspect ratio thumbnail
                </p>
              </div>

              {/* Description (Optional) */}
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Description <span className="text-neutral-500">(optional)</span>
                </label>
                <textarea
                  value={uploadData.description}
                  onChange={(e) => setUploadData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Optional description..."
                  rows={3}
                  className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 px-4 py-2 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadAsset}
                  disabled={uploading || !uploadData.name.trim() || !uploadData.filePath.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      Create Asset
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && previewAsset && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 transition-all duration-300 ease-in-out">
          <div className="bg-neutral-800 border border-neutral-700 rounded-lg w-[75vw] h-[80vh] overflow-auto transform transition-all duration-300 ease-in-out scale-100">
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
                    {(previewAsset.branded || previewAsset.metadata?.branded || previewAsset.metadata?.export_metadata?.branded) && (
                      <>
                        <span className="text-neutral-400">→</span>
                        <span className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded font-bold">⚠ BRANDED</span>
                      </>
                    )}
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
                {/* Large Preview Image with Interactive Sequence */}
                <div className="aspect-square bg-neutral-700 rounded-lg overflow-hidden">
                  <SequenceThumbnail
                    assetId={previewAsset.id || previewAsset._key}
                    assetName={formatAssetName(previewAsset)}
                    thumbnailFrame={previewAsset.thumbnail_frame}
                    fallbackIcon={
                      previewAsset.category === 'Characters' ? '🎭' :
                      previewAsset.category === 'Props' ? '📦' :
                      previewAsset.category === 'Environments' ? '🏞️' :
                      previewAsset.category === 'Vehicles' ? '🚗' :
                      previewAsset.category === 'Effects' ? '✨' :
                      '🎨'
                    }
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Asset Details */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white mb-2">Asset Information</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Asset Name:</span>
                        <span className="text-white font-medium">{formatAssetNameJSX(previewAsset)}</span>
                      </div>
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
                        <span className="text-orange-400">{previewAsset.metadata?.hierarchy?.render_engine || previewAsset.metadata?.render_engine || 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Size:</span>
                        <span className="text-neutral-300">
                          {(() => {
                            const totalBytes = previewAsset.file_sizes?.estimated_total_size || 0;
                            if (totalBytes === 0) return 'Calculating...';
                            if (totalBytes < 1024 * 1024) return `${Math.round(totalBytes / 1024)} KB`;
                            else if (totalBytes < 1024 * 1024 * 1024) return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                            else return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                          })()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Version:</span>
                        <span className="text-purple-400 font-medium">
                          {(() => {
                            const assetId = previewAsset.id || previewAsset._key || '';
                            if (assetId.length >= 16) {
                              // Extract version only (last 3 characters): 11 base + 2 variant + 3 version
                              return `v${assetId.substring(13)}`;
                            }
                            return 'v001';
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
                    {/* Main Action Buttons */}
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
                          console.log('DEBUG: Opening folder for asset:', previewAsset.id);
                          console.log('DEBUG: Asset data:', previewAsset);
                          console.log('DEBUG: Full URL:', `http://localhost:8000/api/v1/assets/${previewAsset.id}/open-folder`);
                          
                          const response = await fetch(`http://localhost:8000/api/v1/assets/${previewAsset.id}/open-folder`, {
                            method: 'POST'
                          });
                          
                          if (response.ok) {
                            const result = await response.json();
                            console.log('DEBUG: Folder open success:', result);
                            alert(`✅ ${result.message}`);
                          } else {
                            const error = await response.json();
                            console.log('DEBUG: Folder open failed:', error);
                            alert(`❌ Failed to open folder: ${error.detail || 'Unknown error'}\n\nAsset ID: ${previewAsset.id}`);
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
                    
                    {/* Smaller ID Copy Buttons */}
                    <div className="flex gap-2 pt-2">
                      <button 
                        onClick={() => copyVersionId(previewAsset)}
                        className="flex-1 bg-neutral-600 hover:bg-neutral-700 text-white py-2 px-3 rounded-md transition-colors flex items-center justify-center gap-2 text-sm"
                      >
                        <Copy size={14} />
                        Copy Version ID
                      </button>
                      <button 
                        onClick={() => copyVariantId(previewAsset)}
                        className="flex-1 bg-neutral-600 hover:bg-neutral-700 text-white py-2 px-3 rounded-md transition-colors flex items-center justify-center gap-2 text-sm"
                      >
                        <Copy size={14} />
                        Copy Variant ID
                      </button>
                    </div>
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
            
            {/* Jump To Library Button */}
            <div className="flex justify-center mt-12">
              <button
                onClick={handleJumpToLibrary}
                className="group bg-neutral-800 hover:bg-neutral-750 border border-neutral-700 hover:border-blue-500 text-white px-6 py-2 rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-105"
              >
                <div className="flex items-center gap-2">
                  <span className="text-base group-hover:text-blue-400 transition-colors">Jump To Library</span>
                  <ArrowLeft className="rotate-180 group-hover:text-blue-400 transition-colors" size={16} />
                </div>
              </button>
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
            
            {/* Jump To Library Button */}
            <div className="flex justify-center mt-12">
              <button
                onClick={handleJumpToLibrary}
                className="group bg-neutral-800 hover:bg-neutral-750 border border-neutral-700 hover:border-blue-500 text-white px-6 py-2 rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-105"
              >
                <div className="flex items-center gap-2">
                  <span className="text-base group-hover:text-blue-400 transition-colors">Jump To Library</span>
                  <ArrowLeft className="rotate-180 group-hover:text-blue-400 transition-colors" size={16} />
                </div>
              </button>
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
            
            {/* Jump To Library Button */}
            <div className="flex justify-center mt-12">
              <button
                onClick={handleJumpToLibrary}
                className="group bg-neutral-800 hover:bg-neutral-750 border border-neutral-700 hover:border-blue-500 text-white px-6 py-2 rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-105"
              >
                <div className="flex items-center gap-2">
                  <span className="text-base group-hover:text-blue-400 transition-colors">Jump To Library</span>
                  <ArrowLeft className="rotate-180 group-hover:text-blue-400 transition-colors" size={16} />
                </div>
              </button>
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
                    {(selectedFilters.creator !== 'all' || selectedFilters.showVariants || selectedFilters.showVersions || !selectedFilters.showBranded) && (
                      <span className="text-blue-400">Filtered</span>
                    )}
                  </div>
                </div>

                {viewMode === 'grid' ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                    {filteredAssets.map(asset => {
                      const CardComponent = getAssetCardComponent(asset);
                      return (
                        <CardComponent 
                          key={asset.id} 
                          asset={asset} 
                          formatAssetName={formatAssetName}
                          formatAssetNameJSX={formatAssetNameJSX}
                          openPreview={openPreview}
                        />
                      );
                    })}
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
                      <div key={asset.id} className={`grid grid-cols-12 gap-4 p-4 border-b transition-colors ${
                        asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded
                          ? 'border-yellow-600/30 bg-yellow-600/5 hover:bg-yellow-600/8'
                          : 'border-neutral-700 hover:bg-neutral-750'
                      }`}>
                        <div className="col-span-4">
                          <div className="flex items-center gap-2">
                            <div className="font-medium text-white">{formatAssetName(asset)}</div>
                            {(asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded) && (
                              <span className="text-yellow-500 text-sm font-bold">⚠</span>
                            )}
                          </div>
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