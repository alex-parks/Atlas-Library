// Texture Asset Badge Component
// Specialized for uploaded Texture assets
import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

const TextureBadge = ({ asset, formatAssetNameJSX }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageList, setImageList] = useState([]);
  const [imageResolutions, setImageResolutions] = useState({});

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
    
    return 'Standard';
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

  // Map texture types to their abbreviations
  const getTextureTypeAbbr = (filename) => {
    const lower = filename.toLowerCase();
    if (lower.includes('base') && lower.includes('color')) return 'BC';
    if (lower.includes('albedo')) return 'BC';
    if (lower.includes('alpha')) return 'A';
    if (lower.includes('metallic') || lower.includes('metalness')) return 'M';
    if (lower.includes('roughness')) return 'R';
    if (lower.includes('normal')) return 'N';
    if (lower.includes('opacity')) return 'O';
    if (lower.includes('displacement') || lower.includes('height')) return 'D';
    return '?';
  };

  // Get texture types from image list
  const getTextureTypes = () => {
    return imageList.map((img, index) => ({
      abbr: getTextureTypeAbbr(img.filename || ''),
      index: index,
      filename: img.filename
    }));
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
          
          {/* Texture Specific Fields - 2x2 layout with UV Layout */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
            <div>
              <span className="text-neutral-400">Type:</span>
              <div className="text-purple-400 font-medium">Texture Map</div>
            </div>
            <div>
              <span className="text-neutral-400">Resolution:</span>
              <div className="text-cyan-300 font-medium truncate">{getCurrentResolution()}</div>
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
          <div className="flex items-center justify-center py-1 px-3">
            <div className="flex items-center gap-2 text-purple-400 hover:text-white transition-colors">
              <span className="text-lg">🖼️</span>
              <span className="text-xs font-medium">Texture Info</span>
              {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
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