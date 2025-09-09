# Object-Oriented Asset Type System
# Base classes for different asset types with shared functionality

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseAsset(ABC):
    """Abstract base class for all assets"""
    
    def __init__(self, asset_data: Dict[str, Any]):
        self.asset_data = asset_data
        self.id = asset_data.get('id') or asset_data.get('_key')
        self.name = asset_data.get('name', 'Unknown')
        self.description = asset_data.get('description', '')
        self.created_at = asset_data.get('created_at')
        self.created_by = asset_data.get('created_by', 'Unknown')
        self.tags = asset_data.get('tags', [])
    
    @property
    @abstractmethod
    def asset_type(self) -> str:
        """Return the asset type identifier"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> str:
        """Return the dimension (2D or 3D)"""
        pass
    
    @abstractmethod
    def get_badge_type(self) -> str:
        """Return the frontend badge component type"""
        pass
    
    @abstractmethod
    def get_info_fields(self) -> List[Dict[str, Any]]:
        """Return the fields to display in the asset info badge"""
        pass
    
    @abstractmethod
    def get_preview_type(self) -> str:
        """Return the preview modal type"""
        pass
    
    def get_thumbnail_path(self) -> Optional[str]:
        """Get the path to the thumbnail folder"""
        if 'paths' in self.asset_data:
            if 'thumbnail' in self.asset_data['paths']:
                return self.asset_data['paths']['thumbnail']
            if 'asset_folder' in self.asset_data['paths']:
                return str(Path(self.asset_data['paths']['asset_folder']) / 'Thumbnail')
        return None
    
    def get_uid(self) -> str:
        """Extract UID from asset ID"""
        if self.id and len(self.id) >= 16:
            return self.id[:11]  # First 11 characters
        return 'UNKNOWN'
    
    def get_variant_id(self) -> str:
        """Extract variant ID from asset ID"""
        if self.id and len(self.id) >= 16:
            return self.id[11:13]  # Characters 11-12
        return 'AA'
    
    def get_version(self) -> str:
        """Extract version from asset ID"""
        if self.id and len(self.id) >= 16:
            return self.id[13:16]  # Characters 13-15
        return '001'
    
    def format_file_size(self, size_bytes: Optional[int]) -> str:
        """Format file size in human readable format"""
        if not size_bytes or size_bytes == 0:
            return "Calc..."
        
        if size_bytes < 1024 * 1024:
            return f"{round(size_bytes / 1024)} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{(size_bytes / (1024 * 1024)):.1f} MB"
        else:
            return f"{(size_bytes / (1024 * 1024 * 1024)):.2f} GB"


class Asset2D(BaseAsset):
    """Base class for 2D assets - completely different from 3D"""
    
    @property
    def dimension(self) -> str:
        return "2D"
    
    def get_resolution(self) -> str:
        """Get image resolution"""
        return self.asset_data.get('metadata', {}).get('resolution', 'Unknown')
    
    def get_color_space(self) -> str:
        """Get color space information"""
        return self.asset_data.get('metadata', {}).get('color_space', 'sRGB')


class Asset3D(BaseAsset):
    """Base class for all 3D assets"""
    
    @property
    def dimension(self) -> str:
        return "3D"
    
    def get_render_engine(self) -> str:
        """Get render engine"""
        metadata = self.asset_data.get('metadata', {})
        return (metadata.get('hierarchy', {}).get('render_engine') or 
                metadata.get('render_engine') or 'Unknown')
    
    def get_file_size(self) -> str:
        """Get total file size"""
        size_bytes = self.asset_data.get('file_sizes', {}).get('estimated_total_size', 0)
        return self.format_file_size(size_bytes)


class HoudiniAsset(Asset3D):
    """Houdini Digital Asset - traditional 3D asset with Houdini-specific properties"""
    
    @property
    def asset_type(self) -> str:
        return "Houdini Asset"
    
    def get_badge_type(self) -> str:
        return "HoudiniAssetBadge"
    
    def get_preview_type(self) -> str:
        return "HoudiniPreview"
    
    def get_houdini_version(self) -> str:
        """Get Houdini version"""
        return self.asset_data.get('metadata', {}).get('houdini_version', 'Unknown')
    
    def get_artist(self) -> str:
        """Get artist name"""
        return self.asset_data.get('artist', 'Unknown')
    
    def get_info_fields(self) -> List[Dict[str, Any]]:
        """Return Houdini-specific info fields"""
        return [
            {
                'label': 'Render Engine',
                'value': self.get_render_engine(),
                'color': 'text-orange-400'
            },
            {
                'label': 'Size',
                'value': self.get_file_size(),
                'color': 'text-neutral-300'
            },
            {
                'label': 'Artist',
                'value': self.get_artist(),
                'color': 'text-green-400'
            },
            {
                'label': 'Houdini Ver',
                'value': self.get_houdini_version(),
                'color': 'text-blue-300'
            },
            {
                'label': 'Asset Ver',
                'value': f'v{self.get_version()}',
                'color': 'text-purple-300'
            },
            {
                'label': 'Created',
                'value': self.created_at.split('T')[0] if self.created_at else 'Unknown',
                'color': 'text-cyan-300'
            }
        ]


class TextureAsset(Asset3D):
    """Texture Asset - uploaded texture files"""
    
    @property
    def asset_type(self) -> str:
        return "Texture"
    
    def get_badge_type(self) -> str:
        return "TextureBadge"
    
    def get_preview_type(self) -> str:
        return "TexturePreview"
    
    def get_resolution(self) -> str:
        """Get texture resolution"""
        return self.asset_data.get('metadata', {}).get('resolution', 'Unknown')
    
    def get_format(self) -> str:
        """Get file format"""
        if 'paths' in self.asset_data and 'template_file' in self.asset_data['paths']:
            return self.asset_data['paths']['template_file'].split('.')[-1].upper()
        return self.asset_data.get('metadata', {}).get('file_format', 'Unknown').upper()
    
    def get_uv_layout(self) -> str:
        """Get UV layout type"""
        return self.asset_data.get('metadata', {}).get('uv_layout', 'Standard')
    
    def is_seamless(self) -> str:
        """Check if texture is seamless/tileable"""
        seamless = self.asset_data.get('metadata', {}).get('seamless') or \
                  self.asset_data.get('metadata', {}).get('tiling')
        return 'Yes' if seamless else 'No'
    
    def get_info_fields(self) -> List[Dict[str, Any]]:
        """Return Texture-specific info fields"""
        return [
            {
                'label': 'Type',
                'value': 'Texture Map',
                'color': 'text-purple-400'
            },
            {
                'label': 'Resolution',
                'value': self.get_resolution(),
                'color': 'text-cyan-300'
            },
            {
                'label': 'Format',
                'value': self.get_format(),
                'color': 'text-orange-300'
            },
            {
                'label': 'Size',
                'value': self.get_file_size(),
                'color': 'text-neutral-300'
            },
            {
                'label': 'UV Layout',
                'value': self.get_uv_layout(),
                'color': 'text-blue-300'
            },
            {
                'label': 'Seamless',
                'value': self.is_seamless(),
                'color': 'text-green-400'
            }
        ]


class HDRIAsset(Asset3D):
    """HDRI Environment Map Asset"""
    
    @property
    def asset_type(self) -> str:
        return "HDRI"
    
    def get_badge_type(self) -> str:
        return "HDRIBadge"
    
    def get_preview_type(self) -> str:
        return "HDRIPreview"
    
    def get_resolution(self) -> str:
        """Get HDRI resolution"""
        return self.asset_data.get('metadata', {}).get('resolution', 'Unknown')
    
    def get_format(self) -> str:
        """Get file format"""
        if 'paths' in self.asset_data and 'template_file' in self.asset_data['paths']:
            return self.asset_data['paths']['template_file'].split('.')[-1].upper()
        return self.asset_data.get('metadata', {}).get('file_format', 'EXR')
    
    def get_location(self) -> str:
        """Get capture location or environment type"""
        return self.asset_data.get('metadata', {}).get('location', 'Studio')
    
    def get_info_fields(self) -> List[Dict[str, Any]]:
        """Return HDRI-specific info fields"""
        return [
            {
                'label': 'Type',
                'value': 'HDRI Map',
                'color': 'text-orange-400'
            },
            {
                'label': 'Resolution',
                'value': self.get_resolution(),
                'color': 'text-cyan-300'
            },
            {
                'label': 'Format',
                'value': self.get_format(),
                'color': 'text-purple-300'
            },
            {
                'label': 'Size',
                'value': self.get_file_size(),
                'color': 'text-neutral-300'
            },
            {
                'label': 'Created',
                'value': self.created_at.split('T')[0] if self.created_at else 'Unknown',
                'color': 'text-cyan-300'
            },
            {
                'label': 'Location',
                'value': self.get_location(),
                'color': 'text-green-400'
            }
        ]


# Asset Factory
class AssetFactory:
    """Factory to create appropriate asset objects based on asset data"""
    
    @staticmethod
    def create_asset(asset_data: Dict[str, Any]) -> BaseAsset:
        """Create the appropriate asset object based on asset data"""
        
        # Determine asset type from various sources
        asset_type = None
        
        # Check asset_type field first (from uploads)
        if 'asset_type' in asset_data:
            asset_type = asset_data['asset_type']
        elif 'category' in asset_data:
            asset_type = asset_data['category']
        else:
            # Infer from file paths or other metadata
            if 'paths' in asset_data and 'template_file' in asset_data['paths']:
                filename = asset_data['paths']['template_file'].lower()
                if any(ext in filename for ext in ['.hdr', '.hdri', '.exr']) and 'hdri' in filename:
                    asset_type = 'HDRI'
                elif any(ext in filename for ext in ['.jpg', '.png', '.tiff', '.tga', '.exr']):
                    asset_type = 'Textures'
                else:
                    asset_type = 'Assets'  # Default to Houdini asset
            else:
                asset_type = 'Assets'  # Default to Houdini asset
        
        # Create appropriate asset object
        if asset_type in ['HDRI', 'HDRIs']:
            return HDRIAsset(asset_data)
        elif asset_type in ['Textures', 'Texture']:
            return TextureAsset(asset_data)
        else:
            # Default to Houdini Asset for anything else (Assets, FX, Materials, HDAs, etc.)
            return HoudiniAsset(asset_data)