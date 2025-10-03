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

    def __init__(self):
        self._config_data = None
        self._config_file_path = None
        self._load_config()

    def _find_config_file(self) -> Optional[Path]:
        """Find the atlas_config.json file relative to this module"""
        # Start from this file's location
        current_file = Path(__file__).resolve()

        # Go up to bl-atlas-houdini directory (current_file -> python -> bl-atlas-houdini)
        bl_atlas_root = current_file.parent.parent

        # Look for config file
        config_file = bl_atlas_root / "config" / "atlas_config.json"

        if config_file.exists():
            return config_file

        # Fallback: look in current directory
        fallback_config = Path.cwd() / "atlas_config.json"
        if fallback_config.exists():
            return fallback_config

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
        return {
            "api_base_url": "http://library.blacksmith.tv:8000",
            "database_url": "http://library.blacksmith.tv:8529",
            "asset_library_3d": "/net/library/atlaslib/3D",
            "houdini_hda_path": "../otls/render_farm.hda",
            "houdini_hda_type": "blacksmith::render_farm::1.0",
            "version": "3.0",
            "description": "Blacksmith Atlas Standalone Configuration (Default)"
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
        return self._config_data.get("houdini_hda_type", "blacksmith::render_farm::1.0")

    def get(self, key: str, default: Any = None) -> Any:
        """Get any configuration value by key"""
        return self._config_data.get(key, default)

    def dump_config(self) -> str:
        """Get a string representation of the current configuration"""
        return json.dumps(self._config_data, indent=2)

# Global config instance
config = AtlasConfig()