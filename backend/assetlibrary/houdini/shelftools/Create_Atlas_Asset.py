#!/usr/bin/env python3
"""
Blacksmith Atlas - Create Atlas Asset
=====================================

This script creates an Atlas Asset subnet from selected Houdini nodes.
It can be used directly in a Houdini shelf button by copying the entire contents.

Usage:
1. Select nodes in Houdini
2. Run this script (or paste into shelf button)
3. Configure the created subnet's parameters
4. Click 'Export Atlas Asset' button in the subnet

Author: Blacksmith VFX
Version: 2.1
"""

# Blacksmith Atlas - Create Atlas Asset
import hou
import sys
from pathlib import Path
import importlib

print("\n" + "🏭"*20)
print("BLACKSMITH ATLAS - CREATE ASSET")
print("🏭"*20 + "\n")

try:
    # Check selected nodes
    selected_nodes = hou.selectedNodes()
    if not selected_nodes:
        hou.ui.displayMessage(
            "Please select nodes to create an Atlas Asset.",
            severity=hou.severityType.Warning,
            title="No Selection"
        )
        print("❌ No nodes selected - exiting")
    else:
        print(f"✅ Found {len(selected_nodes)} selected nodes")

        # Setup paths
        backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
        _3d_path = backend_path / "assetlibrary" / "_3D"

        # Add to sys.path
        for path in [backend_path, _3d_path]:
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
                print(f"✅ Added to sys.path: {path}")

        # Clear modules
        modules_to_clear = [
            'shelf_create_atlas_asset',
            'copy_to_atlas_asset',
            'assetlibrary._3D.copy_to_atlas_asset',
            'assetlibrary._3D.shelf_create_atlas_asset'
        ]

        cleared = 0
        for module_name in list(sys.modules.keys()):
            if any(m in module_name for m in ['shelf_create_atlas_asset', 'copy_to_atlas_asset', 'assetlibrary']):
                del sys.modules[module_name]
                cleared += 1

        if cleared > 0:
            print(f"🔄 Cleared {cleared} cached modules")

        # Try the import
        print("\n📦 Attempting import...")

        try:
            # Try direct import first
            import copy_to_atlas_asset
            print("✅ Imported copy_to_atlas_asset directly")

            # Reload for development
            importlib.reload(copy_to_atlas_asset)
            print("✅ Reloaded module")

            # Run the function
            print("\n🚀 Running copy_selected_to_atlas_asset()...")
            result = copy_to_atlas_asset.copy_selected_to_atlas_asset()

            if result:
                print("\n🎉 SUCCESS! Atlas asset created.")
            else:
                print("\n⚠️ Function returned False - check console for details")

        except ImportError as e:
            print(f"\n❌ Import Error: {e}")
            print("Trying alternative import method...")

            # Try shelf module approach
            try:
                import shelf_create_atlas_asset
                importlib.reload(shelf_create_atlas_asset)
                print("✅ Imported shelf_create_atlas_asset")

                result = shelf_create_atlas_asset.main()

                if result:
                    print("\n🎉 SUCCESS! Atlas asset created via shelf module.")
                else:
                    print("\n⚠️ Shelf module returned False")

            except Exception as e2:
                print(f"❌ Alternative import also failed: {e2}")
                raise

except Exception as e:
    error_msg = f"Atlas Create Error:\n{str(e)}"
    print(f"\n❌ ERROR: {error_msg}")

    # Show full traceback in console
    import traceback
    traceback.print_exc()

    # Show user-friendly error
    hou.ui.displayMessage(
        error_msg + "\n\nCheck the Python Shell for details.",
        severity=hou.severityType.Error,
        title="Atlas Create Error"
    )

print("\n" + "="*60)