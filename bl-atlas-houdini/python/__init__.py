#!/usr/bin/env python3
"""
Blacksmith Atlas - Standalone Python Package
===========================================

Standalone version of the Blacksmith Atlas tools for Houdini.
This package provides all the functionality needed to create and export
Atlas assets without dependencies on the main Atlas codebase.

Author: Blacksmith VFX
Version: 3.0 (Standalone)
"""

__version__ = "3.0"
__author__ = "Blacksmith VFX"
__description__ = "Standalone Blacksmith Atlas tools for Houdini"

# Import main modules for easy access
try:
    from . import config_manager
    from . import api_client
    from . import atlas_ui
    from . import houdiniae

    print("✅ Blacksmith Atlas Standalone Package loaded successfully")
    print(f"   Version: {__version__}")
    print(f"   Modules: config_manager, api_client, atlas_ui, houdiniae")

except ImportError as e:
    print(f"⚠️ Some Atlas modules could not be imported: {e}")

# Expose main classes and functions
try:
    from .houdiniae import TemplateAssetExporter
    from .api_client import AtlasAPIClient, call_atlas_api_ingestion
    from .atlas_ui import copy_selected_to_atlas_asset, add_atlas_export_parameters
    from .config_manager import config

    __all__ = [
        'TemplateAssetExporter',
        'AtlasAPIClient',
        'call_atlas_api_ingestion',
        'copy_selected_to_atlas_asset',
        'add_atlas_export_parameters',
        'config'
    ]

except ImportError as e:
    print(f"⚠️ Could not import main Atlas classes: {e}")
    __all__ = []