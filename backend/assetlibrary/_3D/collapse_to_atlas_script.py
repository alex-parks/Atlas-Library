#!/usr/bin/env python3
"""
Blacksmith Atlas - Simple Collapse Script
=========================================

Run this script in Houdini to collapse selected nodes to Atlas Asset.
You can also assign this to a shelf button for easy access.

USAGE:
1. Select nodes in Houdini
2. Run this script in the Python Shell or from a shelf button
3. Enter asset name when prompted
4. Configure parameters and export
"""

import hou

def collapse_selected_to_atlas_asset():
    """
    Collapse selected nodes into an Atlas Asset subnet with parameters
    
    This function provides compatibility with both shelf button and right-click menu usage.
    For enhanced right-click menu functionality, see right_click_collapse.py
    """
    
    # Import and use the enhanced right-click collapse function
    try:
        from assetlibrary._3D.right_click_collapse import collapse_nodes_to_atlas_asset
        return collapse_nodes_to_atlas_asset()
    except ImportError:
        # Fallback to original implementation if right_click_collapse is not available
        return collapse_selected_to_atlas_asset_original()

def collapse_selected_to_atlas_asset_original():
    """Original collapse implementation (preserved for compatibility)"""
    
    print("🏭 BLACKSMITH ATLAS - COLLAPSE TO ASSET")
    print("=" * 50)
    
    try:
        # Get selected nodes
        selected_nodes = hou.selectedNodes()
        if not selected_nodes:
            hou.ui.displayMessage("❌ Please select nodes to collapse into Atlas Asset.", 
                                severity=hou.severityType.Warning)
            return False
        
        print(f"📦 Found {len(selected_nodes)} selected nodes:")
        for node in selected_nodes:
            print(f"   • {node.name()} ({node.type().name()})")
        
        # Verify all nodes have the same parent
        parent = selected_nodes[0].parent()
        for node in selected_nodes[1:]:
            if node.parent() != parent:
                hou.ui.displayMessage("❌ All selected nodes must be in the same context.", 
                                    severity=hou.severityType.Error)
                return False
        
        print(f"📂 Parent context: {parent.path()}")
        
        # Get asset name from user
        result = hou.ui.readInput("Atlas Asset Name", 
                                ("Enter name for the Atlas Asset:",), 
                                ("MyAtlasAsset",))
        if result[0] == 0:  # User clicked OK
            asset_name = result[1].strip()
            if not asset_name:
                print("❌ Asset name cannot be empty")
                return False
        else:
            print("❌ User cancelled")
            return False
        
        print(f"🏷️ Asset name: '{asset_name}'")
        
        # Create the subnet by collapsing selected nodes
        print("🔄 Collapsing nodes into subnet...")
        try:
            subnet = parent.collapseIntoSubnet(selected_nodes, asset_name)
            subnet.setComment("Blacksmith Atlas Asset - Ready for Export")
            subnet.setColor(hou.Color(0.2, 0.6, 1.0))  # Blue color
            
            print(f"✅ Created subnet: {subnet.path()}")
            
        except Exception as collapse_error:
            print(f"❌ Failed to collapse nodes: {collapse_error}")
            hou.ui.displayMessage(f"Failed to collapse nodes: {collapse_error}", 
                                severity=hou.severityType.Error)
            return False
        
        # Add Atlas-specific parameters
        print("⚙️ Adding Atlas export parameters...")
        success = add_atlas_export_parameters(subnet, asset_name)
        
        if success:
            # Layout the subnet
            try:
                subnet.layoutChildren()
            except:
                pass
            
            # Position and select the subnet
            subnet.setSelected(True, clear_all_selected=True)
            
            # Show success message
            success_msg = f"""✅ Atlas Asset Created Successfully!

Asset: {asset_name}
Subnet: {subnet.path()}
Nodes: {len(selected_nodes)} collapsed

NEXT STEPS:
1. Configure parameters in the subnet
2. Click 'Export Atlas Asset' button
3. Asset will be saved to library

The subnet is now ready for export!"""
            
            hou.ui.displayMessage(success_msg, title="Atlas Asset Created")
            
            print("🎉 Atlas Asset creation complete!")
            print(f"   Subnet: {subnet.path()}")
            print(f"   Ready for export with {len(selected_nodes)} nodes")
            
            return True
            
        else:
            print("⚠️ Subnet created but parameter setup failed")
            return False
        
    except Exception as e:
        error_msg = f"❌ Error creating Atlas Asset: {str(e)}"
        print(error_msg)
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        
        import traceback
        traceback.print_exc()
        return False

def add_atlas_export_parameters(subnet, asset_name):
    """Add comprehensive Atlas export parameters to the subnet"""
    try:
        print(f"   Adding parameters to {subnet.name()}...")
        
        # Get the parameter template group
        ptg = subnet.parmTemplateGroup()
        
        # Create main Atlas Export folder
        atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", hou.folderType.Collapsible)
        atlas_folder.setDefaultValue(1)  # Open by default
        
        # Asset Information Section
        info_folder = hou.FolderParmTemplate("asset_info", "Asset Information", hou.folderType.Simple)
        
        # Asset name
        asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name_parm.setDefaultValue([asset_name])
        asset_name_parm.setHelp("Name of the asset for export to the library")
        info_folder.addParmTemplate(asset_name_parm)
        
        # Subcategory menu
        subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                               ["props", "characters", "environments", "vehicles", 
                                                "architecture", "furniture", "weapons", "organic", 
                                                "hard_surface", "general"],
                                               ["Props", "Characters", "Environments", "Vehicles",
                                                "Architecture", "Furniture", "Weapons", "Organic",
                                                "Hard Surface", "General"])
        subcategory_parm.setDefaultValue(0)  # Default to Props
        subcategory_parm.setHelp("Asset subcategory for library organization")
        info_folder.addParmTemplate(subcategory_parm)
        
        # Description
        description_parm = hou.StringParmTemplate("description", "Description", 1)
        description_parm.setDefaultValue([f"Atlas asset: {asset_name}"])
        description_parm.setHelp("Detailed description of the asset")
        info_folder.addParmTemplate(description_parm)
        
        # Tags
        tags_parm = hou.StringParmTemplate("tags", "Tags", 1)
        tags_parm.setDefaultValue([""])
        tags_parm.setHelp("Comma-separated tags for searching (e.g., vehicle, helicopter, military)")
        info_folder.addParmTemplate(tags_parm)
        
        atlas_folder.addParmTemplate(info_folder)
        
        # Export Controls Section
        controls_folder = hou.FolderParmTemplate("export_controls", "Export Controls", hou.folderType.Simple)
        
        # Status display
        status_parm = hou.StringParmTemplate("export_status", "Status", 1)
        status_parm.setDefaultValue(["Ready to export"])
        status_parm.setReadOnly(True)
        status_parm.setHelp("Current export status")
        controls_folder.addParmTemplate(status_parm)
        
        # Export button
        export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
        export_btn.setHelp("Export this Atlas Asset as a template to the library")
        
        # Create the export callback script
        export_script = '''
# Blacksmith Atlas Asset Export
try:
    import sys
    from pathlib import Path
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    # Get current subnet
    subnet = hou.pwd()
    
    print(f"🏭 Starting Atlas Asset export from {subnet.path()}")
    
    # Get parameters
    asset_name = subnet.parm("asset_name").eval().strip()
    subcategory_idx = int(subnet.parm("subcategory").eval())
    description = subnet.parm("description").eval().strip()
    tags = subnet.parm("tags").eval().strip()
    
    # Validation
    if not asset_name:
        hou.ui.displayMessage("❌ Asset name is required!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("❌ Export failed - No asset name")
        raise Exception("Asset name is required")
    
    # Convert subcategory index to name
    subcategories = ["Props", "Characters", "Environments", "Vehicles", "Architecture", 
                    "Furniture", "Weapons", "Organic", "Hard_Surface", "General"]
    subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Props"
    
    # Update status
    subnet.parm("export_status").set("🔄 Exporting...")
    
    print(f"📋 Export parameters:")
    print(f"   Asset: {asset_name}")
    print(f"   Category: {subcategory}")
    print(f"   Description: {description}")
    print(f"   Tags: {tags}")
    
    # Create exporter
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,
        description=description,
        tags=tags.split(',') if tags else []
    )
    
    # Get nodes to export (all children of subnet)
    nodes_to_export = subnet.children()
    if not nodes_to_export:
        hou.ui.displayMessage("❌ No nodes found inside subnet to export!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("❌ Export failed - No nodes")
        raise Exception("No nodes to export")
    
    print(f"📦 Exporting {len(nodes_to_export)} nodes as template")
    
    # Perform export
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        # Update status
        subnet.parm("export_status").set(f"✅ Exported successfully!")
        
        # Show success message
        success_msg = f"""✅ Atlas Asset Export Successful!

Asset: {asset_name}
ID: {exporter.asset_id}
Category: Assets/{subcategory}/

Location: {exporter.asset_folder}

Template Method:
• Template file: {asset_name}.hip
• Metadata: asset_info.json
• Perfect reconstruction guaranteed

The asset is now available in the Atlas library!"""
        
        hou.ui.displayMessage(success_msg, title="Atlas Export Complete")
        
        print(f"🎉 Export completed successfully!")
        print(f"   Location: {exporter.asset_folder}")
        
    else:
        subnet.parm("export_status").set("❌ Export failed")
        hou.ui.displayMessage("❌ Export failed! Check the console for details.", 
                            severity=hou.severityType.Error)
        print("❌ Export failed!")

except Exception as e:
    print(f"❌ Export error: {e}")
    import traceback
    traceback.print_exc()
    
    # Update status
    try:
        subnet = hou.pwd()
        if subnet.parm("export_status"):
            subnet.parm("export_status").set(f"❌ Export error")
    except:
        pass
    
    hou.ui.displayMessage(f"Export error: {e}", severity=hou.severityType.Error)
'''
        
        export_btn.setScriptCallback(export_script)
        export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        controls_folder.addParmTemplate(export_btn)
        
        # Info button
        info_btn = hou.ButtonParmTemplate("atlas_info", "ℹ️ About Atlas Assets")
        info_btn.setHelp("Show information about Atlas Assets")
        info_btn.setScriptCallback('''
info_text = """🏭 BLACKSMITH ATLAS ASSETS

Template-based asset system using Houdini's native serialization.

KEY FEATURES:
• Perfect reconstruction using saveChildrenToFile()
• No complex JSON serialization needed
• Works with any Houdini nodes/networks
• Future-proof and version-independent

WORKFLOW:
1. Select nodes and collapse to Atlas Asset
2. Configure asset parameters
3. Export creates .hip template + metadata
4. Import reconstructs perfectly with loadChildrenFromFile()

LIBRARY LOCATION:
/net/library/atlaslib/3D/Assets/{subcategory}/

This approach is infinitely more reliable than JSON reconstruction!"""

hou.ui.displayMessage(info_text, title="About Atlas Assets")
''')
        info_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        controls_folder.addParmTemplate(info_btn)
        
        atlas_folder.addParmTemplate(controls_folder)
        
        # Add the main folder to the parameter group
        ptg.addParmTemplate(atlas_folder)
        
        # Apply parameters to subnet
        subnet.setParmTemplateGroup(ptg)
        
        print(f"   ✅ Added comprehensive Atlas parameters")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to add parameters: {e}")
        import traceback
        traceback.print_exc()
        return False

# Main execution
if __name__ == "__main__":
    collapse_selected_to_atlas_asset()

# Also make it available as a function
def run_atlas_collapse():
    """Wrapper function for shelf buttons"""
    return collapse_selected_to_atlas_asset()

print("🏭 Blacksmith Atlas collapse script loaded")
print("💡 Run: collapse_selected_to_atlas_asset() or run_atlas_collapse()")
