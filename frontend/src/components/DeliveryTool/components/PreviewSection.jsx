// frontend/src/components/DeliveryTool/components/PreviewSection.jsx

import React from 'react';
import { Eye, Play, FileText } from 'lucide-react';

const PreviewSection = ({
  cleanedData,
  enabledGroups,
  enabledDeliverables,
  showPreview,
  setShowPreview,
  isProcessing,
  generateAllTTGFiles
}) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">4. Preview & Generate TTG Files</h2>
        <div className="flex gap-3">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Eye size={18} />
            {showPreview ? 'Hide Preview' : 'Show Preview'}
          </button>
          <button
            onClick={generateAllTTGFiles}
            disabled={isProcessing}
            className={`px-6 py-2 rounded-lg flex items-center gap-2 transition-colors ${
              isProcessing
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Generating...
              </>
            ) : (
              <>
                <Play size={18} />
                Generate All TTG Files
              </>
            )}
          </button>
        </div>
      </div>

      {/* File Preview */}
      {showPreview && (
        <div className="bg-neutral-600 rounded-lg p-4 mb-6">
          <h3 className="text-white font-medium mb-3">Files that will be generated:</h3>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {(() => {
              let previewDeliverables = [];
              cleanedData.deliverable_groups.forEach(group => {
                if (enabledGroups.has(group.groupTitle)) {
                  previewDeliverables.push(...group.deliverables);
                } else {
                  const individualEnabled = group.deliverables.filter(d => enabledDeliverables.has(d.id));
                  previewDeliverables.push(...individualEnabled);
                }
              });

              return previewDeliverables.map((delivery, index) => {
                const safeTitle = delivery.video_title.replace(/[^a-zA-Z0-9\-_]/g, '_');
                const safePlatform = delivery.platform.replace(/[^a-zA-Z0-9\-_]/g, '_');
                const filename = `${safeTitle}_${safePlatform}_${delivery.suggested_slate_format}_slate.ttg`;

                return (
                  <div key={index} className="flex items-center justify-between bg-neutral-500 rounded p-3">
                    <div className="flex items-center gap-3">
                      <FileText className="text-blue-400" size={16} />
                      <span className="text-white text-sm font-mono">{filename}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="text-neutral-400">{delivery.ship_date}</span>
                      <span className={`px-2 py-1 rounded text-white ${
                        delivery.shipped ? 'bg-green-600' : 'bg-yellow-600'
                      }`}>
                        {delivery.shipped ? 'Shipped' : 'Not Shipped'}
                      </span>
                      <span className={`px-2 py-1 rounded text-white ${
                        delivery.suggested_slate_format === '16x9' ? 'bg-blue-600' :
                        delivery.suggested_slate_format === '9x16' ? 'bg-green-600' :
                        delivery.suggested_slate_format === '1x1' ? 'bg-purple-600' :
                        'bg-orange-600'
                      }`}>
                        {delivery.suggested_slate_format}
                      </span>
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviewSection;