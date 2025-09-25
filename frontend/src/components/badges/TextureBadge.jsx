import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, MoreVertical, Edit, Copy, Eye, Trash2 } from 'lucide-react';
import config from '../../utils/config';

const TextureBadge = ({ asset, formatAssetNameJSX, onEditAsset, onPreviewAsset, onCopyAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [hasPreview, setHasPreview] = useState(false);
  const [availableTextures, setAvailableTextures] = useState([]);
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

  // Check for preview image and available textures for texture sets
  const checkPreviewAndTextures = async () => {
      try {
        const assetId = asset.id || asset._key;
        const isTextureSet = asset.metadata?.subcategory === 'Texture Sets' || asset.subcategory === 'Texture Sets';
        
        if (isTextureSet) {
          // Check for textures and preview using the texture-images API
          try {
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

                // First, try to use explicit texture_set_info from asset metadata
                console.log(`🔍 Asset ${assetId} metadata:`, asset.metadata?.texture_set_info);
                console.log(`🔍 Asset ${assetId} texture images:`, textureData.images);

                if (asset.metadata?.texture_set_info?.texture_slots) {
                  const textureSlots = asset.metadata.texture_set_info.texture_slots;
                  console.log(`📋 Using explicit texture slots for ${assetId}:`, textureSlots);

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

                    console.log(`🔍 Checking slot ${slotKey} (${displayType}) for filename: ${originalFilename}`);

                    // Check if there's an image with this filename in textureData
                    const matchingImage = textureData.images.find(img =>
                      img.is_preview !== true && img.filename === originalFilename
                    );

                    console.log(`🔍 Matching image for ${originalFilename}:`, matchingImage);

                    if (matchingImage && displayType) {
                      foundTextures.push(displayType);
                      console.log(`✅ Found ${displayType} (${slotKey}) texture: ${originalFilename}`);
                    } else {
                      console.log(`❌ No match for ${slotKey} (${displayType}) - filename: ${originalFilename}`);
                    }
                  }
                } else {
                  // Fallback to old filename-based detection for legacy assets
                  console.log(`⚠️ No texture_set_info found for ${assetId}, using filename fallback`);
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
                      console.log(`Found ${textureType} in:`, textureData.images[matchingTextureIndex].filename);
                    }
                  }
                }

                console.log(`Asset ${assetId} - Preview: ${hasPreviewImg}, Textures:`, foundTextures);
                setAvailableTextures(foundTextures);
              } else {
                setAvailableTextures([]);
              }
            } else {
              console.log(`No texture data for asset ${assetId}`);
              setHasPreview(false);
              setAvailableTextures([]);
            }
          } catch (error) {
            console.error('Failed to fetch texture images for asset', assetId, ':', error);
            setHasPreview(false);
            setAvailableTextures([]);
          }
        } else {
          setHasPreview(false);
          setAvailableTextures([]);
        }
      } catch (error) {
        setHasPreview(false);
        setAvailableTextures([]);
      }
    };

  // Listen for preview updates specifically for this asset
  useEffect(() => {
    const handleAssetSpecificUpdate = (event) => {
      const { assetId } = event.detail;
      const currentAssetId = asset.id || asset._key;
      
      // Only trigger re-check if this is OUR asset
      if (assetId === currentAssetId) {
        // Force a re-check of preview availability and textures
        checkPreviewAndTextures();
      }
    };
    
    window.addEventListener('assetPreviewUpdated', handleAssetSpecificUpdate);
    return () => window.removeEventListener('assetPreviewUpdated', handleAssetSpecificUpdate);
  }, [asset.id, asset._key]);

  // Initial check and when asset changes
  useEffect(() => {
    if (asset.id || asset._key) {
      checkPreviewAndTextures();
    }
  }, [asset.id, asset._key]); // Removed asset._image_updated to prevent all badges updating when any asset changes

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

      {/* Test badge - always visible for debugging */}
      <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 text-xs z-30">
        TEST
      </div>
      
      {/* Texture Set Preview and Available Textures - Always visible */}
      <div className="absolute bottom-16 left-2 flex gap-1 z-30 bg-black/50 p-1 rounded">
        {/* Always show this for debugging */}
        <span className="px-2 py-1 text-xs font-bold rounded bg-yellow-500 text-black">
          DEBUG
        </span>
        
        {/* Preview badge */}
        {hasPreview && (
          <span className="px-2 py-1 text-xs font-bold rounded bg-purple-600 text-white border border-white">
            P
          </span>
        )}
        
        {/* Available texture badges */}
        {availableTextures.map((textureType, index) => (
          <span
            key={textureType}
            className="px-2 py-1 text-xs font-bold rounded bg-cyan-600 text-white border border-white"
            title={`${textureType} Texture Available`}
          >
            {textureType}
          </span>
        ))}

        {/* Extra textures count badge */}
        {(() => {
          const extraTexturesCount = asset.metadata?.texture_set_info?.extra_textures?.length || 0;
          return extraTexturesCount > 0 ? (
            <span
              className="px-2 py-1 text-xs font-bold rounded bg-white/50 text-white border border-blue-500"
              title={`${extraTexturesCount} Additional Texture${extraTexturesCount !== 1 ? 's' : ''} Available`}
            >
              +{extraTexturesCount}
            </span>
          ) : null;
        })()}

        {/* Show count */}
        <span className="px-1 py-1 text-xs bg-green-500 text-white rounded">
          {availableTextures.length}
        </span>
      </div>

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
        
      </div>
    </div>
  );
};

export default TextureBadge;