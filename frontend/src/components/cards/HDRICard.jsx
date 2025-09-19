// HDRI Asset Card Component
// Full card component for HDRI environment map assets
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, MoreVertical, Edit } from 'lucide-react';
import SequenceThumbnail from '../SequenceThumbnail';

const HDRICard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview, onEditAsset }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.hdri-card-dropdown-menu')) {
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

  // Helper functions specific to HDRI assets
  const getResolution = () => {
    return asset.metadata?.resolution || asset.metadata?.dimensions || 'Unknown';
  };

  const getFormat = () => {
    if (asset.paths?.template_file) {
      return asset.paths.template_file.split('.').pop()?.toUpperCase() || 'Unknown';
    }
    return asset.metadata?.file_format?.toUpperCase() || 'EXR';
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

  const getCategory = () => {
    // Get category from hierarchy.subcategory or infer from metadata
    return asset.hierarchy?.subcategory || asset.metadata?.subcategory || 'Studio';
  };

  const getCreatedDate = () => {
    return asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown';
  };

  const getEnvironmentType = () => {
    // Use category from hierarchy or metadata
    return getCategory();
  };

  const getAssetVersion = () => {
    const assetId = asset.id || asset._key || '';
    if (assetId.length >= 16) {
      return `v${assetId.substring(13)}`;
    }
    return 'v001';
  };

  return (
    <div className="group relative">
      <div className={`bg-gray-800 rounded-lg overflow-hidden border transition-all duration-200 hover:shadow-lg relative ${
        asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded 
          ? 'border-yellow-600/60 hover:border-yellow-500/80 hover:shadow-yellow-500/5 ring-1 ring-yellow-600/10' 
          : 'border-orange-500/30 hover:border-orange-400 hover:shadow-orange-500/10'
      }`}>
        <div className="aspect-square bg-gray-700 relative overflow-hidden hdri-thumbnail-container">
          {/* HDRI Thumbnail with aspect ratio preservation and zoom/pan functionality */}
          <style>{`
            .hdri-thumbnail-container img {
              object-fit: cover !important;
              object-position: center !important;
            }
          `}</style>
          <SequenceThumbnail
            assetId={asset.id || asset._key}
            assetName={formatAssetName(asset)}
            thumbnailFrame={asset.thumbnail_frame}
            fallbackIcon="🌅"
            onClick={() => openPreview(asset)}
            className="w-full h-full"
            hideZoomMessage={true}
          />
          

          {/* Resolution Tag - Top Right */}
          <div className="absolute top-2 right-2">
            {getResolution() !== 'Unknown' && (
              <span className="px-2 py-1 text-xs rounded font-medium bg-cyan-500/20 text-cyan-300 backdrop-blur-sm">
                {getResolution()}
              </span>
            )}
          </div>

          {/* Category Tag - Bottom Left */}
          <div className="absolute bottom-2 left-2">
            <span className="px-2 py-1 text-xs rounded font-medium bg-green-500/20 text-green-300 backdrop-blur-sm">
              📍 {getCategory()}
            </span>
          </div>

          {/* Format Tag - Bottom Right */}
          <div className="absolute bottom-2 right-2">
            <span className="px-2 py-1 text-xs rounded font-medium bg-purple-500/20 text-purple-300 backdrop-blur-sm">
              {getFormat()}
            </span>
          </div>

          {/* Branded Badge - Middle Left */}
          {(asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded) && (
            <div className="absolute top-1/2 left-2 transform -translate-y-1/2">
              <span className="px-2 py-1 text-xs rounded font-bold bg-yellow-500/20 text-yellow-300 backdrop-blur-sm">
                ⚠ BRANDED
              </span>
            </div>
          )}

          {/* Three Dots Menu - Top Right */}
          <div className="absolute top-2 right-2 z-20">
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
                <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50 min-w-[160px] hdri-card-dropdown-menu">
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
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Asset Information Badge */}
        <div className="absolute bottom-0 left-0 right-0 z-10">
          {/* Expanded Content Panel */}
          <div className={`bg-gray-800/95 border-t border-l border-r border-gray-700 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
            isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
          }`}>
            <div className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">🌅</span>
                <h3 className="text-white font-semibold text-sm truncate">{formatAssetNameJSX(asset)}</h3>
              </div>
              
              {/* HDRI Specific Fields - 2x3 layout */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500">
                <div>
                  <span className="text-gray-400">Type:</span>
                  <div className="text-orange-400 font-medium">HDRI Map</div>
                </div>
                <div>
                  <span className="text-gray-400">Resolution:</span>
                  <div className="text-cyan-300 font-medium truncate">{getResolution()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Format:</span>
                  <div className="text-purple-300 font-medium">{getFormat()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Size:</span>
                  <div className="text-gray-300">{getFileSize()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Environment:</span>
                  <div className="text-green-400 font-medium">{getEnvironmentType()}</div>
                </div>
                <div>
                  <span className="text-gray-400">Created:</span>
                  <div className="text-gray-300 font-medium truncate">{getCreatedDate()}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Always visible tab at bottom */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <div 
              className="bg-orange-500/10 border border-orange-500/30 rounded-t-lg shadow-lg cursor-pointer hover:bg-orange-500/20 transition-all duration-200"
              onMouseEnter={handleBannerHover}
              onMouseLeave={handleBannerLeave}
              onClick={handleBannerClick}
            >
              <div className="flex items-center justify-center py-1 px-3">
                <div className="flex items-center gap-2 text-orange-400 hover:text-white transition-colors">
                  <span className="text-lg">🌅</span>
                  <span className="text-xs font-medium">HDRI Info</span>
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

export default HDRICard;