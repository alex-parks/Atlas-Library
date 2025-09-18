// Texture Set Sequence Component - Shows Preview first, then textures in BC, R, M, N, O, D order
import React, { useState, useEffect, useRef } from 'react';

const TextureSetSequence = ({ 
  assetId, 
  assetName, 
  asset = {},
  fallbackIcon = '🖼️',
  className = "w-full h-full object-cover",
  onClick = () => {},
  externalFrameIndex = null,
  hideZoomMessage = false,
  onFrameChange = () => {}
}) => {
  const [sequenceData, setSequenceData] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isHovering, setIsHovering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const containerRef = useRef(null);
  
  // Zoom functionality state
  const [zoom, setZoom] = useState(1);
  const [zoomCenter, setZoomCenter] = useState({ x: 0.5, y: 0.5 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const imageRef = useRef(null);

  // Fetch texture set sequence data when component mounts
  useEffect(() => {
    if (!assetId) {
      setLoading(false);
      setError(true);
      return;
    }

    const fetchTextureSetSequence = async () => {
      try {
        // Build the texture sequence with preview first, then BC, R, M, N, O, D order
        const frames = [];
        let frameIndex = 0;
        
        // First, check what images are available and find preview
        let previewIndex = -1;
        try {
          const textureResponse = await fetch(`http://localhost:8000/api/v1/assets/${assetId}/texture-images`);
          if (textureResponse.ok) {
            const textureData = await textureResponse.json();
            
            // Find preview image in the list
            previewIndex = textureData.images?.findIndex(img => 
              img.is_preview || 
              img.filename?.toLowerCase().includes('preview') ||
              img.path?.toLowerCase().includes('preview')
            ) ?? -1;
            
            // If we found a preview, add it first
            if (previewIndex !== -1) {
              const cacheBust = `_t=${Date.now()}`;
              frames.push({
                index: frameIndex++,
                type: 'preview',
                name: 'Preview',
                url: `/api/v1/assets/${assetId}/texture-image/${previewIndex}?${cacheBust}`,
                description: 'Preview Image'
              });
              console.log(`Added preview image at index ${previewIndex}`);
            }
          }
        } catch (error) {
          console.log('Preview check error:', error);
          // Preview doesn't exist, continue
        }
        
        // Then, add texture images in BC, R, M, N, O, D order (but not the preview we already added)
        try {
          // Re-fetch texture data if we didn't get it in the preview check
          let textureData;
          if (previewIndex === -1) {
            const textureResponse = await fetch(`http://localhost:8000/api/v1/assets/${assetId}/texture-images`);
            if (textureResponse.ok) {
              textureData = await textureResponse.json();
            }
          } else {
            // We already have the texture data from the preview check
            const textureResponse = await fetch(`http://localhost:8000/api/v1/assets/${assetId}/texture-images`);
            if (textureResponse.ok) {
              textureData = await textureResponse.json();
            }
          }
          
          if (textureData) {
            // Define the order: BC (Base Color), R (Roughness), M (Metallic), N (Normal), O (Opacity), D (Displacement)
            const textureOrder = ['BC', 'R', 'M', 'N', 'O', 'D'];
            const textureTypeMap = {
              'BC': ['basecolor', 'albedo', 'diffuse', 'base_color', 'color'],
              'R': ['roughness', 'rough'],
              'M': ['metallic', 'metalness', 'metal'],
              'N': ['normal', 'bump', 'nrm'],
              'O': ['opacity', 'alpha', 'transparency'],
              'D': ['displacement', 'height', 'disp']
            };
            
            // Add textures in the specified order (skip preview index if we already added it)
            for (const textureType of textureOrder) {
              const keywords = textureTypeMap[textureType] || [];
              
              // Find matching texture with its array index
              const matchingTextureIndex = textureData.images?.findIndex(img => {
                const filename = img.filename.toLowerCase();
                return keywords.some(keyword => filename.includes(keyword));
              });
              
              // Only add if it's not the preview we already added
              if (matchingTextureIndex !== -1 && matchingTextureIndex !== undefined && matchingTextureIndex !== previewIndex) {
                const matchingTexture = textureData.images[matchingTextureIndex];
                const cacheBust = `_t=${Date.now()}`;
                frames.push({
                  index: frameIndex++,
                  type: 'texture',
                  textureType: textureType,
                  name: textureType,
                  url: `/api/v1/assets/${assetId}/texture-image/${matchingTextureIndex}?${cacheBust}`,
                  description: `${textureType} Texture`,
                  filename: matchingTexture.filename
                });
                // console.log(`Added ${textureType} texture at index ${matchingTextureIndex}`);
              }
            }
          }
        } catch (error) {
          console.log('Could not fetch texture images:', error);
        }
        
        // If we have frames, create sequence data
        if (frames.length > 0) {
          setSequenceData({
            asset_id: assetId,
            frame_count: frames.length,
            frames: frames
          });
          setCurrentFrame(0);
          setLoading(false);
          setError(false);
          return;
        }
        
        // Fallback to regular thumbnail if no textures found
        const cacheBuster = asset._image_updated ? `?_t=${asset._image_updated}` : '';
        const singleResponse = await fetch(`http://localhost:8000/thumbnails/${assetId}${cacheBuster}`);
        
        if (singleResponse.ok) {
          setSequenceData({
            asset_id: assetId,
            frame_count: 1,
            frames: [{
              index: 0,
              type: 'thumbnail',
              name: 'Thumbnail',
              url: `/thumbnails/${assetId}${cacheBuster}`,
              description: 'Asset Thumbnail'
            }]
          });
          setCurrentFrame(0);
          setLoading(false);
          setError(false);
          return;
        }
        
        throw new Error('No images available');
        
      } catch (err) {
        console.log(`No images for texture set ${assetId}:`, err.message);
        setError(true);
        setLoading(false);
      }
    };

    fetchTextureSetSequence();
  }, [assetId, asset._image_updated]);

  // Update current frame when external frame index changes (for arrow navigation)
  useEffect(() => {
    if (externalFrameIndex !== null && sequenceData && sequenceData.frames) {
      const validIndex = Math.max(0, Math.min(externalFrameIndex, sequenceData.frames.length - 1));
      setCurrentFrame(validIndex);
    }
  }, [externalFrameIndex, sequenceData]);

  // Notify parent component when current frame changes
  useEffect(() => {
    if (sequenceData && sequenceData.frames && sequenceData.frames[currentFrame]) {
      const frameData = sequenceData.frames[currentFrame];
      onFrameChange(frameData);
    }
  }, [currentFrame, sequenceData, onFrameChange]);

  // Handle scroll wheel for zoom
  const handleWheel = (e) => {
    e.preventDefault();
    
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left) / rect.width;
    const mouseY = (e.clientY - rect.top) / rect.height;
    
    const zoomSensitivity = 0.1;
    const deltaY = e.deltaY;
    const zoomDelta = deltaY > 0 ? -zoomSensitivity : zoomSensitivity;
    
    setZoom(prevZoom => {
      const newZoom = Math.max(1, Math.min(5, prevZoom + zoomDelta));
      
      if (prevZoom === 1 && newZoom > 1) {
        setZoomCenter({ x: mouseX, y: mouseY });
        setPanOffset({ x: 0, y: 0 });
      }
      
      return newZoom;
    });
  };

  // Handle mouse movement for panning only (no scrubbing)
  const handleMouseMove = (e) => {
    if (isDragging && zoom > 1) {
      // Handle panning when zoomed in
      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;
      
      setPanOffset(prevOffset => ({
        x: prevOffset.x + deltaX / zoom,
        y: prevOffset.y + deltaY / zoom
      }));
      
      setDragStart({ x: e.clientX, y: e.clientY });
      return;
    }
  };

  // Handle mouse down for panning
  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
      e.preventDefault();
    }
  };

  // Handle mouse up
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Reset to first frame and zoom when mouse leaves
  const handleMouseLeave = () => {
    setIsHovering(false);
    setIsDragging(false);
    
    // Reset zoom and pan
    setZoom(1);
    setZoomCenter({ x: 0.5, y: 0.5 });
    setPanOffset({ x: 0, y: 0 });
    
    // Reset to first frame (preview or first texture)
    setCurrentFrame(0);
  };

  const handleMouseEnter = () => {
    setIsHovering(true);
  };

  // Navigation functions
  const goToPreviousFrame = () => {
    if (sequenceData && sequenceData.frames.length > 0) {
      setCurrentFrame(prev => prev > 0 ? prev - 1 : sequenceData.frames.length - 1);
    }
  };

  const goToNextFrame = () => {
    if (sequenceData && sequenceData.frames.length > 0) {
      setCurrentFrame(prev => prev < sequenceData.frames.length - 1 ? prev + 1 : 0);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!isHovering) return;
    
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      goToPreviousFrame();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      goToNextFrame();
    }
  };

  // Add keyboard event listener
  useEffect(() => {
    if (isHovering) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isHovering, sequenceData]);

  // Add global mouse up listener for dragging
  useEffect(() => {
    if (isDragging) {
      const handleGlobalMouseUp = () => setIsDragging(false);
      document.addEventListener('mouseup', handleGlobalMouseUp);
      return () => document.removeEventListener('mouseup', handleGlobalMouseUp);
    }
  }, [isDragging]);

  // Render loading state
  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-700">
        <div className="text-gray-500 text-sm">Loading...</div>
      </div>
    );
  }

  // Render error state (fallback to icon)
  if (error || !sequenceData) {
    return (
      <div 
        className="text-gray-500 text-3xl flex items-center justify-center w-full h-full cursor-pointer"
        onClick={onClick}
      >
        {fallbackIcon}
      </div>
    );
  }

  // Get current frame URL
  const getCurrentFrameUrl = () => {
    if (!sequenceData || !sequenceData.frames || sequenceData.frames.length === 0) {
      return null;
    }
    
    const frame = sequenceData.frames[currentFrame];
    return frame ? `http://localhost:8000${frame.url}` : null;
  };

  const frameUrl = getCurrentFrameUrl();
  const currentFrameData = sequenceData.frames[currentFrame];

  // Calculate transform style for zoom and pan
  const getImageTransform = () => {
    if (zoom === 1) return {};
    
    const centerX = zoomCenter.x * 100;
    const centerY = zoomCenter.y * 100;
    const offsetX = panOffset.x;
    const offsetY = panOffset.y;
    
    return {
      transform: `scale(${zoom}) translate(${offsetX}px, ${offsetY}px)`,
      transformOrigin: `${centerX}% ${centerY}%`,
      transition: isDragging ? 'none' : 'transform 0.1s ease-out'
    };
  };

  return (
    <div 
      ref={containerRef}
      className={`w-full h-full relative overflow-hidden ${zoom > 1 ? 'cursor-grab' : 'cursor-pointer'} ${isDragging ? 'cursor-grabbing' : ''}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      onClick={(e) => {
        // Only trigger onClick if not zoomed and not dragging
        if (zoom === 1 && !isDragging) {
          onClick(e);
        }
      }}
      title={sequenceData?.frame_count > 1 ? 
        `Texture Set: ${sequenceData.frame_count} images - ${currentFrameData?.description || 'Unknown'}${zoom > 1 ? ` - Zoom: ${zoom.toFixed(1)}x` : ''}` : 
        assetName
      }
      style={{ userSelect: 'none' }}
    >
      {frameUrl ? (
        <img
          ref={imageRef}
          src={frameUrl}
          alt={`${assetName} - ${currentFrameData?.description || 'Image'}`}
          className={className}
          style={getImageTransform()}
          onError={(e) => {
            console.error(`Failed to load frame ${currentFrame} for texture set ${assetId}`);
            console.error(`Failed URL: ${frameUrl}`);
            console.error(`Error details:`, e);
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'flex';
          }}
          draggable={false}
        />
      ) : null}
      
      {/* Fallback icon */}
      <div 
        className="text-gray-500 text-3xl flex items-center justify-center w-full h-full"
        style={{ display: frameUrl ? 'none' : 'flex' }}
      >
        {fallbackIcon}
      </div>

      {/* Navigation arrows - show when hovering and multiple frames */}
      {sequenceData && isHovering && sequenceData.frame_count > 1 && zoom === 1 && (
        <>
          {/* Left arrow */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              goToPreviousFrame();
            }}
            className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/70 hover:bg-black/90 text-white rounded-full p-2 transition-all duration-200 hover:scale-110"
            title="Previous texture"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m15 18-6-6 6-6"/>
            </svg>
          </button>
          
          {/* Right arrow */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              goToNextFrame();
            }}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/70 hover:bg-black/90 text-white rounded-full p-2 transition-all duration-200 hover:scale-110"
            title="Next texture"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m9 18 6-6-6-6"/>
            </svg>
          </button>
        </>
      )}

      {/* Zoom indicator - only show when zoomed */}
      {sequenceData && isHovering && zoom > 1 && (
        <div className="absolute top-2 left-2">
          <div className="bg-black/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded">
            Zoom: {zoom.toFixed(1)}x
          </div>
        </div>
      )}
      
      {/* Zoom instructions - show briefly when hovering */}
      {isHovering && zoom === 1 && !hideZoomMessage && (
        <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm text-white text-xs px-2 py-1 rounded opacity-70">
          Scroll to zoom
        </div>
      )}
      
    </div>
  );
};

export default TextureSetSequence;