// Interactive Thumbnail Sequence Component
import React, { useState, useEffect, useRef } from 'react';

const SequenceThumbnail = ({ 
  assetId, 
  assetName, 
  fallbackIcon = '🎨',
  className = "w-full h-full object-cover",
  onClick = () => {} 
}) => {
  const [sequenceData, setSequenceData] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isHovering, setIsHovering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const containerRef = useRef(null);

  // Fetch sequence data when component mounts
  useEffect(() => {
    if (!assetId) {
      setLoading(false);
      setError(true);
      return;
    }

    const fetchSequenceData = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/assets/${assetId}/thumbnail-sequence`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        if (data.frame_count > 1) {
          setSequenceData(data);
          setCurrentFrame(0);
        } else if (data.frame_count === 1) {
          // Single frame - treat as regular thumbnail
          setSequenceData(data);
          setCurrentFrame(0);
        } else {
          throw new Error('No frames available');
        }
        
        setLoading(false);
        setError(false);
      } catch (err) {
        console.log(`No thumbnail sequence for asset ${assetId}:`, err.message);
        setError(true);
        setLoading(false);
      }
    };

    fetchSequenceData();
  }, [assetId]);

  // Handle mouse movement for scrubbing
  const handleMouseMove = (e) => {
    if (!sequenceData || sequenceData.frame_count <= 1 || !isHovering || !containerRef.current) {
      return;
    }

    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const progress = Math.max(0, Math.min(1, x / rect.width));
    
    // Map progress (0-1) to frame index (0 to frame_count-1)
    const frameIndex = Math.floor(progress * (sequenceData.frame_count - 1));
    setCurrentFrame(frameIndex);
  };

  // Reset to first frame when mouse leaves
  const handleMouseLeave = () => {
    setIsHovering(false);
    if (sequenceData && sequenceData.frame_count > 1) {
      setCurrentFrame(0);
    }
  };

  const handleMouseEnter = () => {
    setIsHovering(true);
  };

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

  return (
    <div 
      ref={containerRef}
      className="w-full h-full relative overflow-hidden cursor-pointer"
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      title={sequenceData?.frame_count > 1 ? 
        `Sequence: ${sequenceData.frame_count} frames (Frame ${currentFrame + 1})` : 
        assetName
      }
    >
      {frameUrl ? (
        <img
          src={frameUrl}
          alt={`${assetName} - Frame ${currentFrame + 1}`}
          className={className}
          onError={(e) => {
            console.error(`Failed to load frame ${currentFrame} for asset ${assetId}`);
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'flex';
          }}
        />
      ) : null}
      
      {/* Fallback icon */}
      <div 
        className="text-neutral-500 text-3xl flex items-center justify-center w-full h-full"
        style={{ display: frameUrl ? 'none' : 'flex' }}
      >
        {fallbackIcon}
      </div>

      {/* Frame indicator - only show when actively scrubbing */}
      {sequenceData && sequenceData.frame_count > 1 && isHovering && (
        <div className="absolute top-2 left-2 bg-black/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded">
          {currentFrame + 1}/{sequenceData.frame_count}
        </div>
      )}
    </div>
  );
};

export default SequenceThumbnail;