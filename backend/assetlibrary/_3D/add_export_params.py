#!/usr/bin/env python3
"""
Blacksmith Atlas - Add Export Parameters to Subnet
==================================================

Run this script to add Atlas export parameters to a selected subnet.
Use this if the right-click collapse didn't add parameters properly.

USAGE:
1. Select the Atlas subnet
2. Run this script in Houdini Python console
"""

import hou

def add_atlas_export_parameters_to_selected():
    """Add Atlas export parameters to the currently selected subnet"""
    
    try:
        selected_nodes = hou.selectedNodes()
        if not selected_nodes:
            hou.ui.displayMessage("❌ Please select an Atlas subnet first.", 
                                severity=hou.severityType.Warning, 
                                title="Add Export Parameters")
            return False
        
        if len(selected_nodes) > 1:
            hou.ui.displayMessage("❌ Please select only one subnet.", 
                                severity=hou.severityType.Warning, 
                                title="Add Export Parameters")
            return False
        
        subnet = selected_nodes[0]
        
        # Verify it's a subnet
        if subnet.type().name() != 'subnet':
            hou.ui.displayMessage(f"❌ Selected node '{subnet.name()}' is not a subnet.\nPlease select an Atlas subnet.", 
                                severity=hou.severityType.Error, 
                                title="Add Export Parameters")
            return False
        
        print(f"🔧 Adding Atlas export parameters to: {subnet.path()}")
        
        # Get asset name from subnet name
        asset_name = subnet.name()
        
        # Add the parameters
        success = add_atlas_parameters(subnet, asset_name)
        
        if success:
            # Make sure subnet is selected and visible
            subnet.setSelected(True, clear_all_selected=True)
            
            success_msg = f"""✅ Atlas Export Parameters Added!

Subnet: {subnet.path()}
Asset: {asset_name}

NEXT STEPS:
1. Configure parameters in the subnet
2. Click '🚀 Export Atlas Asset' button
3. Asset will be saved to Atlas library

The subnet now has full export capabilities!"""
            
            hou.ui.displayMessage(success_msg, title="Export Parameters Added")
            print("✅ Atlas export parameters added successfully!")
            return True
        else:
            hou.ui.displayMessage("❌ Failed to add export parameters. Check console for details.", 
                                severity=hou.severityType.Error, 
                                title="Parameter Error")
            return False
            
    except Exception as e:
        error_msg = f"Error adding export parameters: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Error")
        return False

def add_atlas_parameters(subnet, asset_name):
    """Add comprehensive Atlas export parameters to a subnet"""
    try:
        print(f"   📋 Adding parameters to {subnet.name()}...")
        
        # Get existing parameter template group
        ptg = subnet.parmTemplateGroup()
        
        # Create main Atlas Export folder
        atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", hou.folderType.Collapsible)
        atlas_folder.setDefaultValue(1)  # Open by default
        
        # Asset Information
        asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name_parm.setDefaultValue([asset_name])
        atlas_folder.addParmTemplate(asset_name_parm)
        
        # Asset Type
        asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                              ["assets", "fx", "materials", "hdas"],
                                              ["Assets", "FX", "Materials", "HDAs"])
        asset_type_parm.setDefaultValue(0)  # Default to Assets
        asset_type_parm.setScriptCallback("hou.pwd().parm('subcategory').revert()")  # Clear subcategory when changed
        asset_type_parm.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        atlas_folder.addParmTemplate(asset_type_parm)
        
        # Subcategory (dynamic based on Asset Type)
        subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                               ["blacksmith_asset", "megascans", "kitbash"],  # Default for Assets
                                               ["Blacksmith Asset", "Megascans", "Kitbash"])
        subcategory_parm.setDefaultValue(0)  # Default to first option
        subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 0 }")  # Show for Assets
        atlas_folder.addParmTemplate(subcategory_parm)
        
        # FX Subcategory
        fx_subcategory_parm = hou.MenuParmTemplate("fx_subcategory", "Subcategory", 
                                                  ["blacksmith_fx", "atmosphere", "flip", "pyro"],
                                                  ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"])
        fx_subcategory_parm.setDefaultValue(0)
        fx_subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 1 }")  # Show for FX
        atlas_folder.addParmTemplate(fx_subcategory_parm)
        
        # Materials Subcategory
        materials_subcategory_parm = hou.MenuParmTemplate("materials_subcategory", "Subcategory", 
                                                         ["blacksmith_materials", "redshift", "karma"],
                                                         ["Blacksmith Materials", "Redshift", "Karma"])
        materials_subcategory_parm.setDefaultValue(0)
        materials_subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 2 }")  # Show for Materials
        atlas_folder.addParmTemplate(materials_subcategory_parm)
        
        # HDAs Subcategory
        hdas_subcategory_parm = hou.MenuParmTemplate("hdas_subcategory", "Subcategory", 
                                                    ["blacksmith_hdas"],
                                                    ["Blacksmith HDAs"])
        hdas_subcategory_parm.setDefaultValue(0)
        hdas_subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 3 }")  # Show for HDAs
        atlas_folder.addParmTemplate(hdas_subcategory_parm)
        
        # Render Engine
        render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine", 
                                                 ["redshift", "karma"],
                                                 ["Redshift", "Karma"])
        render_engine_parm.setDefaultValue(0)  # Default to Redshift
        atlas_folder.addParmTemplate(render_engine_parm)
        
        # Description
        description_parm = hou.StringParmTemplate("description", "Description", 1)
        description_parm.setDefaultValue([f"Atlas asset: {asset_name}"])
        atlas_folder.addParmTemplate(description_parm)
        
        # Metadata Text Area
        metadata_parm = hou.StringParmTemplate("metadata", "Metadata (for search)", 5)  # 5 lines
        metadata_parm.setStringType(hou.stringParmType.Regular)
        metadata_parm.setDefaultValue(["Enter searchable metadata keywords, descriptions, or notes here..."])
        atlas_folder.addParmTemplate(metadata_parm)
        
        # Tags
        tags_parm = hou.StringParmTemplate("tags", "Search Tags", 1)
        tags_parm.setDefaultValue([""])
        atlas_folder.addParmTemplate(tags_parm)
        
        # Export status
        status_parm = hou.StringParmTemplate("export_status", "Export Status", 1)
        status_parm.setDefaultValue(["Ready to export"])
        status_parm.setReadOnly(True)
        atlas_folder.addParmTemplate(status_parm)
        
        # Export button with comprehensive callback
        export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
        export_btn.setScriptCallback(create_export_script())
        export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        atlas_folder.addParmTemplate(export_btn)
        
        # Info button
        info_btn = hou.ButtonParmTemplate("atlas_info", "ℹ️ About Atlas")
        info_btn.setScriptCallback(create_info_script())
        info_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        atlas_folder.addParmTemplate(info_btn)
        
        # Add folder to parameter group
        ptg.addParmTemplate(atlas_folder)
        
        # Apply to subnet
        subnet.setParmTemplateGroup(ptg)
        
        print(f"   ✅ Added Atlas export parameters")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to add parameters: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_export_script():
    """Create the export callback script"""
    return '''
# Blacksmith Atlas Export
import sys
from pathlib import Path

try:
    print("🏭 BLACKSMITH ATLAS EXPORT")
    print("=" * 40)
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Import with reload for development
    import importlib
    if 'assetlibrary._3D.houdiniae' in sys.modules:
        importlib.reload(sys.modules['assetlibrary._3D.houdiniae'])
    
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    subnet = hou.pwd()
    print(f"📦 Exporting from: {subnet.path()}")
    
    # Get parameters
    asset_name = subnet.parm("asset_name").eval().strip()
    asset_type_idx = int(subnet.parm("asset_type").eval())
    description = subnet.parm("description").eval().strip()
    metadata = subnet.parm("metadata").eval().strip()
    tags_str = subnet.parm("tags").eval().strip()
    render_engine_idx = int(subnet.parm("render_engine").eval())
    
    if not asset_name:
        subnet.parm("export_status").set("❌ No asset name")
        hou.ui.displayMessage("Asset name required!", severity=hou.severityType.Error)
        raise Exception("Asset name required")
    
    # Convert asset type and get subcategory
    asset_types = ["Assets", "FX", "Materials", "HDAs"]
    asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
    
    # Get the appropriate subcategory based on asset type
    subcategory = "Unknown"
    if asset_type_idx == 0:  # Assets
        subcategory_idx = int(subnet.parm("subcategory").eval())
        subcategories = ["Blacksmith Asset", "Megascans", "Kitbash"]
        subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Blacksmith Asset"
    elif asset_type_idx == 1:  # FX
        subcategory_idx = int(subnet.parm("fx_subcategory").eval())
        subcategories = ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"]
        subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Blacksmith FX"
    elif asset_type_idx == 2:  # Materials
        subcategory_idx = int(subnet.parm("materials_subcategory").eval())
        subcategories = ["Blacksmith Materials", "Redshift", "Karma"]
        subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Blacksmith Materials"
    elif asset_type_idx == 3:  # HDAs
        subcategory_idx = int(subnet.parm("hdas_subcategory").eval())
        subcategories = ["Blacksmith HDAs"]
        subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Blacksmith HDAs"
    
    # Get render engine
    render_engines = ["Redshift", "Karma"]
    render_engine = render_engines[render_engine_idx] if render_engine_idx < len(render_engines) else "Redshift"
    
    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    subnet.parm("export_status").set("🔄 Exporting...")
    
    print(f"🏷️ Asset: {asset_name}")
    print(f"📂 Asset Type: {asset_type}")
    print(f"📋 Subcategory: {subcategory}")
    print(f"🎨 Render Engine: {render_engine}")
    print(f"📝 Description: {description}")
    print(f"📄 Metadata: {metadata[:100]}..." if len(metadata) > 100 else f"📄 Metadata: {metadata}")
    print(f"🏷️ Tags: {tags_list}")
    
    # Create extended tags list including metadata for search
    extended_tags = tags_list.copy()
    extended_tags.extend([asset_type.lower(), subcategory.lower().replace(' ', '_'), render_engine.lower()])
    if metadata and metadata != "Enter searchable metadata keywords, descriptions, or notes here...":
        # Add metadata words as tags
        metadata_words = [word.strip().lower() for word in metadata.split() if len(word.strip()) > 2]
        extended_tags.extend(metadata_words)
    
    # Create exporter
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=f"{asset_type}/{subcategory}",  # Hierarchical category
        description=description,
        tags=extended_tags,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=metadata
    )
    
    # Get nodes to export
    nodes_to_export = subnet.children()
    if not nodes_to_export:
        subnet.parm("export_status").set("❌ No nodes")
        hou.ui.displayMessage("No nodes found to export!", severity=hou.severityType.Error)
        raise Exception("No nodes to export")
    
    print(f"📦 Exporting {len(nodes_to_export)} nodes...")
    
    # Export
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        subnet.parm("export_status").set("✅ Export complete!")
        hou.ui.displayMessage(f"Export successful!\\n\\nLocation: {exporter.asset_folder}", 
                            title="Atlas Export Complete")
        print(f"✅ Export complete: {exporter.asset_folder}")
    else:
        subnet.parm("export_status").set("❌ Export failed")
        hou.ui.displayMessage("Export failed! Check console.", severity=hou.severityType.Error)

except Exception as e:
    print(f"❌ Export error: {e}")
    try:
        hou.pwd().parm("export_status").set("❌ Error")
    except:
        pass
    hou.ui.displayMessage(f"Export error: {e}", severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
'''

def create_info_script():
    """Create the info callback script"""
    return '''
info = """🏭 BLACKSMITH ATLAS EXPORT

WORKFLOW:
1. Configure asset name and category
2. Add description and search tags
3. Click 'Export Atlas Asset' button
4. Asset saved with textures and metadata

FEATURES:
• Template-based perfect reconstruction
• Automatic texture extraction
• Multiple export formats
• Organized library structure

LOCATION: /net/library/atlaslib/3D/Assets/"""

hou.ui.displayMessage(info, title="Atlas Export Info")
'''

# Main execution
if __name__ == "__main__":
    add_atlas_export_parameters_to_selected()

# Also provide the function for direct calling
def run():
    """Wrapper function for easy calling"""
    return add_atlas_export_parameters_to_selected()

print("🔧 Atlas export parameter script loaded")
print("💡 Run: add_atlas_export_parameters_to_selected() or run()")