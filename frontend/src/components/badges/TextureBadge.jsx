import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, MoreVertical, Edit, Copy, Eye, Trash2 } from 'lucide-react';

const TextureBadge = ({ asset, formatAssetNameJSX, onEditAsset, onPreviewAsset, onCopyAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageList, setImageList] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  const handleBannerHover = () => !isClickedOpen && setIsExpanded(true);
  const handleBannerLeave = () => !isClickedOpen && setIsExpanded(false);
  const handleBannerClick = () => {
    setIsClickedOpen(!isClickedOpen);
    setIsExpanded(!isClickedOpen);
  };

  // Helper functions
  const getResolution = () => asset.metadata?.resolution || asset.metadata?.dimensions || 'Unknown';
  
  const getFormat = () => {
    if (asset.metadata?.file_format) return asset.metadata.file_format.toUpperCase();
    
    if (asset.paths?.thumbnails?.length > 0) {
      const extensions = new Set(
        asset.paths.thumbnails
          .map(file => file.split('.').pop()?.toUpperCase())
          .filter(Boolean)
      );
      
      if (extensions.size > 1) return 'Mixed';
      if (extensions.size === 1) return Array.from(extensions)[0];
    }
    
    return asset.paths?.template_file?.split('.').pop()?.toUpperCase() || 'Unknown';
  };

  const getFileSize = () => {
    const totalBytes = asset.file_sizes?.estimated_total_size || 0;
    if (totalBytes === 0) return <span className="text-gray-500">Calc...</span>;
    
    const mb = 1024 * 1024;
    const gb = mb * 1024;
    
    if (totalBytes < mb) return `${Math.round(totalBytes / 1024)} KB`;
    if (totalBytes < gb) return `${(totalBytes / mb).toFixed(1)} MB`;
    return `${(totalBytes / gb).toFixed(2)} GB`;
  };

  const getUVLayout = () => {
    const textureType = asset.texture_type || asset.metadata?.texture_type;
    if (textureType === 'seamless') return 'Seamless';
    if (textureType === 'uv_tile') return 'UV Tile';
    
    const seamless = asset.seamless || asset.metadata?.seamless || asset.metadata?.tiling;
    const uvTile = asset.uv_tile || asset.metadata?.uv_tile || asset.metadata?.uvtile;
    
    if (uvTile) return 'UV Tile';
    if (seamless) return 'Seamless';
    return null;
  };

  // Load image list for navigation
  useEffect(() => {
    const loadImageList = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/assets/${asset.id || asset._key}/texture-images`);
        if (response.ok) {
          const data = await response.json();
          setImageList(data.images || []);
          // Reset image index when image list changes to prevent corruption
          setCurrentImageIndex(0);
        }
      } catch (error) {
        console.log('No texture images found:', error);
        setImageList([]);
        setCurrentImageIndex(0);
      }
    };

    if (asset.id || asset._key) {
      loadImageList();
    }
  }, [asset.id, asset._key]);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!showDropdown) return;
    
    const handleClickOutside = (event) => {
      if (!event.target.closest('.texture-dropdown-menu')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showDropdown]);

  // Navigation with bounds checking to prevent corruption
  const navigateImage = (direction) => {
    if (imageList.length <= 1) return;
    
    setCurrentImageIndex(prev => {
      const newIndex = direction === 'left' 
        ? (prev === 0 ? imageList.length - 1 : prev - 1)
        : (prev === imageList.length - 1 ? 0 : prev + 1);
      
      // Ensure index is within bounds
      return Math.max(0, Math.min(newIndex, imageList.length - 1));
    });
  };

  // Get texture type abbreviation using upload metadata only
  const getTextureTypeAbbr = (filename, imageObj = null) => {
    // Preview image
    if (imageObj?.is_preview || imageObj?.isPreview || filename === 'Preview.png') {
      return 'P';
    }
    
    const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';
    
    if (!isTextureSet) {
      // Single texture - use subcategory
      const subcategory = (asset.metadata?.subcategory || asset.subcategory)?.toLowerCase();
      if (!subcategory) return 'T';
      
      if (subcategory.includes('alpha')) return 'A';
      if (subcategory.includes('base') && subcategory.includes('color')) return 'BC';
      if (subcategory.includes('albedo')) return 'BC';
      if (subcategory.includes('metallic')) return 'M';
      if (subcategory.includes('roughness')) return 'R';
      if (subcategory.includes('normal')) return 'N';
      if (subcategory.includes('opacity')) return 'O';
      if (subcategory.includes('displacement') || subcategory.includes('height')) return 'D';
      return 'T';
    }
    
    // Texture set - use texture slot metadata
    const slots = asset.metadata?.texture_set_info?.texture_slots;
    if (!slots) return 'T';
    
    for (const [slotKey, slotInfo] of Object.entries(slots)) {
      if (slotInfo.original_filename === filename) {
        const typeMap = {
          'BaseColor': 'BC', 'Metallic': 'M', 'Roughness': 'R',
          'Normal': 'N', 'Opacity': 'O', 'Displacement': 'D'
        };
        return typeMap[slotInfo.type] || 'T';
      }
    }
    
    return 'T';
  };

  // Get texture types with safe index bounds checking
  const getTextureTypes = () => {
    if (!imageList || imageList.length === 0) return [];
    
    return imageList.map((img, index) => ({
      abbr: getTextureTypeAbbr(img.filename || '', img),
      index: index,
      filename: img.filename,
      isPreview: img.is_preview || img.isPreview || false
    }));
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 z-10">
      {/* Expanded Content Panel - slides up from bottom */}
      <div className={`bg-gray-800/95 border-t border-l border-r border-gray-700 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
        isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="p-3">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">🖼️</span>
            <h3 className="text-white font-semibold text-sm truncate">{formatAssetNameJSX(asset)}</h3>
          </div>
          
          {/* Texture Info Grid */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
            <div>
              <span className="text-gray-400">Type:</span>
              <div className="text-purple-400 font-medium">Texture Map</div>
            </div>
            <div>
              <span className="text-gray-400">Resolution:</span>
              <div className="text-cyan-300 font-medium truncate">{getResolution()}</div>
            </div>
            <div>
              <span className="text-gray-400">Format:</span>
              <div className="text-orange-300 font-medium">{getFormat()}</div>
            </div>
            <div>
              <span className="text-gray-400">Size:</span>
              <div className="text-gray-300">{getFileSize()}</div>
            </div>
            {getUVLayout() && (
              <div className="col-span-2">
                <span className="text-gray-400">UV Layout:</span>
                <div className="text-blue-300 font-medium">{getUVLayout()}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Texture Type Indicators */}
      {imageList.length > 1 && (
        <div className="absolute -top-8 left-1 flex gap-1 items-center">
          {getTextureTypes().map((textureType, idx) => {
            const isActive = currentImageIndex === textureType.index;
            return (
              <span
                key={`${textureType.filename}-${idx}`}
                className={`px-1.5 py-0.5 text-xs font-bold rounded transition-all duration-200 cursor-pointer ${
                  isActive 
                    ? 'bg-purple-500 text-white' 
                    : 'bg-black/40 text-gray-400 border border-gray-600/50 hover:bg-gray-600/50'
                }`}
                title={textureType.filename}
                onClick={(e) => {
                  e.stopPropagation();
                  if (textureType.index >= 0 && textureType.index < imageList.length) {
                    setCurrentImageIndex(textureType.index);
                  }
                }}
              >
                {textureType.abbr}
              </span>
            );
          })}
        </div>
      )}

      {/* Always visible tab at bottom - Texture themed */}
      <div className="relative group">
        <div 
          className="bg-purple-500/10 border border-purple-500/30 rounded-t-lg shadow-lg cursor-pointer hover:bg-purple-500/20 transition-all duration-200"
          onMouseEnter={handleBannerHover}
          onMouseLeave={handleBannerLeave}
          onClick={handleBannerClick}
        >
          <div className="flex items-center justify-between py-1 px-3">
            <div className="flex items-center gap-2 text-purple-400 hover:text-white transition-colors">
              <span className="text-lg">🖼️</span>
              <span className="text-xs font-medium">Texture Info</span>
              {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
            </div>
            
            {/* Three-dot menu button */}
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDropdown(!showDropdown);
                }}
                className="text-purple-400 hover:text-white p-1 rounded transition-colors opacity-0 group-hover:opacity-100"
                title="Asset Actions"
              >
                <MoreVertical size={12} />
              </button>
              
              {/* Dropdown menu */}
              {showDropdown && (
                <div className="absolute right-0 bottom-full mb-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50 min-w-[140px] texture-dropdown-menu">
                  <div className="py-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDropdown(false);
                        onEditAsset?.(asset);
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                    >
                      <Edit size={14} />
                      Edit Texture
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDropdown(false);
                        onPreviewAsset?.(asset);
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                    >
                      <Eye size={14} />
                      Preview
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDropdown(false);
                        onCopyAsset?.(asset);
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                    >
                      <Copy size={14} />
                      Copy Info
                    </button>
                    <div className="border-t border-gray-700 my-1"></div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDropdown(false);
                        console.log('Delete texture:', asset.name);
                        // Add delete functionality later
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-red-600/20 hover:text-red-300 transition-colors"
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Navigation Arrows - Only visible on hover for Texture Sets with multiple images */}
        {imageList.length > 1 && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigateImage('left');
              }}
              className="absolute left-1 top-1/2 transform -translate-y-1/2 bg-black/60 hover:bg-black/80 text-white rounded-full p-0.5 transition-all duration-200 backdrop-blur-sm z-20 opacity-0 group-hover:opacity-100"
            >
              <ChevronLeft size={10} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigateImage('right');
              }}
              className="absolute right-1 top-1/2 transform -translate-y-1/2 bg-black/60 hover:bg-black/80 text-white rounded-full p-0.5 transition-all duration-200 backdrop-blur-sm z-20 opacity-0 group-hover:opacity-100"
            >
              <ChevronRight size={10} />
            </button>
            
          </>
        )}
      </div>
    </div>
  );
};

export default TextureBadge;