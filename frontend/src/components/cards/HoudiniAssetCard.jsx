// Houdini Asset Card Component
// Full card component for traditional Houdini 3D assets
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, MoreVertical, Edit, Trash2, Eye, Copy } from 'lucide-react';
import SequenceThumbnail from '../SequenceThumbnail';

const HoudiniAssetCard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview, onEditAsset, onDeleteAsset, onCopyAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
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

  // Helper functions
  const getRenderEngine = () => {
    return asset.metadata?.hierarchy?.render_engine || asset.metadata?.render_engine || 'Unknown';
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

  const getAssetVersion = () => {
    const assetId = asset.id || asset._key || '';
    if (assetId.length >= 16) {
      return `v${assetId.substring(13)}`;
    }
    return 'v001';
  };

  const getCreatedDate = () => {
    return asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown';
  };

  const getHoudiniVersion = () => {
    return asset.metadata?.houdini_version || 'Unknown';
  };

  const getArtist = () => {
    return asset.artist || 'Unknown';
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.asset-dropdown-menu')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  return (
    <div className="group relative">
      <div className={`bg-gray-800 rounded-lg overflow-hidden border transition-all duration-200 hover:shadow-lg relative ${
        asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded 
          ? 'border-yellow-600/60 hover:border-yellow-500/80 hover:shadow-yellow-500/5 ring-1 ring-yellow-600/10' 
          : 'border-gray-700 hover:border-blue-500 hover:shadow-blue-500/10'
      }`}>
        <div className="aspect-square bg-gray-700 relative overflow-hidden houdini-thumbnail-container">
          <style>{`
            .houdini-thumbnail-container img {
              object-fit: cover !important;
              object-position: center !important;
            }
          `}</style>
          <SequenceThumbnail
            assetId={asset.id || asset._key}
            assetName={formatAssetName(asset)}
            thumbnailFrame={asset.thumbnail_frame}
            fallbackIcon={
              asset.category === 'Characters' ? '🎭' :
              asset.category === 'Props' ? '📦' :
              asset.category === 'Environments' ? '🏞️' :
              asset.category === 'Vehicles' ? '🚗' :
              asset.category === 'Effects' ? '✨' :
              '🎨'
            }
            onClick={() => openPreview(asset)}
            hideZoomMessage={true}
          />
          
          {/* Version Tag - Bottom Left (standard position for Houdini assets) */}
          <div className="absolute bottom-2 left-2">
            <span className="px-2 py-1 text-xs rounded font-medium bg-blue-500/20 text-blue-300 backdrop-blur-sm">
              {getAssetVersion()}
            </span>
          </div>
          
          {/* Render Engine Tags - Bottom Right */}
          <div className="absolute bottom-2 right-2">
            {getRenderEngine() !== 'Unknown' && (
              <span className="px-2 py-1 text-xs rounded font-medium bg-orange-500/20 text-orange-300 backdrop-blur-sm">
                {getRenderEngine()}
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
                <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50 min-w-[160px] asset-dropdown-menu">
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
                      Edit Asset
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
                        onDeleteAsset?.(asset);
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

          {/* Branded Badge - Top Center (moved to avoid conflict with menu) */}
          {(asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded) && (
            <div className="absolute top-2 left-1/2 transform -translate-x-1/2">
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
                <span className="text-lg">🎨</span>
                <h3 className="text-white font-semibold text-sm truncate">{formatAssetNameJSX(asset)}</h3>
              </div>
              
              {/* Houdini Asset Specific Fields - 2x3 layout */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
                <div>
                  <span className="text-gray-400">Render Engine:</span>
                  <div className="text-orange-400 font-medium truncate">{getRenderEngine()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Size:</span>
                  <div className="text-gray-300">{getFileSize()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Artist:</span>
                  <div className="text-green-400 font-medium truncate">{getArtist()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Houdini Ver:</span>
                  <div className="text-blue-300 font-medium">{getHoudiniVersion()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Asset Ver:</span>
                  <div className="text-purple-300 font-medium">{getAssetVersion()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Created:</span>
                  <div className="text-cyan-300 font-medium">{getCreatedDate()}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Always visible tab at bottom */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <div 
              className="bg-blue-500/10 border border-blue-500/30 rounded-t-lg shadow-lg cursor-pointer hover:bg-blue-500/20 transition-all duration-200"
              onMouseEnter={handleBannerHover}
              onMouseLeave={handleBannerLeave}
              onClick={handleBannerClick}
            >
              <div className="flex items-center justify-center py-1 px-3">
                <div className="flex items-center gap-2 text-blue-400 hover:text-white transition-colors">
                  <span className="text-lg">🎨</span>
                  <span className="text-xs font-medium">Asset Info</span>
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

export default HoudiniAssetCard;