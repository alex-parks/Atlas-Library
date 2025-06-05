// frontend/src/components/DeliveryTool/components/PreviewModal.jsx

import React from 'react';
import { Download } from 'lucide-react';

const PreviewModal = ({
  previewSlate,
  previewFormat,
  setPreviewFormat,
  setPreviewSlate,
  parseTTGContent
}) => {
  const downloadSingleTTG = (ttgFile) => {
    const blob = new Blob([ttgFile.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = ttgFile.filename;
    a.style.display = 'none';
    a.target = '_self';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white">Preview: {previewSlate.filename}</h3>
          <div className="flex items-center gap-4">
            {/* Format Toggle Switch */}
            <div className="flex items-center gap-3">
              <span className={`text-sm ${previewFormat === 'readable' ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                Readable
              </span>
              <button
                onClick={() => setPreviewFormat(previewFormat === 'ttg' ? 'readable' : 'ttg')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  previewFormat === 'ttg' ? 'bg-blue-600' : 'bg-neutral-500'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    previewFormat === 'ttg' ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`text-sm ${previewFormat === 'ttg' ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                TTG
              </span>
            </div>
            <button
              onClick={() => setPreviewSlate(null)}
              className="text-neutral-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="bg-neutral-800 rounded-lg p-4">
          {previewFormat === 'readable' ? (
            <div className="space-y-4">
              {(() => {
                const parsedData = parseTTGContent(previewSlate.content);
                return Object.entries(parsedData).map(([label, value]) => (
                  <div key={label} className="flex items-start gap-4 py-2 border-b border-neutral-600 last:border-b-0">
                    <div className="w-32 flex-shrink-0">
                      <span className="text-blue-400 font-medium text-sm">{label}:</span>
                    </div>
                    <div className="flex-1">
                      <span className="text-white text-sm">"{value}"</span>
                    </div>
                  </div>
                ));
              })()}

              {/* Additional Technical Info */}
              <div className="mt-6 pt-4 border-t border-neutral-600">
                <h4 className="text-neutral-400 text-xs font-medium mb-3 uppercase tracking-wide">Technical Details</h4>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Template:</span>
                    <span className="text-purple-400">{previewSlate.template}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">File Size:</span>
                    <span className="text-green-400">{Math.round(previewSlate.size / 1024)} KB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Aspect Ratio:</span>
                    <span className="text-orange-400">{previewSlate.delivery.suggested_slate_format}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Ship Date:</span>
                    <span className="text-cyan-400">{previewSlate.delivery.ship_date}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap max-h-96 overflow-auto">
              {previewSlate.content}
            </pre>
          )}
        </div>

        <div className="mt-4 flex gap-2">
          <button
            onClick={() => downloadSingleTTG(previewSlate)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Download size={16} />
            Download TTG
          </button>
          {previewFormat === 'readable' && (
            <button
              onClick={() => {
                const parsedData = parseTTGContent(previewSlate.content);
                const readableText = Object.entries(parsedData)
                  .map(([label, value]) => `${label}: "${value}"`)
                  .join('\n');

                navigator.clipboard.writeText(readableText).then(() => {
                  console.log('Readable format copied to clipboard');
                });
              }}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg flex items-center gap-2"
            >
              📋 Copy Readable
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PreviewModal;