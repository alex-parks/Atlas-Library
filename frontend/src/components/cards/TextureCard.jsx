// Texture Asset Card Component
// Full card component for uploaded Texture assets
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, MoreVertical, Edit, Eye, Copy, Trash2 } from 'lucide-react';
import SequenceThumbnail from '../SequenceThumbnail';

const TextureCard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview, onEditAsset, onCopyAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageList, setImageList] = useState([]);
  const [imageResolutions, setImageResolutions] = useState({});
  const [showDropdown, setShowDropdown] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.texture-card-dropdown-menu')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

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
    
    // Check thumbnail files for extensions
    if (asset.paths?.thumbnails && asset.paths.thumbnails.length > 0) {
      // Get all unique extensions from thumbnail files
      const extensions = new Set();
      asset.paths.thumbnails.forEach(file => {
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

  // Get category type for badge
  const getCategoryType = () => {
    if (asset.metadata?.subcategory) {
      return asset.metadata.subcategory;
    }
    return asset.subcategory || asset.metadata?.alpha_subcategory || 'Texture';
  };

  // Get category badge color and text
  const getCategoryBadge = () => {
    const category = getCategoryType().toLowerCase();
    if (category.includes('alpha')) {
      return { text: 'Alpha', color: 'bg-white/90 text-black' };
    } else if (category.includes('texture set') || category.includes('textureset')) {
      return { text: 'Texture Set', color: 'bg-gray-500/90 text-white' };
    } else if (category.includes('general')) {
      return { text: 'General', color: 'bg-gray-500/90 text-white' };
    } else if (category.includes('displacement')) {
      return { text: 'Displacement', color: 'bg-gray-500/90 text-white' };
    } else if (category.includes('normal')) {
      return { text: 'Normal', color: 'bg-gray-500/90 text-white' };
    } else if (category.includes('base') && category.includes('color')) {
      return { text: 'Base Color', color: 'bg-gray-500/90 text-white' };
    } else if (category.includes('metallic')) {
      return { text: 'Metallic', color: 'bg-gray-500/90 text-white' };
    } else if (category.includes('roughness')) {
      return { text: 'Roughness', color: 'bg-gray-500/90 text-white' };
    }
    return { text: getCategoryType(), color: 'bg-gray-500/90 text-white' };
  };

  // Get texture type (Seamless or UV Tile)
  const getTextureType = () => {
    // Debug logging
    console.log('🔍 Checking texture type for asset:', asset.id, {
      texture_type: asset.texture_type,
      metadata_texture_type: asset.metadata?.texture_type,
      seamless: asset.seamless,
      metadata_seamless: asset.metadata?.seamless,
      uv_tile: asset.uv_tile,
      metadata_uv_tile: asset.metadata?.uv_tile,
      full_asset: asset
    });
    
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

  // Load image list for navigation
  useEffect(() => {
    const loadImageList = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/assets/${asset.id || asset._key}/texture-images`);
        if (response.ok) {
          const data = await response.json();
          console.log('🖼️ Texture images loaded:', data);
          
          // Images are now naturally sorted alphabetically by priority prefix
          setImageList(data.images || []);
          setImageResolutions(data.resolutions || {});
        }
      } catch (error) {
        console.log('No additional texture images found:', error);
      }
    };

    if (asset.id || asset._key) {
      loadImageList();
    }
  }, [asset.id, asset._key]);

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

  // Map texture types to their abbreviations using ONLY upload metadata (NO filename parsing)
  const getTextureTypeAbbr = (filename, imageObj = null) => {
    console.log('🔍 TextureCard - Getting texture type for:', filename, 'imageObj:', imageObj);
    
    // Check if this is a Preview image first
    if (imageObj?.is_preview || imageObj?.isPreview || filename === 'Preview.png') {
      console.log('✅ TextureCard - Detected Preview image');
      return 'P'; // Preview abbreviation
    }
    
    // Check if this is a single texture (not a texture set)
    const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';
    
    if (!isTextureSet) {
      // For single textures, use the uploaded subcategory (no filename parsing)
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
    
    // For texture sets, use texture slot metadata EXCLUSIVELY (no filename parsing)
    if (asset.metadata?.texture_set_info?.texture_slots) {
      const slots = asset.metadata.texture_set_info.texture_slots;
      console.log('🔍 TextureCard - Available texture slots:', slots);
      console.log('🔍 TextureCard - Looking for filename:', filename);
      
      // Find which slot this filename corresponds to by original_filename match
      for (const [slotKey, slotInfo] of Object.entries(slots)) {
        console.log(`🔍 TextureCard - Checking slot ${slotKey}: ${slotInfo.original_filename} vs ${filename}`);
        if (slotInfo.original_filename === filename) {
          // Map slot types to abbreviations
          const typeMap = {
            'BaseColor': 'BC',
            'Metallic': 'M', 
            'Roughness': 'R',
            'Normal': 'N',
            'Opacity': 'O',
            'Displacement': 'D'
          };
          const result = typeMap[slotInfo.type] || 'T';
          console.log(`✅ TextureCard - Found match! ${slotInfo.type} -> ${result}`);
          return result;
        }
      }
      console.log('❌ TextureCard - No matching slot found for filename');
    } else {
      console.log('❌ TextureCard - No texture_set_info.texture_slots found in asset metadata');
    }
    
    // If we get here, something is wrong with the metadata
    console.warn(`⚠️ TextureCard - No texture slot found for filename: ${filename}`);
    return 'T'; // Default to generic texture instead of '?'
  };

  // Define texture priority order (Preview first, then texture maps)
  const TEXTURE_PRIORITY = {
    'P': 0,  // Preview (always first)
    'BC': 1, // Base Color
    'M': 2,  // Metallic
    'R': 3,  // Roughness
    'N': 4,  // Normal
    'O': 5,  // Opacity
    'D': 6,  // Displacement
    'A': 7,  // Alpha (single textures)
    'T': 8,  // Generic texture
    '?': 99  // Unknown
  };

  // Get texture types from image list in priority order
  const getTextureTypes = () => {
    // Since imageList is already sorted by priority, just map with current index
    return imageList.map((img, index) => ({
      abbr: getTextureTypeAbbr(img.filename || '', img),
      index: index,
      filename: img.filename,
      isPreview: img.is_preview || img.isPreview || false
    }));
  };

  // No longer needed - removing version display
  // const getAssetVersion = () => {
  //   const assetId = asset.id || asset._key || '';
  //   if (assetId.length >= 16) {
  //     return `v${assetId.substring(13)}`;
  //   }
  //   return 'v001';
  // };

  return (
    <div className="group relative">
      <div className={`bg-gray-800 rounded-lg overflow-hidden border transition-all duration-200 hover:shadow-lg relative ${
        asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded 
          ? 'border-yellow-600/60 hover:border-yellow-500/80 hover:shadow-yellow-500/5 ring-1 ring-yellow-600/10' 
          : 'border-purple-500/30 hover:border-purple-400 hover:shadow-purple-500/10'
      }`}>
        <div className="aspect-square bg-gray-700 relative overflow-hidden">
          {imageList.length > 1 ? (
            // Custom image display for texture navigation
            <div className="w-full h-full relative">
              {imageList[currentImageIndex] ? (
                <img
                  src={`http://localhost:8000/api/v1/assets/${asset.id || asset._key}/texture-image/${currentImageIndex}`}
                  alt={`${formatAssetName(asset)} - Image ${currentImageIndex + 1}`}
                  className="w-full h-full object-cover cursor-pointer"
                  onClick={() => openPreview(asset)}
                  onError={(e) => {
                    console.error(`Failed to load texture image ${currentImageIndex}:`, imageList[currentImageIndex]?.path);
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              {/* Fallback icon */}
              <div 
                className="text-gray-500 text-3xl flex items-center justify-center w-full h-full absolute inset-0"
                style={{ display: 'none' }}
              >
                🖼️
              </div>
            </div>
          ) : (
            // Direct image with proper aspect ratio for single textures
            <div className="w-full h-full relative">
              <img
                src={`http://localhost:8000/thumbnails/${asset.id || asset._key}${asset._image_updated ? `?_t=${asset._image_updated}` : ''}`}
                alt={formatAssetName(asset)}
                className="w-full h-full object-cover cursor-pointer"
                style={{
                  objectFit: 'cover',
                  objectPosition: 'center'
                }}
                onClick={() => openPreview(asset)}
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              {/* Fallback icon */}
              <div 
                className="text-gray-500 text-3xl flex items-center justify-center w-full h-full absolute inset-0"
                style={{ display: 'none' }}
              >
                🖼️
              </div>
            </div>
          )}
          
          {/* Category Badge - Top Left */}
          <div className="absolute top-2 left-2">
            <span className={`px-2 py-1 text-xs rounded font-medium backdrop-blur-sm ${getCategoryBadge().color}`}>
              {getCategoryBadge().text}
            </span>
          </div>

          {/* Resolution Tag - Top Right (slides left on hover to make room for menu) */}
          <div className="absolute top-2 right-2 group-hover:right-14 transition-all duration-200">
            {getCurrentResolution() !== 'Unknown' && (
              <span className="px-2 py-1 text-xs rounded font-medium bg-cyan-500/20 text-cyan-300 backdrop-blur-sm">
                {getCurrentResolution()}
              </span>
            )}
          </div>

          {/* Three-dot menu button - Top Right (appears on hover) */}
          <div className="absolute top-2 right-2">
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDropdown(!showDropdown);
                }}
                className="bg-black/60 hover:bg-black/80 text-white rounded-lg p-2 transition-all duration-200 backdrop-blur-sm opacity-0 group-hover:opacity-100"
                title="Asset Actions"
              >
                <MoreVertical size={14} />
              </button>
              
              {/* Dropdown menu */}
              {showDropdown && (
                <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50 min-w-[160px] texture-card-dropdown-menu">
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
                        // Add delete functionality later - textures might use different delete logic
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-red-600/20 hover:text-red-300 transition-colors"
                    >
                      <Trash2 size={14} />
                      Move to Trashbin
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Texture Type Tag - Bottom Right (Only show for Seamless) */}
          {getTextureType() === 'Seamless' && (
            <div className="absolute bottom-2 right-2">
              <span className="px-2 py-1 text-xs rounded font-medium bg-orange-500/20 text-orange-300 backdrop-blur-sm">
                Seamless
              </span>
            </div>
          )}

          {/* Navigation Arrows - Only visible on hover for Texture Sets with multiple images */}
          {imageList.length > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigateImage('left');
                }}
                className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/60 hover:bg-black/80 text-white rounded-full p-1 transition-all duration-200 backdrop-blur-sm opacity-0 group-hover:opacity-100"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigateImage('right');
                }}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/60 hover:bg-black/80 text-white rounded-full p-1 transition-all duration-200 backdrop-blur-sm opacity-0 group-hover:opacity-100"
              >
                <ChevronRight size={16} />
              </button>
              
            </>
          )}

          {/* Texture Type Indicators - Bottom Left */}
          {imageList.length > 1 && (
            <div className="absolute bottom-2 left-2 flex gap-1 items-center">
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

          {/* Branded Badge - Middle Right */}
          {(asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded) && (
            <div className="absolute top-1/2 right-2 transform -translate-y-1/2">
              <span className="px-2 py-1 text-xs rounded font-bold bg-yellow-500/20 text-yellow-300 backdrop-blur-sm">
                ⚠ BRANDED
              </span>
            </div>
          )}
        </div>

        {/* Asset Information Badge */}
        <div className="absolute bottom-0 left-0 right-0 z-10">
          {/* Expanded Content Panel */}
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
                <div>
                  <span className="text-gray-400">UV Layout:</span>
                  <div className="text-blue-300 font-medium">{getUVLayout()}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Always visible tab at bottom */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <div 
              className="bg-purple-500/10 border border-purple-500/30 rounded-t-lg shadow-lg cursor-pointer hover:bg-purple-500/20 transition-all duration-200"
              onMouseEnter={handleBannerHover}
              onMouseLeave={handleBannerLeave}
              onClick={handleBannerClick}
            >
              <div className="flex items-center justify-center py-1 px-3">
                <div className="flex items-center gap-2 text-purple-400 hover:text-white transition-colors">
                  <span className="text-lg">🖼️</span>
                  <span className="text-xs font-medium">Texture Info</span>
                  {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextureCard;