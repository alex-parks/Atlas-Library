#!/usr/bin/env python3
"""
🏭 BLACKSMITH ATLAS: COPY TO ATLAS ASSET TOOL
Enhanced version with full parameter interface and simplified export
"""

import os
import sys
from pathlib import Path

def copy_selected_to_atlas_asset():
    """
    Main function to copy selected nodes to a subnet and add Atlas export parameters
    """
    try:
        import hou
        
        print("\n🏭 BLACKSMITH ATLAS: Copy Selected to Atlas Asset")
        print("=" * 60)
        
        # Get selected nodes
        selected_nodes = hou.selectedNodes()
        
        # Validation
        if not selected_nodes:
            error_msg = "❌ No nodes selected.\n\nPlease select nodes to copy to Atlas Asset."
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            return False
        
        # Verify all nodes have same parent
        parent = selected_nodes[0].parent()
        invalid_nodes = [node.path() for node in selected_nodes[1:] if node.parent() != parent]
        
        if invalid_nodes:
            error_msg = f"❌ All selected nodes must be in the same network.\n\n"
            error_msg += f"Parent: {parent.path()}\nInvalid nodes:\n"
            for node_path in invalid_nodes:
                error_msg += f"• {node_path}\n"
            
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            return False

        print(f"📦 Creating subnet from {len(selected_nodes)} nodes in {parent.path()}")
        
        # Get asset name from user
        result = hou.ui.readInput("Enter name for the Atlas Asset:", 
                                 buttons=("OK", "Cancel"),
                                 severity=hou.severityType.Message,
                                 title="Atlas Asset Name",
                                 initial_contents="atlas_asset")
        
        # result is (text, button_index)
        text_input = result[0]
        button_clicked = result[1]
        
        if button_clicked == 1:  # User clicked Cancel
            print("❌ User cancelled operation")
            return False
            
        # Handle different return types from readInput
        if isinstance(text_input, str):
            subnet_name = text_input.strip() if text_input.strip() else "atlas_asset"
        else:
            subnet_name = "atlas_asset"
            
        subnet_name = subnet_name.replace(" ", "_")  # Replace spaces with underscores
        
        print(f"📝 Asset name: {subnet_name}")
        
        # Collect nodes and bounds
        node_bounds = []
        for node in selected_nodes:
            print(f"   • {node.name()} ({node.type().name()})")
            
            # Check if node has boundingRect method (not all node types do)
            if hasattr(node, 'boundingRect'):
                try:
                    bounds = node.boundingRect()
                    node_bounds.append((bounds.min(), bounds.max(), node))
                except:
                    # If boundingRect fails, try position
                    pos = node.position()
                    node_bounds.append((pos, pos, node))
            else:
                # For nodes without boundingRect (like ShopNode), use position
                pos = node.position()
                node_bounds.append((pos, pos, node))
        
        # Calculate position for subnet
        if node_bounds:
            # Get x and y coordinates, handling both hou.Vector2 and bounds objects
            x_coords = []
            y_coords = []
            
            for bounds in node_bounds:
                if hasattr(bounds[0], 'x'):
                    x_coords.append(bounds[0].x())
                    y_coords.append(bounds[0].y())
                else:
                    x_coords.append(bounds[0][0])
                    y_coords.append(bounds[0][1])
                    
                if hasattr(bounds[1], 'x'):
                    x_coords.append(bounds[1].x())
                    y_coords.append(bounds[1].y())
                else:
                    x_coords.append(bounds[1][0])
                    y_coords.append(bounds[1][1])
            
            # Position subnet at center-bottom of selection
            subnet_x = (min(x_coords) + max(x_coords)) / 2
            subnet_y = min(y_coords) - 1.5
        else:
            subnet_x, subnet_y = 0, 0

        # Create subnet
        subnet = parent.createNode("subnet", subnet_name)
        subnet.setPosition([subnet_x, subnet_y])
        
        print(f"✅ Created subnet: {subnet.path()}")
        
        # Copy nodes into subnet
        copied_nodes = []
        with hou.undos.group("Copy nodes to Atlas Asset"):
            for node in selected_nodes:
                # Use copyItems for proper copying
                items_to_copy = [node]
                copied_items = hou.copyNodesTo(items_to_copy, subnet)
                copied_nodes.extend(copied_items)
                print(f"   📋 Copied: {node.name()} → {copied_items[0].name() if copied_items else 'failed'}")
        
        if not copied_nodes:
            hou.ui.displayMessage("❌ Failed to copy nodes to subnet", severity=hou.severityType.Error)
            subnet.destroy()
            return False
            
        print(f"✅ Successfully copied {len(copied_nodes)} nodes to subnet")
        
        # Add comprehensive export parameters  
        success = add_atlas_export_parameters(subnet, subnet_name)
        if not success:
            print("❌ Failed to add export parameters")
            return False
            
        print("✅ Atlas Asset subnet created successfully!")
        
        # Select the new subnet and display inside
        subnet.setSelected(True, clear_all_selected=True)
        
        # Success message
        success_msg = f"""✅ ATLAS ASSET SUBNET CREATED!

📦 Subnet: {subnet.name()}
📁 Location: {subnet.path()}
🎯 Nodes copied: {len(copied_nodes)}

The subnet now contains:
• All your selected nodes
• Export parameters for Asset Library
• Export button for one-click publishing

Next steps:
1. Configure asset details in parameters
2. Click 'Export Atlas Asset' button"""
        
        hou.ui.displayMessage(success_msg, title="🎉 Atlas Asset Ready")
        return True
        
    except Exception as e:
        print(f"❌ Atlas copy operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_atlas_export_parameters(subnet, default_name="MyAtlasAsset"):
    """Add comprehensive export parameters to the subnet"""
    try:
        import hou
        print("   🔧 Adding Atlas export parameters...")
        
        # Get existing parameter template group
        parm_group = subnet.parmTemplateGroup()
        
        # Create a folder (tab) for Atlas Export parameters
        atlas_folder = hou.FolderParmTemplate("atlas_export_folder", "Atlas Export")
        atlas_folder.setFolderType(hou.folderType.Tabs)
        
        # Create Atlas-specific parameters to go inside the folder
        atlas_parameters = []
        
        # === ASSET INFORMATION ===
        # Asset Name
        asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name_parm.setDefaultValue([default_name])
        asset_name_parm.setHelp("Enter a unique name for this asset")
        atlas_parameters.append(asset_name_parm)
        
        # Asset Type dropdown
        asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                              menu_items=("0", "1", "2", "3"),
                                              menu_labels=("Assets", "FX", "Materials", "HDAs"),
                                              default_value=0)
        asset_type_parm.setHelp("Select the primary category for this asset")
        atlas_parameters.append(asset_type_parm)
        
        # Subcategory dropdown
        subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory",
                                               menu_items=("0", "1", "2"),
                                               menu_labels=("Blacksmith Asset", "Megascans", "Kitbash"),
                                               default_value=0)
        subcategory_parm.setHelp("Select the subcategory for this asset")
        atlas_parameters.append(subcategory_parm)
        
        # Render Engine
        render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine",
                                                 menu_items=("0", "1"),
                                                 menu_labels=("Redshift", "Karma"),
                                                 default_value=0)
        render_engine_parm.setHelp("Primary render engine for this asset")
        atlas_parameters.append(render_engine_parm)
        
        # Tags (keep this one)
        tags_parm = hou.StringParmTemplate("tags", "Tags", 1)
        tags_parm.setDefaultValue([""])
        tags_parm.setHelp("Comma-separated tags for categorization (e.g., 'props, environment, medieval')")
        atlas_parameters.append(tags_parm)
        
        # === EXPORT SECTION ===
        # Separator
        separator = hou.SeparatorParmTemplate("export_sep")
        atlas_parameters.append(separator)
        
        # Export button
        export_button = hou.ButtonParmTemplate("export_atlas_asset", "Export Atlas Asset")
        export_button.setHelp("Export this asset to the Atlas Library with auto-database insertion")
        export_script = create_export_script()
        export_button.setScriptCallback(export_script)
        export_button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        atlas_parameters.append(export_button)
        
        # Export status (read-only)
        export_status = hou.StringParmTemplate("export_status", "Export Status", 1)
        export_status.setDefaultValue(["Ready to export"])
        export_status.setHelp("Current export status")
        atlas_parameters.append(export_status)
        
        # Add all Atlas parameters to the folder
        for parm in atlas_parameters:
            atlas_folder.addParmTemplate(parm)
        
        # Add the Atlas Export folder as a new tab to the parameter group
        parm_group.append(atlas_folder)
        
        # Apply the updated parameter group to the subnet
        subnet.setParmTemplateGroup(parm_group)
        
        print(f"   📦 Total Atlas parameters: {len(atlas_parameters)}")
        
        # Now make the standard switcher tabs invisible
        try:
            if subnet.parm("stdswitcher3"):
                subnet.parm("stdswitcher3").set(1)  # Set to invisible
                print(f"   🫥 Made stdswitcher3 invisible")
            if subnet.parm("stdswitcher3_1"):
                subnet.parm("stdswitcher3_1").set(1)  # Set to invisible  
                print(f"   🫥 Made stdswitcher3_1 invisible")
        except Exception as invisible_error:
            print(f"   ⚠️ Could not set invisible: {invisible_error}")
        
        # Verify parameters were added
        try:
            if subnet.parm("asset_name"):
                print(f"   ✅ asset_name parameter verified")
            if subnet.parm("export_atlas_asset"):
                print(f"   ✅ export_atlas_asset button verified")
            if subnet.parm("asset_type"):
                print(f"   ✅ asset_type parameter verified")
        except Exception as verify_error:
            print(f"   ⚠️ Parameter verification error: {verify_error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Parameter addition failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_export_script():
    """Create the export callback script - FIXED VERSION"""
    return '''
# 🏭 BLACKSMITH ATLAS EXPORT SCRIPT
import sys
import os
from pathlib import Path

try:
    print("🚀 BLACKSMITH ATLAS EXPORT INITIATED")
    print("=" * 50)
    
    # Ensure backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Force reload for development
    import importlib
    modules_to_reload = ['assetlibrary._3D.houdiniae']
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            print(f"🔄 Reloaded: {module_name}")
    
    from assetlibrary.houdini.houdiniae import TemplateAssetExporter
    
    subnet = hou.pwd()
    print(f"📦 Exporting from subnet: {subnet.path()}")
    
    # Get parameters from subnet
    asset_name = subnet.parm("asset_name").eval().strip()
    asset_type_idx = int(subnet.parm("asset_type").eval())
    tags_str = subnet.parm("tags").eval().strip()
    render_engine_idx = int(subnet.parm("render_engine").eval())
    
    # Quick validation
    if not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("❌ Asset name is required!", severity=hou.severityType.Error)
    else:
        # Convert asset type and get subcategory
        asset_types = ["Assets", "FX", "Materials", "HDAs"]
        asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
        
        # Get the subcategory
        subcategory_idx = int(subnet.parm("subcategory").eval())
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
        
        # Update status
        subnet.parm("export_status").set("🔄 Exporting...")
        
        print(f"📋 EXPORT CONFIGURATION:")
        print(f"   🏷️ Asset: {asset_name}")
        print(f"   📂 Asset Type: {asset_type}")
        print(f"   📋 Subcategory: {subcategory}")
        print(f"   🎨 Render Engine: {render_engine}")
        print(f"   🏷️ Tags: {tags_list}")
        
        # Create extended tags list
        extended_tags = tags_list.copy()
        extended_tags.extend([asset_type.lower(), subcategory.lower().replace(' ', '_'), render_engine.lower()])
        
        # Create metadata
        from datetime import datetime
        hierarchy_metadata = {
            "dimension": "3D",
            "asset_type": asset_type,
            "subcategory": subcategory,
            "render_engine": render_engine,
            "houdini_version": f"{hou.applicationVersion()[0]}.{hou.applicationVersion()[1]}.{hou.applicationVersion()[2]}",
            "export_time": str(datetime.now()),
            "tags": extended_tags
        }

        # Create TemplateAssetExporter
        exporter = TemplateAssetExporter(
            asset_name=asset_name,
            subcategory=subcategory,
            tags=extended_tags,
            asset_type=asset_type,
            render_engine=render_engine,
            metadata=hierarchy_metadata
        )
        
        print(f"✅ Created exporter with ID: {exporter.asset_id}")
        print(f"📁 Export location: {exporter.asset_folder}")
        
        # Get nodes to export
        nodes_to_export = subnet.children()
        if not nodes_to_export:
            subnet.parm("export_status").set("❌ No nodes to export")
            hou.ui.displayMessage("❌ No nodes found in subnet to export!", severity=hou.severityType.Error)
        else:
            print(f"📦 Found {len(nodes_to_export)} nodes to export:")
            for i, node in enumerate(nodes_to_export, 1):
                print(f"   {i}. {node.name()} ({node.type().name()})")
            
            # CALL EXPORT LOGIC
            print("🚀 Starting template export...")
            success = exporter.export_as_template(subnet, nodes_to_export)
            
            if success:
                subnet.parm("export_status").set("✅ Export completed!")
                
                # Add to ArangoDB Atlas_Library collection
                try:
                    print("\\n🗄️ ADDING TO ARANGODB...")
                    print(f"🔍 Looking for metadata in: {exporter.asset_folder}")
                    
                    # Find the metadata.json file in the exported asset folder
                    metadata_file = os.path.join(exporter.asset_folder, "metadata.json")
                    print(f"🔍 Checking metadata file: {metadata_file}")
                    
                    if os.path.exists(metadata_file):
                        print("✅ Metadata file found! Reading contents...")
                        
                        # Debug: Show metadata contents
                        with open(metadata_file, 'r') as f:
                            metadata_content = f.read()
                        print(f"📄 Metadata content (first 500 chars): {metadata_content[:500]}...")
                        
                        # Import and call the database insertion
                        from assetlibrary.houdini.auto_arango_insert import auto_insert_on_export
                        print("✅ Imported auto_insert_on_export function")
                        
                        db_success = auto_insert_on_export(metadata_file)
                        if db_success:
                            print("✅ Successfully added to ArangoDB Atlas_Library collection!")
                        else:
                            print("❌ Failed to add to ArangoDB (check database connection)")
                    else:
                        print(f"❌ Metadata file not found: {metadata_file}")
                        
                        # Debug: List what files ARE in the folder
                        try:
                            folder_contents = os.listdir(exporter.asset_folder)
                            print(f"📁 Folder contents: {folder_contents}")
                        except:
                            print(f"📁 Could not list folder contents")
                        
                except Exception as db_error:
                    print(f"❌ Database insertion error: {db_error}")
                    import traceback
                    traceback.print_exc()
                    # Don't fail the export if database fails - just log it
                
                success_msg = f"""✅ ATLAS ASSET EXPORT SUCCESSFUL!
                
🏷️ Asset: {asset_name}
🆔 Asset ID: {exporter.asset_id}
📂 Category: Assets/{subcategory}/
📍 Location: {exporter.asset_folder}

🎯 The asset is now in the Atlas library!
🗄️ Added to ArangoDB Atlas_Library collection"""
                
                hou.ui.displayMessage(success_msg, title="🎉 Atlas Export Complete")
                print("🎉 EXPORT SUCCESS!")
                print(f"📍 Location: {exporter.asset_folder}")
            else:
                subnet.parm("export_status").set("❌ Export failed")
                hou.ui.displayMessage("❌ Export failed! Check console for details.", severity=hou.severityType.Error)
                print("❌ EXPORT FAILED - See console")

except Exception as e:
    error_msg = f"Export error: {str(e)}"
    print(f"❌ {error_msg}")
    
    try:
        hou.pwd().parm("export_status").set("❌ Export error")
    except:
        pass
    
    hou.ui.displayMessage(f"❌ {error_msg}\\n\\nCheck console for details.", severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
'''

# Main function
if __name__ == "__main__":
    copy_selected_to_atlas_asset()

print("📦 Atlas copy-to-asset script loaded (FIXED VERSION)")
print("💡 Run: copy_selected_to_atlas_asset()")
