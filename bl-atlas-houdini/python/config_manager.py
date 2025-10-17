#!/usr/bin/env python3
"""
Blacksmith Atlas - Standalone Configuration Manager
==================================================

Lightweight configuration management for the standalone Atlas tools.
Loads configuration from atlas_config.json relative to the bl-atlas-houdini directory.

Author: Blacksmith VFX
Version: 3.0 (Standalone)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class AtlasConfig:
    """Standalone configuration manager for Blacksmith Atlas"""

    def __init__(self, use_network=False):
        self._config_data = None
        self._config_file_path = None
        self._use_network = use_network
        self._load_config()

    def _find_config_file(self) -> Optional[Path]:
        """Find the atlas_config.json file relative to this module"""
        # Start from this file's location
        current_file = Path(__file__).resolve()

        # Go up to bl-atlas-houdini directory (current_file -> python -> bl-atlas-houdini)
        bl_atlas_root = current_file.parent.parent

        # Choose config file based on network preference
        if self._use_network:
            config_filename = "atlas_network_config.json"
            print("🌐 Using network configuration")
        else:
            config_filename = "atlas_local_config.json"
            print("🏠 Using local configuration")

        # Look for config file
        config_file = bl_atlas_root / "config" / config_filename

        if config_file.exists():
            return config_file

        # NO FALLBACK - fail if the requested config is not found
        # This prevents accidentally writing to the wrong database
        print(f"❌ Required config file not found: {config_file}")
        return None

    def _load_config(self):
        """Load configuration from JSON file"""
        config_file = self._find_config_file()

        if not config_file:
            print("⚠️  Atlas config file not found, using defaults")
            self._config_data = self._get_default_config()
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)

            self._config_file_path = config_file
            print(f"✅ Loaded Atlas config from: {config_file}")

        except Exception as e:
            print(f"⚠️  Error loading config file {config_file}: {e}")
            print("Using default configuration")
            self._config_data = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        if self._use_network:
            return {
                "api_base_url": "https://library.blacksmith.tv/api",
                "database_url": "http://library.blacksmith.tv:8529",
                "asset_library_3d": "/net/library/atlaslib/3D",
                "houdini_hda_path": "../otls/object_dev_tuna_unalan_1_1_lookdev_thumbnail_5_0.hda",
                "houdini_hda_type": "dev_tuna.unalan_1.1::lookdev_thumbnail::5.0",
                "version": "3.0",
                "description": "Blacksmith Atlas Network Configuration (Default)",
                "environment": "network",
                "api_timeout": 30,
                "retry_attempts": 3,
                "use_ssl": True,
                "verify_ssl": True
            }
        else:
            return {
                "api_base_url": "http://localhost:8000",
                "database_url": "http://localhost:8529",
                "asset_library_3d": "/net/library/atlaslib/3D",
                "houdini_hda_path": "../otls/object_dev_tuna_unalan_1_1_lookdev_thumbnail_5_0.hda",
                "houdini_hda_type": "dev_tuna.unalan_1.1::lookdev_thumbnail::5.0",
                "version": "3.0",
                "description": "Blacksmith Atlas Local Configuration (Default)",
                "environment": "local"
            }

    @property
    def api_base_url(self) -> str:
        """Get the Atlas API base URL"""
        return self._config_data.get("api_base_url", "http://library.blacksmith.tv:8000")

    @property
    def database_url(self) -> str:
        """Get the Atlas database URL"""
        return self._config_data.get("database_url", "http://library.blacksmith.tv:8529")

    @property
    def asset_library_3d(self) -> str:
        """Get the 3D asset library path"""
        return self._config_data.get("asset_library_3d", "/net/library/atlaslib/3D")

    @property
    def houdini_hda_path(self) -> str:
        """Get the path to the Houdini HDA file"""
        hda_path = self._config_data.get("houdini_hda_path", "../otls/render_farm.hda")

        # If it's a relative path, make it relative to the config file
        if not os.path.isabs(hda_path) and self._config_file_path:
            config_dir = self._config_file_path.parent
            return str((config_dir / hda_path).resolve())

        return hda_path

    @property
    def houdini_hda_type(self) -> str:
        """Get the Houdini HDA type name"""
        return self._config_data.get("houdini_hda_type", "dev_tuna.unalan_1.1::lookdev_thumbnail::5.0")

    @property
    def environment(self) -> str:
        """Get the current environment (local/network)"""
        return self._config_data.get("environment", "local")

    @property
    def api_timeout(self) -> int:
        """Get the API timeout in seconds"""
        return self._config_data.get("api_timeout", 30)

    @property
    def retry_attempts(self) -> int:
        """Get the number of retry attempts for API calls"""
        return self._config_data.get("retry_attempts", 3)

    @property
    def use_ssl(self) -> bool:
        """Check if SSL should be used"""
        return self._config_data.get("use_ssl", False)

    @property
    def verify_ssl(self) -> bool:
        """Check if SSL certificates should be verified"""
        return self._config_data.get("verify_ssl", True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get any configuration value by key"""
        return self._config_data.get(key, default)

    def dump_config(self) -> str:
        """Get a string representation of the current configuration"""
        return json.dumps(self._config_data, indent=2)

    def is_network_mode(self) -> bool:
        """Check if running in network mode"""
        return self._use_network

# Factory functions for different configurations
def get_local_config():
    """Get local configuration instance"""
    return AtlasConfig(use_network=False)

def get_network_config():
    """Get network configuration instance"""
    return AtlasConfig(use_network=True)

# DO NOT auto-load configs on import - let callers specify what they need
config = None
network_config = None