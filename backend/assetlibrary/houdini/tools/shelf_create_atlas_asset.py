#!/usr/bin/env python3
"""
Blacksmith Atlas - Create Atlas Asset (Shelf Module)
==================================================

This module contains the logic for the "Create Atlas Asset" shelf button.
The shelf button just imports and calls the main function from this module.
"""

import hou
import sys
from pathlib import Path

def create_atlas_asset():
    """Main function to collapse selected nodes to Atlas Asset"""
    
    print("🏭 BLACKSMITH ATLAS - COLLAPSE TO ASSET")
    
    # Get selected nodes
    selected_nodes = hou.selectedNodes()
    if not selected_nodes:
        hou.ui.displayMessage("❌ Please select nodes to collapse into Atlas Asset.", 
                            severity=hou.severityType.Warning)
        return
    
    # Verify same parent
    parent = selected_nodes[0].parent()
    for node in selected_nodes[1:]:
        if node.parent() != parent:
            hou.ui.displayMessage("❌ All selected nodes must be in the same context.", 
                                severity=hou.severityType.Error)
            return
    
    # Get asset name
    result = hou.ui.readInput("Enter name for the Atlas Asset:", 
                            initial_contents="MyAtlasAsset",
                            title="Atlas Asset Name")
    if result[0] != 0 or not result[1].strip():
        return
    
    asset_name = result[1].strip()
    
    try:
        # Create an empty subnet first
        subnet = parent.createNode("subnet", asset_name)
        subnet.setComment("Blacksmith Atlas Asset - Ready for Export")
        subnet.setColor(hou.Color(0.2, 0.6, 1.0))  # Blue
        
        print(f"📦 Created subnet: {subnet.path()}")
        
        # Copy selected nodes into the subnet
        print(f"📋 Copying {len(selected_nodes)} nodes into subnet...")
        copied_nodes = []
        
        for node in selected_nodes:
            # Copy each node into the subnet
            copied_node = subnet.copyItems([node])[0]
            copied_nodes.append(copied_node)
            print(f"   ✅ Copied: {node.name()} -> {copied_node.name()}")
        
        # Try to maintain connections between copied nodes
        print("🔗 Reconnecting copied nodes...")
        for i, original_node in enumerate(selected_nodes):
            copied_node = copied_nodes[i]
            
            # Reconnect inputs if the input nodes were also copied
            for input_idx in range(len(original_node.inputs())):
                input_node = original_node.inputConnections()[input_idx].inputNode() if original_node.inputConnections() else None
                if input_node and input_node in selected_nodes:
                    # Find the corresponding copied input node
                    original_input_idx = selected_nodes.index(input_node)
                    copied_input_node = copied_nodes[original_input_idx]
                    copied_node.setInput(input_idx, copied_input_node)
        
        # Layout nodes inside subnet
        try:
            subnet.layoutChildren()
        except:
            pass
        
        # Add Atlas parameters
        add_atlas_parameters(subnet, asset_name)
        
        # Select and position the subnet near the original nodes
        if selected_nodes:
            # Position subnet near the first selected node
            first_node_pos = selected_nodes[0].position()
            subnet.setPosition([first_node_pos[0] + 3, first_node_pos[1]])  # Offset to the right
        
        subnet.setSelected(True, clear_all_selected=True)
        
        hou.ui.displayMessage(f"✅ Atlas Asset '{asset_name}' created successfully!\n\n{len(copied_nodes)} nodes copied into subnet.\nOriginal nodes preserved.\n\nConfigure parameters and click 'Export Atlas Asset' button.", 
                            title="Atlas Asset Created")
        
        print(f"✅ Created Atlas Asset: {subnet.path()}")
        print(f"📋 Original nodes preserved, {len(copied_nodes)} nodes copied")
        
    except Exception as e:
        hou.ui.displayMessage(f"❌ Error: {e}", severity=hou.severityType.Error)

def add_atlas_parameters(subnet, asset_name):
    """Add export parameters to subnet"""
    ptg = subnet.parmTemplateGroup()
    
    # Create individual parameters first
    # Asset name
    asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
    asset_name_parm.setDefaultValue([asset_name])
    
    # Asset Type
    asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                          ["assets", "fx", "materials", "hdas"],
                                          ["Assets", "FX", "Materials", "HDAs"])
    asset_type_parm.setDefaultValue(0)  # Default to Assets
    asset_type_parm.setScriptCallback('''
node = hou.pwd()
asset_type = node.parm("asset_type").eval()

# Define subcategory options for each asset type
subcategory_options = {
    0: (["blacksmith_asset", "megascans", "kitbash"], ["Blacksmith Asset", "Megascans", "Kitbash"]),
    1: (["blacksmith_fx", "atmosphere", "flip", "pyro"], ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"]),
    2: (["blacksmith_materials", "redshift_mat", "karma_mat"], ["Blacksmith Materials", "Redshift", "Karma"]),
    3: (["blacksmith_hdas"], ["Blacksmith HDAs"])
}

# Get the parameter template group
ptg = node.parmTemplateGroup()

# Find the subcategory parameter
subcategory_parm = ptg.find("subcategory")
if subcategory_parm:
    # Get the new menu items for the selected asset type
    menu_items, menu_labels = subcategory_options.get(asset_type, (["blacksmith_asset"], ["Blacksmith Asset"]))
    
    # Update the subcategory parameter with new menu items
    subcategory_parm.setMenuItems(menu_items)
    subcategory_parm.setMenuLabels(menu_labels)
    subcategory_parm.setDefaultValue(0)
    
    # Replace the parameter template
    ptg.replace(subcategory_parm.name(), subcategory_parm)
    node.setParmTemplateGroup(ptg)
    
    # Reset the subcategory parameter to first option
    node.parm("subcategory").set(0)
''')
    asset_type_parm.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    
    # Dynamic Subcategory dropdown (starts with Assets options)
    subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                           ["blacksmith_asset", "megascans", "kitbash"],
                                           ["Blacksmith Asset", "Megascans", "Kitbash"])
    subcategory_parm.setDefaultValue(0)
    
    # Render Engine
    render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine", 
                                             ["redshift", "karma"],
                                             ["Redshift", "Karma"])
    render_engine_parm.setDefaultValue(0)  # Default to Redshift
    
    # Tags
    tags_parm = hou.StringParmTemplate("tags", "Search Tags", 1)
    tags_parm.setDefaultValue([""])
    
    # Export status
    status_parm = hou.StringParmTemplate("export_status", "Status", 1)
    status_parm.setDefaultValue(["Ready to export"])
    status_parm.setTags({"editor": "readonly"})
    
    # Export button
    export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
    export_btn.setScriptCallback(get_export_script())
    export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    
    # Create folder with parameters
    parm_list = [asset_name_parm, asset_type_parm, subcategory_parm, render_engine_parm,
                 tags_parm, status_parm, export_btn]
    atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", parm_list, hou.folderType.Collapsible)
    atlas_folder.setDefaultValue(1)
    
    ptg.addParmTemplate(atlas_folder)
    subnet.setParmTemplateGroup(ptg)

def get_export_script():
    """Return the export script for the button"""
    return '''
print("🚀 Export button clicked!")
try:
    import sys
    from pathlib import Path
    
    print("📥 Setting up paths...")
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Also add the _3D directory path directly
    _3d_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D")
    if str(_3d_path) not in sys.path:
        sys.path.insert(0, str(_3d_path))
    
    print("📦 Loading modules...")
    
    # Force reload the module to pick up changes
    import importlib
    
    # Remove from cache if exists
    modules_to_remove = [
        'assetlibrary.houdini.houdiniae',
        'houdiniae'
    ]
    for mod in modules_to_remove:
        if mod in sys.modules:
            del sys.modules[mod]
    
    # Try direct import first
    try:
        import houdiniae
        importlib.reload(houdiniae)
        TemplateAssetExporter = houdiniae.TemplateAssetExporter
        print("✅ Loaded houdiniae module directly")
    except ImportError as e:
        print(f"⚠️ Direct import failed: {e}")
        # Fallback to full path import
        from assetlibrary._3D import houdiniae
        importlib.reload(houdiniae)
        TemplateAssetExporter = houdiniae.TemplateAssetExporter
        print("✅ Loaded houdiniae module via assetlibrary path")
    
    print("📋 Getting subnet parameters...")
    subnet = hou.pwd()
    asset_name = subnet.parm("asset_name").eval().strip()
    
    if not asset_name:
        print("❌ No asset name provided")
        hou.ui.displayMessage("Asset name required!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("No asset name")
        raise Exception("Asset name required")
    
    # Get new parameter structure
    asset_type_idx = int(subnet.parm("asset_type").eval())
    subcategory_idx = int(subnet.parm("subcategory").eval())
    tags_str = subnet.parm("tags").eval().strip()
    render_engine_idx = int(subnet.parm("render_engine").eval())
    
    # Convert asset type
    asset_types = ["Assets", "FX", "Materials", "HDAs"]
    asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
    
    # Get subcategory based on asset type and current selection
    subcategory_options = {
        0: ["Blacksmith Asset", "Megascans", "Kitbash"],
        1: ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"],
        2: ["Blacksmith Materials", "Redshift", "Karma"],
        3: ["Blacksmith HDAs"]
    }
    
    available_subcategories = subcategory_options.get(asset_type_idx, ["Blacksmith Asset"])
    subcategory = available_subcategories[subcategory_idx] if subcategory_idx < len(available_subcategories) else available_subcategories[0]
    
    # Get render engine
    render_engines = ["Redshift", "Karma"]
    render_engine = render_engines[render_engine_idx] if render_engine_idx < len(render_engines) else "Redshift"
    
    # Process tags
    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    print(f"📋 Asset: {asset_name}")
    print(f"📂 Asset Type: {asset_type}")
    print(f"📋 Subcategory: {subcategory}")
    print(f"🎨 Render Engine: {render_engine}")
    print(f"🏷️ Tags: {tags_list}")
    
    subnet.parm("export_status").set("Exporting...")
    
    # Debug: Check for materials before export
    print("🔍 Checking nodes for materials...")
    nodes_to_export = subnet.children()
    material_count = 0
    
    for node in nodes_to_export:
        print(f"   Node: {node.name()} ({node.type().name()})")
        
        # Check shop_materialpath
        if node.parm("shop_materialpath"):
            mat_path = node.parm("shop_materialpath").eval()
            if mat_path:
                print(f"   Material: {mat_path}")
                material_count += 1
            else:
                print("   No material assigned")
        else:
            print("   No shop_materialpath parameter")
    
    print(f"Found {material_count} material assignments before export")
    
    # Store the export context in metadata
    export_context = subnet.parent().path()
    print(f"📍 Export context: {export_context}")
    
    print("🏭 Creating exporter...")
    
    # Create extended tags list for search
    extended_tags = tags_list.copy()
    extended_tags.extend([asset_type.lower(), subcategory.lower().replace(' ', '_'), render_engine.lower()])
    
    # Create comprehensive metadata for frontend filtering
    from datetime import datetime
    hierarchy_metadata = {
        "dimension": "3D",  # Always 3D from Houdini
        "asset_type": asset_type,  # Assets, FX, Materials, HDAs
        "subcategory": subcategory,  # Blacksmith Asset, Megascans, etc.
        "render_engine": render_engine,
        "export_context": export_context,
        "houdini_version": f"{hou.applicationVersion()[0]}.{hou.applicationVersion()[1]}.{hou.applicationVersion()[2]}",
        "export_time": str(datetime.now()),
        "tags": extended_tags
    }
    
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,  # Just the subcategory name (e.g. "Blacksmith Asset")
        description=f"Atlas {asset_type} asset: {asset_name}",  # Auto-generate description
        tags=extended_tags,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=hierarchy_metadata  # Pass structured metadata instead of empty string
    )
    
    if not nodes_to_export:
        print("❌ No nodes to export")
        hou.ui.displayMessage("No nodes to export!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("No nodes")
        raise Exception("No nodes to export")
    
    print(f"🚀 Starting export of {len(nodes_to_export)} nodes...")
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        print("✅ Export successful!")
        
        # Update metadata file to ensure hierarchy data is preserved
        metadata_file = exporter.asset_folder / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            # Ensure hierarchy metadata is present for frontend filtering
            metadata.update(hierarchy_metadata)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"📝 Updated metadata with hierarchy data for frontend filtering")
            print(f"   📊 Dimension: {hierarchy_metadata['dimension']}")
            print(f"   📂 Asset Type: {hierarchy_metadata['asset_type']}")
            print(f"   📋 Subcategory: {hierarchy_metadata['subcategory']}")
        
        subnet.parm("export_status").set("Exported!")
        
        # Show enhanced success message with template file info
        template_file = exporter.clipboard_folder / f"{asset_name}_template.hip"
        success_message = ("Atlas Asset exported successfully!\\n\\n" +
                          "Location: " + str(exporter.asset_folder) + "\\n\\n" +
                          "TEMPLATE FILE READY!\\n" +
                          "A template file has been created with pre-mapped paths:\\n" +
                          str(template_file) + "\\n\\n" +
                          "To use in any scene:\\n" +
                          "1. Navigate to desired context (e.g., inside geo node)\\n" +
                          "2. Python Console: parent_node.loadChildrenFromFile('" + str(template_file) + "')\\n" +
                          "   OR File > Merge and select the template file\\n\\n" +
                          "All paths are already mapped - it just works!")
        
        hou.ui.displayMessage(success_message, title="Export Complete - Template Ready!")
    else:
        print("❌ Export failed")
        subnet.parm("export_status").set("Export failed")
        hou.ui.displayMessage("Export failed!", severity=hou.severityType.Error)

except Exception as e:
    print(f"❌ Export error: {e}")
    import traceback
    traceback.print_exc()
    try:
        hou.pwd().parm("export_status").set("Error: " + str(e))
    except:
        pass
    hou.ui.displayMessage("Export error: " + str(e), severity=hou.severityType.Error)
'''

# Main function to call from shelf button
def main():
    """Main entry point for shelf button"""
    create_atlas_asset()

if __name__ == "__main__":
    main()
