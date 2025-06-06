// frontend/src/components/DeliveryTool/utils/fileUtils.js

/**
 * Check if folder selection is available in the current browser
 */
export const isFolderSelectionSupported = () => {
  return 'showDirectoryPicker' in window;
};

/**
 * Get a user-friendly description of the current save method
 */
export const getSaveMethodDescription = () => {
  if (window.selectedDirectoryHandle) {
    return 'Files will be saved directly to your selected folder';
  } else {
    return 'Files will be downloaded to your Downloads folder';
  }
};

/**
 * Format bytes to human readable size
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};