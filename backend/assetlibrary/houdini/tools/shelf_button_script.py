# Blacksmith Atlas - Collapse to Atlas Asset (Shelf Button)
# Copy this entire script and paste it into a Houdini shelf button

import hou
im    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    # Force reload the module to pick up changes - MORE AGGRESSIVE
    import importlib
    import sys
    from assetlibrary._3D import houdiniae
    
    # Remove from cache and reload
    if 'assetlibrary._3D.houdiniae' in sys.modules:
        del sys.modules['assetlibrary._3D.houdiniae']
    if 'houdiniae' in sys.modules:
        del sys.modules['houdiniae']
    
    # Reimport and reload
    from assetlibrary._3D import houdiniae
    importlib.reload(houdiniae)
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    print("🔄 Aggressively reloaded houdiniae module for latest changes")s
from pathlib import Path

def collapse_to_atlas_asset():
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
    
    # Subcategory
    subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                           ["props", "characters", "environments", "vehicles", "general"],
                                           ["Props", "Characters", "Environments", "Vehicles", "General"])
    
    # Description
    description_parm = hou.StringParmTemplate("description", "Description", 1)
    description_parm.setDefaultValue([f"Atlas asset: {asset_name}"])
    
    # Export status
    status_parm = hou.StringParmTemplate("export_status", "Status", 1)
    status_parm.setDefaultValue(["Ready to export"])
    
    # Export button
    export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
    export_btn.setScriptCallback(get_export_script())
    export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    
    # Create folder with parameters
    parm_list = [asset_name_parm, subcategory_parm, description_parm, status_parm, export_btn]
    atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", parm_list, hou.folderType.Collapsible)
    atlas_folder.setDefaultValue(1)
    
    ptg.addParmTemplate(atlas_folder)
    subnet.setParmTemplateGroup(ptg)

def get_export_script():
    """Return the export script for the button"""
    return '''
try:
    import sys
    from pathlib import Path
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    # Force reload the module to pick up changes
    import importlib
    from assetlibrary._3D import houdiniae
    importlib.reload(houdiniae)
    print("Reloaded houdiniae module for latest changes")
    
    subnet = hou.pwd()
    asset_name = subnet.parm("asset_name").eval().strip()
    
    if not asset_name:
        hou.ui.displayMessage("Asset name required!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("No asset name")
        raise Exception("Asset name required")
    
    subcategory_idx = int(subnet.parm("subcategory").eval())
    subcategories = ["Props", "Characters", "Environments", "Vehicles", "General"]
    subcategory = subcategories[subcategory_idx]
    description = subnet.parm("description").eval().strip()
    
    subnet.parm("export_status").set("Exporting...")
    
    # Debug: Check for materials before export
    print("PRE-EXPORT DEBUG: Checking nodes for materials...")
    nodes_to_export = subnet.children()
    material_count = 0
    
    for node in nodes_to_export:
        print("Node: " + node.name() + " (" + node.type().name() + ")")
        
        # Check shop_materialpath
        if node.parm("shop_materialpath"):
            mat_path = node.parm("shop_materialpath").eval()
            if mat_path:
                print("Material: " + mat_path)
                material_count += 1
            else:
                print("No material assigned")
        else:
            print("No shop_materialpath parameter")
    
    print("Found " + str(material_count) + " material assignments before export")
    
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,
        description=description
    )
    
    if not nodes_to_export:
        hou.ui.displayMessage("No nodes to export!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("No nodes")
        raise Exception("No nodes to export")
    
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        subnet.parm("export_status").set("Exported!")
        hou.ui.displayMessage("Atlas Asset exported successfully! Location: " + str(exporter.asset_folder), 
                            title="Export Complete")
    else:
        subnet.parm("export_status").set("Export failed")
        hou.ui.displayMessage("Export failed!", severity=hou.severityType.Error)

except Exception as e:
    print("Export error: " + str(e))
    try:
        hou.pwd().parm("export_status").set("Error")
    except:
        pass
    hou.ui.displayMessage("Export error: " + str(e), severity=hou.severityType.Error)
'''

# Run the main function
collapse_to_atlas_asset()
