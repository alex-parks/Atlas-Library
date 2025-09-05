#!/usr/bin/env python3
"""
Blacksmith Atlas - Configuration Manager
========================================

Centralized configuration management for all Atlas components.
Loads configuration from atlas_config.json and provides easy access to paths and settings.

Author: Blacksmith VFX
Version: 1.0
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AtlasConfig:
    """Singleton configuration manager for Blacksmith Atlas"""
    
    _instance = None
    _config_data = None
    _config_file_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AtlasConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from atlas_config.json"""
        try:
            # Try to find config file
            possible_paths = [
                # From backend directory
                Path(__file__).parent.parent.parent / "config" / "atlas_config.json",
                # From project root
                Path(__file__).parent.parent.parent / "atlas_config.json",
                # From current working directory
                Path.cwd() / "config" / "atlas_config.json",
                Path.cwd() / "atlas_config.json",
            ]
            
            config_path = None
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            
            if not config_path:
                raise FileNotFoundError(f"Could not find atlas_config.json in any of these locations: {[str(p) for p in possible_paths]}")
            
            self._config_file_path = config_path
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            
            logger.info(f"✅ Atlas configuration loaded from: {config_path}")
            
            # Validate essential paths
            self._validate_config()
            
        except Exception as e:
            logger.error(f"❌ Failed to load Atlas configuration: {e}")
            # Load default fallback config
            self._load_fallback_config()
    
    def _validate_config(self):
        """Validate that essential configuration exists"""
        required_paths = [
            'paths.asset_library_root',
            'paths.asset_library_3d', 
            'paths.backend_root',
            'api.backend_url'
        ]
        
        for path_key in required_paths:
            if not self.get(path_key):
                logger.warning(f"⚠️ Missing required config path: {path_key}")
    
    def _load_fallback_config(self):
        """Load fallback configuration if main config fails"""
        self._config_data = {
            "paths": {
                "asset_library_root": "/net/library/atlaslib",
                "asset_library_3d": "/net/library/atlaslib/3D",
                "asset_library_2d": "/net/library/atlaslib/2D",
                "houdini": {
                    "render_farm_hda": "/path/to/render_farm.hda",
                    "hda_type_name": "blacksmith::render_farm::1.0"
                },
                "backend_root": "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend"
            },
            "api": {
                "backend_url": "http://localhost:8000",
                "frontend_url": "http://localhost:3011"
            }
        }
        logger.warning("⚠️ Using fallback configuration")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'paths.asset_library_root')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key_path.split('.')
            value = self._config_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting config key '{key_path}': {e}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'paths.asset_library_root')
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key_path.split('.')
            config_ref = self._config_data
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            # Set the final key
            config_ref[keys[-1]] = value
            
            logger.info(f"✅ Config updated: {key_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting config key '{key_path}': {e}")
            return False
    
    def save(self) -> bool:
        """Save current configuration back to file"""
        try:
            if not self._config_file_path:
                logger.error("No config file path available for saving")
                return False
            
            # Update timestamp
            from datetime import datetime
            self._config_data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            with open(self._config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2)
            
            logger.info(f"✅ Configuration saved to: {self._config_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
            return False
    
    def reload(self) -> bool:
        """Reload configuration from file"""
        try:
            self._load_config()
            logger.info("✅ Configuration reloaded")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reload configuration: {e}")
            return False
    
    # Convenience properties for commonly used paths
    @property
    def asset_library_root(self) -> str:
        """Get the root asset library path"""
        return self.get('paths.asset_library_root', '/net/library/atlaslib')
    
    @property
    def asset_library_3d(self) -> str:
        """Get the 3D asset library path"""
        return self.get('paths.asset_library_3d', '/net/library/atlaslib/3D')
    
    @property
    def asset_library_2d(self) -> str:
        """Get the 2D asset library path"""
        return self.get('paths.asset_library_2d', '/net/library/atlaslib/2D')
    
    @property
    def houdini_hda_path(self) -> str:
        """Get the Houdini render farm HDA path"""
        return self.get('paths.houdini.render_farm_hda', '/path/to/render_farm.hda')
    
    @property
    def houdini_hda_type(self) -> str:
        """Get the Houdini HDA type name"""
        return self.get('paths.houdini.hda_type_name', 'blacksmith::render_farm::1.0')
    
    @property
    def backend_url(self) -> str:
        """Get the backend API URL"""
        return self.get('api.backend_url', 'http://localhost:8000')
    
    @property
    def frontend_url(self) -> str:
        """Get the frontend URL"""
        return self.get('api.frontend_url', 'http://localhost:3011')
    
    @property
    def thumbnails_path(self) -> str:
        """Get the thumbnails directory path"""
        return self.get('paths.thumbnails', self.asset_library_root + '/thumbnails')
    
    def get_category_path(self, dimension: str, category: str, subcategory: str = None) -> str:
        """
        Build full path for asset category
        
        Args:
            dimension: '3D' or '2D'
            category: Asset category (e.g., 'Assets', 'FX')
            subcategory: Asset subcategory (e.g., 'Blacksmith Asset')
            
        Returns:
            Full path to category folder
        """
        if dimension == '3D':
            base_path = self.asset_library_3d
        elif dimension == '2D':
            base_path = self.asset_library_2d
        else:
            base_path = self.asset_library_root
        
        path = Path(base_path) / category
        
        if subcategory:
            # Convert subcategory name to folder name
            subcategory_folder = subcategory.replace(' ', '')
            path = path / subcategory_folder
        
        return str(path)
    
    def get_asset_path(self, dimension: str, category: str, subcategory: str, asset_id: str) -> str:
        """
        Build full path for specific asset
        
        Args:
            dimension: '3D' or '2D'
            category: Asset category
            subcategory: Asset subcategory
            asset_id: Asset ID
            
        Returns:
            Full path to asset folder
        """
        category_path = self.get_category_path(dimension, category, subcategory)
        return str(Path(category_path) / asset_id)
    
    def __str__(self):
        """String representation showing key paths"""
        return f"""AtlasConfig:
  Asset Library: {self.asset_library_root}
  3D Library: {self.asset_library_3d}
  2D Library: {self.asset_library_2d}
  Houdini HDA: {self.houdini_hda_path}
  Backend URL: {self.backend_url}
  Config File: {self._config_file_path}"""

# Global instance
config = AtlasConfig()

# Convenience functions for quick access
def get_config(key_path: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config.get(key_path, default)

def set_config(key_path: str, value: Any) -> bool:
    """Set configuration value"""
    return config.set(key_path, value)

def save_config() -> bool:
    """Save configuration to file"""
    return config.save()

def reload_config() -> bool:
    """Reload configuration from file"""
    return config.reload()

# Example usage:
if __name__ == "__main__":
    # Test the configuration system
    print("🔧 Testing Atlas Configuration System")
    print("="*50)
    
    print(f"Asset Library Root: {config.asset_library_root}")
    print(f"3D Library: {config.asset_library_3d}")
    print(f"Houdini HDA: {config.houdini_hda_path}")
    print(f"Backend URL: {config.backend_url}")
    
    print(f"\nCategory Path Example: {config.get_category_path('3D', 'Assets', 'Blacksmith Asset')}")
    print(f"Asset Path Example: {config.get_asset_path('3D', 'Assets', 'Blacksmith Asset', 'TEST123AA001')}")
    
    print(f"\nConfiguration Summary:")
    print(config)