// frontend/src/components/DeliveryTool/components/OutputPathSection.jsx

import React from 'react';
import { FolderOpen, CheckCircle } from 'lucide-react';

const OutputPathSection = ({ outputPath, setOutputPath }) => {

  const selectFolder = async () => {
    console.log('🔄 Starting folder selection...');

    try {
      // Method 1: Try modern File System Access API first
      if ('showDirectoryPicker' in window) {
        console.log('📁 Using showDirectoryPicker API');

        const dirHandle = await window.showDirectoryPicker({
          mode: 'readwrite'
        });

        console.log('✅ Directory handle received:', dirHandle);

        // Store the handle globally for file saving
        window.selectedDirectoryHandle = dirHandle;

        // Set the display path
        const folderName = dirHandle.name;
        console.log('📂 Setting path to:', folderName);
        setOutputPath(folderName);

        console.log('✅ Path set successfully');
        return;
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('❌ User cancelled folder selection');
        return;
      }
      console.log('⚠️ showDirectoryPicker failed:', error);
    }

    // Method 2: Fallback to webkitdirectory
    console.log('📁 Using webkitdirectory fallback');

    const input = document.createElement('input');
    input.type = 'file';
    input.webkitdirectory = true;
    input.multiple = true;

    const handleFiles = (event) => {
      const files = event.target.files;
      console.log('📂 Files received:', files.length);

      if (files && files.length > 0) {
        const firstFile = files[0];
        console.log('📄 First file:', firstFile);
        console.log('📄 WebkitRelativePath:', firstFile.webkitRelativePath);

        // Extract folder path
        let folderPath = '';
        if (firstFile.webkitRelativePath) {
          const pathParts = firstFile.webkitRelativePath.split('/');
          console.log('🗂️ Path parts:', pathParts);

          if (pathParts.length > 1) {
            pathParts.pop(); // Remove filename
            folderPath = pathParts.join('/');
          } else {
            folderPath = pathParts[0] || 'Selected Folder';
          }
        }

        if (!folderPath) {
          folderPath = 'Selected Folder';
        }

        console.log('📂 Setting folder path to:', folderPath);
        setOutputPath(folderPath);

        // Store for download functionality
        window.selectedFolderFiles = Array.from(files);
        window.selectedFolderPath = folderPath;

        console.log('✅ Folder selection complete');
      }
    };

    input.addEventListener('change', handleFiles);
    input.click();
  };

  const clearPath = () => {
    console.log('🗑️ Clearing output path');
    setOutputPath('');
    delete window.selectedDirectoryHandle;
    delete window.selectedFolderFiles;
    delete window.selectedFolderPath;
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
              placeholder="No folder selected - click 'Select Folder' or type path manually"
              value={outputPath}
              onChange={(e) => {
                console.log('✏️ Manual path entered:', e.target.value);
                setOutputPath(e.target.value);
              }}
              className="w-full bg-neutral-600 border border-neutral-500 rounded-lg px-4 py-3 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={selectFolder}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg flex items-center gap-2 transition-colors text-white font-medium"
          >
            <FolderOpen size={18} />
            Select Folder
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

        {/* Status Display */}
        {outputPath ? (
          <div className="bg-green-900/20 border border-green-500 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="text-green-400" size={20} />
              <span className="text-green-400 font-medium">Save location set:</span>
              <span className="text-white">{outputPath}</span>
              {window.selectedDirectoryHandle && (
                <span className="text-green-300 text-sm ml-2">✓ Direct save enabled</span>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-3">
            <p className="text-yellow-400 text-sm">
              ⚠️ Please select a save location - files will save as individual TTG files
            </p>
          </div>
        )}

        {/* Debug Info */}
        <div className="text-xs text-neutral-500">
          <p className="mb-1">💡 Debug Info:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Current path: {outputPath || 'None'}</li>
            <li>Directory handle: {window.selectedDirectoryHandle ? 'Available' : 'Not available'}</li>
            <li>Browser support: {('showDirectoryPicker' in window) ? 'Modern API' : 'Legacy webkitdirectory'}</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default OutputPathSection;