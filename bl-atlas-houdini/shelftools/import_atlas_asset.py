#!/usr/bin/env python3
"""
Blacksmith Atlas - Import Atlas Asset (Standalone)
=================================================

This script provides a simple browser to import Atlas assets from the library.
Standalone version that works without the main Atlas codebase.

Usage:
1. Run this script (or paste into shelf button)
2. Browse and select assets from the Atlas library
3. Import into current Houdini scene

Author: Blacksmith VFX
Version: 3.0 (Standalone)
"""

import hou
import os
import sys
from pathlib import Path
import json

print("\n" + "📚"*20)
print("BLACKSMITH ATLAS - IMPORT ASSET (STANDALONE)")
print("📚"*20 + "\n")

try:
    # Auto-detect the bl-atlas-houdini directory
    # Try multiple methods since __file__ may not be available in shelf buttons
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
        if test_path.exists() and (test_path / "python" / "config_manager.py").exists():
            bl_atlas_root = test_path
            break

    # Method 2: If not found, try to detect from current working directory
    if not bl_atlas_root:
        cwd = Path.cwd()
        # Look for bl-atlas-houdini in current directory or parent directories
        for parent in [cwd] + list(cwd.parents):
            for subdir in parent.iterdir() if parent.exists() else []:
                if subdir.name == "bl-atlas-houdini" and (subdir / "python" / "config_manager.py").exists():
                    bl_atlas_root = subdir
                    break
            if bl_atlas_root:
                break

    if not bl_atlas_root:
        raise Exception("Could not find bl-atlas-houdini directory. Please ensure it's installed in a standard location.")

    python_path = bl_atlas_root / "python"
    print(f"📁 BL-Atlas root: {bl_atlas_root}")

    # Add python directory to sys.path
    if str(python_path) not in sys.path:
        sys.path.insert(0, str(python_path))
        print(f"✅ Added to sys.path: {python_path}")

    # Import configuration
    try:
        from config_manager import get_network_config
        config = get_network_config()
        print("✅ Loaded Atlas network configuration")
    except ImportError as e:
        print(f"⚠️ Could not load config: {e}")
        # Use fallback
        class FallbackConfig:
            @property
            def asset_library_3d(self):
                return "/net/library/atlaslib/3D"
        config = FallbackConfig()

    # Get the asset library path
    library_path = Path(config.asset_library_3d)

    if not library_path.exists():
        hou.ui.displayMessage(
            f"❌ Asset library not found: {library_path}\n\nPlease check the configuration.",
            severity=hou.severityType.Error,
            title="Library Not Found"
        )
        raise Exception("Asset library not found")

    print(f"📚 Asset library: {library_path}")

    # Find all asset directories
    asset_dirs = []
    for category_dir in library_path.iterdir():
        if category_dir.is_dir():
            for subcategory_dir in category_dir.iterdir():
                if subcategory_dir.is_dir():
                    for asset_dir in subcategory_dir.iterdir():
                        if asset_dir.is_dir():
                            # Check if it has a template file
                            template_file = asset_dir / "template.hipnc"
                            if template_file.exists():
                                asset_dirs.append({
                                    'name': asset_dir.name,
                                    'path': str(asset_dir),
                                    'template': str(template_file),
                                    'category': category_dir.name,
                                    'subcategory': subcategory_dir.name
                                })

    if not asset_dirs:
        hou.ui.displayMessage(
            "📚 No Atlas assets found in the library.\n\nThe library appears to be empty.",
            severity=hou.severityType.Warning,
            title="No Assets Found"
        )
        print("📚 No assets found in library")
    else:
        print(f"📚 Found {len(asset_dirs)} assets in library")

        # Create a simple selection dialog
        asset_names = []
        for asset in asset_dirs:
            display_name = f"{asset['name']} ({asset['category']}/{asset['subcategory']})"
            asset_names.append(display_name)

        # Show selection dialog
        selection = hou.ui.selectFromList(
            asset_names,
            message="Select an Atlas asset to import:",
            title="🏭 Atlas Asset Library",
            column_header="Available Assets",
            num_visible_rows=15,
            clear_on_cancel=True
        )

        if selection:
            selected_index = selection[0]
            selected_asset = asset_dirs[selected_index]

            print(f"📦 Selected asset: {selected_asset['name']}")
            print(f"📁 Template: {selected_asset['template']}")

            # Import the asset
            try:
                # Get current context
                current_context = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
                if current_context:
                    current_node = current_context.currentNode()
                    if current_node:
                        parent = current_node
                    else:
                        parent = current_context.root()
                else:
                    # Fallback to obj context
                    parent = hou.node("/obj")

                print(f"📍 Importing into: {parent.path()}")

                # Load the template
                nodes = parent.loadChildrenFromFile(selected_asset['template'])

                if nodes:
                    print(f"✅ Imported {len(nodes)} nodes:")
                    for node in nodes:
                        print(f"   • {node.name()} ({node.type().name()})")

                    # Select the imported nodes
                    for node in nodes:
                        node.setSelected(True, clear_all_selected=(node == nodes[0]))

                    # Frame the imported nodes
                    if current_context:
                        current_context.frameSelection()

                    success_msg = f"""✅ ATLAS ASSET IMPORTED SUCCESSFULLY!

📦 Asset: {selected_asset['name']}
📂 Category: {selected_asset['category']}/{selected_asset['subcategory']}
📍 Location: {parent.path()}
🎯 Nodes: {len(nodes)} imported

The asset has been loaded into your scene!"""

                    hou.ui.displayMessage(success_msg, title="🎉 Import Complete")
                    print("🎉 IMPORT SUCCESS!")

                else:
                    hou.ui.displayMessage(
                        "❌ No nodes were imported from the template file.",
                        severity=hou.severityType.Error,
                        title="Import Failed"
                    )
                    print("❌ No nodes imported")

            except Exception as import_error:
                error_msg = f"Import failed: {str(import_error)}"
                print(f"❌ {error_msg}")
                hou.ui.displayMessage(
                    f"❌ {error_msg}\n\nCheck the Python Shell for details.",
                    severity=hou.severityType.Error,
                    title="Import Error"
                )

        else:
            print("📚 User cancelled asset selection")

except Exception as e:
    error_msg = f"Atlas Import Error:\n{str(e)}"
    print(f"\n❌ ERROR: {error_msg}")

    # Show full traceback in console
    import traceback
    traceback.print_exc()

    # Show user-friendly error
    hou.ui.displayMessage(
        error_msg + "\n\nCheck the Python Shell for details.",
        severity=hou.severityType.Error,
        title="Atlas Import Error"
    )

print("\n" + "="*60)