// Texture Asset Card Component
// Full card component for uploaded Texture assets
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, MoreVertical, Edit, Eye, Copy, Trash2, RefreshCw } from 'lucide-react';
import SequenceThumbnail from '../SequenceThumbnail';
import TextureSetSequence from '../TextureSetSequence';
import config from '../../utils/config';

// Texture Type Badges Component - Shows all available texture types for texture sets
const TextureTypeBadges = ({ asset, onRefresh, currentFrameType, onBadgeClick }) => {
  const [hasPreview, setHasPreview] = useState(false);
  const [availableTextures, setAvailableTextures] = useState([]);
  const [loading, setLoading] = useState(true);

  const assetId = asset.id || asset._key;
  const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';

  // Check for preview image and available textures for texture sets
  const checkTextureTypes = async () => {
    if (!isTextureSet) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const textureResponse = await fetch(`${config.backendUrl}/api/v1/assets/${assetId}/texture-images`);
      
      if (textureResponse.ok) {
        const textureData = await textureResponse.json();
        
        // Check if there's a preview image
        const hasPreviewImg = textureData.images?.some(img =>
          img.is_preview === true ||
          img.filename?.toLowerCase().includes('preview') ||
          img.path?.toLowerCase().includes('preview')
        ) || false;
        
        setHasPreview(hasPreviewImg);
        
        // Find available texture types using explicit texture slot information
        if (textureData.images && textureData.images.length > 0) {
          const foundTextures = [];

          console.log(`🔍 TextureCard Asset ${assetId} metadata:`, asset.metadata?.texture_set_info);
          console.log(`🔍 TextureCard Asset ${assetId} texture images:`, textureData.images);

          // First, try to use explicit texture_set_info from asset metadata
          if (asset.metadata?.texture_set_info?.texture_slots) {
            const textureSlots = asset.metadata.texture_set_info.texture_slots;
            console.log(`📋 TextureCard using explicit texture slots for ${assetId}:`, textureSlots);

            // Map texture slots to display abbreviations
            const slotToDisplayMap = {
              'baseColor': 'BC',
              'metallic': 'M',
              'roughness': 'R',
              'normal': 'N',
              'opacity': 'O',
              'displacement': 'D'
            };

            // Check each texture slot to see if we have a corresponding image
            for (const [slotKey, slotInfo] of Object.entries(textureSlots)) {
              const originalFilename = slotInfo.original_filename;
              const displayType = slotToDisplayMap[slotKey];

              console.log(`🔍 TextureCard checking slot ${slotKey} (${displayType}) for filename: ${originalFilename}`);

              // Check if there's an image with this filename in textureData
              const matchingImage = textureData.images.find(img =>
                img.is_preview !== true && img.filename === originalFilename
              );

              console.log(`🔍 TextureCard matching image for ${originalFilename}:`, matchingImage);

              if (matchingImage && displayType) {
                foundTextures.push(displayType);
                console.log(`✅ TextureCard found ${displayType} (${slotKey}) texture: ${originalFilename}`);
              } else {
                console.log(`❌ TextureCard no match for ${slotKey} (${displayType}) - filename: ${originalFilename}`);
              }
            }
          } else {
            // Fallback to old filename-based detection for legacy assets
            console.log(`⚠️ TextureCard no texture_set_info found for ${assetId}, using filename fallback`);
            const textureOrder = ['BC', 'R', 'M', 'N', 'O', 'D'];
            const textureTypeMap = {
              'BC': ['basecolor', 'albedo', 'diffuse', 'base_color', 'color'],
              'R': ['roughness', 'rough'],
              'M': ['metallic', 'metalness', 'metal'],
            'N': ['normal', 'bump', 'nrm'],
            'O': ['opacity', 'alpha', 'transparency'],
            'D': ['displacement', 'height', 'disp']
          };
          
          // Find matching textures (exclude preview images)
          for (const textureType of textureOrder) {
            const keywords = textureTypeMap[textureType] || [];
            
            const matchingTextureIndex = textureData.images?.findIndex(img => {
              // Skip preview images for texture type detection
              if (img.is_preview === true ||
                  img.filename?.toLowerCase().includes('preview') ||
                  img.path?.toLowerCase().includes('preview')) {
                return false;
              }
              
              const filename = img.filename.toLowerCase();
              return keywords.some(keyword => filename.includes(keyword));
            });
            
            if (matchingTextureIndex !== -1 && matchingTextureIndex !== undefined) {
              foundTextures.push(textureType);
            }
          }
          }

          console.log(`📋 TextureCard final textures for ${assetId}:`, foundTextures);
          setAvailableTextures(foundTextures);
        } else {
          setAvailableTextures([]);
        }
      } else {
        setHasPreview(false);
        setAvailableTextures([]);
      }
    } catch (error) {
      console.error('Failed to fetch texture types for asset', assetId, ':', error);
      setHasPreview(false);
      setAvailableTextures([]);
    } finally {
      setLoading(false);
    }
  };

  // Initial check and when asset changes
  useEffect(() => {
    if (assetId) {
      checkTextureTypes();
    }
  }, [assetId, isTextureSet]);

  // Only show badges for texture sets
  if (!isTextureSet || loading) {
    return null;
  }

  // If no textures found, don't show anything
  if (!hasPreview && availableTextures.length === 0) {
    return null;
  }

  // Function to get badge styling based on whether it's currently active
  const getBadgeStyle = (badgeType) => {
    const isActive = currentFrameType === badgeType;
    if (badgeType === 'preview') {
      return isActive 
        ? "px-1.5 py-0.5 text-xs font-bold rounded bg-purple-500 text-white border border-purple-500" 
        : "px-1.5 py-0.5 text-xs font-bold rounded bg-transparent text-white border border-purple-400";
    } else {
      return isActive 
        ? "px-1.5 py-0.5 text-xs font-bold rounded bg-blue-500 text-white border border-blue-500" 
        : "px-1.5 py-0.5 text-xs font-bold rounded bg-transparent text-white border border-blue-400";
    }
  };

  return (
    <div className="absolute bottom-2 left-2 flex gap-1 z-20 group/badges">
      {/* Preview badge */}
      {hasPreview && (
        <span 
          className={`cursor-pointer transition-all duration-200 ${getBadgeStyle('preview')}`}
          onClick={(e) => {
            e.stopPropagation();
            onBadgeClick?.('preview');
          }}
          title="Preview Image"
        >
          P
        </span>
      )}
      
      {/* Available texture badges */}
      {availableTextures.map((textureType) => (
        <span
          key={textureType}
          className={`cursor-pointer transition-all duration-200 ${getBadgeStyle(textureType)}`}
          onClick={(e) => {
            e.stopPropagation();
            onBadgeClick?.(textureType);
          }}
          title={`${textureType} Texture`}
        >
          {textureType}
        </span>
      ))}

      {/* Extra textures count badge */}
      {(() => {
        const extraTexturesCount = asset.metadata?.texture_set_info?.extra_textures?.length || 0;
        return extraTexturesCount > 0 ? (
          <span
            className="px-1.5 py-0.5 text-xs font-bold rounded bg-white/50 text-white border border-blue-400"
            title={`${extraTexturesCount} Additional Texture${extraTexturesCount !== 1 ? 's' : ''} Available`}
          >
            +{extraTexturesCount}
          </span>
        ) : null;
      })()}
      
      {/* Refresh button - shows on hover */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRefresh?.();
          checkTextureTypes(); // Re-check texture types
        }}
        className="opacity-0 group-hover/badges:opacity-100 group-hover:opacity-100 transition-opacity duration-200 px-1.5 py-0.5 text-xs rounded bg-gray-600 hover:bg-gray-500 text-white"
        title="Refresh texture data"
      >
        <RefreshCw size={10} />
      </button>
    </div>
  );
};

// Smart texture image display component
const TextureImage = ({ asset, refreshKey, formatAssetName, openPreview, onFrameChange, externalFrameIndex }) => {
  const assetId = asset.id || asset._key;
  const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';
  
  // For texture sets, use the new TextureSetSequence component
  if (isTextureSet) {
    return (
      <TextureSetSequence
        assetId={assetId}
        assetName={formatAssetName(asset)}
        asset={asset}
        fallbackIcon="🖼️"
        className="w-full h-full object-cover"
        onClick={() => openPreview(asset)}
        hideZoomMessage={true}
        onFrameChange={onFrameChange}
        externalFrameIndex={externalFrameIndex}
      />
    );
  }
  
  // For non-texture sets, show regular thumbnail
  return (
    <img
      src={`${config.backendUrl}/thumbnails/${assetId}?_t=${refreshKey || Date.now()}`}
      alt={formatAssetName(asset)}
      className="w-full h-full object-cover cursor-pointer"
      onClick={() => openPreview(asset)}
    />
  );
};

const TextureCard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview, onEditAsset, onCopyAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  
  // State for texture sequence navigation
  const [currentFrameType, setCurrentFrameType] = useState(null);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [sequenceMapping, setSequenceMapping] = useState([]);

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

  // Simple preview state - no complex event listeners
  const [refreshKey, setRefreshKey] = useState(0);
  
  // Simple force refresh function
  const handleForceRefresh = () => {
    setRefreshKey(Date.now());
  };

  // Handle frame changes from TextureSetSequence
  const handleFrameChange = (frameData) => {
    if (frameData && frameData.type) {
      if (frameData.type === 'preview') {
        setCurrentFrameType('preview');
      } else if (frameData.textureType) {
        setCurrentFrameType(frameData.textureType);
      } else {
        setCurrentFrameType(null);
      }
    }
  };

  // Handle badge clicks to navigate to specific texture type
  const handleBadgeClick = (textureType) => {
    // Find the frame index for this texture type
    if (sequenceMapping.length > 0) {
      const targetFrame = sequenceMapping.findIndex(frame => {
        if (textureType === 'preview') {
          return frame.type === 'preview';
        } else {
          return frame.textureType === textureType;
        }
      });
      
      if (targetFrame !== -1) {
        setCurrentFrameIndex(targetFrame);
      }
    }
  };
  
  // Simple function to check if this texture set has a preview
  const hasPreview = () => {
    const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';
    return isTextureSet; // For now, assume all texture sets can have previews - we'll check when rendering
  };

  // Get current image resolution - always use actual resolution, not thumbnail
  const getCurrentResolution = () => {
    return getResolution();
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
          {/* Smart texture display with sequence support */}
          <TextureImage 
            asset={asset} 
            refreshKey={refreshKey}
            formatAssetName={formatAssetName}
            openPreview={openPreview}
            onFrameChange={handleFrameChange}
            externalFrameIndex={currentFrameIndex}
          />
          
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

          {/* Texture Type Badges - Bottom Left (for texture sets) */}
          <TextureTypeBadges 
            asset={asset} 
            onRefresh={handleForceRefresh}
            currentFrameType={currentFrameType}
            onBadgeClick={handleBadgeClick}
          />

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