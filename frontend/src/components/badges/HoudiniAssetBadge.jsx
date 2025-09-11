// Houdini Asset Badge Component
// Specialized for traditional Houdini 3D assets (Assets, FX, Materials, HDAs)
import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const HoudiniAssetBadge = ({ asset, formatAssetNameJSX }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);

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

  return (
    <div className="absolute bottom-0 left-0 right-0 z-10">
      {/* Expanded Content Panel - slides up from bottom */}
      <div className={`bg-gray-800/95 border-t border-l border-r border-gray-700 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
        isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="p-3">
          <h3 className="text-white font-semibold text-sm mb-2 truncate">{formatAssetNameJSX(asset)}</h3>
          
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

      {/* Always visible tab at bottom - Houdini themed */}
      <div 
        className="bg-gray-800/95 border border-gray-700 rounded-t-lg shadow-lg cursor-pointer hover:bg-gray-700/95 transition-all duration-200"
        onMouseEnter={handleBannerHover}
        onMouseLeave={handleBannerLeave}
        onClick={handleBannerClick}
      >
        <div className="flex items-center justify-center py-1 px-3">
          <div className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <span className="text-xs font-medium">Asset Info</span>
            {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HoudiniAssetBadge;