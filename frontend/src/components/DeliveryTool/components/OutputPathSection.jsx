// frontend/src/components/DeliveryTool/components/OutputPathSection.jsx

import React, { useRef } from 'react';
import { FolderOpen, CheckCircle } from 'lucide-react';

const OutputPathSection = ({ outputPath, setOutputPath }) => {
  const folderInputRef = useRef(null);

  const selectOutputFolder = async () => {
    try {
      if ('showDirectoryPicker' in window) {
        const dirHandle = await window.showDirectoryPicker();
        setOutputPath(dirHandle.name);
        window.selectedDirectoryHandle = dirHandle;
        window.hasFolderSelected = true;
        return;
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        return;
      }
      // If showDirectoryPicker fails, fall back to file input
    }

    // Fallback to webkitdirectory
    folderInputRef.current?.click();
  };

  const handleFolderSelect = (event) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const firstFile = files[0];
      let folderPath = '';

      if (firstFile.webkitRelativePath) {
        const pathParts = firstFile.webkitRelativePath.split('/');
        pathParts.pop(); // Remove filename to get folder path
        folderPath = pathParts.join('/');
      }

      if (!folderPath) {
        folderPath = 'Selected Folder';
      }

      setOutputPath(folderPath);
      window.selectedFolderPath = folderPath;
      window.hasFolderSelected = true; // Flag for manual paths
    }
  };

  const clearPath = () => {
    setOutputPath('');
    delete window.selectedDirectoryHandle;
    delete window.selectedFolderPath;
    if (folderInputRef.current) {
      folderInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 mb-8">
      <h2 className="text-xl font-semibold text-white mb-4">2. Choose Save Location</h2>

      <div className="space-y-4">
        {/* Folder Selection */}
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Click 'Browse' to select output folder or type path manually..."
              value={outputPath}
              onChange={(e) => {
                setOutputPath(e.target.value);
                // Set flag when user types manual path
                if (e.target.value.trim()) {
                  window.selectedFolderPath = e.target.value.trim();
                  window.hasFolderSelected = true;
                } else {
                  delete window.selectedFolderPath;
                  delete window.hasFolderSelected;
                }
              }}
              className="w-full bg-neutral-600 border border-neutral-500 rounded-lg px-4 py-3 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={selectOutputFolder}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg flex items-center gap-2 transition-colors text-white font-medium"
          >
            <FolderOpen size={18} />
            Browse
          </button>
          {outputPath && (
            <button
              onClick={clearPath}
              className="bg-red-600 hover:bg-red-700 px-4 py-3 rounded-lg text-white font-medium"
            >
              Clear
            </button>
          )}
        </div>

        {/* Hidden folder input - modified to show "Open" like CSV upload */}
        <input
          ref={folderInputRef}
          type="file"
          onChange={handleFolderSelect}
          className="hidden"
          webkitdirectory=""
          directory=""
          multiple
        />

        {/* Status Display */}
        {outputPath ? (
          <div className="bg-green-900/20 border border-green-500 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="text-green-400" size={20} />
              <span className="text-green-400 font-medium">Save location:</span>
              <span className="text-white">{outputPath}</span>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-3">
            <p className="text-yellow-400 text-sm">
              Select a folder to save TTG files
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OutputPathSection;