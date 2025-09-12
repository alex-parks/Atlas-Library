// Texture Asset Badge Component
// Specialized for uploaded Texture assets
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, MoreVertical, Edit, Copy, Eye, Trash2 } from 'lucide-react';

const TextureBadge = ({ asset, formatAssetNameJSX, onEditAsset, onPreviewAsset, onCopyAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageList, setImageList] = useState([]);
  const [imageResolutions, setImageResolutions] = useState({});
  const [showDropdown, setShowDropdown] = useState(false);

  const handleBannerHover = () => {
    if (!isClickedOpen) {
      setIsExpanded(true);
    }
  };

  const handleBannerLeave = () => {
    if (!isClickedOpen) {
      setIsExpanded(false);
    }
  };

  const handleBannerClick = () => {
    if (isClickedOpen) {
      setIsClickedOpen(false);
      setIsExpanded(false);
    } else {
      setIsClickedOpen(true);
      setIsExpanded(true);
    }
  };

  // Helper functions specific to Texture assets
  const getResolution = () => {
    return asset.metadata?.resolution || asset.metadata?.dimensions || 'Unknown';
  };

  const getFormat = () => {
    // Check for format in metadata first
    if (asset.metadata?.file_format) {
      return asset.metadata.file_format.toUpperCase();
    }
    
    // Check copied files for extensions
    if (asset.paths?.copied_files && asset.paths.copied_files.length > 0) {
      // Get all unique extensions from copied files
      const extensions = new Set();
      asset.paths.copied_files.forEach(file => {
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
    if (asset.paths?.template_file) {
      return asset.paths.template_file.split('.').pop()?.toUpperCase() || 'Unknown';
    }
    
    return 'Unknown';
  };

  const getFileSize = () => {
    const totalBytes = asset.file_sizes?.estimated_total_size || 0;
    if (totalBytes === 0) return <span className="text-gray-500">Calc...</span>;
    
    if (totalBytes < 1024 * 1024) {
      return `${Math.round(totalBytes / 1024)} KB`;
    } else if (totalBytes < 1024 * 1024 * 1024) {
      return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
    } else {
      return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
  };

  const getUVLayout = () => {
    // Check the new texture_type field first
    const textureType = asset.texture_type || asset.metadata?.texture_type;
    if (textureType) {
      if (textureType === 'seamless') return 'Seamless';
      if (textureType === 'uv_tile') return 'UV Tile';
    }
    
    // Fallback to legacy seamless/uv_tile fields
    const seamless = asset.seamless || asset.metadata?.seamless || asset.metadata?.tiling;
    const uvTile = asset.uv_tile || asset.metadata?.uv_tile || asset.metadata?.uvtile;
    
    if (uvTile) return 'UV Tile';
    if (seamless) return 'Seamless';
    
    return null;
  };

  const getCreatedDate = () => {
    return asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown';
  };

  // Load image list for navigation
  useEffect(() => {
    const loadImageList = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/assets/${asset.id || asset._key}/texture-images`);
        if (response.ok) {
          const data = await response.json();
          console.log('🖼️ Texture images loaded for badge:', data);
          
          // Backend now returns images in correct position order (BC-M-R-N-O-D)
          setImageList(data.images || []);
          setImageResolutions(data.resolutions || {});
        }
      } catch (error) {
        console.log('No additional texture images found for badge:', error);
      }
    };

    if (asset.id || asset._key) {
      loadImageList();
    }
  }, [asset.id, asset._key]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.texture-dropdown-menu')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  // Navigation functions
  const navigateImage = (direction) => {
    if (imageList.length <= 1) return;
    
    setCurrentImageIndex(prev => {
      if (direction === 'left') {
        return prev === 0 ? imageList.length - 1 : prev - 1;
      } else {
        return prev === imageList.length - 1 ? 0 : prev + 1;
      }
    });
  };

  // Get current image resolution - always use actual resolution, not thumbnail
  const getCurrentResolution = () => {
    return getResolution();
  };

  // Map texture types to their abbreviations using metadata texture slots
  const getTextureTypeAbbr = (filename) => {
    // Check if this is a single texture (not a texture set)
    const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';
    
    if (!isTextureSet) {
      // For single textures, use the uploaded subcategory instead of parsing filename
      const subcategory = asset.metadata?.subcategory || asset.subcategory;
      if (subcategory) {
        const subcategoryLower = subcategory.toLowerCase();
        if (subcategoryLower.includes('alpha')) return 'A';
        if (subcategoryLower.includes('base') && subcategoryLower.includes('color')) return 'BC';
        if (subcategoryLower.includes('albedo')) return 'BC';
        if (subcategoryLower.includes('metallic')) return 'M';
        if (subcategoryLower.includes('roughness')) return 'R';
        if (subcategoryLower.includes('normal')) return 'N';
        if (subcategoryLower.includes('opacity')) return 'O';
        if (subcategoryLower.includes('displacement') || subcategoryLower.includes('height')) return 'D';
      }
      return 'T'; // Generic texture for single textures without clear subcategory
    }
    
    // For texture sets, check texture slot metadata (more reliable)
    if (asset.metadata?.texture_set_info?.texture_slots) {
      const slots = asset.metadata.texture_set_info.texture_slots;
      // Find which slot this filename corresponds to
      for (const [slotKey, slotInfo] of Object.entries(slots)) {
        if (filename.includes(`_${slotInfo.position}_${slotInfo.type}_`)) {
          // Map slot types to abbreviations
          const typeMap = {
            'BaseColor': 'BC',
            'Metallic': 'M', 
            'Roughness': 'R',
            'Normal': 'N',
            'Opacity': 'O',
            'Displacement': 'D'
          };
          return typeMap[slotInfo.type] || '?';
        }
      }
    }
    
    const lower = filename.toLowerCase();
    
    // New format: AssetName_Position_Type_thumbnail.png (for texture sets)
    if (lower.includes('_0_basecolor')) return 'BC';
    if (lower.includes('_1_metallic')) return 'M';
    if (lower.includes('_2_roughness')) return 'R';
    if (lower.includes('_3_normal')) return 'N';
    if (lower.includes('_4_opacity')) return 'O';
    if (lower.includes('_5_displacement')) return 'D';
    
    // Legacy fallback for older texture sets only
    if (lower.includes('displacement') || lower.includes('height') || lower.includes('disp')) return 'D';
    if (lower.includes('base') && lower.includes('color')) return 'BC';
    if (lower.includes('albedo')) return 'BC';
    if (lower.includes('alpha')) return 'A';
    if (lower.includes('metallic') || lower.includes('metalness')) return 'M';
    if (lower.includes('roughness')) return 'R';
    if (lower.includes('normal')) return 'N';
    if (lower.includes('opacity')) return 'O';
    return '?';
  };

  // Get texture types in the correct display order (BC-M-R-N-O-D)
  const getTextureTypes = () => {
    // Since the backend now returns images sorted by position, we can use them directly
    return imageList.map((img, index) => ({
      abbr: getTextureTypeAbbr(img.filename || ''),
      index: index, // This is now the correct position index
      filename: img.filename
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
          
          {/* Texture Specific Fields - 2x2 layout with UV Layout */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
            <div>
              <span className="text-gray-400">Type:</span>
              <div className="text-purple-400 font-medium">Texture Map</div>
            </div>
            <div>
              <span className="text-gray-400">Resolution:</span>
              <div className="text-cyan-300 font-medium truncate">{getCurrentResolution()}</div>
            </div>
            <div>
              <span className="text-gray-400">Format:</span>
              <div className="text-orange-300 font-medium">{getFormat()}</div>
            </div>
            <div>
              <span className="text-gray-400">Size:</span>
              <div className="text-gray-300">{getFileSize()}</div>
            </div>
            <div>
              <span className="text-gray-400">UV Layout:</span>
              <div className="text-blue-300 font-medium">{getUVLayout()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Texture Type Indicators - Bottom Left */}
      {imageList.length > 1 && (
        <div className="absolute -top-8 left-1 flex gap-1 items-center">
          {getTextureTypes().map((textureType, idx) => (
            <span
              key={idx}
              className={`
                px-1.5 py-0.5 text-xs font-bold rounded transition-all duration-200
                ${currentImageIndex === textureType.index 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-black/40 text-gray-400 border border-gray-600/50'}
              `}
              title={textureType.filename}
            >
              {textureType.abbr}
            </span>
          ))}
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