// HDRI Asset Card Component
// Full card component for HDRI environment map assets
import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import SequenceThumbnail from '../SequenceThumbnail';

const HDRICard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview }) => {
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
    if (totalBytes === 0) return <span className="text-neutral-500">Calc...</span>;
    
    if (totalBytes < 1024 * 1024) {
      return `${Math.round(totalBytes / 1024)} KB`;
    } else if (totalBytes < 1024 * 1024 * 1024) {
      return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
    } else {
      return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
  };

  const getLocation = () => {
    return asset.metadata?.location || 'Studio';
  };

  const getCreatedDate = () => {
    return asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown';
  };

  const getEnvironmentType = () => {
    // Try to infer environment type from metadata or name
    const name = asset.name?.toLowerCase() || '';
    const location = getLocation().toLowerCase();
    
    if (name.includes('outdoor') || location.includes('outdoor') || name.includes('sky')) {
      return 'Outdoor';
    } else if (name.includes('indoor') || location.includes('indoor') || name.includes('interior')) {
      return 'Indoor';
    } else if (name.includes('studio') || location.includes('studio')) {
      return 'Studio';
    }
    return 'Environment';
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
      <div className={`bg-neutral-800 rounded-lg overflow-hidden border transition-all duration-200 hover:shadow-lg relative ${
        asset.branded || asset.metadata?.branded || asset.metadata?.export_metadata?.branded 
          ? 'border-yellow-600/60 hover:border-yellow-500/80 hover:shadow-yellow-500/5 ring-1 ring-yellow-600/10' 
          : 'border-orange-500/30 hover:border-orange-400 hover:shadow-orange-500/10'
      }`}>
        <div className="aspect-square bg-neutral-700 relative overflow-hidden">
          <SequenceThumbnail
            assetId={asset.id || asset._key}
            assetName={formatAssetName(asset)}
            thumbnailFrame={asset.thumbnail_frame}
            fallbackIcon="🌅"
            onClick={() => openPreview(asset)}
          />
          
          {/* Environment Type Tag - Top Left */}
          <div className="absolute top-2 left-2">
            <span className="px-2 py-1 text-xs rounded font-medium bg-blue-500/20 text-blue-300 backdrop-blur-sm">
              {getEnvironmentType()}
            </span>
          </div>

          {/* Version Tag - Top Center (unique position for HDRI) */}
          <div className="absolute top-2 left-1/2 transform -translate-x-1/2">
            <span className="px-3 py-1 text-xs rounded font-bold bg-orange-500/20 text-orange-300 backdrop-blur-sm">
              {getAssetVersion()}
            </span>
          </div>

          {/* Resolution Tag - Top Right */}
          <div className="absolute top-2 right-2">
            {getResolution() !== 'Unknown' && (
              <span className="px-2 py-1 text-xs rounded font-medium bg-cyan-500/20 text-cyan-300 backdrop-blur-sm">
                {getResolution()}
              </span>
            )}
          </div>

          {/* Location Tag - Bottom Left */}
          <div className="absolute bottom-2 left-2">
            <span className="px-2 py-1 text-xs rounded font-medium bg-green-500/20 text-green-300 backdrop-blur-sm">
              📍 {getLocation()}
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
        </div>

        {/* Asset Information Badge */}
        <div className="absolute bottom-0 left-0 right-0 z-10">
          {/* Expanded Content Panel */}
          <div className={`bg-neutral-800/95 border-t border-l border-r border-neutral-700 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
            isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
          }`}>
            <div className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">🌅</span>
                <h3 className="text-white font-semibold text-sm truncate">{formatAssetNameJSX(asset)}</h3>
              </div>
              
              {/* HDRI Specific Fields - 2x3 layout */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
                <div>
                  <span className="text-neutral-400">Type:</span>
                  <div className="text-orange-400 font-medium">HDRI Map</div>
                </div>
                <div>
                  <span className="text-neutral-400">Resolution:</span>
                  <div className="text-cyan-300 font-medium truncate">{getResolution()}</div>
                </div>
                <div>
                  <span className="text-neutral-400">Format:</span>
                  <div className="text-purple-300 font-medium">{getFormat()}</div>
                </div>
                <div>
                  <span className="text-neutral-400">Size:</span>
                  <div className="text-neutral-300">{getFileSize()}</div>
                </div>
                <div>
                  <span className="text-neutral-400">Environment:</span>
                  <div className="text-blue-300 font-medium">{getEnvironmentType()}</div>
                </div>
                <div>
                  <span className="text-neutral-400">Location:</span>
                  <div className="text-green-400 font-medium truncate">{getLocation()}</div>
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