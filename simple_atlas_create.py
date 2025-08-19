# Simple Atlas Create - Everything in one place
import hou

def create_atlas_asset_simple():
    """Simple Atlas Asset creation with parameters - all in one function"""
    
    print("🏭 SIMPLE ATLAS CREATE")
    
    # Get selected nodes
    selected_nodes = hou.selectedNodes()
    if not selected_nodes:
        hou.ui.displayMessage("Please select nodes first!", severity=hou.severityType.Warning)
        return
    
    # Get asset name
    result = hou.ui.readInput("Atlas Asset Name:", initial_contents="MyAtlasAsset")
    if result[0] != 0 or not result[1].strip():
        return
    
    asset_name = result[1].strip()
    parent = selected_nodes[0].parent()
    
    # Create subnet
    subnet = parent.createNode("subnet", asset_name)
    subnet.setComment("Atlas Asset - Ready for Export")
    subnet.setColor(hou.Color(0.2, 0.6, 1.0))
    
    # Copy nodes into subnet
    for node in selected_nodes:
        subnet.copyItems([node])
    
    # Layout nodes
    subnet.layoutChildren()
    
    # ADD PARAMETERS - Simple approach
    ptg = subnet.parmTemplateGroup()
    
    # Asset Name
    asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
    asset_name_parm.setDefaultValue([asset_name])
    
    # Asset Type
    asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                          ["Assets", "FX", "Materials", "HDAs"],
                                          ["Assets", "FX", "Materials", "HDAs"])
    asset_type_parm.setDefaultValue(0)
    
    # Subcategory
    subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                           ["Blacksmith Asset", "Megascans", "Kitbash"],
                                           ["Blacksmith Asset", "Megascans", "Kitbash"])
    subcategory_parm.setDefaultValue(0)
    
    # Render Engine
    render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine", 
                                             ["Redshift", "Karma"],
                                             ["Redshift", "Karma"])
    render_engine_parm.setDefaultValue(0)
    
    # Tags
    tags_parm = hou.StringParmTemplate("tags", "Tags", 1)
    tags_parm.setDefaultValue([""])
    
    # Export Status
    status_parm = hou.StringParmTemplate("export_status", "Status", 1)
    status_parm.setDefaultValue(["Ready to export"])
    
    # Export Button
    export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
    export_btn.setScriptCallback('''
# Simple Export Script
import sys
from pathlib import Path

try:
    print("🚀 Starting Atlas Export...")
    
    # Add paths
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Import exporter
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    # Get subnet and parameters
    subnet = hou.pwd()
    asset_name = subnet.parm("asset_name").eval()
    asset_type_idx = subnet.parm("asset_type").eval()
    subcategory_idx = subnet.parm("subcategory").eval()
    render_engine_idx = subnet.parm("render_engine").eval()
    tags = subnet.parm("tags").eval()
    
    # Convert indices to names
    asset_types = ["Assets", "FX", "Materials", "HDAs"]
    subcategories = ["Blacksmith Asset", "Megascans", "Kitbash"]
    render_engines = ["Redshift", "Karma"]
    
    asset_type = asset_types[asset_type_idx]
    subcategory = subcategories[subcategory_idx]
    render_engine = render_engines[render_engine_idx]
    
    print(f"Asset: {asset_name}")
    print(f"Type: {asset_type}")
    print(f"Subcategory: {subcategory}")
    print(f"Render Engine: {render_engine}")
    
    # Update status
    subnet.parm("export_status").set("Exporting...")
    
    # Create exporter
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,
        description=f"Atlas {asset_type} asset: {asset_name}",
        tags=[tags] if tags else [],
        asset_type=asset_type,
        render_engine=render_engine,
        metadata={}
    )
    
    # Get nodes to export
    nodes_to_export = subnet.children()
    
    if not nodes_to_export:
        subnet.parm("export_status").set("No nodes to export")
        hou.ui.displayMessage("No nodes found in subnet!", severity=hou.severityType.Error)
        raise Exception("No nodes to export")
    
    # Export
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        subnet.parm("export_status").set("✅ Exported!")
        hou.ui.displayMessage(f"Atlas Asset exported successfully!\\n\\nLocation: {exporter.asset_folder}", 
                            title="Export Complete")
        print("✅ Export successful!")
    else:
        subnet.parm("export_status").set("❌ Export failed")
        hou.ui.displayMessage("Export failed! Check console.", severity=hou.severityType.Error)
        print("❌ Export failed")

except Exception as e:
    print(f"❌ Export error: {e}")
    try:
        hou.pwd().parm("export_status").set(f"Error: {str(e)}")
    except:
        pass
    hou.ui.displayMessage(f"Export error: {str(e)}", severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
''')
    export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    
    # Create folder with all parameters
    parameters = [asset_name_parm, asset_type_parm, subcategory_parm, render_engine_parm, tags_parm, status_parm, export_btn]
    atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", parameters, hou.folderType.Collapsible)
    atlas_folder.setDefaultValue(1)  # Open by default
    
    # Add to subnet
    ptg.addParmTemplate(atlas_folder)
    subnet.setParmTemplateGroup(ptg)
    
    # Position and select subnet
    if selected_nodes:
        first_pos = selected_nodes[0].position()
        subnet.setPosition([first_pos[0] + 3, first_pos[1]])
    
    subnet.setSelected(True, clear_all_selected=True)
    
    print(f"✅ Created Atlas Asset: {subnet.path()}")
    print(f"📋 Parameters added - check subnet!")
    
    hou.ui.displayMessage(f"✅ Atlas Asset '{asset_name}' created!\\n\\nSubnet created with export parameters.\\nConfigure and click 'Export Atlas Asset' button.", 
                        title="Atlas Asset Created")

# Call the function
create_atlas_asset_simple()