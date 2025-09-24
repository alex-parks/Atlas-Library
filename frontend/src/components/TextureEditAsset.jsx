// TextureEditAsset Component
// Specialized edit modal for texture assets with texture-specific options
import React, { useState } from 'react';
import { X, Save, Plus, Trash2, Copy, RefreshCw, Palette, Layers, Settings } from 'lucide-react';
import config from '../utils/config';

const TextureEditAsset = ({ 
  isOpen, 
  onClose, 
  asset, 
  onSave,
  apiEndpoint = `${config.backendUrl}/api/v1/assets`
}) => {
  const [editFormData, setEditFormData] = useState({
    name: asset?.name || '',
    description: asset?.description || '',
    tags: asset?.tags || [],
    texture_type: asset?.texture_type || 'seamless',
    seamless: asset?.seamless || false,
    uv_tile: asset?.uv_tile || false,
    alpha_subcategory: asset?.alpha_subcategory || '',
    // Texture-specific fields
    resolution: asset?.resolution || '',
    format: asset?.metadata?.format || '',
    channels: asset?.metadata?.channels || 3,
    bit_depth: asset?.metadata?.bit_depth || 8,
    color_space: asset?.metadata?.color_space || 'sRGB',
    tiling_method: asset?.metadata?.tiling_method || 'repeat',
    material_type: asset?.metadata?.material_type || '',
  });
  
  const [newTagInput, setNewTagInput] = useState('');
  const [previewFilePath, setPreviewFilePath] = useState('');
  const [uploadingPreview, setUploadingPreview] = useState(false);
  const [saving, setSaving] = useState(false);

  if (!isOpen || !asset) return null;

  const handleInputChange = (field, value) => {
    setEditFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddTag = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Prevent form submission
      if (newTagInput.trim()) {
        const newTag = newTagInput.trim().toLowerCase();
        if (!editFormData.tags.includes(newTag)) {
          setEditFormData({
            ...editFormData,
            tags: [...editFormData.tags, newTag]
          });
        }
        setNewTagInput('');
      }
    }
  };

  const removeEditTag = (tagToRemove) => {
    setEditFormData({
      ...editFormData,
      tags: editFormData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const handleUploadPreview = async () => {
    console.log('🚀 PREVIEW UPLOAD: Starting upload process...');
    
    if (!previewFilePath.trim()) {
      alert('❌ Please enter a file path for the preview image');
      return;
    }

    // Basic file path validation
    const allowedExtensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr'];
    const hasValidExtension = allowedExtensions.some(ext => 
      previewFilePath.toLowerCase().endsWith(ext)
    );
    
    if (!hasValidExtension) {
      alert('❌ Please enter a valid image file path (JPG, PNG, TIFF, or EXR)');
      return;
    }

    setUploadingPreview(true);
    try {
      const response = await fetch(`${apiEndpoint}/${asset.id}/update-preview-from-path`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: previewFilePath
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert('✅ Preview image updated successfully!');
        setPreviewFilePath('');
        
        console.log(`✅ PREVIEW UPLOAD: Completed for asset ${asset.id}`);
      } else {
        const errorData = await response.json();
        alert(`❌ Failed to update preview image: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error uploading preview image:', error);
      alert(`❌ Error uploading preview image: ${error.message}`);
    } finally {
      setUploadingPreview(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${apiEndpoint}/${asset.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editFormData)
      });

      if (response.ok) {
        const updatedAsset = await response.json();
        onSave?.(updatedAsset);
        onClose();
        alert('✅ Texture asset updated successfully!');
      } else {
        throw new Error('Failed to update asset');
      }
    } catch (error) {
      console.error('Error updating asset:', error);
      alert('❌ Failed to update asset. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-700">
          <div className="flex items-center gap-3">
            <Palette className="text-cyan-400" size={24} />
            <h2 className="text-xl font-semibold text-white">Edit Texture Asset</h2>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          <form onSubmit={async (e) => {
            e.preventDefault();
            
            try {
              // Only update editable fields
              const updateData = {
                name: editFormData.name,
                tags: editFormData.tags || []
              };
              
              // Send PATCH request to update asset
              const response = await fetch(`${apiEndpoint}/${asset.id}`, {
                method: 'PATCH',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
              });
              
              if (response.ok) {
                // Close modal
                onClose();
                
                // Show success message
                alert('✅ Texture asset updated successfully!');
                
                // Call onSave callback to reload assets
                if (onSave) {
                  const updatedAsset = await response.json();
                  onSave(updatedAsset);
                }
              } else {
                const error = await response.json();
                console.error('Backend error response:', error);
                alert(`❌ Failed to update texture asset: ${error.detail || 'Unknown error'}`);
              }
            } catch (error) {
              console.error('Error updating texture asset:', error);
              alert(`❌ Error updating texture asset: ${error.message}`);
            }
          }} className="space-y-4">
            {/* Asset Name */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Asset Name
              </label>
              <input
                type="text"
                value={editFormData.name || ''}
                onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
                className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
                placeholder="Enter asset name"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Tags
              </label>
              
              {/* Current Tags as Bubbles */}
              {editFormData.tags && editFormData.tags.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 mb-3 p-3 bg-neutral-700/50 border border-neutral-600 rounded-lg">
                  <span className="text-xs text-neutral-400 font-medium">Current Tags:</span>
                  {editFormData.tags.map((tag, index) => (
                    <div key={`${tag}-${index}`} className="flex items-center gap-1 bg-green-600/20 border border-green-500/60 rounded-full px-3 py-1 text-sm backdrop-blur-sm">
                      <span className="text-green-200 font-medium">{tag}</span>
                      <button
                        type="button"
                        onClick={() => removeEditTag(tag)}
                        className="text-green-300 hover:text-white transition-colors p-0.5 rounded-full hover:bg-green-500/20"
                        title={`Remove "${tag}" tag`}
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add New Tag Input */}
              <input
                type="text"
                value={newTagInput}
                onChange={(e) => setNewTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-green-400 focus:bg-neutral-600 transition-all"
                placeholder="Type a tag and press Enter to add..."
              />
              <p className="text-xs text-neutral-400 mt-1">Press Enter to add tags. Click the X on existing tags to remove them.</p>
            </div>

            {/* Preview Image Update - Only show for Texture Sets */}
            {asset.asset_type === 'Textures' && asset.category === 'Texture Sets' && (
              <div className="border-t border-neutral-700 pt-4">
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Update Preview Image
                </label>
                <p className="text-xs text-neutral-400 mb-3">
                  Enter the file path to a new preview image for this texture set. Supported formats: JPG, PNG, TIFF, EXR
                </p>
                
                <div className="space-y-3">
                  {/* File Path Input */}
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={previewFilePath}
                      onChange={(e) => setPreviewFilePath(e.target.value)}
                      className="w-full bg-neutral-700 border border-neutral-600 rounded-lg px-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-green-400 focus:bg-neutral-600 transition-all"
                      placeholder="/path/to/preview/image.jpg"
                    />
                    <p className="text-xs text-neutral-500">
                      Enter the full path to the image file you want to use as preview
                    </p>
                  </div>
                  
                  {/* Upload Button */}
                  {previewFilePath.trim() && (
                    <button
                      type="button"
                      onClick={handleUploadPreview}
                      disabled={uploadingPreview}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors disabled:cursor-not-allowed"
                    >
                      {uploadingPreview ? (
                        <>
                          <RefreshCw size={16} className="animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <RefreshCw size={16} />
                          Update Preview Image
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg flex items-center gap-2 transition-colors"
              >
                <Save size={16} />
                Save Changes
              </button>
              <button
                type="button"
                onClick={onClose}
                className="bg-neutral-700 hover:bg-neutral-600 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TextureEditAsset;