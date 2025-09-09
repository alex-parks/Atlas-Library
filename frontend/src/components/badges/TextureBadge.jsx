// Texture Asset Badge Component
// Specialized for uploaded Texture assets
import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const TextureBadge = ({ asset, formatAssetNameJSX }) => {
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

  // Helper functions specific to Texture assets
  const getResolution = () => {
    return asset.metadata?.resolution || asset.metadata?.dimensions || 'Unknown';
  };

  const getFormat = () => {
    if (asset.paths?.template_file) {
      return asset.paths.template_file.split('.').pop()?.toUpperCase() || 'Unknown';
    }
    return asset.metadata?.file_format?.toUpperCase() || 'Unknown';
  };

  const getFileSize = () => {
    const totalBytes = asset.file_sizes?.estimated_total_size || 0;
    if (totalBytes === 0) return <span className="text-neutral-500">Calc...</span>;
    
    if (totalBytes < 1024 * 1024) {
      return `${Math.round(totalBytes / 1024)} KB`;
    } else if (totalBytes < 1024 * 1024 * 1024) {
      return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
    } else {
      return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
  };

  const getUVLayout = () => {
    return asset.metadata?.uv_layout || 'Standard';
  };

  const getSeamless = () => {
    const seamless = asset.metadata?.seamless || asset.metadata?.tiling;
    return seamless ? 'Yes' : 'No';
  };

  const getCreatedDate = () => {
    return asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown';
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 z-10">
      {/* Expanded Content Panel - slides up from bottom */}
      <div className={`bg-neutral-800/95 border-t border-l border-r border-neutral-700 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
        isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="p-3">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">🖼️</span>
            <h3 className="text-white font-semibold text-sm truncate">{formatAssetNameJSX(asset)}</h3>
          </div>
          
          {/* Texture Specific Fields - 2x3 layout */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
            <div>
              <span className="text-neutral-400">Type:</span>
              <div className="text-purple-400 font-medium">Texture Map</div>
            </div>
            <div>
              <span className="text-neutral-400">Resolution:</span>
              <div className="text-cyan-300 font-medium truncate">{getResolution()}</div>
            </div>
            <div>
              <span className="text-neutral-400">Format:</span>
              <div className="text-orange-300 font-medium">{getFormat()}</div>
            </div>
            <div>
              <span className="text-neutral-400">Size:</span>
              <div className="text-neutral-300">{getFileSize()}</div>
            </div>
            <div>
              <span className="text-neutral-400">UV Layout:</span>
              <div className="text-blue-300 font-medium">{getUVLayout()}</div>
            </div>
            <div>
              <span className="text-neutral-400">Seamless:</span>
              <div className="text-green-400 font-medium">{getSeamless()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Always visible tab at bottom - Texture themed */}
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
  );
};

export default TextureBadge;