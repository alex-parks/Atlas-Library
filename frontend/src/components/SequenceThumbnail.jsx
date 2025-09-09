// Interactive Thumbnail Sequence Component
import React, { useState, useEffect, useRef } from 'react';

const SequenceThumbnail = ({ 
  assetId, 
  assetName, 
  fallbackIcon = '🎨',
  className = "w-full h-full object-cover",
  onClick = () => {},
  thumbnailFrame = null  // Frame number to show when not hovering
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

  // Fetch sequence data when component mounts
  useEffect(() => {
    if (!assetId) {
      setLoading(false);
      setError(true);
      return;
    }

    const fetchSequenceData = async () => {
      try {
        // First try to fetch thumbnail sequence
        const sequenceResponse = await fetch(`http://localhost:8000/api/v1/assets/${assetId}/thumbnail-sequence`);
        
        if (sequenceResponse.ok) {
          const data = await sequenceResponse.json();
          
          if (data.frame_count > 1) {
            setSequenceData(data);
            
            // Find the index of the thumbnail frame if specified
            let initialFrame = 0;
            if (thumbnailFrame && data.frames) {
              const frameIndex = data.frames.findIndex(f => f.frame_number === thumbnailFrame);
              if (frameIndex !== -1) {
                initialFrame = frameIndex;
              }
            }
            setCurrentFrame(initialFrame);
          } else if (data.frame_count === 1) {
            // Single frame - treat as regular thumbnail
            setSequenceData(data);
            setCurrentFrame(0);
          } else {
            throw new Error('No frames available');
          }
          
          setLoading(false);
          setError(false);
          return;
        }
        
        // If sequence fails, try single thumbnail endpoint (for single images)
        const singleResponse = await fetch(`http://localhost:8000/thumbnails/${assetId}`);
        
        if (singleResponse.ok) {
          // Create a mock sequence data for single thumbnail
          setSequenceData({
            asset_id: assetId,
            frame_count: 1,
            frame_range: { start: 1, end: 1 },
            base_url: `/thumbnails/${assetId}`,
            frames: [
              {
                index: 0,
                frame_number: 1,
                filename: 'thumbnail.png',
                url: `/thumbnails/${assetId}`
              }
            ]
          });
          setCurrentFrame(0);
          setLoading(false);
          setError(false);
          return;
        }
        
        throw new Error('No thumbnail available');
        
      } catch (err) {
        console.log(`No thumbnail for asset ${assetId}:`, err.message);
        setError(true);
        setLoading(false);
      }
    };

    fetchSequenceData();
  }, [assetId, thumbnailFrame]);

  // Handle scroll wheel for zoom
  const handleWheel = (e) => {
    e.preventDefault();
    
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left) / rect.width;
    const mouseY = (e.clientY - rect.top) / rect.height;
    
    // Zoom sensitivity
    const zoomSensitivity = 0.1;
    const deltaY = e.deltaY;
    const zoomDelta = deltaY > 0 ? -zoomSensitivity : zoomSensitivity;
    
    setZoom(prevZoom => {
      const newZoom = Math.max(1, Math.min(5, prevZoom + zoomDelta));
      
      // Update zoom center to mouse position when zooming in from 1x
      if (prevZoom === 1 && newZoom > 1) {
        setZoomCenter({ x: mouseX, y: mouseY });
        setPanOffset({ x: 0, y: 0 }); // Reset pan when starting to zoom
      }
      
      return newZoom;
    });
  };

  // Handle mouse movement for scrubbing (updated to work with zoom)
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
    
    // Original scrubbing functionality (only when not zoomed and not dragging)
    if (!sequenceData || sequenceData.frame_count <= 1 || !isHovering || !containerRef.current || zoom > 1) {
      return;
    }

    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const progress = Math.max(0, Math.min(1, x / rect.width));
    
    // Map progress (0-1) to frame index (0 to frame_count-1)
    const frameIndex = Math.floor(progress * (sequenceData.frame_count - 1));
    setCurrentFrame(frameIndex);
  };

  // Handle mouse down for panning
  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
      e.preventDefault(); // Prevent text selection
    }
  };

  // Handle mouse up
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Reset to thumbnail frame and zoom when mouse leaves
  const handleMouseLeave = () => {
    setIsHovering(false);
    setIsDragging(false);
    
    // Reset zoom and pan
    setZoom(1);
    setZoomCenter({ x: 0.5, y: 0.5 });
    setPanOffset({ x: 0, y: 0 });
    
    // Reset to thumbnail frame or first frame
    if (sequenceData && sequenceData.frame_count > 1) {
      let resetFrame = 0;
      if (thumbnailFrame && sequenceData.frames) {
        const frameIndex = sequenceData.frames.findIndex(f => f.frame_number === thumbnailFrame);
        if (frameIndex !== -1) {
          resetFrame = frameIndex;
        }
      }
      setCurrentFrame(resetFrame);
    }
  };

  const handleMouseEnter = () => {
    setIsHovering(true);
  };

  // Add global mouse up listener for when dragging extends outside the component
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
      <div className="w-full h-full flex items-center justify-center bg-neutral-700">
        <div className="text-neutral-500 text-sm">Loading...</div>
      </div>
    );
  }

  // Render error state (fallback to icon)
  if (error || !sequenceData) {
    return (
      <div 
        className="text-neutral-500 text-3xl flex items-center justify-center w-full h-full cursor-pointer"
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
        `Sequence: ${sequenceData.frame_count} frames${
          sequenceData.frames && sequenceData.frames[currentFrame] && sequenceData.frames[currentFrame].frame_number 
            ? ` (Frame ${sequenceData.frames[currentFrame].frame_number})` 
            : sequenceData.frame_range 
              ? ` (Frame ${sequenceData.frame_range.start + currentFrame})` 
              : ` (Frame ${currentFrame + 1})`
        }${zoom > 1 ? ` - Zoom: ${zoom.toFixed(1)}x` : ''}` : 
        assetName
      }
      style={{ userSelect: 'none' }} // Prevent text selection when dragging
    >
      {frameUrl ? (
        <img
          ref={imageRef}
          src={frameUrl}
          alt={`${assetName} - Frame ${currentFrame + 1}`}
          className={className}
          style={getImageTransform()}
          onError={(e) => {
            console.error(`Failed to load frame ${currentFrame} for asset ${assetId}`);
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'flex';
          }}
          draggable={false} // Prevent image drag
        />
      ) : null}
      
      {/* Fallback icon */}
      <div 
        className="text-neutral-500 text-3xl flex items-center justify-center w-full h-full"
        style={{ display: frameUrl ? 'none' : 'flex' }}
      >
        {fallbackIcon}
      </div>

      {/* Frame indicator and zoom level - show when actively scrubbing or zoomed */}
      {sequenceData && isHovering && (
        <div className="absolute top-2 left-2 space-y-1">
          {/* Frame indicator - only show for sequences */}
          {sequenceData.frame_count > 1 && (
            <div className="bg-black/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded">
              {sequenceData.frames && sequenceData.frames[currentFrame] && sequenceData.frames[currentFrame].frame_number 
                ? `Frame: ${sequenceData.frames[currentFrame].frame_number}` 
                : sequenceData.frame_range 
                  ? `Frame: ${sequenceData.frame_range.start + currentFrame}` 
                  : `Frame: ${currentFrame + 1}/${sequenceData.frame_count}`}
            </div>
          )}
          
          {/* Zoom indicator - only show when zoomed */}
          {zoom > 1 && (
            <div className="bg-black/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded">
              Zoom: {zoom.toFixed(1)}x
            </div>
          )}
        </div>
      )}
      
      {/* Zoom instructions - show briefly when hovering */}
      {isHovering && zoom === 1 && (
        <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm text-white text-xs px-2 py-1 rounded opacity-70">
          Scroll to zoom
        </div>
      )}
    </div>
  );
};

export default SequenceThumbnail;