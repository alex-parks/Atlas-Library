// New Asset Library with Navigation Structure
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Search, Grid3X3, List, Filter, Upload, Copy, Eye, X, Settings, Save, FolderOpen, Database, RefreshCw, ArrowLeft, Folder, ExternalLink, MoreVertical, Edit, Trash2, Wrench, Moon, Sun, Palette, ChevronLeft, ChevronRight, ChevronUp, ChevronDown, Download } from 'lucide-react';
import SequenceThumbnail from './SequenceThumbnail';
import TextureSetSequence from './TextureSetSequence';
import HoudiniAssetBadge from './badges/HoudiniAssetBadge';
import TextureBadge from './badges/TextureBadge';
import HDRIBadge from './badges/HDRIBadge';
import HoudiniAssetCard from './cards/HoudiniAssetCard';
import TextureCard from './cards/TextureCard';
import HDRICard from './cards/HDRICard';
import TextureEditAsset from './TextureEditAsset';
import config from '../utils/config';

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
  handleAccentColorChange,
  onDbStatusChange 
}) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Pagination/virtual scrolling state
  const [displayedAssets, setDisplayedAssets] = useState([]);
  const [filteredAssetsState, setFilteredAssetsState] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const ASSETS_PER_PAGE = 50;
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [filterTab, setFilterTab] = useState('3d-assets'); // '3d-assets', 'textures', 'materials', 'hdri'
  const [badgeSize, setBadgeSize] = useState(50); // Badge size slider (0-100, default 50 = medium)

  // Calculate dynamic grid classes based on badge size
  const getGridClasses = () => {
    if (badgeSize <= 25) {
      // Small: More cards per row
      return "grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 2xl:grid-cols-12 gap-2";
    } else if (badgeSize <= 75) {
      // Medium: Default layout
      return "grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4";
    } else {
      // Large: Fewer cards per row, bigger cards
      return "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6";
    }
  };
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [settingsTab, setSettingsTab] = useState('theme'); // 'theme' or 'database'
  const [dbStatus, setDbStatus] = useState({ status: 'unknown', assets_count: 0 });
  const [lastBackup, setLastBackup] = useState(null);
  const [backupLoading, setBackupLoading] = useState(false);
  const [showControls, setShowControls] = useState(true); // Controls for sticky header minimize/expand
  const [isScrolled, setIsScrolled] = useState(false); // Track if user has scrolled

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
      { id: 'Alpha', name: 'Alpha', icon: '🔳', description: 'Alpha maps and transparency textures' },
      { id: 'Texture Sets', name: 'Texture Sets', icon: '📦', description: 'Complete material texture sets' },
      { id: 'Base Color', name: 'Base Color', icon: '🎨', description: 'Diffuse/Albedo color maps' },
      { id: 'Roughness', name: 'Roughness', icon: '⚪', description: 'Surface roughness maps' },
      { id: 'Normal', name: 'Normal', icon: '🔵', description: 'Normal/bump maps' },
      { id: 'Metallic', name: 'Metallic', icon: '⚫', description: 'Metallic/specular maps' },
      { id: 'Displacement', name: 'Displacement', icon: '📐', description: 'Height/displacement maps' },
      { id: 'Other', name: 'Other', icon: '🌐', description: 'Other texture types' }
    ],
    'HDRI': [
      { id: 'Outdoor', name: 'Outdoor', icon: '🏞️', description: 'Outdoor environment HDRIs' },
      { id: 'Skies', name: 'Skies', icon: '☁️', description: 'Sky dome HDRIs' },
      { id: 'Indoor', name: 'Indoor', icon: '🏠', description: 'Indoor environment HDRIs' },
      { id: 'Studio', name: 'Studio', icon: '📸', description: 'Studio lighting HDRIs' },
      { id: 'Sunrise/Sunset', name: 'Sunrise/Sunset', icon: '🌅', description: 'Dawn and dusk HDRIs' },
      { id: 'Night', name: 'Night', icon: '🌙', description: 'Night time HDRIs' },
      { id: 'Nature', name: 'Nature', icon: '🌳', description: 'Natural environment HDRIs' },
      { id: 'Urban', name: 'Urban', icon: '🏙️', description: 'City and urban HDRIs' },
      { id: 'Other', name: 'Other', icon: '🌐', description: 'Other HDRI categories' }
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
  const [newUploadTagInput, setNewUploadTagInput] = useState('');

  // Texture edit modal state
  const [showTextureEditModal, setShowTextureEditModal] = useState(false);
  const [editingTextureAsset, setEditingTextureAsset] = useState(null);

  // Upload Asset modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadData, setUploadData] = useState({
    assetType: 'Textures', // 'Textures' or 'HDRI'
    name: '',
    filePath: '',
    previewPath: '', // Preview JPEG/PNG for HDRIs
    previewImagePath: '', // Preview image for texture badge display
    tags: [], // Upload tags array
    description: '',
    subcategory: 'Alpha', // Default for Textures
    alphaSubcategory: 'General', // For Alpha textures
    textureType: 'seamless', // 'seamless' or 'uv_tile'
    textureSetPaths: {
      baseColor: '',
      metallic: '',
      roughness: '',
      normal: '',
      opacity: '',
      displacement: ''
    }
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
    apiEndpoint: `${config.backendUrl}/api/v1/assets`,
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

  // Check backup status when settings panel opens
  useEffect(() => {
    if (showSettingsPanel && settingsTab === 'database') {
      checkBackupStatus();
    }
  }, [showSettingsPanel, settingsTab]);

  // Scroll listener to detect when user scrolls
  useEffect(() => {
    const handleScroll = (e) => {
      const scrollTop = e.target.scrollTop;
      setIsScrolled(scrollTop > 100); // Show minimize button after scrolling 100px
    };

    // Find the scroll container (App.jsx content area)
    const scrollContainer = document.querySelector('.flex-1.overflow-auto');
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll);
      return () => scrollContainer.removeEventListener('scroll', handleScroll);
    }

    // Fallback to window scroll if container not found
    const handleWindowScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      setIsScrolled(scrollTop > 100);
    };

    window.addEventListener('scroll', handleWindowScroll);
    return () => window.removeEventListener('scroll', handleWindowScroll);
  }, []);

  // Update displayed assets when filtered assets change
  useEffect(() => {
    setCurrentPage(1);
    updateDisplayedAssets(filteredAssetsState, 1);
  }, [filteredAssetsState]);

  // Clean event listener for preview image updates (multi-user safe)
  // Removed complex preview update system to fix duplicate key issues
  // Now each TextureCard handles its own cache-busting independently

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
    // Set limit to maximum to show all assets (default is 100)
    params.set('limit', '1000');
    
    const url = `${settings.apiEndpoint}${params.toString() ? '?' + params.toString() : ''}`;
    
    fetch(url)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        // API returns {items: [...], total: n, limit: n, offset: n}
        const assets = data.items || [];
        setAssets(Array.isArray(assets) ? assets : []);
        // Reset pagination when new assets are loaded
        setCurrentPage(1);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load assets:', err);
        setLoading(false);
        setAssets([]);
        setDisplayedAssets([]);
      });
  };

  // Function to update displayed assets based on pagination
  const updateDisplayedAssets = (allAssets, page = 1) => {
    const startIndex = 0;
    const endIndex = page * ASSETS_PER_PAGE;
    const assetsToDisplay = allAssets.slice(startIndex, endIndex);
    setDisplayedAssets(assetsToDisplay);
  };

  // Function to load more assets (for scroll loading) - will be defined after filteredAssets
  let loadMoreAssets;

  const checkDatabaseStatus = () => {
    fetch(`${config.backendUrl}/health`)
      .then(res => res.json())
      .then(data => {
        const newDbStatus = {
          status: data.components?.database?.status || data.status || 'unknown',
          assets_count: data.components?.database?.assets_count || 0,
          database_type: data.components?.database?.type || 'unknown'
        };
        setDbStatus(newDbStatus);
        if (onDbStatusChange) {
          onDbStatusChange(newDbStatus);
        }
      })
      .catch(err => {
        console.error('Failed to check database status:', err);
        const errorDbStatus = { status: 'error', assets_count: 0 };
        setDbStatus(errorDbStatus);
        if (onDbStatusChange) {
          onDbStatusChange(errorDbStatus);
        }
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

  // Upload modal tag management functions
  const handleAddUploadTag = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent form submission
      if (newUploadTagInput.trim()) {
        const newTag = newUploadTagInput.trim().toLowerCase();
        if (!uploadData.tags.includes(newTag)) {
          setUploadData({
            ...uploadData,
            tags: [...uploadData.tags, newTag]
          });
        }
        setNewUploadTagInput('');
      }
    }
  };

  const removeUploadTag = (tagToRemove) => {
    setUploadData({
      ...uploadData,
      tags: uploadData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  // Format asset name to show "{Original Name} - {Variant Name}" for variants
  const formatAssetName = (asset) => {
    // Check if this is a variant (variant_id is not "AA" - the original)
    // For 3D assets from Houdini: 16-character ID (11 base + 2 variant + 3 version)
    // For HDRI/Texture uploads: 10-character ID (no variants/versions)
    const variantId = asset.variant_id || (asset.id && asset.id.length === 16 ? asset.id.substring(11, 13) : 'AA');
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
    // For 3D assets from Houdini: 16-character ID (11 base + 2 variant + 3 version)
    // For HDRI/Texture uploads: 10-character ID (no variants/versions)
    const variantId = asset.variant_id || (asset.id && asset.id.length === 16 ? asset.id.substring(11, 13) : 'AA');
    const variantName = asset.variant_name || asset.metadata?.variant_name;
    
    // If it's the original (AA variant) or no variant name, just show the original name
    if (variantId === 'AA' || !variantName || variantName === 'default') {
      return <span>{asset.name}</span>;
    }
    
    // For variants, show "Original Name" in white and "- Variant Name" in darker gray
    return (
      <span>
        {asset.name} <span className="text-gray-400">- {variantName}</span>
      </span>
    );
  };

  // Use state for filtered assets to avoid circular dependency
  useEffect(() => {
    const filtered = assets.filter(asset => {
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
                       // Derive from asset ID: 3D assets (16 chars) use positions 11-13, HDRI/Textures (10 chars) default to 'AA'
                       (asset.id && asset.id.length === 16 ? asset.id.substring(11, 13) : 'AA');
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
    
    setFilteredAssetsState(filtered);
  }, [assets, selectedFilters, currentView, selectedDimension, selectedCategory, selectedSubcategory, activeFilters]);

  // Define loadMoreAssets function
  loadMoreAssets = useCallback(() => {
    if (isLoadingMore || displayedAssets.length >= filteredAssetsState.length) return;
    
    setIsLoadingMore(true);
    setTimeout(() => {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      updateDisplayedAssets(filteredAssetsState, nextPage);
      setIsLoadingMore(false);
    }, 300); // Small delay to show loading state
  }, [filteredAssetsState, isLoadingMore, displayedAssets.length, currentPage]);

  // Removed debug logging for performance

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
        const response = await fetch(`${config.backendUrl}/admin/save-config`, {
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
      const response = await fetch(`${config.backendUrl}/health`);
      if (response.ok) {
        const data = await response.json();
        const newDbStatus = {
          status: data.status,
          assets_count: data.components?.database?.assets_count || 0,
          database_type: data.components?.database?.type || 'Unknown'
        };
        setDbStatus(newDbStatus);
        if (onDbStatusChange) {
          onDbStatusChange(newDbStatus);
        }
        alert('✅ Connection successful!\n\nDatabase: ' + (data.components?.database?.type || 'Unknown') + '\nAssets: ' + (data.components?.database?.assets_count || 0));
      } else {
        alert(`❌ Connection failed: ${response.status} ${response.statusText}`);
        const errorDbStatus = { status: 'error', assets_count: 0, database_type: 'Unknown' };
        setDbStatus(errorDbStatus);
        if (onDbStatusChange) {
          onDbStatusChange(errorDbStatus);
        }
      }
    } catch (error) {
      alert(`❌ Connection failed: ${error.message}`);
      const errorDbStatus = { status: 'error', assets_count: 0, database_type: 'Unknown' };
      setDbStatus(errorDbStatus);
      if (onDbStatusChange) {
        onDbStatusChange(errorDbStatus);
      }
    }
  };

  const checkBackupStatus = async () => {
    try {
      const response = await fetch(`${config.backendUrl}/api/v1/database/backup/status`);
      if (response.ok) {
        const data = await response.json();
        setLastBackup(data.last_backup);
      }
    } catch (error) {
      console.error('Failed to check backup status:', error);
    }
  };

  const handleBackupDatabase = async () => {
    setBackupLoading(true);
    try {
      const response = await fetch(`${config.backendUrl}/api/v1/database/backup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Database backup completed successfully!\n\nFile: ${result.backup_file}\nAssets: ${result.total_assets}\nTime: ${new Date(result.timestamp).toLocaleString()}`);
        // Refresh backup status
        checkBackupStatus();
      } else {
        const error = await response.json();
        alert(`❌ Backup failed: ${error.detail}`);
      }
    } catch (error) {
      alert(`❌ Backup failed: ${error.message}`);
    } finally {
      setBackupLoading(false);
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
    // Validate name is always required
    if (!uploadData.name.trim()) {
      alert('❌ Please fill in the Asset Name field');
      return;
    }

    // For texture sets, validate base color path (required), other paths are optional
    if (uploadData.assetType === 'Textures' && uploadData.subcategory === 'Texture Sets') {
      if (!uploadData.textureSetPaths.baseColor.trim()) {
        alert('❌ Please provide at least a Base Color file path for Texture Sets');
        return;
      }
    } else {
      // For all other asset types, file path is optional as requested
      // No validation needed for file path - it's now optional
    }

    setUploading(true);
    try {
      console.log('🔧 Uploading asset:', uploadData);

      const response = await fetch(`${config.backendUrl}/api/v1/assets/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          asset_type: uploadData.assetType,
          name: uploadData.name,
          // HDRI uploads: Always include file_path
          ...(uploadData.assetType === 'HDRI' && { 
            file_path: uploadData.filePath,
            // Include preview_path for HDRIs if provided
            ...(uploadData.previewPath && { preview_path: uploadData.previewPath })
          }),
          // Texture uploads: Handle different subcategories
          ...(uploadData.assetType === 'Textures' && {
            // Include preview image path for all textures if provided
            ...(uploadData.previewImagePath && { preview_image_path: uploadData.previewImagePath }),
            // For Texture Sets: Send texture_set_paths, no file_path
            ...(uploadData.subcategory === 'Texture Sets' && { texture_set_paths: uploadData.textureSetPaths }),
            // For Alpha textures: Include alpha_subcategory and file_path
            ...(uploadData.subcategory === 'Alpha' && { 
              alpha_subcategory: uploadData.alphaSubcategory,
              ...(uploadData.filePath && { file_path: uploadData.filePath })
            }),
            // For other single texture types: Include file_path
            ...(uploadData.subcategory !== 'Texture Sets' && uploadData.subcategory !== 'Alpha' && uploadData.filePath && { file_path: uploadData.filePath })
          }),
          description: uploadData.description || '',
          dimension: '3D',
          subcategory: uploadData.subcategory,
          created_by: 'web_uploader',
          // Add texture type metadata for Textures
          ...(uploadData.assetType === 'Textures' && {
            texture_type: uploadData.textureType,
            seamless: uploadData.textureType === 'seamless',
            uv_tile: uploadData.textureType === 'uv_tile'
          })
        })
      });

      console.log('🔧 Texture Type Debug:', {
        assetType: uploadData.assetType,
        textureType: uploadData.textureType,
        seamless: uploadData.textureType === 'seamless',
        uv_tile: uploadData.textureType === 'uv_tile'
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
          previewPath: '',
          previewImagePath: '', // Reset preview image path
          description: '',
          tags: [], // Reset tags
          subcategory: 'Alpha',
          alphaSubcategory: 'General',
          textureType: 'seamless',
          textureSetPaths: {
            baseColor: '',
            metallic: '',
            roughness: '',
            normal: '',
            opacity: '',
            displacement: ''
          }
        });
        setShowUploadModal(false);
        setNewUploadTagInput(''); // Reset upload tag input
        
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

  const handleEditAsset = (asset) => {
    // Determine if this is a texture asset
    const isTexture = asset.asset_type === 'Textures' || asset.asset_type === 'Texture' || 
                     asset.category === 'Textures' || asset.category === 'Texture' ||
                     (asset.paths?.template_file && 
                      (asset.paths.template_file.toLowerCase().includes('.jpg') || 
                       asset.paths.template_file.toLowerCase().includes('.png') || 
                       asset.paths.template_file.toLowerCase().includes('.tiff') || 
                       asset.paths.template_file.toLowerCase().includes('.tga')));
    
    if (isTexture) {
      // Use specialized texture edit modal
      setEditingTextureAsset(asset);
      setShowTextureEditModal(true);
    } else {
      // Use regular edit modal for 3D assets
      setEditingAsset(asset);
      setEditFormData({
        name: asset.name || '',
        description: asset.description || '',
        tags: asset.tags || [],
        thumbnail_frame: asset.thumbnail_frame
      });
      setShowEditModal(true);
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

  // Scroll detection for infinite loading
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const windowHeight = window.innerHeight;
      const docHeight = document.documentElement.offsetHeight;
      
      // Load more when user is 200px from bottom
      if (scrollTop + windowHeight >= docHeight - 200) {
        loadMoreAssets();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadMoreAssets]);

  const assetCategories = [...new Set(assets.map(asset => asset.category))];
  const creators = [...new Set(assets.map(asset => asset.artist).filter(Boolean))];

  // Simple Texture Modal Preview Component (delegates to backend for ordering)
  const TextureModalPreview = ({ asset }) => {
    const [currentFrameIndex, setCurrentFrameIndex] = useState(null);
    const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';

    // For texture sets, use the new TextureSetSequence component
    if (isTextureSet) {
      return (
        <TextureSetSequence
          assetId={asset.id || asset._key}
          assetName={formatAssetName(asset)}
          asset={asset}
          fallbackIcon="🖼️"
          className="w-full h-full object-contain"
          externalFrameIndex={currentFrameIndex}
          hideZoomMessage={false}
        />
      );
    }

    // For non-texture sets, use the simple SequenceThumbnail
    return (
      <SequenceThumbnail
        assetId={asset.id || asset._key}
        assetName={formatAssetName(asset)}
        thumbnailFrame={asset.thumbnail_frame}
        fallbackIcon="🖼️"
        disableScrubbing={false}
        className="w-full h-full object-contain"
      />
    );
  };

  // Texture File Copy Buttons Component
  const TextureFileCopyButtons = ({ asset }) => {
    const [availableTextures, setAvailableTextures] = useState([]);

    // Load available texture files from the asset
    useEffect(() => {
      const loadTextureFiles = async () => {
        let textureFiles = [];
        
        try {
          // First try the texture-images endpoint (for texture sets)
          const response = await fetch(`${config.backendUrl}/api/v1/assets/${asset.id || asset._key}/texture-images`);
          if (response.ok) {
            const data = await response.json();
            // Available texture files loaded from endpoint
            if (data.images && data.images.length > 0) {
              textureFiles = data.images;
            }
          }
        } catch (error) {
          console.log('Texture images endpoint failed:', error);
        }
        
        // If no texture files found from endpoint, check asset paths for single textures
        if (textureFiles.length === 0) {
          // Checking asset paths for single texture files
          
          // Check various possible locations for texture files
          const possibleFilePaths = [
            ...(asset.paths?.thumbnails || []),
            ...(asset.paths?.preview_files || []),
            ...(asset.paths?.textures || []),
            ...(asset.metadata?.textures?.files || [])
          ];
          
          if (possibleFilePaths.length > 0) {
            textureFiles = possibleFilePaths.map(filePath => {
              const filename = typeof filePath === 'string' ? filePath.split('/').pop() : filePath;
              return { 
                filename: filename, 
                path: typeof filePath === 'string' ? filePath : filename 
              };
            });
            // Found texture files from paths
          }
          
          // If still no files, check if this is a single texture by examining the asset name and category
          if (textureFiles.length === 0 && asset.asset_type === 'Textures') {
            // Single texture detected, using asset name as filename
            // For single textures, use the asset name as the filename
            const assetName = asset.name || 'texture';
            textureFiles = [{ 
              filename: `${assetName}.png`, // Default extension, will be detected from actual file
              path: `${asset.paths?.folder_path || ''}/Assets/${assetName}.png`
            }];
          }
        }
        
        // Final texture files array ready
        setAvailableTextures(textureFiles);
      };

      if (asset.id || asset._key) {
        loadTextureFiles();
      }
    }, [asset.id, asset._key]);

    // Define texture types and their display names
    const textureTypeMap = {
      'base_color': { name: 'Copy Base Color', keywords: ['base', 'color', 'albedo'] },
      'metallic': { name: 'Copy Metallic', keywords: ['metallic', 'metalness'] },
      'roughness': { name: 'Copy Roughness', keywords: ['roughness'] },
      'normal': { name: 'Copy Normal', keywords: ['normal'] },
      'displacement': { name: 'Copy Displacement', keywords: ['displacement', 'height'] },
      'alpha': { name: 'Copy Alpha', keywords: ['alpha', 'opacity'] }
    };

    // Find texture files for each type based on upload metadata, not filename
    const getTextureByType = (type) => {
      const typeInfo = textureTypeMap[type];
      if (!typeInfo) return null;

      // Check if this is a single texture (not a texture set)
      const subcategory = asset.subcategory || asset.metadata?.subcategory;
      const isTextureSet = subcategory === 'Texture Sets' || asset.metadata?.texture_set_info;
      
      if (!isTextureSet) {
        // For single textures, match based on the uploaded subcategory
        const subcategoryToTypeMap = {
          'Alpha': 'alpha',
          'Base Color': 'base_color', 
          'Albedo': 'base_color',
          'Metallic': 'metallic',
          'Roughness': 'roughness',
          'Normal': 'normal',
          'Displacement': 'displacement',
          'Height': 'displacement'
        };
        
        // Check if the asset's subcategory matches the requested type
        const assetTextureType = subcategoryToTypeMap[subcategory] || 
                                 subcategoryToTypeMap[asset.alpha_subcategory];
        
        if (assetTextureType === type && availableTextures.length > 0) {
          // Single texture match found
          return availableTextures[0]; // Return the single texture file
        }
      } else {
        // For texture sets - check texture_set_paths in metadata
        if (asset.metadata?.texture_set_info?.provided_paths) {
          const textureSetPaths = asset.metadata.texture_set_info.provided_paths;
          
          // Map texture types to the texture set keys
          const textureSetKeyMap = {
            'base_color': ['baseColor', 'albedo'],
            'metallic': ['metallic', 'metalness'],
            'roughness': ['roughness'],
            'normal': ['normal'],
            'displacement': ['displacement', 'height'],
            'alpha': ['alpha', 'opacity']
          };
          
          const possibleKeys = textureSetKeyMap[type] || [];
          for (const key of possibleKeys) {
            if (textureSetPaths[key]) {
              // Find the texture file that matches this texture set path
              const pathFilename = textureSetPaths[key].split('/').pop();
              const matchingTexture = availableTextures.find(texture => 
                texture.filename === pathFilename || texture.path.includes(pathFilename)
              );
              if (matchingTexture) {
                // Texture set match found
                return matchingTexture;
              }
            }
          }
        }
      }

      // No fallback filename parsing - rely only on upload metadata/subcategory
      // No texture found for this type
      return null;
    };

    // Copy texture file path to clipboard
    const copyTextureFilePath = async (textureType, texture) => {
      try {
        let fullTexturePath;
        let actualFilename = texture.filename;

        // PRIORITY 1: Find the actual asset file from copied_files based on texture type matching
        if (asset.paths?.copied_files && asset.paths.copied_files.length > 0) {
          console.log(`🔍 Looking for ${textureType} in copied_files:`, asset.paths.copied_files);
          
          // Get the type keywords for matching
          const typeKeywords = textureTypeMap[textureType]?.keywords || [];
          
          // Try to find matching file in copied_files
          const matchingFile = asset.paths.copied_files.find(filePath => {
            const filename = filePath.split('/').pop().toLowerCase();
            // Remove common texture suffixes to get base name for comparison
            const baseFilename = filename.replace(/\.(jpg|jpeg|png|tiff|tif|exr)$/i, '').toLowerCase();
            
            // Check if any of the type keywords are in the filename
            return typeKeywords.some(keyword => baseFilename.includes(keyword.toLowerCase()));
          });
          
          if (matchingFile) {
            fullTexturePath = matchingFile;
            actualFilename = matchingFile.split('/').pop();
            console.log(`📋 Found matching copied file: ${fullTexturePath}`);
          } else {
            console.log(`⚠️ No matching copied file found for ${textureType}, trying fallback...`);
          }
        }

        // PRIORITY 2: Fallback to constructed path using folder_path + Assets + filename
        if (!fullTexturePath && asset.paths?.folder_path) {
          fullTexturePath = `${asset.paths.folder_path}/Assets/${texture.filename}`;
          console.log(`📋 Constructed path from folder_path: ${fullTexturePath}`);
        } 
        
        // PRIORITY 3: Final fallback construction for texture assets
        if (!fullTexturePath) {
          const assetId = asset.id || asset._key;
          const subcategory = asset.metadata?.subcategory || asset.subcategory || 'TextureSet';
          fullTexturePath = `/net/library/atlaslib/3D/Textures/${subcategory}/${assetId}/Assets/${texture.filename}`;
          console.log(`📋 Fallback constructed path: ${fullTexturePath}`);
        }

        await navigator.clipboard.writeText(fullTexturePath);
        
        // Show success message
        const message = `✅ ${textureTypeMap[textureType].name} path copied!\n\n📄 File: ${actualFilename}\n📂 Path: ${fullTexturePath}`;
        alert(message);
        console.log(`📋 ${textureType} texture path copied:`, fullTexturePath);

      } catch (error) {
        console.error(`Failed to copy ${textureType} path:`, error);
        alert(`❌ Failed to copy ${textureTypeMap[textureType].name} path to clipboard`);
      }
    };

    if (availableTextures.length === 0) {
      return null; // No textures to show buttons for
    }

    return (
      <div className="space-y-2 mb-4">
        <div className="text-sm text-gray-400 font-medium mb-2">Copy Individual Textures:</div>
        <div className="space-y-1">
          {Object.entries(textureTypeMap).map(([type, typeInfo]) => {
            const texture = getTextureByType(type);
            if (!texture) return null; // Don't show button if texture doesn't exist

            return (
              <button
                key={type}
                onClick={() => copyTextureFilePath(type, texture)}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-md transition-colors bg-gray-500/20 text-gray-300 hover:bg-gray-500/30 text-sm font-medium"
                title={`Copy ${typeInfo.name} file path: ${texture.filename}`}
              >
                <Copy size={14} />
                {typeInfo.name}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-900 text-gray-100">
      {/* Sticky Controls Section with Tab */}
      <div className="sticky top-0 z-[40] group">
        {/* Grey Controls Area */}
        {showControls && (
          <div className="bg-gray-500 border-b border-gray-400 shadow-lg p-6">
            {/* Search and Controls - Only show in assets view */}
            {currentView === 'assets' && (
          <div className="space-y-4">
            {/* Main Controls Row */}
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-4 top-1/2 transform -trangray-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search assets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-gray-700/50 border border-gray-600/30 rounded-xl pl-12 pr-4 py-3 text-gray-100 placeholder-gray-400 focus:outline-none focus:border-blue-400/50 focus:bg-gray-700/70 transition-all duration-200 backdrop-blur-sm shadow-lg"
                />
              </div>

              <div className="flex items-center gap-1 bg-gray-700/50 border border-gray-600/30 rounded-xl p-1 backdrop-blur-sm shadow-lg">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2.5 rounded-lg transition-all duration-200 ${viewMode === 'grid' ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg' : 'hover:bg-gray-600/50 text-gray-400 hover:text-gray-300'}`}
                >
                  <Grid3X3 size={18} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2.5 rounded-lg transition-all duration-200 ${viewMode === 'list' ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg' : 'hover:bg-gray-600/50 text-gray-400 hover:text-gray-300'}`}
                >
                  <List size={18} />
                </button>
              </div>

              {/* Filter Button moved to same row */}
              <div className="relative">
                <button
                onClick={() => setShowFilterMenu(!showFilterMenu)}
                className={`px-5 py-2.5 rounded-xl flex items-center gap-2 transition-all duration-200 font-medium ${
                  showFilterMenu ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg' : 'bg-gray-700/50 border border-gray-600/30 hover:bg-gray-600/50 text-gray-300 hover:text-gray-200 backdrop-blur-sm shadow-lg'
                }`}
              >
                <Filter size={18} />
                Filter
                {(selectedFilters.creator !== 'all' || selectedFilters.showVariants || selectedFilters.showVersions || !selectedFilters.showBranded) && (
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                )}
              </button>

              {showFilterMenu && (
                <>
                  {/* Backdrop to block interaction with assets behind */}
                  <div 
                    className="fixed inset-0 z-[55]" 
                    onClick={() => setShowFilterMenu(false)}
                  ></div>
                  <div className="absolute right-0 top-14 bg-gray-800 border border-gray-600/30 rounded-xl shadow-2xl z-[60] w-96 pointer-events-auto backdrop-blur-lg">
                    <div className="p-5">
                      <div className="flex items-center justify-between mb-5">
                        <h3 className="text-gray-200 font-semibold text-lg">Filters</h3>
                        <button
                          onClick={() => setShowFilterMenu(false)}
                          className="text-gray-400 hover:text-gray-200 p-1 rounded-lg hover:bg-gray-700/50 transition-all duration-200"
                        >
                          <X size={18} />
                        </button>
                      </div>

                      {/* Filter Tabs */}
                      <div className="flex flex-wrap border-b border-gray-600/30 mb-5 -mx-1">
                        <button
                          onClick={() => setFilterTab('3d-assets')}
                          className={`flex-1 min-w-0 mx-1 px-2 py-2.5 text-xs font-medium transition-all duration-200 rounded-t-lg ${
                            filterTab === '3d-assets' 
                              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-400/10' 
                              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
                          }`}
                        >
                          3D Assets
                        </button>
                        <button
                          onClick={() => setFilterTab('textures')}
                          className={`flex-1 min-w-0 mx-1 px-2 py-2.5 text-xs font-medium transition-all duration-200 rounded-t-lg ${
                            filterTab === 'textures' 
                              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-400/10' 
                              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
                          }`}
                        >
                          Textures
                        </button>
                        <button
                          onClick={() => setFilterTab('materials')}
                          className={`flex-1 min-w-0 mx-1 px-2 py-2.5 text-xs font-medium transition-all duration-200 rounded-t-lg ${
                            filterTab === 'materials' 
                              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-400/10' 
                              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
                          }`}
                        >
                          Materials
                        </button>
                        <button
                          onClick={() => setFilterTab('hdri')}
                          className={`flex-1 min-w-0 mx-1 px-2 py-2.5 text-xs font-medium transition-all duration-200 rounded-t-lg ${
                            filterTab === 'hdri' 
                              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-400/10' 
                              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/30'
                          }`}
                        >
                          HDRI
                        </button>
                      </div>

                      {/* Tab Content */}
                      {filterTab === '3d-assets' && (
                        <>
                          <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Display Options</label>
                            <div className="space-y-2">
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedFilters.showVariants}
                                  onChange={(e) => handleFilterChange('showVariants', e.target.checked)}
                                  className="text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-gray-300 text-sm">Variants</span>
                                <span className="text-gray-500 text-xs">(Show all variants)</span>
                              </label>
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedFilters.showVersions}
                                  onChange={(e) => handleFilterChange('showVersions', e.target.checked)}
                                  className="text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-gray-300 text-sm">Versions</span>
                                <span className="text-gray-500 text-xs">(Show all versions)</span>
                              </label>
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedFilters.showBranded}
                                  onChange={(e) => handleFilterChange('showBranded', e.target.checked)}
                                  className="text-yellow-600 focus:ring-yellow-500"
                                />
                                <span className="text-gray-300 text-sm">Branded</span>
                                <span className="text-gray-500 text-xs">(Show branded assets)</span>
                              </label>
                            </div>
                          </div>

                          <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Creator</label>
                            <select
                              value={selectedFilters.creator}
                              onChange={(e) => handleFilterChange('creator', e.target.value)}
                              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                            >
                              <option value="all">All Creators</option>
                              {creators.map(creator => (
                                <option key={creator} value={creator}>{creator}</option>
                              ))}
                            </select>
                          </div>
                        </>
                      )}

                      {filterTab === 'textures' && (
                        <div className="mb-4">
                          <div className="text-center py-8 text-gray-400">
                            <p className="text-sm">Texture filters coming soon...</p>
                          </div>
                        </div>
                      )}

                      {filterTab === 'materials' && (
                        <div className="mb-4">
                          <div className="text-center py-8 text-gray-400">
                            <p className="text-sm">Material filters coming soon...</p>
                          </div>
                        </div>
                      )}

                      {filterTab === 'hdri' && (
                        <div className="mb-4">
                          <div className="text-center py-8 text-gray-400">
                            <p className="text-sm">HDRI filters coming soon...</p>
                          </div>
                        </div>
                      )}

                      <button
                        onClick={clearFilters}
                        className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 rounded text-sm transition-colors"
                      >
                        Clear All Filters
                      </button>
                    </div>
                  </div>
                </>
              )}
              </div>

              {/* Tag Search Input - moved to same row as Filter button */}
              <div className="relative flex-1 max-w-md">
                <input
                  type="text"
                  placeholder="Filter by tags (e.g., tree, human, redshift)..."
                  value={tagSearchTerm}
                  onChange={(e) => setTagSearchTerm(e.target.value)}
                  onKeyDown={handleTagSearch}
                  className="w-full bg-gray-600/50 border border-gray-500 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-green-400 focus:bg-gray-600 transition-all text-sm"
                />
              </div>
              
              {/* Clear all tags button */}
              {activeTagFilters.length > 0 && (
                <button
                  onClick={clearAllTagFilters}
                  className="px-3 py-2 bg-gray-600 hover:bg-gray-500 border border-gray-500 rounded-lg text-gray-300 hover:text-white text-sm transition-colors"
                  title="Clear all tag filters"
                >
                  Clear Tags
                </button>
              )}

              {/* Active Tag Filters - Tag Bubbles moved to same row */}
              {activeTagFilters.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 font-medium">Tags:</span>
                  <div className="flex flex-wrap items-center gap-1">
                    {activeTagFilters.map((tag, index) => (
                      <div key={`${tag}-${index}`} className="flex items-center gap-1 bg-green-600/20 border border-green-500/60 rounded-full px-2 py-1 text-xs backdrop-blur-sm">
                        <span className="text-green-200 font-medium">{tag}</span>
                        <button
                          onClick={() => removeTagFilter(tag)}
                          className="text-green-300 hover:text-white transition-colors p-0.5 rounded-full hover:bg-green-500/20"
                          title={`Remove "${tag}" tag filter`}
                        >
                          <X size={10} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}


              {/* Action Buttons - moved to far right of same row */}
              <div className="flex gap-3 ml-auto">
                <button
                  onClick={syncDatabase}
                  disabled={loading}
                  className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 px-5 py-2.5 rounded-xl flex items-center gap-2 transition-all duration-200 shadow-lg hover:shadow-violet-500/25 font-medium"
                >
                  <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                  Sync DB
                </button>
                <button 
                  onClick={() => setShowUploadModal(true)}
                  className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 px-5 py-2.5 rounded-xl flex items-center gap-2 transition-all duration-200 shadow-lg hover:shadow-blue-500/25 font-medium"
                >
                  <Upload size={18} />
                  Upload Asset
                </button>
                <button
                  onClick={() => setShowSettingsPanel(true)}
                  className="bg-gray-700/50 hover:bg-gray-600/50 border border-gray-600/30 px-5 py-2.5 rounded-xl flex items-center gap-2 transition-all duration-200 backdrop-blur-sm shadow-lg hover:shadow-lg font-medium"
                >
                  <Settings size={18} />
                  Settings
                </button>
              </div>
            </div>

          </div>
        )}

        {/* Breadcrumb Navigation */}
        {currentView !== 'dimension' && (
          <div className="flex items-center gap-4 text-sm text-gray-400 mt-4">
            <div className="flex items-center gap-2">
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
            
            {/* Active Navigation Filters - positioned right next to breadcrumb */}
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
          </div>
        )}

        {/* Minimize Toggle Tab - Always visible when minimized, hover-only when maximized */}
        <div className={`flex justify-center transition-opacity duration-200 pointer-events-none ${
          showControls 
            ? 'opacity-0 group-hover:opacity-100' 
            : 'opacity-100'
        }`}>
          <button
            onClick={() => setShowControls(!showControls)}
            className="bg-gray-600 hover:bg-gray-400 hover:shadow-xl text-gray-300 hover:text-white hover:scale-105 active:scale-95 active:bg-gray-800 transition-all duration-200 rounded-b-md px-4 py-1 shadow-lg border-l border-r border-b border-gray-400 hover:border-gray-200 pointer-events-auto"
            title={showControls ? "Minimize search area" : "Expand search area"}
          >
            <span className="transform transition-transform duration-200 inline-block hover:scale-110">
              {showControls ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </span>
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettingsPanel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Settings</h2>
              <button
                onClick={() => setShowSettingsPanel(false)}
                className="text-gray-400 hover:text-white"
              >
                <X size={24} />
              </button>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-1 mb-6 bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setSettingsTab('theme')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  settingsTab === 'theme'
                    ? 'bg-gray-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Palette size={16} className="inline mr-2" />
                Theme
              </button>
              <button
                onClick={() => setSettingsTab('database')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  settingsTab === 'database'
                    ? 'bg-gray-600 text-white'
                    : 'text-gray-400 hover:text-white'
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
                    <div className="p-2 rounded-lg bg-gray-700">
                      {darkMode ? (
                        <Moon className="w-5 h-5 text-blue-500" />
                      ) : (
                        <Sun className="w-5 h-5 text-yellow-500" />
                      )}
                    </div>
                    <div>
                      <div className="text-gray-300 font-medium">
                        {darkMode ? 'Dark Mode' : 'Light Mode'}
                      </div>
                      <p className="text-xs text-gray-500">
                        {darkMode ? 'Dark mode for low-light environments' : 'Light mode for bright environments'}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => handleDarkModeToggle && handleDarkModeToggle(!darkMode)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      darkMode ? 'bg-blue-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        darkMode ? 'trangray-x-6' : 'trangray-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Accent Color Selection */}
                <div>
                  <div className="text-gray-300 font-medium mb-3">Accent Color</div>
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
                            : 'border-gray-600 hover:border-gray-500'
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
                  <div className="bg-gray-700 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Database:</span>
                        <div className={`font-medium ${
                          dbStatus.status === 'healthy' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {dbStatus.status === 'healthy' ? 'Connected' : 'Disconnected'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-400">Assets:</span>
                        <div className="text-blue-400 font-medium">{dbStatus.assets_count}</div>
                      </div>
                      <div>
                        <span className="text-gray-400">Type:</span>
                        <div className="text-purple-400 font-medium">{dbStatus.database_type || 'ArangoDB Community Edition'}</div>
                      </div>
                      <div>
                        <span className="text-gray-400">API:</span>
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

                {/* Database Backup Button */}
                <div className="mt-6">
                  <h3 className="text-white font-medium mb-4">Database Backup</h3>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <div className="text-gray-300 font-medium">Backup Database</div>
                        <p className="text-sm text-gray-400">
                          {lastBackup 
                            ? `Last backup: ${new Date(lastBackup.timestamp).toLocaleDateString()} at ${new Date(lastBackup.timestamp).toLocaleTimeString()}`
                            : 'No backups found'
                          }
                        </p>
                      </div>
                      <button
                        onClick={handleBackupDatabase}
                        disabled={backupLoading}
                        className="bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 disabled:cursor-not-allowed text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <Download size={16} />
                        {backupLoading ? 'Creating Backup...' : 'Backup Now'}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500">
                      Creates a JSON backup of all assets in the Atlas_Library collection. Backup files are saved inside the Docker container at /app/backups/
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Close Button */}
            <div className="flex justify-end mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={() => setShowSettingsPanel(false)}
                className="bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
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
          <div className="bg-gray-800 border border-gray-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-xl font-semibold text-white">Edit Asset</h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingAsset(null);
                  setEditFormData({});
                  setNewTagInput('');
                }}
                className="text-gray-400 hover:text-white transition-colors"
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
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Asset Name
                    </label>
                    <input
                      type="text"
                      value={editFormData.name || ''}
                      onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                      placeholder="Enter asset name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
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
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-green-500"
                      placeholder="Default frame"
                      min="1001"
                      step="1"
                      title="Frame number to show when not hovering (e.g., 1001, 1015)"
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={editFormData.description || ''}
                    onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    placeholder="Enter asset description"
                    rows={3}
                  />
                </div>


                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Tags
                  </label>
                  
                  {/* Current Tags as Bubbles */}
                  {editFormData.tags && editFormData.tags.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 mb-3 p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                      <span className="text-xs text-gray-400 font-medium">Current Tags:</span>
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
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-green-400 focus:bg-gray-600 transition-all"
                    placeholder="Type a tag and press Enter to add..."
                  />
                  <p className="text-xs text-gray-400 mt-1">Press Enter to add tags. Click the X on existing tags to remove them.</p>
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
                    className="bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Texture Edit Modal */}
      {showTextureEditModal && editingTextureAsset && (
        <TextureEditAsset
          isOpen={showTextureEditModal}
          onClose={() => {
            setShowTextureEditModal(false);
            setEditingTextureAsset(null);
          }}
          asset={editingTextureAsset}
          onSave={(updatedAsset) => {
            // Update the asset in our current list to maintain cache-busting data
            setAssets(prevAssets => 
              prevAssets.map(asset => 
                (asset.id === updatedAsset.id || asset._key === updatedAsset._key)
                  ? { ...asset, ...updatedAsset }
                  : asset
              )
            );
            
            // Also reload assets to get any other changes
            loadAssets();
          }}
          apiEndpoint={settings.apiEndpoint}
        />
      )}

      {/* Upload Asset Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-lg w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-xl font-semibold text-white">Upload Asset</h2>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setNewUploadTagInput('');
                }}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Asset Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Asset Type <span className="text-red-400">*</span>
                </label>
                <select
                  value={uploadData.assetType}
                  onChange={(e) => {
                    const newAssetType = e.target.value;
                    // Reset all fields when switching between HDRI and Textures to prevent contamination
                    if (newAssetType === 'HDRI') {
                      setUploadData(prev => ({
                        name: prev.name, // Keep name
                        tags: prev.tags, // Keep tags
                        assetType: 'HDRI',
                        subcategory: 'Outdoor', // Default HDRI subcategory
                        filePath: '',
                        previewPath: '',
                        previewImagePath: '', // Clear preview image path when switching to HDRI
                        description: '',
                        // Clear all texture-specific fields
                        alphaSubcategory: '',
                        textureType: 'seamless',
                        textureSetPaths: {
                          baseColor: '',
                          metallic: '',
                          roughness: '',
                          normal: '',
                          opacity: '',
                          displacement: ''
                        }
                      }));
                    } else if (newAssetType === 'Textures') {
                      setUploadData(prev => ({
                        name: prev.name, // Keep name
                        tags: prev.tags, // Keep tags
                        assetType: 'Textures',
                        subcategory: 'Alpha', // Default texture subcategory
                        alphaSubcategory: 'General', // Default alpha subcategory
                        textureType: 'seamless', // Default texture type
                        filePath: '',
                        description: '',
                        previewImagePath: prev.previewImagePath || '', // Keep preview image path for textures
                        // Clear all HDRI-specific fields
                        previewPath: '',
                        // Initialize texture set paths
                        textureSetPaths: {
                          baseColor: '',
                          metallic: '',
                          roughness: '',
                          normal: '',
                          opacity: '',
                          displacement: ''
                        }
                      }));
                    }
                  }}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="Textures">🖼️ Textures</option>
                  <option value="HDRI">🌅 HDRI</option>
                </select>
              </div>

              {/* Texture Category Selection - Only show for Texture type */}
              {uploadData.assetType === 'Textures' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Category <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={uploadData.subcategory}
                    onChange={(e) => {
                      const newSubcategory = e.target.value;
                      // Reset relevant fields when switching texture subcategories
                      if (newSubcategory === 'Alpha') {
                        setUploadData(prev => ({
                          ...prev,
                          subcategory: 'Alpha',
                          alphaSubcategory: 'General', // Default alpha subcategory
                          filePath: prev.filePath || '', // Keep existing file path
                          tags: prev.tags || [], // Keep existing tags
                          // Clear texture set paths
                          textureSetPaths: {
                            baseColor: '',
                            metallic: '',
                            roughness: '',
                            normal: '',
                            opacity: '',
                            displacement: ''
                          }
                        }));
                      } else if (newSubcategory === 'Texture Sets') {
                        setUploadData(prev => ({
                          ...prev,
                          subcategory: 'Texture Sets',
                          alphaSubcategory: '', // Clear alpha subcategory
                          filePath: '', // Clear single file path for texture sets
                          tags: prev.tags || [], // Keep existing tags
                          textureSetPaths: {
                            baseColor: prev.textureSetPaths?.baseColor || '',
                            metallic: prev.textureSetPaths?.metallic || '',
                            roughness: prev.textureSetPaths?.roughness || '',
                            normal: prev.textureSetPaths?.normal || '',
                            opacity: prev.textureSetPaths?.opacity || '',
                            displacement: prev.textureSetPaths?.displacement || ''
                          }
                        }));
                      } else {
                        // Other texture types (Base Color, Roughness, etc.)
                        setUploadData(prev => ({
                          ...prev,
                          subcategory: newSubcategory,
                          tags: prev.tags || [], // Keep existing tags
                          alphaSubcategory: '', // Clear alpha subcategory
                          filePath: prev.filePath || '', // Keep existing file path
                          // Clear texture set paths
                          textureSetPaths: {
                            baseColor: '',
                            metallic: '',
                            roughness: '',
                            normal: '',
                            opacity: '',
                            displacement: ''
                          }
                        }));
                      }
                    }}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Alpha">🔳 Alpha</option>
                    <option value="Texture Sets">📦 Texture Sets</option>
                    <option value="Base Color">🎨 Base Color</option>
                    <option value="Roughness">⚪ Roughness</option>
                    <option value="Normal">🔵 Normal</option>
                    <option value="Metallic">⚫ Metallic</option>
                    <option value="Displacement">📐 Displacement</option>
                    <option value="Other">🌐 Other</option>
                  </select>
                </div>
              )}

              {/* Alpha Subcategory - Only show for Alpha textures */}
              {uploadData.assetType === 'Textures' && uploadData.subcategory === 'Alpha' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Alpha Type <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={uploadData.alphaSubcategory}
                    onChange={(e) => setUploadData(prev => ({ ...prev, alphaSubcategory: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="General">🔳 General</option>
                    <option value="Grunge">🟫 Grunge</option>
                    <option value="Scratches">⚡ Scratches</option>
                    <option value="Cracks">🔺 Cracks</option>
                    <option value="Rust">🟤 Rust</option>
                    <option value="Rain">💧 Rain</option>
                    <option value="Dust">🌫️ Dust</option>
                    <option value="Stains">🔴 Stains</option>
                    <option value="Smudge">👆 Smudge</option>
                  </select>
                </div>
              )}

              {/* HDRI Category Selection - Only show for HDRI type */}
              {uploadData.assetType === 'HDRI' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Category <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={uploadData.subcategory}
                    onChange={(e) => setUploadData(prev => ({ ...prev, subcategory: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Outdoor">🏞️ Outdoor</option>
                    <option value="Skies">☁️ Skies</option>
                    <option value="Indoor">🏠 Indoor</option>
                    <option value="Studio">📸 Studio</option>
                    <option value="Sunrise/Sunset">🌅 Sunrise/Sunset</option>
                    <option value="Night">🌙 Night</option>
                    <option value="Nature">🌳 Nature</option>
                    <option value="Urban">🏙️ Urban</option>
                    <option value="Other">🌐 Other</option>
                  </select>
                </div>
              )}

              {/* Asset Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Asset Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={uploadData.name}
                  onChange={(e) => setUploadData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter asset name..."
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Preview Image - For Textures only */}
              {uploadData.assetType === 'Textures' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Preview Image
                  </label>
                  <input
                    type="text"
                    value={uploadData.previewImagePath}
                    onChange={(e) => setUploadData(prev => ({ ...prev, previewImagePath: e.target.value }))}
                    placeholder="/net/general/your/path/preview.jpg"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-sm"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Optional preview image for texture badge display (supports: .jpg, .png, .tiff)<br/>
                    Will be copied to Preview folder and displayed first in texture cards
                  </p>
                </div>
              )}

              {/* Single File Path - For non-texture-set uploads */}
              {(uploadData.assetType === 'HDRI' || (uploadData.assetType === 'Textures' && uploadData.subcategory !== 'Texture Sets')) && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    {uploadData.assetType === 'HDRI' ? 'EXR File Path' : 'File Path'} <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={uploadData.filePath}
                    onChange={(e) => setUploadData(prev => ({ ...prev, filePath: e.target.value }))}
                    placeholder={uploadData.assetType === 'HDRI' ? "/net/general/your/path/environment.exr" : "/net/general/your/path/texture.jpg"}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-sm"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Full path to the {uploadData.assetType === 'HDRI' ? 'EXR/HDR' : 'texture'} file (supports: {uploadData.assetType === 'HDRI' ? '.exr, .hdr' : '.jpg, .png, .tiff, .exr'})<br/>
                    Available paths: /net/general/... or /net/library/library/... or /app/assets/...
                  </p>
                </div>
              )}

              {/* Texture Set File Paths - Only show for Texture Sets */}
              {uploadData.assetType === 'Textures' && uploadData.subcategory === 'Texture Sets' && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Texture Set Files</h3>
                  
                  <div className="grid grid-cols-1 gap-3">
                    {/* Base Color */}
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">
                        🎨 Base Color <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        value={uploadData.textureSetPaths.baseColor}
                        onChange={(e) => setUploadData(prev => ({
                          ...prev,
                          textureSetPaths: { ...prev.textureSetPaths, baseColor: e.target.value }
                        }))}
                        placeholder="/net/library/library/your/path/material_BaseColor.jpg"
                        className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
                      />
                    </div>

                    {/* Metallic */}
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">
                        ⚫ Metallic <span className="text-gray-500">(optional)</span>
                      </label>
                      <input
                        type="text"
                        value={uploadData.textureSetPaths.metallic}
                        onChange={(e) => setUploadData(prev => ({
                          ...prev,
                          textureSetPaths: { ...prev.textureSetPaths, metallic: e.target.value }
                        }))}
                        placeholder="/net/library/library/your/path/material_Metallic.jpg"
                        className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
                      />
                    </div>

                    {/* Roughness */}
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">
                        ⚪ Roughness <span className="text-gray-500">(optional)</span>
                      </label>
                      <input
                        type="text"
                        value={uploadData.textureSetPaths.roughness}
                        onChange={(e) => setUploadData(prev => ({
                          ...prev,
                          textureSetPaths: { ...prev.textureSetPaths, roughness: e.target.value }
                        }))}
                        placeholder="/net/library/library/your/path/material_Roughness.jpg"
                        className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
                      />
                    </div>

                    {/* Normal */}
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">
                        🔵 Normal <span className="text-gray-500">(optional)</span>
                      </label>
                      <input
                        type="text"
                        value={uploadData.textureSetPaths.normal}
                        onChange={(e) => setUploadData(prev => ({
                          ...prev,
                          textureSetPaths: { ...prev.textureSetPaths, normal: e.target.value }
                        }))}
                        placeholder="/net/library/library/your/path/material_Normal.jpg"
                        className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
                      />
                    </div>

                    {/* Opacity */}
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">
                        🔳 Opacity <span className="text-gray-500">(optional)</span>
                      </label>
                      <input
                        type="text"
                        value={uploadData.textureSetPaths.opacity}
                        onChange={(e) => setUploadData(prev => ({
                          ...prev,
                          textureSetPaths: { ...prev.textureSetPaths, opacity: e.target.value }
                        }))}
                        placeholder="/net/library/library/your/path/material_Opacity.jpg"
                        className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
                      />
                    </div>

                    {/* Displacement */}
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">
                        📐 Displacement <span className="text-gray-500">(optional)</span>
                      </label>
                      <input
                        type="text"
                        value={uploadData.textureSetPaths.displacement}
                        onChange={(e) => setUploadData(prev => ({
                          ...prev,
                          textureSetPaths: { ...prev.textureSetPaths, displacement: e.target.value }
                        }))}
                        placeholder="/net/library/library/your/path/material_Displacement.jpg"
                        className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
                      />
                    </div>
                  </div>

                  <p className="text-xs text-gray-400">
                    At least Base Color is required. All texture files will be organized in the material folder.<br/>
                    Supported formats: .jpg, .png, .tiff, .exr
                  </p>
                </div>
              )}

              {/* Preview JPEG/PNG - Only show for HDRI */}
              {uploadData.assetType === 'HDRI' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Preview JPEG/PNG <span className="text-gray-500">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={uploadData.previewPath}
                    onChange={(e) => setUploadData(prev => ({ ...prev, previewPath: e.target.value }))}
                    placeholder="/net/general/your/path/preview.jpg"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 font-mono text-sm"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Optional preview image for web display (supports: .jpg, .jpeg, .png)<br/>
                    If not provided, no thumbnail will be generated
                  </p>
                </div>
              )}


              {/* Texture Type Settings - Only show for Textures */}
              {uploadData.assetType === 'Textures' && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-300">Texture Properties</h3>
                  
                  {/* Seamless/UV Tile Toggle */}
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-300">Texture Type</label>
                      <p className="text-xs text-gray-400">Choose how this texture should be displayed</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="textureType"
                          value="seamless"
                          checked={uploadData.textureType === 'seamless'}
                          onChange={(e) => setUploadData(prev => ({ ...prev, textureType: e.target.value }))}
                          className="w-4 h-4 text-orange-500 bg-gray-700 border-gray-600 focus:ring-orange-500"
                        />
                        <span className="text-sm text-orange-300">Seamless</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="textureType"
                          value="uv_tile"
                          checked={uploadData.textureType === 'uv_tile'}
                          onChange={(e) => setUploadData(prev => ({ ...prev, textureType: e.target.value }))}
                          className="w-4 h-4 text-blue-500 bg-gray-700 border-gray-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-blue-300">UV Tile</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Tags Section */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tags
                </label>
                
                {/* Current Tags as Bubbles */}
                {uploadData.tags && uploadData.tags.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 mb-3 p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
                    <span className="text-xs text-gray-400 font-medium">Current Tags:</span>
                    {uploadData.tags.map((tag, index) => (
                      <div key={`${tag}-${index}`} className="flex items-center gap-1 bg-green-600/20 border border-green-500/60 rounded-full px-3 py-1 text-sm backdrop-blur-sm">
                        <span className="text-green-200 font-medium">{tag}</span>
                        <button
                          type="button"
                          onClick={() => removeUploadTag(tag)}
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
                  value={newUploadTagInput}
                  onChange={(e) => setNewUploadTagInput(e.target.value)}
                  onKeyDown={handleAddUploadTag}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-green-400 focus:bg-gray-600 transition-all"
                  placeholder="Type a tag and press Enter to add..."
                />
                <p className="text-xs text-gray-400 mt-1">Press Enter to add tags. Click the X on existing tags to remove them.</p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setNewUploadTagInput('');
                  }}
                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadAsset}
                  disabled={uploading || !uploadData.name.trim() || 
                    (uploadData.assetType === 'Textures' && uploadData.subcategory === 'Texture Sets' 
                      ? !uploadData.textureSetPaths.baseColor.trim() 
                      : false)}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center gap-2"
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
          <div className="bg-gray-800 border border-gray-700 rounded-lg w-[75vw] max-h-[80vh] overflow-auto transform transition-all duration-300 ease-in-out scale-100">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div>
                <h2 className="text-xl font-semibold text-white">{previewAsset.name}</h2>
                <div className="flex items-center gap-4 mt-2">
                  {/* Hierarchy Path */}
                  <div className="flex items-center gap-2 text-sm">
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded">{previewAsset.metadata?.dimension || '3D'}</span>
                    <span className="text-gray-400">→</span>
                    <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded">{previewAsset.metadata?.asset_type || previewAsset.category}</span>
                    <span className="text-gray-400">→</span>
                    <span className="px-2 py-1 bg-green-600/20 text-green-300 rounded">{previewAsset.metadata?.subcategory || 'General'}</span>
                    {(previewAsset.branded || previewAsset.metadata?.branded || previewAsset.metadata?.export_metadata?.branded) && (
                      <>
                        <span className="text-gray-400">→</span>
                        <span className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded font-bold">⚠ BRANDED</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              {/* Custom HDRI Preview Modal Layout */}
              {(previewAsset.asset_type === 'HDRIs' || previewAsset.category === 'HDRIs' || previewAsset.asset_type === 'HDRI') ? (
                <div className="space-y-6">
                  {/* Full HDRI Thumbnail - Centered and Uncropped */}
                  <div className="flex justify-center">
                    <div className="bg-gray-700 rounded-lg overflow-hidden relative" style={{ maxWidth: '100%', maxHeight: '60vh' }}>
                      <SequenceThumbnail
                        assetId={previewAsset.id || previewAsset._key}
                        assetName={formatAssetName(previewAsset)}
                        thumbnailFrame={previewAsset.thumbnail_frame}
                        fallbackIcon="🌅"
                        className="w-auto h-auto max-w-full max-h-[60vh] object-contain"
                      />
                    </div>
                  </div>
                  
                  {/* HDRI Information Below Image */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">HDRI Environment Information</h3>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Resolution:</span>
                          <div className="text-cyan-300 font-medium">{previewAsset.metadata?.resolution || previewAsset.metadata?.dimensions || 'Unknown'}</div>
                        </div>
                        <div>
                          <span className="text-gray-400">Format:</span>
                          <div className="text-purple-300 font-medium">
                            {previewAsset.paths?.template_file 
                              ? previewAsset.paths.template_file.split('.').pop()?.toUpperCase() || 'Unknown'
                              : previewAsset.metadata?.file_format?.toUpperCase() || 'EXR'}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-400">Size:</span>
                          <div className="text-white">
                            {(() => {
                              const totalBytes = previewAsset.file_sizes?.estimated_total_size || 0;
                              if (totalBytes === 0) return 'Calculating...';
                              if (totalBytes < 1024 * 1024) return `${Math.round(totalBytes / 1024)} KB`;
                              else if (totalBytes < 1024 * 1024 * 1024) return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                              else return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                            })()}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-400">Environment:</span>
                          <div className="text-green-400 font-medium">{previewAsset.hierarchy?.subcategory || previewAsset.metadata?.subcategory || 'Studio'}</div>
                        </div>
                        <div>
                          <span className="text-gray-400">ID:</span>
                          <div className="text-white font-mono text-xs">{previewAsset.id}</div>
                        </div>
                        <div>
                          <span className="text-gray-400">Created:</span>
                          <div className="text-white">{previewAsset.created_at ? new Date(previewAsset.created_at).toLocaleDateString() : 'Unknown'}</div>
                        </div>
                        {previewAsset.artist && (
                          <div>
                            <span className="text-gray-400">Artist:</span>
                            <div className="text-blue-300 font-medium">{previewAsset.artist}</div>
                          </div>
                        )}
                        {(previewAsset.branded || previewAsset.metadata?.branded) && (
                          <div>
                            <span className="text-gray-400">Status:</span>
                            <div className="text-yellow-300 font-bold">⚠ BRANDED</div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Description if available */}
                    {previewAsset.description && (
                      <div>
                        <h3 className="text-lg font-medium text-white mb-2">Description</h3>
                        <div className="bg-gray-700/50 rounded-lg p-3">
                          <p className="text-white text-sm leading-relaxed">{previewAsset.description}</p>
                        </div>
                      </div>
                    )}
                    
                    {/* Action Buttons for HDRI */}
                    <div className="space-y-3 pt-4">
                      <button 
                        onClick={async () => {
                          try {
                            // Get the HDRI file path from the asset's copied files (should be the .exr/.hdr file)
                            const hdriFiles = previewAsset.paths?.copied_files || previewAsset.metadata?.paths?.copied_files || [];
                            if (hdriFiles.length === 0) {
                              alert('❌ HDRI file path not found in asset data');
                              return;
                            }
                            
                            // Get the first (and should be only) HDRI file path
                            let hdriPath = hdriFiles[0];
                            
                            // Convert from container path to network path if needed
                            if (hdriPath.startsWith('/app/assets/')) {
                              hdriPath = hdriPath.replace('/app/assets/', '/net/library/atlaslib/');
                            }
                            
                            // Copy to clipboard
                            await navigator.clipboard.writeText(hdriPath);
                            
                            // Show success message
                            let message = `✅ HDRI file path copied to clipboard!\n\n`;
                            message += `🌅 Asset: ${previewAsset.name}\n`;
                            message += `📁 HDRI File: ${hdriPath}`;
                            
                            alert(message);
                            console.log('📋 HDRI file path copied to clipboard:', hdriPath);
                            
                          } catch (error) {
                            console.error('Error copying HDRI path:', error);
                            alert('❌ Failed to copy HDRI path. Please check console for details.');
                          }
                        }}
                        className="w-full bg-orange-600 hover:bg-orange-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                      >
                        <Copy size={20} />
                        Copy HDRI Path
                      </button>
                      
                      <button 
                        onClick={async () => {
                          try {
                            // Get the asset folder path
                            let folderPath = previewAsset.paths?.folder_path || previewAsset.paths?.asset_folder || previewAsset.folder_path;
                            
                            if (!folderPath) {
                              alert('❌ Asset folder path not found in asset data');
                              return;
                            }
                            
                            // Convert from container path to network path if needed
                            if (folderPath.startsWith('/app/assets/')) {
                              folderPath = folderPath.replace('/app/assets/', '/net/library/atlaslib/');
                            }
                            
                            // Copy to clipboard
                            await navigator.clipboard.writeText(folderPath);
                            
                            // Show success message
                            let message = `✅ Asset folder path copied to clipboard!\n\n`;
                            message += `🌅 Asset: ${previewAsset.name}\n`;
                            message += `📂 Folder: ${folderPath}`;
                            
                            alert(message);
                            console.log('📋 Asset folder path copied to clipboard:', folderPath);
                            
                          } catch (error) {
                            console.error('Error copying asset folder path:', error);
                            alert('❌ Failed to copy asset folder path. Please check console for details.');
                          }
                        }}
                        className="w-full bg-gray-600 hover:bg-gray-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                      >
                        <Copy size={20} />
                        Copy Asset Folder Path
                      </button>
                    </div>
                  </div>
                </div>
              ) : (previewAsset.asset_type === 'Assets' || previewAsset.category === 'Assets' || previewAsset.metadata?.asset_type === 'Assets') ? (
                /* Houdini Assets Preview Layout - Side by side with full aspect ratio */
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Large Preview Image with Interactive Sequence - Full aspect ratio */}
                  <div className="bg-gray-700 rounded-lg overflow-hidden relative flex items-center justify-center" style={{ minHeight: '400px' }}>
                    <SequenceThumbnail
                      assetId={previewAsset.id || previewAsset._key}
                      assetName={formatAssetName(previewAsset)}
                      thumbnailFrame={previewAsset.thumbnail_frame}
                      fallbackIcon="🎨"
                      className="w-full h-full object-contain"
                    />
                  </div>

                  {/* Houdini Asset Details */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">Asset Information</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Asset Name:</span>
                          <span className="text-white font-medium text-lg">{formatAssetNameJSX(previewAsset)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">ID:</span>
                          <span className="text-white font-mono">{previewAsset.id}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Category:</span>
                          <span className="text-white">{previewAsset.category}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Size:</span>
                          <span className="text-white">
                            {(() => {
                              const totalBytes = previewAsset.file_sizes?.estimated_total_size || 0;
                              if (totalBytes === 0) return 'Calculating...';
                              if (totalBytes < 1024 * 1024) return `${Math.round(totalBytes / 1024)} KB`;
                              else if (totalBytes < 1024 * 1024 * 1024) return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                              else return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                            })()}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Description for Houdini Assets */}
                    {previewAsset.description && (
                      <div>
                        <h3 className="text-lg font-medium text-white mb-2">Description</h3>
                        <div className="bg-gray-700/50 rounded-lg p-3">
                          <p className="text-white text-sm leading-relaxed">{previewAsset.description}</p>
                        </div>
                      </div>
                    )}

                    {/* Technical Details for Houdini Assets */}
                    {previewAsset.metadata && (
                      <div>
                        <h3 className="text-lg font-medium text-white mb-2">Technical Details</h3>
                        <div className="space-y-1 text-sm">
                          {(previewAsset.metadata.hierarchy?.render_engine || previewAsset.metadata.render_engine) && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Render Engine:</span>
                              <span className="text-white">{previewAsset.metadata.hierarchy?.render_engine || previewAsset.metadata.render_engine}</span>
                            </div>
                          )}
                          {previewAsset.artist && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Artist:</span>
                              <span className="text-white">{previewAsset.artist}</span>
                            </div>
                          )}
                          {previewAsset.metadata.houdini_version && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Houdini Version:</span>
                              <span className="text-white">{previewAsset.metadata.houdini_version}</span>
                            </div>
                          )}
                          {previewAsset.metadata.export_time && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Export Time:</span>
                              <span className="text-white">{new Date(previewAsset.metadata.export_time).toLocaleString()}</span>
                            </div>
                          )}
                          {previewAsset.created_at && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Created:</span>
                              <span className="text-white">{new Date(previewAsset.created_at).toLocaleDateString()}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Action Buttons for Houdini Assets */}
                    <div className="space-y-3 pt-4">
                      <button 
                        onClick={async () => {
                          try {
                            // Copy asset ID directly to clipboard
                            await navigator.clipboard.writeText(previewAsset.id);
                            
                            // Show success message
                            alert(`✅ Asset ID copied to clipboard!\n\nAsset ID: ${previewAsset.id}`);
                            console.log('📋 Asset ID copied to clipboard:', previewAsset.id);
                            
                          } catch (clipboardError) {
                            console.log('Could not copy to clipboard:', clipboardError);
                            alert(`❌ Could not copy to clipboard, but here's the Asset ID:\n\n${previewAsset.id}`);
                          }
                        }}
                        className="w-full bg-orange-600 hover:bg-orange-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                      >
                        <Copy size={20} />
                        Copy Asset ID
                      </button>
                      
                      <button 
                        onClick={async () => {
                          try {
                            console.log('Getting folder path for asset:', previewAsset.id);
                            
                            const response = await fetch(`${config.backendUrl}/api/v1/assets/${previewAsset.id}/copy-folder-path`, {
                              method: 'POST'
                            });
                            
                            if (response.ok) {
                              const result = await response.json();
                              console.log('Folder path response:', result);
                              
                              // Copy to clipboard
                              try {
                                await navigator.clipboard.writeText(result.folder_path);
                                
                                // Show success message
                                let message = `✅ Folder path copied to clipboard!\n\n`;
                                message += `🎨 Asset: ${result.asset_name}\n`;
                                message += `📂 Path: ${result.folder_path}\n`;
                                message += `📋 Status: ${result.folder_exists ? 'Folder exists' : 'Folder may not exist'}`;
                                
                                alert(message);
                                console.log('📋 Folder path copied to clipboard:', result.folder_path);
                                
                              } catch (clipboardError) {
                                console.log('Could not copy to clipboard:', clipboardError);
                                alert(`❌ Could not copy to clipboard, but here's the path:\n\n${result.folder_path}`);
                              }
                            } else {
                              const error = await response.json();
                              console.log('Failed to get folder path:', error);
                              alert(`❌ Failed to get folder path: ${error.detail || 'Unknown error'}\n\nAsset ID: ${previewAsset.id}`);
                            }
                          } catch (error) {
                            console.error('Error getting folder path:', error);
                            alert('❌ Failed to get folder path. Please check console for details.');
                          }
                        }}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                      >
                        <Copy size={20} />
                        Copy Folder Path
                      </button>
                      
                      <button
                        onClick={async () => {
                          try {
                            const response = await fetch(`${config.backendUrl}/api/v1/assets/${previewAsset.id}/open-folder`, {
                              method: 'POST'
                            });
                            
                            const result = await response.json();
                            
                            if (response.ok) {
                              alert(`✅ ${result.message || 'Folder opened successfully!'}`);
                            } else {
                              alert(`❌ ${result.detail || 'Failed to open folder'}`);
                            }
                          } catch (error) {
                            console.error('Error opening folder:', error);
                            alert('❌ Failed to open folder. Please check console for details.');
                          }
                        }}
                        className="w-full bg-gray-600 hover:bg-gray-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                      >
                        <FolderOpen size={20} />
                        Open in Explorer
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* Regular Preview Layout for Texture assets */
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Large Preview Image with Interactive Sequence - Texture specific or regular */}
                  <div className="aspect-square bg-gray-700 rounded-lg overflow-hidden relative">
                    {(previewAsset.asset_type === 'Textures' || previewAsset.category === 'Textures') ? (
                      <TextureModalPreview key={`modal-${previewAsset.id || previewAsset._key}`} asset={previewAsset} />
                    ) : (
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
                    )}
                  </div>

                {/* Asset Details */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white mb-2">Asset Information</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Asset Name:</span>
                        <span className="text-white font-medium text-lg">{formatAssetNameJSX(previewAsset)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">ID:</span>
                        <span className="text-white font-mono">{previewAsset.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Category:</span>
                        <span className="text-white">{previewAsset.category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Size:</span>
                        <span className="text-white">
                          {(() => {
                            const totalBytes = previewAsset.file_sizes?.estimated_total_size || 0;
                            if (totalBytes === 0) return 'Calculating...';
                            if (totalBytes < 1024 * 1024) return `${Math.round(totalBytes / 1024)} KB`;
                            else if (totalBytes < 1024 * 1024 * 1024) return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                            else return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                          })()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Description for 3D Assets */}
                  {!(previewAsset.asset_type === 'Textures' || previewAsset.category === 'Textures') && previewAsset.description && (
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">Description</h3>
                      <div className="bg-gray-700/50 rounded-lg p-3">
                        <p className="text-white text-sm leading-relaxed">{previewAsset.description}</p>
                      </div>
                    </div>
                  )}

                  {/* Technical Details - Different for Textures vs 3D Assets */}
                  {(previewAsset.asset_type === 'Textures' || previewAsset.category === 'Textures') ? (
                    /* Texture-specific technical details */
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">Texture Details</h3>
                      <div className="space-y-1 text-sm">
                        {(previewAsset.metadata?.resolution || previewAsset.resolution) && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Resolution:</span>
                            <span className="text-white">{previewAsset.metadata?.resolution || previewAsset.resolution}</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-400">Format:</span>
                          <span className="text-white">{(() => {
                            // Check for format in metadata first
                            if (previewAsset.metadata?.file_format) {
                              return previewAsset.metadata.file_format.toUpperCase();
                            }
                            
                            // Check preview files for extensions
                            if (previewAsset.paths?.preview_files && previewAsset.paths.preview_files.length > 0) {
                              // Get all unique extensions from preview files
                              const extensions = new Set();
                              previewAsset.paths.preview_files.forEach(file => {
                                const extension = file.split('.').pop()?.toLowerCase();
                                if (extension) {
                                  extensions.add(extension.toUpperCase());
                                }
                              });
                              
                              // If multiple different formats, return "Mixed"
                              if (extensions.size > 1) {
                                return 'Mixed';
                              }
                              
                              // If only one format, return it
                              if (extensions.size === 1) {
                                return Array.from(extensions)[0];
                              }
                            }
                            
                            // Fallback to template file
                            if (previewAsset.paths?.template_file) {
                              return previewAsset.paths.template_file.split('.').pop()?.toUpperCase() || 'Unknown';
                            }
                            
                            return 'Unknown';
                          })()}</span>
                        </div>
                        {previewAsset.created_at && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Created:</span>
                            <span className="text-white">{new Date(previewAsset.created_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    /* 3D Asset-specific technical details */
                    previewAsset.metadata && (
                      <div>
                        <h3 className="text-lg font-medium text-white mb-2">Technical Details</h3>
                        <div className="space-y-1 text-sm">
                          {(previewAsset.metadata.hierarchy?.render_engine || previewAsset.metadata.render_engine) && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Render Engine:</span>
                              <span className="text-white">{previewAsset.metadata.hierarchy?.render_engine || previewAsset.metadata.render_engine}</span>
                            </div>
                          )}
                          {previewAsset.artist && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Artist:</span>
                              <span className="text-white">{previewAsset.artist}</span>
                            </div>
                          )}
                          {previewAsset.metadata.houdini_version && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Houdini Version:</span>
                              <span className="text-white">{previewAsset.metadata.houdini_version}</span>
                            </div>
                          )}
                          {previewAsset.metadata.export_time && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Export Time:</span>
                              <span className="text-white">{new Date(previewAsset.metadata.export_time).toLocaleString()}</span>
                            </div>
                          )}
                          {previewAsset.created_at && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Created:</span>
                              <span className="text-white">{new Date(previewAsset.created_at).toLocaleDateString()}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  )}

                  {/* Action Buttons */}
                  <div className="space-y-3 pt-4">
                    {/* Main Action Buttons - Different for textures vs other assets */}
                    {(previewAsset.asset_type === 'Textures' || previewAsset.category === 'Textures') ? (
                      /* Texture assets - Individual texture file copy buttons + Copy Folder Path */
                      <>
                        {/* Individual Texture Copy Buttons */}
                        <TextureFileCopyButtons asset={previewAsset} />
                        
                        {/* Copy Folder Path */}
                        <button 
                          onClick={async () => {
                            try {
                              console.log('Getting folder path for asset:', previewAsset.id);
                              
                              const response = await fetch(`${config.backendUrl}/api/v1/assets/${previewAsset.id}/copy-folder-path`, {
                                method: 'POST'
                              });
                              
                              if (response.ok) {
                                const result = await response.json();
                                console.log('Folder path response:', result);
                                
                                // Copy to clipboard
                                try {
                                  await navigator.clipboard.writeText(result.folder_path);
                                  
                                  // Show success message
                                  let message = `✅ Folder path copied to clipboard!\n\n`;
                                  message += `📁 Asset: ${result.asset_name}\n`;
                                  message += `📂 Path: ${result.folder_path}\n`;
                                  message += `📋 Status: ${result.folder_exists ? 'Folder exists' : 'Folder may not exist'}`;
                                  
                                  alert(message);
                                  console.log('📋 Folder path copied to clipboard:', result.folder_path);
                                  
                                } catch (clipboardError) {
                                  console.log('Could not copy to clipboard:', clipboardError);
                                  alert(`❌ Could not copy to clipboard, but here's the path:\n\n${result.folder_path}`);
                                }
                              } else {
                                const error = await response.json();
                                console.log('Failed to get folder path:', error);
                                alert(`❌ Failed to get folder path: ${error.detail || 'Unknown error'}\n\nAsset ID: ${previewAsset.id}`);
                              }
                            } catch (error) {
                              console.error('Error getting folder path:', error);
                              alert('❌ Failed to get folder path. Please check console for details.');
                            }
                          }}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                        >
                          <Copy size={20} />
                          Copy Folder Path
                        </button>
                      </>
                    ) : (
                      /* Non-texture assets - Show both buttons */
                      <>
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
                              console.log('Getting folder path for asset:', previewAsset.id);
                              
                              const response = await fetch(`${config.backendUrl}/api/v1/assets/${previewAsset.id}/copy-folder-path`, {
                                method: 'POST'
                              });
                              
                              if (response.ok) {
                                const result = await response.json();
                                console.log('Folder path response:', result);
                                
                                // Copy to clipboard
                                try {
                                  await navigator.clipboard.writeText(result.folder_path);
                                  
                                  // Show success message
                                  let message = `✅ Folder path copied to clipboard!\n\n`;
                                  message += `📁 Asset: ${result.asset_name}\n`;
                                  message += `📂 Path: ${result.folder_path}\n`;
                                  message += `📋 Status: ${result.folder_exists ? 'Folder exists' : 'Folder may not exist'}`;
                                  
                                  alert(message);
                                  console.log('📋 Folder path copied to clipboard:', result.folder_path);
                                  
                                } catch (clipboardError) {
                                  console.log('Could not copy to clipboard:', clipboardError);
                                  alert(`❌ Could not copy to clipboard, but here's the path:\n\n${result.folder_path}`);
                                }
                              } else {
                                const error = await response.json();
                                console.log('Failed to get folder path:', error);
                                alert(`❌ Failed to get folder path: ${error.detail || 'Unknown error'}\n\nAsset ID: ${previewAsset.id}`);
                              }
                            } catch (error) {
                              console.error('Error getting folder path:', error);
                              alert('❌ Failed to get folder path. Please check console for details.');
                            }
                          }}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-3 font-medium"
                        >
                          <Copy size={20} />
                          Copy Folder Path
                        </button>
                        
                        {/* Smaller ID Copy Buttons - Only for non-texture assets */}
                        <div className="flex gap-2 pt-2">
                          <button 
                            onClick={() => copyVersionId(previewAsset)}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-3 rounded-md transition-colors flex items-center justify-center gap-2 text-sm"
                          >
                            <Copy size={14} />
                            Copy Version ID
                          </button>
                          <button 
                            onClick={() => copyVariantId(previewAsset)}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-3 rounded-md transition-colors flex items-center justify-center gap-2 text-sm"
                          >
                            <Copy size={14} />
                            Copy Variant ID
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
              )}
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
              <p className="text-gray-400 text-lg">Select the type of assets you want to browse</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {dimensions.map(dimension => (
                <button
                  key={dimension.id}
                  onClick={() => dimension.id === '3D' && handleDimensionSelect(dimension.id)}
                  className={`group relative overflow-hidden bg-gray-800 border border-gray-700 rounded-xl p-8 transition-all duration-300 ${
                    dimension.id === '3D' 
                      ? 'hover:bg-gray-750 hover:border-blue-500 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-105 cursor-pointer' 
                      : 'cursor-not-allowed opacity-75'
                  }`}
                  disabled={dimension.id === '2D'}
                >
                  {/* Coming Soon Banner for 2D */}
                  {dimension.id === '2D' && (
                    <div className="absolute inset-0 flex items-center justify-center z-10">
                      <div className="bg-gradient-to-r from-gray-800 to-gray-600 text-white font-bold text-2xl py-3 px-8 rounded-full shadow-2xl transform rotate-[-15deg] animate-[pulse_4s_ease-in-out_infinite]">
                        Coming Soon
                      </div>
                    </div>
                  )}
                  
                  <div className={`text-8xl mb-6 transition-transform duration-300 ${dimension.id === '3D' ? 'group-hover:scale-110' : ''} ${dimension.id === '2D' ? 'blur-[2px]' : ''}`}>
                    {dimension.icon}
                  </div>
                  <h3 className={`text-3xl font-bold text-white mb-3 transition-colors ${dimension.id === '3D' ? 'group-hover:text-blue-400' : ''} ${dimension.id === '2D' ? 'blur-[2px]' : ''}`}>
                    {dimension.name}
                  </h3>
                  <p className={`text-gray-400 transition-colors ${dimension.id === '3D' ? 'group-hover:text-gray-300' : ''} ${dimension.id === '2D' ? 'blur-[2px]' : ''}`}>
                    {dimension.description}
                  </p>
                  <div className={`mt-6 inline-flex items-center gap-2 text-blue-400 transition-colors ${dimension.id === '3D' ? 'group-hover:text-blue-300' : ''} ${dimension.id === '2D' ? 'blur-[2px]' : ''}`}>
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
                className="group bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-blue-500 text-white px-6 py-2 rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-105"
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
              <p className="text-gray-400 text-lg">Choose a category to browse {selectedDimension} assets</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categories[selectedDimension]?.map(category => {
                const isComingSoon = category.id === 'Materials' || category.id === 'HDAs';
                return (
                  <button
                    key={category.id}
                    onClick={() => !isComingSoon && handleCategorySelect(category.id)}
                    className={`group relative overflow-hidden bg-gray-800 border border-gray-700 rounded-xl p-6 transition-all duration-300 ${
                      !isComingSoon 
                        ? 'hover:bg-gray-750 hover:border-blue-500 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-105 cursor-pointer' 
                        : 'cursor-not-allowed opacity-75'
                    }`}
                    disabled={isComingSoon}
                  >
                    {/* Coming Soon Banner for Materials and HDAs */}
                    {isComingSoon && (
                      <div className="absolute inset-0 flex items-center justify-center z-10">
                        <div className="bg-gradient-to-r from-gray-800 to-gray-600 text-white font-bold text-xl py-2 px-6 rounded-full shadow-2xl transform rotate-[-15deg] animate-[pulse_4s_ease-in-out_infinite]">
                          Coming Soon
                        </div>
                      </div>
                    )}
                    
                    <div className={`text-6xl mb-4 transition-transform duration-300 ${!isComingSoon ? 'group-hover:scale-110' : ''} ${isComingSoon ? 'blur-[2px]' : ''}`}>
                      {category.icon}
                    </div>
                    <h3 className={`text-2xl font-bold text-white mb-2 transition-colors ${!isComingSoon ? 'group-hover:text-blue-400' : ''} ${isComingSoon ? 'blur-[2px]' : ''}`}>
                      {category.name}
                    </h3>
                    <p className={`text-gray-400 transition-colors text-sm ${!isComingSoon ? 'group-hover:text-gray-300' : ''} ${isComingSoon ? 'blur-[2px]' : ''}`}>
                      {category.description}
                    </p>
                    <div className={`mt-4 inline-flex items-center gap-2 text-blue-400 transition-colors ${!isComingSoon ? 'group-hover:text-blue-300' : ''} ${isComingSoon ? 'blur-[2px]' : ''}`}>
                      <Folder size={16} />
                      <span>Browse</span>
                    </div>
                  </button>
                );
              })}
            </div>
            
            {/* Jump To Library Button */}
            <div className="flex justify-center mt-12">
              <button
                onClick={handleJumpToLibrary}
                className="group bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-blue-500 text-white px-6 py-2 rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-105"
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
              <p className="text-gray-400 text-lg">Choose a subcategory from {selectedCategory}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {subcategories[selectedCategory]?.map(subcategory => (
                <button
                  key={subcategory.id}
                  onClick={() => handleSubcategorySelect(subcategory.name)}
                  className="group bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-blue-500 rounded-xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-105"
                >
                  <div className="text-5xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    {subcategory.icon}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                    {subcategory.name}
                  </h3>
                  <p className="text-gray-400 group-hover:text-gray-300 transition-colors text-sm">
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
                className="group bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-blue-500 text-white px-6 py-2 rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-105"
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
                <div className="text-gray-400 text-lg">Loading assets...</div>
              </div>
            ) : (
              <>
                <div className="bg-gray-700 rounded-xl p-4 mb-6 border border-gray-600/30 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-8 text-sm text-gray-300">
                      <span className="font-medium text-gray-200">{filteredAssetsState.length} assets found</span>
                      <span>Path: <span className="text-gray-400 font-mono text-xs">/net/library/atlaslib/{selectedDimension}/{selectedCategory}{selectedSubcategory ? `/${selectedSubcategory}` : ''}</span></span>
                      <span>Database: <span className="text-emerald-400 font-medium">{dbStatus.database_type || 'JSON'}</span></span>
                      {(selectedFilters.creator !== 'all' || selectedFilters.showVariants || selectedFilters.showVersions || !selectedFilters.showBranded) && (
                        <span className="text-cyan-400 font-medium">Filtered</span>
                      )}
                    </div>
                    
                    {/* Badge Size Slider */}
                    <div className="flex items-center gap-3 text-sm text-gray-300">
                      <span className="font-medium">Badge Size:</span>
                      <div className="flex items-center gap-3 bg-gray-600/30 px-3 py-2 rounded-lg border border-gray-500/20">
                        <span className="text-xs font-medium text-gray-400">S</span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={badgeSize}
                          onChange={(e) => setBadgeSize(Number(e.target.value))}
                          className="w-24 h-1.5 rounded-full appearance-none cursor-pointer"
                          style={{
                            background: `linear-gradient(to right, #06b6d4 0%, #06b6d4 ${badgeSize}%, #475569 ${badgeSize}%, #475569 100%)`
                          }}
                        />
                        <style>{`
                          input[type="range"]::-webkit-slider-thumb {
                            appearance: none;
                            width: 18px;
                            height: 18px;
                            border-radius: 50%;
                            background: linear-gradient(135deg, #06b6d4, #0891b2);
                            cursor: pointer;
                            box-shadow: 0 4px 8px rgba(6, 182, 212, 0.3);
                            border: 2px solid rgba(255,255,255,0.2);
                          }
                          input[type="range"]::-moz-range-thumb {
                            width: 18px;
                            height: 18px;
                            border-radius: 50%;
                            background: linear-gradient(135deg, #06b6d4, #0891b2);
                            cursor: pointer;
                            border: 2px solid rgba(255,255,255,0.2);
                            box-shadow: 0 4px 8px rgba(6, 182, 212, 0.3);
                          }
                        `}</style>
                        <span className="text-xs font-medium text-gray-400">L</span>
                      </div>
                    </div>
                  </div>
                </div>

                {viewMode === 'grid' ? (
                  <div className={getGridClasses()}>
                    {displayedAssets.map((asset, index) => {
                      // Debug duplicate keys
                      if ((asset.id || asset._key) === '5480C2A7D0') {
                        console.log(`🔍 GRID RENDER: Asset 5480C2A7D0 at index ${index}`);
                      }
                      const CardComponent = getAssetCardComponent(asset);
                      return (
                        <CardComponent 
                          key={`grid-${asset.id || asset._key}`} 
                          asset={asset} 
                          formatAssetName={formatAssetName}
                          formatAssetNameJSX={formatAssetNameJSX}
                          openPreview={openPreview}
                          onEditAsset={handleEditAsset}
                          onDeleteAsset={handleDeleteAsset}
                          onCopyAsset={copyAssetToClipboard}
                        />
                      );
                    })}
                  </div>
                ) : (
                  <div className="bg-gray-800 rounded-lg overflow-hidden">
                    <div className="grid grid-cols-12 gap-4 p-4 border-b border-gray-700 text-sm font-medium text-gray-400">
                      <div className="col-span-4">Name</div>
                      <div className="col-span-2">Category</div>
                      <div className="col-span-2">Artist</div>
                      <div className="col-span-2">Size</div>
                      <div className="col-span-2">Actions</div>
                    </div>
                    {displayedAssets.map((asset, index) => {
                      // Debug duplicate keys
                      if ((asset.id || asset._key) === '5480C2A7D0') {
                        console.log(`🔍 LIST RENDER: Asset 5480C2A7D0 at index ${index}`);
                      }
                      return (
                        <div key={`list-${asset.id || asset._key}`} className={`grid grid-cols-12 gap-4 p-4 border-b transition-colors ${
                        asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded
                          ? 'border-yellow-600/30 bg-yellow-600/5 hover:bg-yellow-600/8'
                          : 'border-gray-700 hover:bg-gray-750'
                      }`}>
                        <div className="col-span-4">
                          <div className="flex items-center gap-2">
                            <div className="font-medium text-white">{formatAssetName(asset)}</div>
                            {(asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded) && (
                              <span className="text-yellow-500 text-sm font-bold">⚠</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-400 truncate">{asset.description || 'No description'}</div>
                        </div>
                        <div className="col-span-2 text-blue-400">{asset.category}</div>
                        <div className="col-span-2 text-green-400">{asset.artist || 'Unknown'}</div>
                        <div className="col-span-2 text-gray-300">
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
                      );
                    })}
                  </div>
                )}

                {/* Pagination info and load more indicator */}
                {displayedAssets.length > 0 && (
                  <div className="mt-6 flex flex-col items-center space-y-4">
                    <div className="text-gray-400 text-sm">
                      Showing {displayedAssets.length} of {filteredAssetsState.length} assets
                    </div>
                    {isLoadingMore && (
                      <div className="flex items-center space-x-2 text-gray-400">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Loading more assets...</span>
                      </div>
                    )}
                    {displayedAssets.length < filteredAssetsState.length && !isLoadingMore && (
                      <button
                        onClick={loadMoreAssets}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                      >
                        Load More Assets
                      </button>
                    )}
                  </div>
                )}

                {filteredAssetsState.length === 0 && !loading && (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-lg mb-2">No assets found</div>
                    <div className="text-gray-500">
                      Try adjusting your filters or sync the database
                    </div>
                  </div>
                )}

                <div className="mt-8 pt-4 border-t border-gray-700">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm text-gray-400">
                    <div>
                      <span className="block">Total Files:</span>
                      <span className="text-white font-medium">{filteredAssetsState.length}</span>
                    </div>
                    <div>
                      <span className="block">Total Size:</span>
                      <span className="text-white font-medium">
                        {Math.round(filteredAssetsState.reduce((sum, asset) => {
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