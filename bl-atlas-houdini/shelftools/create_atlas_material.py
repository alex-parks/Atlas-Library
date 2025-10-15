#!/usr/bin/env python3
"""
Blacksmith Atlas - Create Atlas Material (Standalone)
====================================================

This script creates an Atlas Material subnet from a selected material node.
Standalone version that works without the main Atlas codebase.

Usage:
1. Select a material node inside a Material Network (matnet)
2. Run this script (or paste into shelf button)
3. Configure the created subnet's parameters
4. Click 'Export Atlas Material' button in the subnet

Author: Blacksmith VFX
Version: 3.0 (Standalone - Materials)
"""

import hou
import sys
import os
from pathlib import Path
import importlib

print("\n" + "🎨"*20)
print("BLACKSMITH ATLAS - CREATE MATERIAL (STANDALONE)")
print("🎨"*20 + "\n")

try:
    # Check selected nodes
    selected_nodes = hou.selectedNodes()
    if not selected_nodes:
        hou.ui.displayMessage(
            "Please select a material node to create an Atlas Material.",
            severity=hou.severityType.Warning,
            title="No Selection"
        )
        print("❌ No material selected - exiting")
    else:
        print(f"✅ Found {len(selected_nodes)} selected node(s)")

        # Verify we're in a material network
        if selected_nodes:
            parent = selected_nodes[0].parent()
            parent_type = parent.type().name()
            print(f"📍 Parent context: {parent.path()} (type: {parent_type})")

            # Check if parent is a material network (matnet, materialbuilder, etc.)
            valid_contexts = ['matnet', 'mat', 'shop', 'materialbuilder', 'vopnet']
            is_material_context = any(ctx in parent_type.lower() for ctx in valid_contexts)

            if not is_material_context:
                hou.ui.displayMessage(
                    f"❌ Materials must be created inside a Material Network.\n\n"
                    f"Current context: {parent.path()}\n"
                    f"Context type: {parent_type}\n\n"
                    f"Please select a material node inside /mat or /shop.",
                    severity=hou.severityType.Error,
                    title="Invalid Context"
                )
                print(f"❌ Invalid context: {parent_type}")
                sys.exit(0)

        # Auto-detect the bl-atlas-houdini directory
        bl_atlas_root = None

        # Method 1: Try common installation locations
        possible_locations = [
            "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/bl-atlas-houdini",
            os.path.expanduser("~/bl-atlas-houdini"),
            "/opt/bl-atlas-houdini",
            "/usr/local/bl-atlas-houdini",
            "C:/Users/" + os.getenv('USERNAME', 'user') + "/bl-atlas-houdini",
            "D:/bl-atlas-houdini"
        ]

        for location in possible_locations:
            test_path = Path(location)
            if test_path.exists() and (test_path / "python" / "atlas_material_ui.py").exists():
                bl_atlas_root = test_path
                break

        # Method 2: If not found, try to detect from current working directory
        if not bl_atlas_root:
            cwd = Path.cwd()
            for parent in [cwd] + list(cwd.parents):
                for subdir in parent.iterdir() if parent.exists() else []:
                    if subdir.name == "bl-atlas-houdini" and (subdir / "python" / "atlas_material_ui.py").exists():
                        bl_atlas_root = subdir
                        break
                if bl_atlas_root:
                    break

        if not bl_atlas_root:
            raise Exception("Could not find bl-atlas-houdini directory. Please ensure it's installed in a standard location.")

        python_path = bl_atlas_root / "python"
        print(f"📁 BL-Atlas root: {bl_atlas_root}")
        print(f"📁 Python path: {python_path}")

        # Add python directory to sys.path
        if str(python_path) not in sys.path:
            sys.path.insert(0, str(python_path))
            print(f"✅ Added to sys.path: {python_path}")

        # Clear any cached modules for development
        modules_to_clear = [
            'atlas_material_ui',
            'houdiniae',
            'api_client',
            'config_manager',
            'metadata_processor'
        ]

        cleared = 0
        for module_name in list(sys.modules.keys()):
            if any(m in module_name for m in modules_to_clear):
                del sys.modules[module_name]
                cleared += 1

        if cleared > 0:
            print(f"🔄 Cleared {cleared} cached modules")

        # Try to import the Atlas Material UI module
        print("\n📦 Attempting import...")

        try:
            import atlas_material_ui
            print("✅ Imported atlas_material_ui module")

            # Reload for development
            importlib.reload(atlas_material_ui)
            print("✅ Reloaded atlas_material_ui module")

            # Run the function
            print("\n🚀 Running copy_selected_to_atlas_material()...")
            result = atlas_material_ui.copy_selected_to_atlas_material()

            if result:
                print("\n🎉 SUCCESS! Atlas material created.")
            else:
                print("\n⚠️ Function returned False - check console for details")

        except ImportError as e:
            print(f"\n❌ Import Error: {e}")
            print("Make sure the bl-atlas-houdini/python directory is properly set up.")
            raise

except Exception as e:
    error_msg = f"Atlas Material Create Error:\n{str(e)}"
    print(f"\n❌ ERROR: {error_msg}")

    # Show full traceback in console
    import traceback
    traceback.print_exc()

    # Show user-friendly error
    hou.ui.displayMessage(
        error_msg + "\n\nCheck the Python Shell for details.",
        severity=hou.severityType.Error,
        title="Atlas Material Create Error"
    )

print("\n" + "="*60)
