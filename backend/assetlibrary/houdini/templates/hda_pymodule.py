#!/usr/bin/env python3
"""
Blacksmith Atlas HDA - PyModule for Template-Based Asset Exporter
================================================================

This PyModule provides template-based asset export using Houdini's native
saveChildrenToFile() and loadChildrenFromFile() methods for perfect reconstruction.

WORKFLOW:
1. Select matnet nodes and Object nodes to include in asset
2. Right click → "Collapse to BL Atlas Asset" 
3. This creates a subnet containing selected nodes
4. Name the asset and configure parameters
5. Export saves .hip template + JSON metadata to library

HDA Setup Instructions:
1. Create Object-level HDA with "Collapse to BL Atlas Asset" functionality
2. Add asset_name, subcategory, and other parameters
3. Place this code in PyModule
4. Set export callback to: hou.phm().export_atlas_asset()
5. Set import callback to: hou.phm().import_atlas_asset()
"""

def reload_modules():
    """Reload all Blacksmith Atlas modules for development"""
    import sys
    import importlib
    from pathlib import Path
    
    try:
        # Add backend path if not already there
        backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        # List of modules to reload
        modules_to_reload = [
            'assetlibrary._3D.houdiniae',
            'assetlibrary.config',
            'assetlibrary.models'
        ]
        
        # Reload each module if it's already imported
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    print(f"🔄 Reloaded {module_name}")
                except Exception as e:
                    print(f"⚠️  Failed to reload {module_name}: {e}")
        
        print("✅ Module reload complete")
        return True
        
    except Exception as e:
        print(f"❌ Module reload failed: {e}")
        return False

def ensure_fresh_import():
    """Ensure we get fresh imports of the modules"""
    import sys
    from pathlib import Path
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Force reload modules before importing
    reload_modules()
    
    # Now import fresh
    from assetlibrary._3D.houdiniae import (
        TemplateAssetExporter,
        list_available_subcategories, 
        search_assets_in_library
    )
    
    return {
        'TemplateAssetExporter': TemplateAssetExporter,
        'list_available_subcategories': list_available_subcategories,
        'search_assets_in_library': search_assets_in_library
    }

def export_atlas_asset():
    """Main export function for template-based asset export"""
    
    # Get the HDA node
    node = hou.pwd()
    
    try:
        print("🏭 Starting Blacksmith Atlas template-based export...")
        
        # Get fresh imports with auto-reload
        modules = ensure_fresh_import()
        TemplateAssetExporter = modules['TemplateAssetExporter']
        
        # Get parameters from HDA
        asset_name = node.parm("asset_name").eval()
        subcategory_value = node.parm("subcategory").eval()
        description = node.parm("description").eval() if node.parm("description") else ""
        tags = node.parm("tags").eval() if node.parm("tags") else ""
        
        print(f"📋 Export Parameters:")
        print(f"   Asset: {asset_name}")
        print(f"   Subcategory: {subcategory_value}")
        print(f"   Description: {description}")
        print(f"   Tags: {tags}")
        
        # Handle menu parameters - convert indices to actual values
        subcategories = ["Props", "Characters", "Environments", "Vehicles", "Architecture", 
                        "Furniture", "Weapons", "Organic", "Hard_Surface", "General"]
        
        # Convert menu indices to actual values
        if isinstance(subcategory_value, (int, float)):
            index = int(subcategory_value)
            subcategory = subcategories[index] if 0 <= index < len(subcategories) else "Props"
        elif isinstance(subcategory_value, str) and subcategory_value.isdigit():
            index = int(subcategory_value)
            subcategory = subcategories[index] if 0 <= index < len(subcategories) else "Props"
        else:
            subcategory = str(subcategory_value) if subcategory_value else "Props"
        
        # Validation
        if not asset_name:
            hou.ui.displayMessage("❌ Asset name is required!", severity=hou.severityType.Error)
            return False
            
        print(f"✅ Final Values: {asset_name} | {subcategory}")
        
        # Create the template exporter
        exporter = TemplateAssetExporter(
            asset_name=asset_name,
            subcategory=subcategory,
            description=description,
            tags=tags.split(',') if tags else []
        )
        print(f"🔧 Template exporter created with ID: {exporter.asset_id}")
        
        # Get the nodes to export from HDA
        # For now, use all children of the HDA as the template
        nodes_to_export = node.children()
        if not nodes_to_export:
            hou.ui.displayMessage("❌ No nodes found inside HDA to export!", severity=hou.severityType.Error)
            return False
        
        print(f"📦 Found {len(nodes_to_export)} nodes to export as template")
        
        # Perform the template export
        print("🎯 Exporting asset template...")
        success = exporter.export_as_template(node, nodes_to_export)
        
        if success:
            # Update HDA parameters with results
            _update_hda_parameters(node, exporter)
            
            # Show success message
            message = f"""✅ Template Asset Export Successful!

Asset: {asset_name}
ID: {exporter.asset_id}
Category: Assets/{subcategory}/

Location: {exporter.asset_folder}

Template Method:
• Template file: {exporter.asset_name}.hip 
• Metadata: asset_info.json
• Perfect reconstruction using Houdini's native methods

The asset template has been saved and can be reconstructed perfectly!"""
            
            hou.ui.displayMessage(message, title="Blacksmith Atlas Template Export Complete")
            
            print(f"🎉 Template export completed successfully!")
            print(f"   Location: {exporter.asset_folder}")
            
            return True
            
        else:
            print("❌ Template export failed!")
            _update_export_status(node, "❌ Export Failed")
            hou.ui.displayMessage("❌ Template export failed! Check the console for details.", 
                                severity=hou.severityType.Error)
            return False
            
    except Exception as e:
        error_msg = f"❌ Export error: {str(e)}"
        print(error_msg)
        _update_export_status(node, "❌ Export Error")
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        
        import traceback
        traceback.print_exc()
        return False

def import_atlas_asset():
    """Import and reconstruct an asset using template files"""
    try:
        print("📥 Starting Blacksmith Atlas template-based import...")
        
        # Get the HDA node
        node = hou.pwd()
        
        # Get asset name to import
        import_name_parm = node.parm("import_name")
        if not import_name_parm:
            hou.ui.displayMessage("No import_name parameter found.", severity=hou.severityType.Warning)
            return False
            
        asset_name = import_name_parm.eval()
        if not asset_name or not asset_name.strip():
            hou.ui.displayMessage("Enter asset name to import.", severity=hou.severityType.Warning)
            return False
        
        print(f"🎯 Looking for asset: {asset_name}")
        
        # Search for the asset in the library
        found_asset = find_asset_by_name(asset_name.strip())
        
        if not found_asset:
            hou.ui.displayMessage(f"Asset '{asset_name}' not found in library.\n\nTip: Try searching with partial names.", 
                                severity=hou.severityType.Warning)
            return False
        
        asset_folder = found_asset['folder']
        template_file = asset_folder / "Data" / f"{found_asset['name']}.hip"
        
        if not template_file.exists():
            hou.ui.displayMessage(f"Template file not found: {template_file}", 
                                severity=hou.severityType.Error)
            return False
        
        print(f"📄 Loading template: {template_file}")
        
        # Load the template into current context
        parent_node = hou.node("/obj")  # Or get from parameter
        
        try:
            # Use Houdini's native loadChildrenFromFile method
            parent_node.loadChildrenFromFile(str(template_file))
            
            # Show success message
            success_msg = f"""✅ Asset Import Successful!

Asset: {found_asset['asset_name']}
Template loaded from: {template_file}

All nodes, connections, and parameters have been reconstructed perfectly!"""
            
            hou.ui.displayMessage(success_msg, title="Blacksmith Atlas Template Import Complete")
            
            print(f"🎉 Template import completed successfully!")
            return True
            
        except Exception as load_error:
            error_msg = f"Failed to load template: {load_error}"
            print(f"❌ {error_msg}")
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            return False
        
    except Exception as e:
        error_msg = f"❌ Import error: {str(e)}"
        print(error_msg)
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        
        import traceback
        traceback.print_exc()
        return False

def collapse_to_atlas_asset():
    """Collapse selected nodes into an Atlas Asset subnet"""
    try:
        print("🔄 Collapsing selected nodes to Blacksmith Atlas Asset...")
        
        # Get selected nodes
        selected_nodes = hou.selectedNodes()
        if not selected_nodes:
            hou.ui.displayMessage("Please select nodes to collapse into Atlas Asset.", 
                                severity=hou.severityType.Warning)
            return False
        
        # Get the common parent
        parent = selected_nodes[0].parent()
        for node in selected_nodes[1:]:
            if node.parent() != parent:
                hou.ui.displayMessage("All selected nodes must be in the same context.", 
                                    severity=hou.severityType.Error)
                return False
        
        # Create subnet
        subnet_name = hou.ui.readInput("Atlas Asset Name", ("Enter name for the Atlas Asset:",))[1]
        if not subnet_name:
            return False
        
        # Create the subnet
        subnet = parent.collapseIntoSubnet(selected_nodes, subnet_name)
        subnet.setComment("Blacksmith Atlas Asset - Ready for Export")
        
        # Add Atlas asset parameters to the subnet
        _add_atlas_parameters(subnet)
        
        print(f"✅ Created Atlas Asset subnet: {subnet.name()}")
        hou.ui.displayMessage(f"Atlas Asset '{subnet_name}' created successfully!\n\nConfigure parameters and use Export button.", 
                            title="Atlas Asset Created")
        
        return True
        
    except Exception as e:
        error_msg = f"❌ Collapse error: {str(e)}"
        print(error_msg)
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        return False

def _add_atlas_parameters(subnet):
    """Add Atlas-specific parameters to the subnet"""
    try:
        # Get the parameter template group
        ptg = subnet.parmTemplateGroup()
        
        # Add Atlas parameters
        folder = hou.FolderParmTemplate("atlas_folder", "Atlas Export")
        
        # Asset name
        asset_name = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name.setDefaultValue([subnet.name()])
        folder.addParmTemplate(asset_name)
        
        # Subcategory menu
        subcategory = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                         ["props", "characters", "environments", "vehicles", 
                                          "architecture", "furniture", "weapons", "organic", 
                                          "hard_surface", "general"],
                                         ["Props", "Characters", "Environments", "Vehicles",
                                          "Architecture", "Furniture", "Weapons", "Organic",
                                          "Hard Surface", "General"])
        folder.addParmTemplate(subcategory)
        
        # Description
        description = hou.StringParmTemplate("description", "Description", 1)
        folder.addParmTemplate(description)
        
        # Tags
        tags = hou.StringParmTemplate("tags", "Tags", 1)
        tags.setHelp("Comma-separated tags for searching")
        folder.addParmTemplate(tags)
        
        # Export button
        export_btn = hou.ButtonParmTemplate("export_btn", "Export Atlas Asset")
        export_btn.setScriptCallback("hou.phm().export_atlas_asset()")
        export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        folder.addParmTemplate(export_btn)
        
        # Add folder to parameter group
        ptg.addParmTemplate(folder)
        
        # Apply parameters
        subnet.setParmTemplateGroup(ptg)
        
        print(f"✅ Added Atlas parameters to {subnet.name()}")
        
    except Exception as e:
        print(f"⚠️ Could not add Atlas parameters: {e}")

def _update_hda_parameters(node, exporter):
    """Helper function to update HDA parameters with export results"""
    try:
        if node.parm("export_status"):
            node.parm("export_status").set("✅ Export Successful!")
        if node.parm("asset_id"):
            node.parm("asset_id").set(exporter.asset_id)
        if node.parm("export_path"):
            node.parm("export_path").set(str(exporter.asset_folder))
    except Exception as e:
        print(f"⚠️ Could not update HDA parameters: {e}")

def _update_export_status(node, status):
    """Helper function to update export status"""
    try:
        if node.parm("export_status"):
            node.parm("export_status").set(status)
    except Exception as e:
        print(f"⚠️ Could not update export status: {e}")

def find_asset_by_name(asset_name):
    """Find an asset in the library by name"""
    try:
        from pathlib import Path
        
        atlas_lib = Path("/net/library/atlaslib/3D/Assets")
        
        if not atlas_lib.exists():
            print("❌ Atlas library not found")
            return None
        
        print(f"🔍 Searching for asset: {asset_name}")
        
        # Search through all subcategories
        for subcategory_folder in atlas_lib.iterdir():
            if subcategory_folder.is_dir():
                for asset_folder in subcategory_folder.iterdir():
                    if asset_folder.is_dir():
                        # Check if folder name contains asset name
                        if asset_name.lower() in asset_folder.name.lower():
                            # Check if it has template file
                            info_file = asset_folder / "Data" / "asset_info.json"
                            if info_file.exists():
                                import json
                                try:
                                    with open(info_file, 'r') as f:
                                        info = json.load(f)
                                    
                                    return {
                                        'folder': asset_folder,
                                        'name': asset_folder.name,
                                        'asset_name': info.get('name', asset_folder.name),
                                        'subcategory': subcategory_folder.name
                                    }
                                except:
                                    continue
        
        print(f"❌ No assets found matching: {asset_name}")
        return None
    
    except Exception as e:
        print(f"❌ Error searching for asset: {e}")
        return None

def get_available_subcategories():
    """Get list of available subcategories for menu"""
    return ["Props", "Characters", "Environments", "Vehicles", "Architecture", 
            "Furniture", "Weapons", "Organic", "Hard_Surface", "General"]

def browse_atlas_library():
    """Browse the Atlas library and show available assets"""
    try:
        from pathlib import Path
        import json
        
        atlas_lib = Path("/net/library/atlaslib/3D/Assets")
        
        if not atlas_lib.exists():
            hou.ui.displayMessage("Atlas library not found.", severity=hou.severityType.Warning)
            return
        
        # Scan for assets
        found_assets = []
        
        for subcategory_folder in atlas_lib.iterdir():
            if subcategory_folder.is_dir():
                subcategory = subcategory_folder.name
                
                for asset_folder in subcategory_folder.iterdir():
                    if asset_folder.is_dir():
                        info_file = asset_folder / "Data" / "asset_info.json"
                        
                        if info_file.exists():
                            try:
                                with open(info_file, 'r') as f:
                                    info = json.load(f)
                                
                                asset_info = {
                                    'name': info.get('name', asset_folder.name),
                                    'id': info.get('id', 'Unknown'),
                                    'subcategory': subcategory,
                                    'description': info.get('description', ''),
                                    'created': info.get('created_at', 'Unknown')
                                }
                                found_assets.append(asset_info)
                                
                            except Exception as e:
                                print(f"⚠️ Error reading {info_file}: {e}")
        
        if not found_assets:
            hou.ui.displayMessage("No assets found in the Atlas library.", 
                                severity=hou.severityType.Warning)
            return
        
        # Format asset list for display
        asset_list = f"🏭 BLACKSMITH ATLAS LIBRARY\n"
        asset_list += f"Found {len(found_assets)} template assets:\n\n"
        
        # Group by subcategory
        by_subcategory = {}
        for asset in found_assets:
            subcategory = asset['subcategory']
            if subcategory not in by_subcategory:
                by_subcategory[subcategory] = []
            by_subcategory[subcategory].append(asset)
        
        for subcategory, assets in by_subcategory.items():
            asset_list += f"📁 {subcategory} ({len(assets)} assets)\n"
            for asset in assets[:5]:  # Show first 5 per category
                asset_list += f"   • {asset['name']} - {asset['description'][:50]}{'...' if len(asset['description']) > 50 else ''}\n"
            if len(assets) > 5:
                asset_list += f"   ... and {len(assets) - 5} more\n"
            asset_list += "\n"
        
        asset_list += f"📍 Location: {atlas_lib}\n"
        asset_list += f"💡 Use Import function to load any asset template!"
        
        hou.ui.displayMessage(asset_list, title="Atlas Library Browser")
        
    except Exception as e:
        hou.ui.displayMessage(f"Error browsing library: {e}", severity=hou.severityType.Error)

# Button callback functions
def export_button_callback():
    """Export button callback"""
    return export_atlas_asset()

def import_button_callback():
    """Import button callback"""
    return import_atlas_asset()

def collapse_button_callback():
    """Collapse button callback"""
    return collapse_to_atlas_asset()

# Legacy function names for compatibility
def export_asset():
    """Legacy function name - redirects to new template export"""
    return export_atlas_asset()

def import_asset():
    """Legacy function name - redirects to new template import"""
    return import_atlas_asset()

# Module initialization
def __init__():
    """Initialize the module"""
    print("🏭 Blacksmith Atlas Template-Based HDA PyModule loaded")

# Auto-run on module load
__init__()
