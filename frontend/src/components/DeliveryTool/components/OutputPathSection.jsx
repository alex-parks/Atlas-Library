// frontend/src/components/DeliveryTool/components/OutputPathSection.jsx

import React, { useState } from 'react';
import { FolderOpen, CheckCircle, AlertCircle } from 'lucide-react';

const OutputPathSection = ({ outputPath, setOutputPath }) => {
  const [folderSelected, setFolderSelected] = useState(false);
  const [isSelecting, setIsSelecting] = useState(false);

  const chooseSaveLocation = async () => {
    setIsSelecting(true);

    try {
      // Method 1: Try the File System Access API (modern browsers)
      if ('showDirectoryPicker' in window) {
        try {
          const dirHandle = await window.showDirectoryPicker({
            mode: 'readwrite',
            startIn: 'desktop'
          });

          // Store the directory handle globally for file saving
          window.selectedDirectoryHandle = dirHandle;

          // Set a user-friendly display name
          const displayName = dirHandle.name || 'Selected Folder';
          setOutputPath(displayName);
          setFolderSelected(true);

          console.log('✅ Folder selected:', dirHandle);

          // Test if we can actually write to this folder
          try {
            const testFile = await dirHandle.getFileHandle('test_write.txt', { create: true });
            await testFile.remove(); // Clean up test file
            console.log('✅ Write permission confirmed');
          } catch (writeError) {
            console.warn('⚠️ Write permission uncertain:', writeError);
          }

          setIsSelecting(false);
          return;

        } catch (fsError) {
          console.log('File System Access API failed:', fsError);
          // Fall through to next method
        }
      }

      // Method 2: Fallback using webkitdirectory (works in most browsers)
      const input = document.createElement('input');
      input.type = 'file';
      input.webkitdirectory = true;
      input.multiple = true;

      // Create a promise to handle the file selection
      const fileSelection = new Promise((resolve, reject) => {
        input.onchange = (e) => {
          const files = Array.from(e.target.files);
          if (files.length > 0) {
            resolve(files);
          } else {
            reject(new Error('No files selected'));
          }
        };

        input.oncancel = () => {
          reject(new Error('Selection cancelled'));
        };

        // Trigger file picker
        input.click();
      });

      try {
        const files = await fileSelection;
        const firstFile = files[0];

        // Extract the folder path
        let folderPath = 'Selected Folder';
        if (firstFile.webkitRelativePath) {
          const pathParts = firstFile.webkitRelativePath.split('/');
          if (pathParts.length > 1) {
            pathParts.pop(); // Remove filename
            folderPath = pathParts.join('/');
          }
        }

        // Store reference for fallback saving
        window.selectedFolderFiles = files;
        window.selectedFolderPath = folderPath;

        setOutputPath(folderPath);
        setFolderSelected(true);

        console.log('✅ Folder selected via webkitdirectory:', folderPath);

      } catch (selectionError) {
        if (selectionError.message !== 'Selection cancelled') {
          console.error('File selection failed:', selectionError);
          throw selectionError;
        }
      }

    } catch (error) {
      console.error('All folder selection methods failed:', error);

      // Final fallback - let user type manually
      const manualPath = prompt(
        'Folder selection failed. Please enter the full path where you want to save TTG files:\n\n' +
        'Examples:\n' +
        '• Windows: C:\\Users\\YourName\\Desktop\\TTG_Files\n' +
        '• macOS: /Users/YourName/Desktop/TTG_Files\n' +
        '• Simple: TTG_Files'
      );

      if (manualPath && manualPath.trim()) {
        setOutputPath(manualPath.trim());
        setFolderSelected(true);
        console.log('✅ Manual path entered:', manualPath);
      }
    }

    setIsSelecting(false);
  };

  const clearSelection = () => {
    setOutputPath('');
    setFolderSelected(false);
    delete window.selectedDirectoryHandle;
    delete window.selectedFolderFiles;
    delete window.selectedFolderPath;
  };

  return (
    <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 mb-8">
      <h2 className="text-xl font-semibold text-white mb-4">2. Choose Save Location</h2>

      <div className="space-y-4">
        {/* Main action area */}
        {!folderSelected ? (
          <div className="border-2 border-dashed border-neutral-500 rounded-lg p-8 text-center">
            <FolderOpen className="mx-auto text-neutral-400 mb-4" size={48} />
            <p className="text-white font-medium mb-2">Choose where to save your TTG files</p>
            <p className="text-neutral-400 text-sm mb-4">
              Select a folder on your computer where the generated TTG files will be saved
            </p>

            <button
              onClick={chooseSaveLocation}
              disabled={isSelecting}
              className={`px-6 py-3 rounded-lg flex items-center gap-2 mx-auto transition-colors ${
                isSelecting 
                  ? 'bg-neutral-600 text-neutral-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isSelecting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Selecting...
                </>
              ) : (
                <>
                  <FolderOpen size={18} />
                  Choose Folder
                </>
              )}
            </button>
          </div>
        ) : (
          // Show selected folder
          <div className="bg-green-900/20 border border-green-500 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-green-400" size={24} />
                <div>
                  <p className="text-white font-medium">Save location selected</p>
                  <p className="text-green-400 text-sm">{outputPath}</p>
                  {window.selectedDirectoryHandle && (
                    <p className="text-xs text-green-300">✓ Direct file saving enabled</p>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={chooseSaveLocation}
                  className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded text-sm transition-colors"
                >
                  Change
                </button>
                <button
                  onClick={clearSelection}
                  className="bg-neutral-600 hover:bg-neutral-500 text-white py-2 px-3 rounded text-sm transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Manual entry option */}
        <div className="border-t border-neutral-600 pt-4">
          <p className="text-neutral-400 text-sm mb-2">Or enter path manually:</p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g., C:\Users\YourName\Desktop\TTG_Files"
              value={outputPath}
              onChange={(e) => {
                setOutputPath(e.target.value);
                setFolderSelected(!!e.target.value.trim());
              }}
              className="flex-1 bg-neutral-600 border border-neutral-500 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500 text-sm"
            />
            {outputPath && (
              <button
                onClick={clearSelection}
                className="bg-red-600 hover:bg-red-700 text-white py-2 px-3 rounded text-sm transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-sm">
          {folderSelected ? (
            <>
              <CheckCircle size={16} className="text-green-400" />
              <span className="text-green-400">Ready to save files</span>
            </>
          ) : (
            <>
              <AlertCircle size={16} className="text-yellow-400" />
              <span className="text-yellow-400">Choose a save location to continue</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default OutputPathSection;