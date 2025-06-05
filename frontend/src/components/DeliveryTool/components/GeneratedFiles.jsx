// frontend/src/components/DeliveryTool/components/GeneratedFiles.jsx

import React, { useState } from 'react';
import { Download, FileText, Eye, CheckCircle, AlertTriangle, FolderOpen } from 'lucide-react';

const GeneratedFiles = ({ ttgFiles, outputPath, setPreviewSlate }) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadStatus, setDownloadStatus] = useState(null);

  const downloadSingleTTG = async (ttgFile) => {
    // If we have a selected folder, save directly there
    if (window.selectedDirectoryHandle) {
      try {
        const fileHandle = await window.selectedDirectoryHandle.getFileHandle(
          ttgFile.filename,
          { create: true }
        );

        const writable = await fileHandle.createWritable();
        await writable.write(ttgFile.content);
        await writable.close();

        setDownloadStatus({
          type: 'success',
          message: `✅ ${ttgFile.filename} saved to ${outputPath}`
        });

        setTimeout(() => setDownloadStatus(null), 3000);
        return;

      } catch (error) {
        console.error('❌ Direct save failed:', error);
      }
    }

    // Fallback to browser download
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

    setDownloadStatus({
      type: 'info',
      message: `📥 ${ttgFile.filename} downloaded to Downloads folder`
    });

    setTimeout(() => setDownloadStatus(null), 3000);
  };

  const downloadAllTTG = async () => {
    if (ttgFiles.length === 0) return;

    setDownloading(true);
    setDownloadStatus(null);

    // If we have a selected folder handle, save directly there
    if (window.selectedDirectoryHandle) {
      try {
        let successCount = 0;
        let failureCount = 0;

        for (const file of ttgFiles) {
          try {
            const fileHandle = await window.selectedDirectoryHandle.getFileHandle(
              file.filename,
              { create: true }
            );

            const writable = await fileHandle.createWritable();
            await writable.write(file.content);
            await writable.close();

            successCount++;

          } catch (error) {
            console.error(`❌ Failed to save ${file.filename}:`, error);
            failureCount++;
          }
        }

        setDownloading(false);

        if (successCount === ttgFiles.length) {
          setDownloadStatus({
            type: 'success',
            message: `✅ Successfully saved all ${successCount} TTG files to ${outputPath}!`
          });
        } else {
          setDownloadStatus({
            type: 'success',
            message: `✅ Saved ${successCount} files, ${failureCount} failed. Check ${outputPath} folder.`
          });
        }

        setTimeout(() => setDownloadStatus(null), 5000);
        return;

      } catch (error) {
        console.error('❌ Bulk direct save failed:', error);
      }
    }

    // Fallback: Download individual TTG files
    try {
      let successCount = 0;

      for (let i = 0; i < ttgFiles.length; i++) {
        const file = ttgFiles[i];

        const blob = new Blob([file.content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');

        a.href = url;
        a.download = file.filename;
        a.style.display = 'none';
        a.target = '_self';

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        successCount++;

        // Small delay between downloads to avoid browser blocking
        if (i < ttgFiles.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      setDownloadStatus({
        type: 'success',
        message: outputPath
          ? `✅ Downloaded ${successCount} TTG files. Move them to: ${outputPath}`
          : `✅ Downloaded ${successCount} TTG files to Downloads folder`
      });

    } catch (error) {
      console.error('❌ Individual downloads failed:', error);
      setDownloadStatus({
        type: 'error',
        message: `❌ Download failed: ${error.message}`
      });
    } finally {
      setDownloading(false);
      setTimeout(() => setDownloadStatus(null), 5000);
    }
  };

  return (
    <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">
          Generated TTG Files ({ttgFiles.length})
        </h2>
        <button
          onClick={downloadAllTTG}
          disabled={downloading}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
            downloading 
              ? 'bg-neutral-600 text-neutral-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-700 text-white'
          }`}
        >
          {downloading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Saving Files...
            </>
          ) : (
            <>
              <Download size={18} />
              Save All TTG Files
            </>
          )}
        </button>
      </div>

      {/* Status Message */}
      {downloadStatus && (
        <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
          downloadStatus.type === 'success' ? 'bg-green-900/20 border border-green-500' :
          downloadStatus.type === 'error' ? 'bg-red-900/20 border border-red-500' :
          'bg-blue-900/20 border border-blue-500'
        }`}>
          {downloadStatus.type === 'success' && <CheckCircle size={18} className="text-green-400" />}
          {downloadStatus.type === 'error' && <AlertTriangle size={18} className="text-red-400" />}
          {downloadStatus.type === 'info' && <Download size={18} className="text-blue-400" />}
          <span className={`text-sm ${
            downloadStatus.type === 'success' ? 'text-green-300' :
            downloadStatus.type === 'error' ? 'text-red-300' :
            'text-blue-300'
          }`}>
            {downloadStatus.message}
          </span>
        </div>
      )}

      {/* Save method info */}
      <div className="mb-4 p-3 bg-neutral-600 rounded-lg">
        <div className="flex items-center gap-2">
          <FolderOpen size={16} className="text-neutral-400" />
          <p className="text-sm text-neutral-300">
            {window.selectedDirectoryHandle
              ? `💾 Files will save directly to: ${outputPath || 'selected folder'}`
              : `📥 Files will download individually${outputPath ? ` (move to: ${outputPath})` : ' to Downloads folder'}`
            }
          </p>
        </div>
      </div>

      {/* File list */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {ttgFiles.map((file) => (
          <div key={file.id} className="bg-neutral-600 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <FileText className="text-blue-400" size={24} />
              <div>
                <h3 className="text-white font-medium text-sm">{file.filename}</h3>
                <p className="text-neutral-400 text-xs">
                  {file.delivery.video_title} • {file.delivery.platform} • {file.template} • {Math.round(file.size / 1024)} KB
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setPreviewSlate(file)}
                className="bg-neutral-500 hover:bg-neutral-400 text-white p-2 rounded-lg transition-colors"
                title="Preview"
              >
                <Eye size={16} />
              </button>
              <button
                onClick={() => downloadSingleTTG(file)}
                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors"
                title="Save Single File"
              >
                <Download size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Summary info */}
      <div className="mt-4 pt-4 border-t border-neutral-600">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-neutral-400">
          <div>
            <span className="block">Total Files:</span>
            <span className="text-white font-medium">{ttgFiles.length}</span>
          </div>
          <div>
            <span className="block">Total Size:</span>
            <span className="text-white font-medium">
              {Math.round(ttgFiles.reduce((sum, file) => sum + file.size, 0) / 1024)} KB
            </span>
          </div>
          <div>
            <span className="block">Formats:</span>
            <span className="text-white font-medium">
              {[...new Set(ttgFiles.map(f => f.delivery.suggested_slate_format))].join(', ')}
            </span>
          </div>
          <div>
            <span className="block">Save Location:</span>
            <span className="text-white font-medium">
              {window.selectedDirectoryHandle ? outputPath : 'Downloads folder'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeneratedFiles;