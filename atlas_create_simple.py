#!/usr/bin/env python3
"""
Atlas Create Simple - Standalone Atlas Asset Creator
===================================================

Simple, editable Atlas asset creation tool.
Edit this file to modify behavior, shelf button will reload automatically.
"""

import hou

def create_atlas_asset():
    """Main function to create Atlas Asset with export parameters"""
    
    print("🏭 ATLAS CREATE SIMPLE")
    print("=" * 50)
    
    # Get selected nodes
    selected_nodes = hou.selectedNodes()
    if not selected_nodes:
        hou.ui.displayMessage("Please select nodes first!", 
                            severity=hou.severityType.Warning,
                            title="Atlas Create")
        return False
    
    print(f"📦 Selected {len(selected_nodes)} nodes")
    
    # Verify same parent
    parent = selected_nodes[0].parent()
    for node in selected_nodes[1:]:
        if node.parent() != parent:
            hou.ui.displayMessage("All nodes must be in the same network!", 
                                severity=hou.severityType.Error,
                                title="Atlas Create")
            return False
    
    # Get asset name
    result = hou.ui.readInput("Enter Atlas Asset Name:", 
                            initial_contents="MyAtlasAsset",
                            title="Atlas Asset Name")
    if result[0] != 0 or not result[1].strip():
        print("❌ Cancelled by user")
        return False
    
    asset_name = result[1].strip()
    print(f"🏷️ Asset name: {asset_name}")
    
    try:
        # Create subnet
        subnet = parent.createNode("subnet", asset_name)
        subnet.setComment("🏭 Atlas Asset - Ready for Export")
        subnet.setColor(hou.Color(0.2, 0.6, 1.0))  # Blue
        
        print(f"📦 Created subnet: {subnet.path()}")
        
        # Copy nodes into subnet
        copied_nodes = []
        for node in selected_nodes:
            copied_node = subnet.copyItems([node])[0]
            copied_nodes.append(copied_node)
            print(f"   ✅ Copied: {node.name()} -> {copied_node.name()}")
        
        # Layout nodes
        try:
            subnet.layoutChildren()
        except:
            pass
        
        # Add Atlas Export Parameters
        success = add_atlas_parameters(subnet, asset_name)
        
        if success:
            print("✅ Atlas export parameters added")
        else:
            print("❌ Failed to add parameters")
        
        # Position and select subnet
        if selected_nodes:
            first_pos = selected_nodes[0].position()
            subnet.setPosition([first_pos[0] + 3, first_pos[1]])
        
        subnet.setSelected(True, clear_all_selected=True)
        
        # Success message
        hou.ui.displayMessage(f"✅ Atlas Asset '{asset_name}' created successfully!\n\n"
                            f"Subnet: {subnet.path()}\n"
                            f"Nodes copied: {len(copied_nodes)}\n"
                            f"Parameters: {'Added' if success else 'Failed'}\n\n"
                            f"Configure parameters and click 'Export Atlas Asset' button.",
                            title="Atlas Asset Created")
        
        print(f"🎉 Atlas Asset created: {subnet.path()}")
        return True
        
    except Exception as e:
        error_msg = f"Error creating Atlas Asset: {str(e)}"
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Atlas Create Error")
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def add_atlas_parameters(subnet, asset_name):
    """Add Atlas export parameters to the subnet"""
    
    try:
        print("⚙️ Adding Atlas export parameters...")
        
        ptg = subnet.parmTemplateGroup()
        
        # Create parameters list
        parameters = []
        
        # Asset Name
        asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name_parm.setDefaultValue([asset_name])
        parameters.append(asset_name_parm)
        
        # Asset Type
        asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                              ["Assets", "FX", "Materials", "HDAs"],
                                              ["Assets", "FX", "Materials", "HDAs"])
        asset_type_parm.setDefaultValue(0)
        parameters.append(asset_type_parm)
        
        # Subcategory
        subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                               ["Blacksmith Asset", "Megascans", "Kitbash"],
                                               ["Blacksmith Asset", "Megascans", "Kitbash"])
        subcategory_parm.setDefaultValue(0)
        parameters.append(subcategory_parm)
        
        # Render Engine
        render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine", 
                                                 ["Redshift", "Karma"],
                                                 ["Redshift", "Karma"])
        render_engine_parm.setDefaultValue(0)
        parameters.append(render_engine_parm)
        
        # Description
        description_parm = hou.StringParmTemplate("description", "Description", 1)
        description_parm.setDefaultValue([f"Atlas asset: {asset_name}"])
        parameters.append(description_parm)
        
        # Tags
        tags_parm = hou.StringParmTemplate("tags", "Tags (comma-separated)", 1)
        tags_parm.setDefaultValue([""])
        parameters.append(tags_parm)
        
        # Export Status
        status_parm = hou.StringParmTemplate("export_status", "Export Status", 1)
        status_parm.setDefaultValue(["Ready to export"])
        status_parm.setReadOnly(True)
        parameters.append(status_parm)
        
        # Export Button
        export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
        export_btn.setScriptCallback(get_export_script())
        export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        parameters.append(export_btn)
        
        # Info Button
        info_btn = hou.ButtonParmTemplate("atlas_info", "ℹ️ Info")
        info_btn.setScriptCallback(get_info_script())
        info_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        parameters.append(info_btn)
        
        # Create Atlas Export folder
        atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", 
                                             parameters, hou.folderType.Collapsible)
        atlas_folder.setDefaultValue(1)  # Open by default
        
        # Add folder to subnet
        ptg.addParmTemplate(atlas_folder)
        subnet.setParmTemplateGroup(ptg)
        
        print(f"   ✅ Added {len(parameters)} parameters in Atlas Export folder")
        return True
        
    except Exception as e:
        print(f"   ❌ Parameter addition failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_export_script():
    """Return the export script for the Export button"""
    return '''
# Atlas Export Script
import sys
from pathlib import Path

try:
    print("🚀 ATLAS EXPORT STARTING...")
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Import exporter
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    # Get current subnet and parameters
    subnet = hou.pwd()
    asset_name = subnet.parm("asset_name").eval().strip()
    asset_type_idx = int(subnet.parm("asset_type").eval())
    subcategory_idx = int(subnet.parm("subcategory").eval())
    render_engine_idx = int(subnet.parm("render_engine").eval())
    description = subnet.parm("description").eval().strip()
    tags_str = subnet.parm("tags").eval().strip()
    
    # Validate asset name
    if not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("Asset name is required!", severity=hou.severityType.Error)
        raise Exception("Asset name required")
    
    # Convert indices to names
    asset_types = ["Assets", "FX", "Materials", "HDAs"]
    subcategories = ["Blacksmith Asset", "Megascans", "Kitbash"]
    render_engines = ["Redshift", "Karma"]
    
    asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
    subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Blacksmith Asset"
    render_engine = render_engines[render_engine_idx] if render_engine_idx < len(render_engines) else "Redshift"
    
    # Process tags
    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    print(f"📋 EXPORT CONFIG:")
    print(f"   Asset: {asset_name}")
    print(f"   Type: {asset_type}")
    print(f"   Subcategory: {subcategory}")
    print(f"   Render Engine: {render_engine}")
    print(f"   Description: {description}")
    print(f"   Tags: {tags_list}")
    
    # Update status
    subnet.parm("export_status").set("🔄 Exporting...")
    
    # Create metadata
    from datetime import datetime
    metadata = {
        "dimension": "3D",
        "asset_type": asset_type,
        "subcategory": subcategory,
        "render_engine": render_engine,
        "export_time": str(datetime.now()),
        "description": description,
        "tags": tags_list + [asset_type.lower(), subcategory.lower().replace(' ', '_'), render_engine.lower()]
    }
    
    # Create exporter
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,
        description=description,
        tags=tags_list,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=metadata
    )
    
    # Get nodes to export
    nodes_to_export = subnet.children()
    if not nodes_to_export:
        subnet.parm("export_status").set("❌ No nodes")
        hou.ui.displayMessage("No nodes found in subnet to export!", severity=hou.severityType.Error)
        raise Exception("No nodes to export")
    
    print(f"📦 Exporting {len(nodes_to_export)} nodes...")
    
    # Export!
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        subnet.parm("export_status").set("✅ Exported!")
        success_msg = f"""✅ Atlas Asset Export Successful!
        
🏷️ Asset: {asset_name}
🆔 ID: {exporter.asset_id}
📂 Type: {asset_type}/{subcategory}
📍 Location: {exporter.asset_folder}

🎯 Asset is now in the Atlas library!"""
        
        hou.ui.displayMessage(success_msg, title="Export Complete")
        print("🎉 EXPORT SUCCESS!")
        
    else:
        subnet.parm("export_status").set("❌ Export failed")
        hou.ui.displayMessage("Export failed! Check console for details.", severity=hou.severityType.Error)
        print("❌ EXPORT FAILED")

except Exception as e:
    error_msg = f"Export error: {str(e)}"
    print(f"❌ {error_msg}")
    
    try:
        hou.pwd().parm("export_status").set(f"❌ Error: {str(e)}")
    except:
        pass
    
    hou.ui.displayMessage(f"❌ {error_msg}\\n\\nCheck console for details.", severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
'''

def get_info_script():
    """Return the info script for the Info button"""
    return '''
info_text = """🏭 ATLAS EXPORT INFO

WORKFLOW:
1. Configure asset name and category
2. Add description and tags
3. Click 'Export Atlas Asset' button
4. Asset saved to Atlas library

FEATURES:
• Template-based reconstruction
• Automatic texture extraction  
• Multiple export formats
• Searchable metadata

LOCATION: /net/library/atlaslib/3D/{category}/

Edit atlas_create_simple.py to modify behavior!"""

hou.ui.displayMessage(info_text, title="Atlas Export Info")
'''

# Main entry point
if __name__ == "__main__":
    create_atlas_asset()