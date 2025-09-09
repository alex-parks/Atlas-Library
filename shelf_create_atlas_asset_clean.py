#!/usr/bin/env python3
"""
Blacksmith Atlas - Create Atlas Asset (Clean Version)
====================================================

This script creates an Atlas Asset subnet from selected Houdini nodes.
It uses the copy_to_atlas_asset.py module for the actual implementation.

Usage:
1. Select nodes in Houdini
2. Run this script (paste into shelf button)
3. Configure the created subnet's parameters including thumbnail options
4. Click 'Export Atlas Asset' button in the subnet

Features:
- Thumbnail options: Automatic (farm render), Choose file, or Disable
- Support for EXR sequences and custom thumbnails
- Full parameter interface with versioning and variants

Author: Blacksmith VFX
Version: 3.0
"""

import hou
import sys
from pathlib import Path

def create_atlas_asset():
    """Main function to create Atlas Asset from selected nodes"""
    
    print("\n🏭 BLACKSMITH ATLAS - CREATE ASSET")
    print("="*50)
    
    try:
        # Check selected nodes
        selected_nodes = hou.selectedNodes()
        if not selected_nodes:
            hou.ui.displayMessage(
                "Please select nodes to create an Atlas Asset.",
                severity=hou.severityType.Warning,
                title="No Selection"
            )
            print("❌ No nodes selected")
            return False

        print(f"✅ Found {len(selected_nodes)} selected nodes")

        # Setup import paths
        backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
        _3d_path = backend_path / "assetlibrary" / "_3D"

        # Add paths to sys.path
        for path in [str(backend_path), str(_3d_path)]:
            if path not in sys.path:
                sys.path.insert(0, path)

        # Clear cached modules for development
        modules_to_clear = [mod for mod in sys.modules.keys() 
                           if 'copy_to_atlas_asset' in mod or 'atlas' in mod.lower()]
        
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Import and run the main function
        import copy_to_atlas_asset
        result = copy_to_atlas_asset.copy_selected_to_atlas_asset()

        if result:
            print("🎉 SUCCESS! Atlas asset created with thumbnail options available.")
            return True
        else:
            print("⚠️ Asset creation completed with warnings - check console")
            return False

    except Exception as e:
        error_msg = f"Atlas Create Error: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        
        import traceback
        traceback.print_exc()
        
        hou.ui.displayMessage(
            f"{error_msg}\n\nCheck the Python Shell for details.",
            severity=hou.severityType.Error,
            title="Atlas Create Error"
        )
        return False

# Main execution
if __name__ == "__main__":
    create_atlas_asset()
else:
    # When pasted into shelf button, run directly
    create_atlas_asset()