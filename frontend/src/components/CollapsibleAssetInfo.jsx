// Collapsible Asset Information Tab Component
import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

const CollapsibleAssetInfo = ({ asset, formatAssetNameJSX }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div 
      className="absolute bottom-0 left-0 right-0 z-10"
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Expanded Content Panel - slides up from bottom */}
      <div className={`bg-neutral-800/95 border-t border-l border-r border-neutral-700 shadow-lg transition-all duration-300 ease-in-out overflow-hidden ${
        isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="p-3">
          <h3 className="text-white font-semibold text-sm mb-2 truncate">{formatAssetNameJSX(asset)}</h3>
          
          {/* Technical Details Grid - 2x3 layout */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-neutral-500">
            <div>
              <span className="text-neutral-400">Render Engine:</span>
              <div className="text-orange-400 font-medium truncate">{asset.metadata?.hierarchy?.render_engine || asset.metadata?.render_engine || 'Unknown'}</div>
            </div>
            <div>
              <span className="text-neutral-400">Size:</span>
              <div className="text-neutral-300">
                {(() => {
                  const totalBytes = asset.file_sizes?.estimated_total_size || 0;
                  
                  if (totalBytes === 0) {
                    return <span className="text-neutral-500">Calc...</span>;
                  }
                  
                  if (totalBytes < 1024 * 1024) {
                    return `${Math.round(totalBytes / 1024)} KB`;
                  } else if (totalBytes < 1024 * 1024 * 1024) {
                    return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
                  } else {
                    return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
                  }
                })()}
              </div>
            </div>
            <div>
              <span className="text-neutral-400">Artist:</span>
              <div className="text-green-400 font-medium truncate">{asset.artist || 'Unknown'}</div>
            </div>
            <div>
              <span className="text-neutral-400">Houdini Ver:</span>
              <div className="text-blue-300 font-medium">{asset.metadata?.houdini_version || 'Unknown'}</div>
            </div>
            <div>
              <span className="text-neutral-400">Asset Ver:</span>
              <div className="text-purple-300 font-medium">
                {(() => {
                  const assetId = asset.id || asset._key || '';
                  if (assetId.length >= 14) {
                    return `v${assetId.substring(11)}`;
                  }
                  return 'v001';
                })()}
              </div>
            </div>
            <div>
              <span className="text-neutral-400">Created:</span>
              <div className="text-cyan-300 font-medium">
                {asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Unknown'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Always visible tab at bottom */}
      <div className="bg-neutral-800/95 border border-neutral-700 rounded-t-lg shadow-lg cursor-pointer hover:bg-neutral-700/95 transition-all duration-200">
        <div className="flex items-center justify-center py-1 px-3">
          <div className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors">
            <span className="text-xs font-medium">Asset Info</span>
            {isExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollapsibleAssetInfo;