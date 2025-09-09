#!/usr/bin/env python3
"""
Test script to verify thumbnail parameters are created correctly
"""

import sys
from pathlib import Path

# Add backend path
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    import hou
    print("✅ Houdini available")
    
    # Import the shelf creation function
    from assetlibrary.houdini.tools.shelf_create_atlas_asset import add_atlas_parameters
    
    # Create a test subnet
    geo = hou.node('/obj').createNode('geo', 'test_atlas_asset')
    subnet = geo.createNode('subnet', 'test_subnet')
    
    # Add Atlas parameters
    print("🔧 Adding Atlas parameters...")
    add_atlas_parameters(subnet, "Test Asset")
    
    # Check if thumbnail parameters exist
    print("\n📋 Checking parameters:")
    
    # List all parameters
    ptg = subnet.parmTemplateGroup()
    
    def print_folder_contents(folder, indent=0):
        prefix = "  " * indent
        print(f"{prefix}📁 {folder.label()}")
        for parm_template in folder.parmTemplates():
            if hasattr(parm_template, 'parmTemplates'):
                # It's a folder
                print_folder_contents(parm_template, indent + 1)
            else:
                # It's a parameter
                print(f"{prefix}  📄 {parm_template.name()} - {parm_template.label()}")
    
    # Find the main Atlas folder
    atlas_folder = ptg.find("atlas_folder")
    if atlas_folder:
        print_folder_contents(atlas_folder)
        
        # Specifically check for thumbnail folder
        thumbnail_folder = None
        for parm_template in atlas_folder.parmTemplates():
            if parm_template.name() == "thumbnail_folder":
                thumbnail_folder = parm_template
                break
        
        if thumbnail_folder:
            print(f"\n✅ Found thumbnail folder: {thumbnail_folder.label()}")
            print(f"   📁 Folder type: {thumbnail_folder.folderType()}")
            print(f"   📋 Contains {len(thumbnail_folder.parmTemplates())} parameters:")
            for parm in thumbnail_folder.parmTemplates():
                print(f"      • {parm.name()} - {parm.label()}")
        else:
            print("\n❌ Thumbnail folder not found!")
    else:
        print("❌ Atlas folder not found!")
    
    # Check if parameters exist on the actual node
    print(f"\n🔍 Checking actual node parameters:")
    if subnet.parm("thumbnail_action"):
        print(f"✅ thumbnail_action parameter exists")
        print(f"   Current value: {subnet.parm('thumbnail_action').eval()}")
        menu_items = subnet.parm("thumbnail_action").menuItems()
        menu_labels = subnet.parm("thumbnail_action").menuLabels()
        print(f"   Menu options: {list(zip(menu_items, menu_labels))}")
    else:
        print("❌ thumbnail_action parameter not found")
        
    if subnet.parm("thumbnail_file"):
        print(f"✅ thumbnail_file parameter exists")
    else:
        print("❌ thumbnail_file parameter not found")
    
    # Clean up
    geo.destroy()
    print("\n🧹 Test completed, cleaned up test nodes")
    
except ImportError:
    print("❌ Houdini not available - this test needs to run inside Houdini")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()