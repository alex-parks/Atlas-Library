// frontend/src/components/DeliveryTool/components/OutputPathSection.jsx

import React from 'react';
import { FolderOpen, CheckCircle, AlertCircle } from 'lucide-react';

const OutputPathSection = ({ outputPath, setOutputPath }) => {
  const selectOutputFolder = async () => {
    try {
      // Check if the File System Access API is available
      if ('showDirectoryPicker' in window) {
        const dirHandle = await window.showDirectoryPicker({
          mode: 'readwrite'
        });

        // Store the handle for later use
        window.selectedDirectoryHandle = dirHandle;

        // Set a user-friendly display name
        setOutputPath(dirHandle.name);

        console.log('✅ Folder selected:', dirHandle.name);
        return;
      } else {
        // Fallback for browsers that don't support showDirectoryPicker
        alert('Your browser doesn\'t support folder selection. Please enter the path manually or use Chrome/Edge.');
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // User cancelled the dialog
        console.log('User cancelled folder selection');
        return;
      }
      console.error('Error selecting folder:', error);
      alert('Failed to select folder. Please try again or enter the path manually.');
    }
  };

  const clearPath = () => {
    setOutputPath('');
    delete window.selectedDirectoryHandle;
    console.log('Path cleared');
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
              placeholder="Click 'Browse' to select folder or enter path manually..."
              value={outputPath}
              onChange={(e) => {
                setOutputPath(e.target.value);
                // Clear the directory handle if user types manually
                delete window.selectedDirectoryHandle;
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

        {/* Browser Compatibility Notice */}
        {!window.showDirectoryPicker && (
          <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="text-yellow-400" size={20} />
              <p className="text-yellow-400 text-sm">
                Folder selection requires Chrome or Edge browser. You can still enter the path manually.
              </p>
            </div>
          </div>
        )}

        {/* Status Display */}
        {outputPath ? (
          <div className="bg-green-900/20 border border-green-500 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="text-green-400" size={20} />
              <span className="text-green-400 font-medium">Save location:</span>
              <span className="text-white">{outputPath}</span>
            </div>
            {window.selectedDirectoryHandle && (
              <p className="text-green-300 text-xs mt-1">
                ✅ Folder access granted - files will save directly
              </p>
            )}
            {!window.selectedDirectoryHandle && outputPath && (
              <p className="text-yellow-300 text-xs mt-1">
                ⚠️ Manual path entered - files will download to Downloads folder
              </p>
            )}
          </div>
        ) : (
          <div className="bg-neutral-600 border border-neutral-500 rounded-lg p-3">
            <p className="text-neutral-300 text-sm">
              Select a folder where TTG files will be saved
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OutputPathSection;