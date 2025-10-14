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
        sys.exit(0)  # Exit cleanly without triggering outer exception handler

    print(f"📚 Asset library: {library_path}")

    # Get clipboard content
    import subprocess
    try:
        clipboard_content = subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except:
        try:
            # Fallback for different clipboard tool
            clipboard_content = subprocess.check_output(['xsel', '--clipboard'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        except:
            clipboard_content = ""

    print(f"📋 Clipboard content: '{clipboard_content}'")

    # Validate clipboard contains 16-character asset ID
    if not clipboard_content or len(clipboard_content) != 16 or not clipboard_content.replace('_', '').isalnum():
        error_msg = f"""❌ INVALID CLIPBOARD CONTENT

Expected: 16-character Asset ID (e.g., 1A9B2148E49AA001)
Current clipboard: {len(clipboard_content)} characters

Clipboard content: "{clipboard_content}"

Please copy an Asset ID from the Atlas Library frontend and try again."""

        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Invalid Clipboard")
        print(f"❌ Expected 16-char ID, got {len(clipboard_content)} characters")
        sys.exit(0)  # Exit cleanly without triggering outer exception handler

    asset_id = clipboard_content
    print(f"✅ Valid Asset ID: {asset_id}")

    # Search for asset folder with this ID
    print(f"🔍 Searching for asset with ID: {asset_id}")
    found_asset_dir = None

    for category_dir in library_path.iterdir():
        if not category_dir.is_dir():
            continue
        for subcategory_dir in category_dir.iterdir():
            if not subcategory_dir.is_dir():
                continue
            for asset_dir in subcategory_dir.iterdir():
                if not asset_dir.is_dir():
                    continue
                # Check if folder name starts with the asset ID
                if asset_dir.name.startswith(asset_id):
                    found_asset_dir = asset_dir
                    print(f"✅ Found asset folder: {asset_dir}")
                    break
            if found_asset_dir:
                break
        if found_asset_dir:
            break

    if not found_asset_dir:
        error_msg = f"""❌ ASSET NOT FOUND

Asset ID: {asset_id}

No asset folder found in library with this ID.

Please check:
- Asset exists in the library
- ID is correct (copied from frontend)
- Asset was exported successfully"""

        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Asset Not Found")
        print(f"❌ No asset folder found for ID: {asset_id}")
        sys.exit(0)  # Exit cleanly without triggering outer exception handler

    # Find available template files
    available_templates = []
    template_files = [
        ("template_redshift.hip", "obj", "Redshift (OBJ)"),
        ("template_karma.hip", "stage", "Karma (STAGE)"),
        ("template_universal.hip", "obj", "Universal (OBJ)"),
        ("template.hipnc", "obj", "Standard (OBJ)"),
        ("template.hip", "obj", "Standard (OBJ)")
    ]

    for template_name, context, display_name in template_files:
        template_path = found_asset_dir / template_name
        if template_path.exists():
            available_templates.append({
                'name': display_name,
                'file': template_name,
                'path': str(template_path),
                'context': context
            })

    if not available_templates:
        error_msg = f"""❌ NO TEMPLATE FILES FOUND

Asset: {found_asset_dir.name}
Location: {found_asset_dir}

No template files found in this asset folder.

Expected files:
- template_redshift.hip
- template_karma.hip
- template_universal.hip
- template.hipnc"""

        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="No Templates")
        print(f"❌ No template files found in: {found_asset_dir}")
        sys.exit(0)  # Exit cleanly without triggering outer exception handler

    print(f"✅ Found {len(available_templates)} template(s):")
    for tmpl in available_templates:
        print(f"   • {tmpl['name']} - {tmpl['file']}")

    # If multiple templates, let user choose
    if len(available_templates) > 1:
        template_names = [t['name'] for t in available_templates]
        selection = hou.ui.selectFromList(
            template_names,
            message=f"Asset: {found_asset_dir.name}\n\nMultiple templates found. Select one to import:",
            title="🏭 Select Template",
            column_header="Available Templates",
            num_visible_rows=len(available_templates),
            clear_on_cancel=True
        )

        if not selection:
            print("❌ User cancelled template selection")
            sys.exit(0)  # User cancelled, exit cleanly

        selected_template = available_templates[selection[0]]
    else:
        # Only one template, use it
        selected_template = available_templates[0]

    print(f"📦 Selected template: {selected_template['name']}")
    print(f"📁 Template file: {selected_template['path']}")

    # Import the asset
    try:
        # Determine parent context based on template type
        if selected_template['context'] == "stage":
            parent = hou.node("/stage")
            print(f"📍 Creating subnet in STAGE context: {parent.path()}")
        else:
            parent = hou.node("/obj")
            print(f"📍 Creating subnet in OBJ context: {parent.path()}")

        # Clean asset name (remove ID prefix if present)
        asset_name = found_asset_dir.name
        if '_' in asset_name:
            parts = asset_name.split('_', 1)
            # If first part looks like an ID (16 chars alphanumeric), use second part
            if len(parts) > 1 and len(parts[0]) == 16 and parts[0].replace('_','').isalnum():
                asset_name = parts[1]

        # Create a new subnet container for the asset
        subnet = parent.createNode("subnet", asset_name)
        print(f"📦 Created subnet: {subnet.path()}")

        # Load the template contents INSIDE the subnet
        subnet.loadChildrenFromFile(selected_template['path'])

        # Get the actual imported nodes from the subnet
        nodes = subnet.children()

        if nodes:
            print(f"✅ Imported {len(nodes)} nodes into subnet:")
            for node in nodes:
                print(f"   • {node.name()} ({node.type().name()})")

            # Select the subnet (but don't change user's current context/view)
            subnet.setSelected(True, clear_all_selected=True)

            context_label = "STAGE" if selected_template['context'] == "stage" else "OBJ"
            success_msg = f"""✅ ATLAS ASSET IMPORTED SUCCESSFULLY!

📦 Asset: {found_asset_dir.name}
🎨 Template: {selected_template['name']}
📍 Context: {context_label}
📂 Subnet: {subnet.path()}
🎯 Nodes: {len(nodes)} imported

The asset has been loaded into a subnet!"""

            hou.ui.displayMessage(success_msg, title="🎉 Import Complete")
            print("🎉 IMPORT SUCCESS!")

        else:
            # Leave empty subnet (deleting triggers pipeline callbacks)
            hou.ui.displayMessage(
                "❌ No nodes were imported from the template file.\n\nThe template may be empty or invalid.\n\nAn empty subnet was created - please delete it manually.",
                severity=hou.severityType.Error,
                title="Import Failed"
            )
            print("❌ No nodes imported - empty subnet left for manual cleanup")

    except Exception as import_error:
        error_msg = f"Import failed: {str(import_error)}"
        print(f"❌ {error_msg}")
        # Don't delete subnet - causes pipeline callback errors
        hou.ui.displayMessage(
            f"❌ {error_msg}\n\nCheck the Python Shell for details.\n\nNote: An empty subnet may have been created - delete it manually.",
            severity=hou.severityType.Error,
            title="Import Error"
        )

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