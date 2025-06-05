// frontend/src/components/DeliveryTool/utils/fileUtils.js

/**
 * Download a single TTG file using the selected folder or fallback to browser download
 */
export const downloadSingleTTG = async (ttgFile) => {
  // Method 1: Try to save directly to the selected folder
  if (window.selectedDirectoryHandle) {
    try {
      const fileHandle = await window.selectedDirectoryHandle.getFileHandle(
        ttgFile.filename,
        { create: true }
      );

      const writable = await fileHandle.createWritable();
      await writable.write(ttgFile.content);
      await writable.close();

      console.log(`✅ File saved directly: ${ttgFile.filename}`);
      return { success: true, method: 'direct', filename: ttgFile.filename };

    } catch (error) {
      console.warn('Direct file save failed, falling back to download:', error);
    }
  }

  // Method 2: Fallback to browser download
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

  console.log(`📥 File downloaded: ${ttgFile.filename}`);
  return { success: true, method: 'download', filename: ttgFile.filename };
};

/**
 * Download all TTG files using the selected folder or create a ZIP
 */
export const downloadAllTTG = async (ttgFiles, outputPath) => {
  if (!ttgFiles || ttgFiles.length === 0) {
    throw new Error('No files to download');
  }

  // Method 1: Try to save all files directly to the selected folder
  if (window.selectedDirectoryHandle) {
    try {
      let successCount = 0;
      const results = [];

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
          results.push({ filename: file.filename, success: true });

        } catch (error) {
          console.error(`Failed to save ${file.filename}:`, error);
          results.push({ filename: file.filename, success: false, error: error.message });
        }
      }

      if (successCount === ttgFiles.length) {
        return {
          success: true,
          method: 'direct',
          message: `Successfully saved ${successCount} TTG files to your selected folder!`,
          results
        };
      } else {
        return {
          success: true,
          method: 'partial',
          message: `Saved ${successCount} of ${ttgFiles.length} files. Some files may have failed.`,
          results
        };
      }

    } catch (error) {
      console.error('Direct folder save failed:', error);
      // Fall through to ZIP method
    }
  }

  // Method 2: Create and download a ZIP file
  try {
    // Import JSZip dynamically
    const JSZip = (await import('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js')).default;
    const zip = new JSZip();

    // Add each TTG file to the zip
    ttgFiles.forEach(file => {
      zip.file(file.filename, file.content);
    });

    // Generate and download the zip
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(zipBlob);
    const a = document.createElement('a');

    a.href = url;
    a.download = `TTG_Files_${new Date().toISOString().split('T')[0]}.zip`;
    a.style.display = 'none';

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    const message = outputPath
      ? `ZIP file downloaded with ${ttgFiles.length} TTG files. Please extract to: ${outputPath}`
      : `ZIP file downloaded with ${ttgFiles.length} TTG files.`;

    return {
      success: true,
      method: 'zip',
      message
    };

  } catch (error) {
    console.error('ZIP creation failed:', error);
    throw new Error('Failed to create ZIP file. Please try again or contact support.');
  }
};

/**
 * Check if folder selection is available in the current browser
 */
export const isFolderSelectionSupported = () => {
  return 'showDirectoryPicker' in window || 'webkitdirectory' in document.createElement('input');
};

/**
 * Get a user-friendly description of the current save method
 */
export const getSaveMethodDescription = () => {
  if (window.selectedDirectoryHandle) {
    return 'Files will be saved directly to your selected folder';
  } else if (window.selectedFolderPath) {
    return 'Files will be downloaded (may need manual placement)';
  } else {
    return 'Files will be downloaded as a ZIP file';
  }
};