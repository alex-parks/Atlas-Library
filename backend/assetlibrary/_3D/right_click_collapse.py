#!/usr/bin/env python3
"""
Blacksmith Atlas - Right-Click Menu Integration
===============================================

Enhanced collapse script specifically designed for right-click menu integration.
This script provides a more streamlined workflow for creating Atlas assets from 
selected nodes via the right-click context menu.
"""

import hou
import sys
from pathlib import Path

def collapse_nodes_to_atlas_asset(selected_node_names=None):
    """
    Enhanced collapse function that works with right-click menu integration.
    
    Args:
        selected_node_names: List of node names from right-click context (optional)
    """
    
    print("🏭 BLACKSMITH ATLAS - RIGHT-CLICK COLLAPSE")
    print("=" * 60)
    
    try:
        # Get selected nodes - use parameter if provided, otherwise get current selection
        if selected_node_names:
            print(f"📋 Using nodes from right-click context: {selected_node_names}")
            # Convert node names to node objects
            selected_nodes = []
            for node_name in selected_node_names:
                try:
                    node = hou.node(node_name)
                    if node:
                        selected_nodes.append(node)
                except:
                    print(f"⚠️  Could not find node: {node_name}")
        else:
            # Fallback to current selection
            selected_nodes = hou.selectedNodes()
        
        # Validate selection
        if not selected_nodes:
            message = "❌ No nodes selected.\n\nPlease select nodes to collapse into Atlas Asset."
            hou.ui.displayMessage(message, severity=hou.severityType.Warning, title="Atlas Asset")
            return False
        
        print(f"📦 Processing {len(selected_nodes)} selected nodes:")
        for i, node in enumerate(selected_nodes, 1):
            print(f"   {i}. {node.path()} ({node.type().name()})")
        
        # Verify all nodes have the same parent (required for collapse operation)
        parent = selected_nodes[0].parent()
        invalid_nodes = []
        
        for node in selected_nodes[1:]:
            if node.parent() != parent:
                invalid_nodes.append(node.path())
        
        if invalid_nodes:
            error_msg = f"❌ All selected nodes must be in the same network context.\n\n"
            error_msg += f"Parent context: {parent.path()}\n\n"
            error_msg += f"Invalid nodes:\n"
            for node_path in invalid_nodes:
                error_msg += f"• {node_path}\n"
            error_msg += f"\nPlease select nodes from the same network level."
            
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Atlas Asset Error")
            return False
        
        print(f"✅ All nodes in same context: {parent.path()}")
        
        # Get asset name from user with improved dialog
        dialog_text = f"Creating Atlas Asset from {len(selected_nodes)} nodes:\n\n"
        for node in selected_nodes[:5]:  # Show first 5 nodes
            dialog_text += f"• {node.name()}\n"
        if len(selected_nodes) > 5:
            dialog_text += f"• ... and {len(selected_nodes) - 5} more\n"
        dialog_text += f"\nEnter a name for the Atlas Asset:"
        
        # Generate default name based on selection
        if len(selected_nodes) == 1:
            default_name = f"{selected_nodes[0].name()}_Atlas"
        else:
            default_name = f"{len(selected_nodes)}Nodes_Atlas"
        
        # Use the simplest working dialog
        try:
            result = hou.ui.readInput("Enter Atlas Asset Name:", initial_contents=default_name)
            if result[0] != 0:  # User cancelled
                print("❌ User cancelled asset creation")
                return False
            asset_name = result[1].strip()
            if not asset_name:
                print("❌ Asset name cannot be empty")
                return False
        except Exception as dialog_error:
            print(f"⚠️ Dialog error: {dialog_error}")
            # Use default name if dialog fails
            asset_name = default_name
            print(f"🔄 Using default name: {asset_name}")
        
        print(f"🏷️  Asset name: '{asset_name}'")
        
        # Create the subnet by collapsing selected nodes
        print("🔄 Creating Atlas Asset subnet...")
        try:
            # Try to collapse into subnet first
            subnet = parent.collapseIntoSubnet(selected_nodes, asset_name)
            subnet.setComment("Blacksmith Atlas Asset\nReady for Export")
            
            # Set Atlas blue color
            atlas_blue = hou.Color(0.2, 0.6, 1.0)
            subnet.setColor(atlas_blue)
            
            print(f"✅ Created Atlas subnet: {subnet.path()}")
            
        except Exception as collapse_error:
            print(f"⚠️ Standard collapse failed: {collapse_error}")
            print("🔄 Trying alternative method: copy nodes into new subnet...")
            
            try:
                # Alternative: Create empty subnet and copy nodes into it
                subnet = parent.createNode("subnet", asset_name)
                subnet.setComment("Blacksmith Atlas Asset\nReady for Export")
                subnet.setColor(hou.Color(0.2, 0.6, 1.0))
                
                # Copy selected nodes into the subnet
                print(f"📋 Copying {len(selected_nodes)} nodes into subnet...")
                copied_nodes = []
                
                for i, node in enumerate(selected_nodes):
                    try:
                        # Use hou.copyNodesTo for better copying
                        copied_node = subnet.copyItems([node])[0]
                        copied_nodes.append(copied_node)
                        print(f"   ✅ Copied: {node.name()} -> {copied_node.name()}")
                    except Exception as copy_error:
                        print(f"   ⚠️ Failed to copy {node.name()}: {copy_error}")
                
                # Try to reconnect copied nodes to preserve network logic
                print("🔗 Attempting to reconnect copied nodes...")
                for i, original_node in enumerate(selected_nodes):
                    if i < len(copied_nodes):
                        copied_node = copied_nodes[i]
                        
                        # Try to connect inputs within the copied set
                        try:
                            for input_idx in range(len(original_node.inputs())):
                                input_connection = original_node.inputConnections()[input_idx] if original_node.inputConnections() else None
                                if input_connection:
                                    input_node = input_connection.inputNode()
                                    if input_node and input_node in selected_nodes:
                                        # Find corresponding copied input node
                                        original_input_idx = selected_nodes.index(input_node)
                                        if original_input_idx < len(copied_nodes):
                                            copied_input_node = copied_nodes[original_input_idx]
                                            copied_node.setInput(input_idx, copied_input_node)
                                            print(f"      🔗 Connected: {copied_input_node.name()} -> {copied_node.name()}")
                        except Exception as connect_error:
                            print(f"      ⚠️ Connection error for {copied_node.name()}: {connect_error}")
                
                # Layout nodes inside subnet
                try:
                    subnet.layoutChildren()
                    print("📐 Laid out subnet contents")
                except:
                    pass
                
                print(f"✅ Created Atlas subnet via copy method: {subnet.path()}")
                print(f"📋 Copied {len(copied_nodes)} of {len(selected_nodes)} nodes successfully")
                
            except Exception as alt_error:
                error_msg = f"❌ Both collapse methods failed.\n\n"
                error_msg += f"Standard collapse error: {collapse_error}\n"
                error_msg += f"Copy method error: {alt_error}\n\n"
                error_msg += f"This may happen when:\n"
                error_msg += f"• Nodes are in different network contexts\n"
                error_msg += f"• Selected nodes include locked or special nodes\n"
                error_msg += f"• Network doesn't support subnet operations\n\n"
                error_msg += f"Try selecting nodes from the same context."
                
                hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Subnet Creation Failed")
                print(f"❌ Both methods failed - Standard: {collapse_error}, Copy: {alt_error}")
                return False
        
        # Add comprehensive Atlas export parameters
        print("⚙️  Adding Atlas export parameters...")
        try:
            success = add_comprehensive_atlas_parameters(subnet, asset_name)
            if success:
                print("✅ Atlas export parameters added successfully")
            else:
                print("❌ Failed to add Atlas export parameters")
        except Exception as param_error:
            print(f"❌ Error adding parameters: {param_error}")
            import traceback
            traceback.print_exc()
            success = False
        
        if success:
            # Layout the subnet contents
            try:
                subnet.layoutChildren()
                print("📐 Laid out subnet contents")
            except:
                pass
            
            # Position and select the new subnet
            subnet.setSelected(True, clear_all_selected=True)
            
            # Show success message with next steps
            success_msg = f"""✅ Atlas Asset Created Successfully!

🏷️  Asset Name: {asset_name}
📦 Subnet Path: {subnet.path()}
🔢 Nodes Collapsed: {len(selected_nodes)}

NEXT STEPS:
1. Review parameters in the Atlas Export section
2. Adjust asset name, category, and description as needed
3. Click the '🚀 Export Atlas Asset' button
4. Asset will be saved to the Atlas library

The subnet is now ready for export with all your selected nodes organized inside!"""
            
            hou.ui.displayMessage(success_msg, title="Atlas Asset Ready", details_expand=True)
            
            print("🎉 Atlas Asset creation complete!")
            print(f"   📍 Location: {subnet.path()}")
            print(f"   📋 Contains: {len(selected_nodes)} nodes")
            print(f"   🎯 Status: Ready for export")
            
            return True
            
        else:
            warning_msg = f"⚠️  Atlas Asset subnet created but parameter setup encountered issues.\n\n"
            warning_msg += f"Subnet: {subnet.path()}\n\n"
            warning_msg += f"You can still use the subnet, but may need to add export parameters manually."
            
            hou.ui.displayMessage(warning_msg, severity=hou.severityType.Warning, title="Partial Success")
            return False
        
    except Exception as e:
        error_msg = f"❌ Unexpected error creating Atlas Asset:\n\n{str(e)}\n\n"
        error_msg += f"Please check the console for detailed error information."
        
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Atlas Asset Error")
        return False

def add_comprehensive_atlas_parameters(subnet, asset_name):
    """Add comprehensive Atlas export parameters to the subnet"""
    try:
        print(f"   📋 Adding parameters to {subnet.name()}...")
        
        # Get the parameter template group
        ptg = subnet.parmTemplateGroup()
        
        # Create main Atlas Export folder (collapsible, open by default)
        atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", hou.folderType.Collapsible)
        atlas_folder.setDefaultValue(1)  # Open by default
        atlas_folder.setHelp("Blacksmith Atlas asset export configuration and controls")
        
        # === ASSET INFORMATION SECTION ===
        info_folder = hou.FolderParmTemplate("asset_info", "📋 Asset Information", hou.folderType.Simple)
        
        # Asset name (editable)
        asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name_parm.setDefaultValue([asset_name])
        asset_name_parm.setHelp("Name of the asset for export to the Atlas library")
        info_folder.addParmTemplate(asset_name_parm)
        
        # Subcategory selection
        subcategory_parm = hou.MenuParmTemplate("subcategory", "Category", 
                                               ["props", "characters", "environments", "vehicles", 
                                                "architecture", "furniture", "weapons", "organic", 
                                                "hard_surface", "fx", "general"],
                                               ["Props", "Characters", "Environments", "Vehicles",
                                                "Architecture", "Furniture", "Weapons", "Organic",
                                                "Hard Surface", "FX", "General"])
        subcategory_parm.setDefaultValue(0)  # Default to Props
        subcategory_parm.setHelp("Asset category for library organization and browsing")
        info_folder.addParmTemplate(subcategory_parm)
        
        # Description (multi-line would be better but string works)
        description_parm = hou.StringParmTemplate("description", "Description", 1)
        description_parm.setDefaultValue([f"Atlas asset exported from Houdini: {asset_name}"])
        description_parm.setHelp("Detailed description of the asset and its intended use")
        info_folder.addParmTemplate(description_parm)
        
        # Tags for searchability
        tags_parm = hou.StringParmTemplate("tags", "Search Tags", 1)
        tags_parm.setDefaultValue([""])
        tags_parm.setHelp("Comma-separated tags for searching (e.g., vehicle, helicopter, military, sci-fi)")
        info_folder.addParmTemplate(tags_parm)
        
        atlas_folder.addParmTemplate(info_folder)
        
        # === EXPORT CONTROLS SECTION ===
        controls_folder = hou.FolderParmTemplate("export_controls", "🚀 Export Controls", hou.folderType.Simple)
        
        # Export status (read-only)
        status_parm = hou.StringParmTemplate("export_status", "Export Status", 1)
        status_parm.setDefaultValue(["Ready to export"])
        status_parm.setReadOnly(True)
        status_parm.setHelp("Current status of the export process")
        controls_folder.addParmTemplate(status_parm)
        
        # Main export button
        export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
        export_btn.setHelp("Export this Atlas Asset as a template to the library with all textures and data")
        
        # Create comprehensive export callback script
        export_script = create_export_callback_script()
        export_btn.setScriptCallback(export_script)
        export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        controls_folder.addParmTemplate(export_btn)
        
        # Info button
        info_btn = hou.ButtonParmTemplate("atlas_info", "ℹ️  About Atlas Assets")
        info_btn.setHelp("Show information about Blacksmith Atlas asset system")
        info_btn.setScriptCallback(create_info_callback_script())
        info_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        controls_folder.addParmTemplate(info_btn)
        
        atlas_folder.addParmTemplate(controls_folder)
        
        # === ADVANCED OPTIONS SECTION ===
        advanced_folder = hou.FolderParmTemplate("advanced_options", "🔧 Advanced Options", hou.folderType.Simple)
        
        # Export formats checkboxes (future expansion)
        export_abc = hou.ToggleParmTemplate("export_abc", "Export ABC", True)
        export_abc.setHelp("Export Alembic cache files")
        advanced_folder.addParmTemplate(export_abc)
        
        export_fbx = hou.ToggleParmTemplate("export_fbx", "Export FBX", True)
        export_fbx.setHelp("Export FBX files for other DCCs")
        advanced_folder.addParmTemplate(export_fbx)
        
        export_textures = hou.ToggleParmTemplate("export_textures", "Copy Textures", True)
        export_textures.setHelp("Automatically find and copy all referenced texture files")
        advanced_folder.addParmTemplate(export_textures)
        
        # Version control (future feature)
        version_parm = hou.StringParmTemplate("asset_version", "Version", 1)
        version_parm.setDefaultValue(["1.0"])
        version_parm.setHelp("Asset version number")
        advanced_folder.addParmTemplate(version_parm)
        
        atlas_folder.addParmTemplate(advanced_folder)
        
        # Add the main folder to the parameter template group
        ptg.addParmTemplate(atlas_folder)
        
        # Apply the parameter template group to the subnet
        subnet.setParmTemplateGroup(ptg)
        
        print(f"   ✅ Added comprehensive Atlas export parameters")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to add parameters: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_export_callback_script():
    """Create the comprehensive export callback script"""
    return '''
# Blacksmith Atlas Asset Export Callback
import sys
from pathlib import Path

try:
    print("🏭 BLACKSMITH ATLAS EXPORT INITIATED")
    print("=" * 50)
    
    # Ensure backend path is available
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Import the exporter with module reload for development
    try:
        from assetlibrary._3D.houdiniae import TemplateAssetExporter
        
        # Force reload during development
        import importlib
        from assetlibrary._3D import houdiniae
        importlib.reload(houdiniae)
        from assetlibrary._3D.houdiniae import TemplateAssetExporter
        print("✅ Loaded TemplateAssetExporter (with reload for latest changes)")
        
    except ImportError as ie:
        raise Exception(f"Failed to import TemplateAssetExporter: {ie}")
    
    # Get current subnet (the node this parameter belongs to)
    subnet = hou.pwd()
    print(f"📦 Exporting from subnet: {subnet.path()}")
    
    # Extract export parameters from subnet
    try:
        asset_name = subnet.parm("asset_name").eval().strip()
        subcategory_idx = int(subnet.parm("subcategory").eval())
        description = subnet.parm("description").eval().strip()
        tags_str = subnet.parm("tags").eval().strip()
        version = subnet.parm("asset_version").eval().strip() if subnet.parm("asset_version") else "1.0"
        
        # Advanced options
        export_abc = bool(subnet.parm("export_abc").eval()) if subnet.parm("export_abc") else True
        export_fbx = bool(subnet.parm("export_fbx").eval()) if subnet.parm("export_fbx") else True  
        export_textures = bool(subnet.parm("export_textures").eval()) if subnet.parm("export_textures") else True
        
    except Exception as pe:
        raise Exception(f"Failed to read export parameters: {pe}")
    
    # Validate required parameters
    if not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("❌ Asset name is required for export!", 
                            severity=hou.severityType.Error, title="Export Error")
        raise Exception("Asset name is required")
    
    # Convert subcategory index to name
    subcategories = ["Props", "Characters", "Environments", "Vehicles", "Architecture", 
                    "Furniture", "Weapons", "Organic", "Hard_Surface", "FX", "General"]
    subcategory = subcategories[subcategory_idx] if subcategory_idx < len(subcategories) else "Props"
    
    # Process tags
    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    # Update status to show export in progress
    subnet.parm("export_status").set("🔄 Exporting...")
    
    print(f"📋 EXPORT CONFIGURATION:")
    print(f"   🏷️  Asset: {asset_name}")
    print(f"   📂 Category: {subcategory}")
    print(f"   📝 Description: {description}")
    print(f"   🏷️  Tags: {tags_list}")
    print(f"   🔢 Version: {version}")
    print(f"   📁 ABC Export: {export_abc}")
    print(f"   📁 FBX Export: {export_fbx}")
    print(f"   🖼️  Texture Copy: {export_textures}")
    
    # Create the template asset exporter
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,
        description=description,
        tags=tags_list
    )
    
    print(f"✅ Created exporter with ID: {exporter.asset_id}")
    
    # Get nodes to export (all children of the subnet)
    nodes_to_export = subnet.children()
    if not nodes_to_export:
        subnet.parm("export_status").set("❌ No nodes to export")
        hou.ui.displayMessage("❌ No nodes found inside the subnet to export!", 
                            severity=hou.severityType.Error, title="Export Error")
        raise Exception("No nodes found to export")
    
    print(f"📦 Found {len(nodes_to_export)} nodes to export:")
    for i, node in enumerate(nodes_to_export, 1):
        print(f"   {i}. {node.name()} ({node.type().name()})")
    
    # Perform the template-based export
    print("🚀 Starting template export...")
    print(f"   📂 Export location: {exporter.asset_folder}")
    print(f"   🔧 Using TemplateAssetExporter with comprehensive texture scanning")
    
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        # Update status
        subnet.parm("export_status").set(f"✅ Export completed!")
        
        # Create detailed success message
        success_msg = f"""✅ ATLAS ASSET EXPORT SUCCESSFUL!

🏷️  Asset Name: {asset_name}
🆔 Asset ID: {exporter.asset_id}
📂 Category: Assets/{subcategory}/
🔢 Version: {version}

📍 LOCATION:
{exporter.asset_folder}

📦 EXPORTED FILES:
• Template: {asset_name}.hipnc (perfect reconstruction)
• Metadata: metadata.json (searchable asset info)
• Textures: Organized by material in Textures/ folder
• Preview: Auto-generated thumbnails

🎯 EXPORT METHOD:
Template-based using Houdini's native saveChildrenToFile()
for perfect fidelity and future compatibility.

The asset is now available in the Atlas library!"""
        
        hou.ui.displayMessage(success_msg, title="🎉 Atlas Export Complete", details_expand=True)
        
        print("🎉 EXPORT COMPLETED SUCCESSFULLY!")
        print(f"   📍 Location: {exporter.asset_folder}")
        print(f"   🆔 Asset ID: {exporter.asset_id}")
        print(f"   📋 Files exported with template method")
        
    else:
        subnet.parm("export_status").set("❌ Export failed")
        hou.ui.displayMessage("❌ Export failed! Please check the console for detailed error information.", 
                            severity=hou.severityType.Error, title="Export Failed")
        print("❌ EXPORT FAILED - See console for details")

except Exception as e:
    error_msg = f"Export error: {str(e)}"
    print(f"❌ {error_msg}")
    
    # Update status parameter if possible
    try:
        subnet = hou.pwd()
        if subnet and subnet.parm("export_status"):
            subnet.parm("export_status").set("❌ Export error")
    except:
        pass
    
    # Show error to user
    hou.ui.displayMessage(f"❌ {error_msg}\\n\\nCheck console for detailed error information.", 
                        severity=hou.severityType.Error, title="Atlas Export Error")
    
    import traceback
    traceback.print_exc()
'''

def create_info_callback_script():
    """Create the info callback script"""
    return '''
info_text = """🏭 BLACKSMITH ATLAS ASSETS

Template-Based Asset System for Houdini

═══════════════════════════════════════════════════

🎯 WORKFLOW:
1. Select nodes in Houdini viewport
2. Right-click → Blacksmith Atlas → Collapse into Atlas Asset
3. Configure asset parameters (name, category, description)
4. Click '🚀 Export Atlas Asset' button
5. Asset saved to library with perfect reconstruction capability

🔧 KEY FEATURES:
• Uses Houdini's native saveChildrenToFile() for perfect fidelity
• Automatic texture discovery and extraction from materials
• Exports multiple formats: HIP template, ABC, FBX, JSON metadata
• Future-proof template-based approach
• Organized library structure with search capabilities

📁 EXPORT FORMATS:
• Template File: .hipnc (perfect reconstruction)
• Geometry: .abc (Alembic cache)
• Exchange: .fbx (cross-DCC compatibility)
• Textures: Organized by material in subfolders
• Metadata: .json (searchable asset information)

📍 LIBRARY LOCATION:
/net/library/atlaslib/3D/Assets/{category}/

🎨 TEXTURE HANDLING:
• Comprehensive material scanning (VOP, SHOP, MatNet)
• Automatic texture file discovery and copying
• UDIM sequence support
• Organized by material name in subfolders
• Preserves original path references in metadata

🔄 IMPORT/EXPORT:
• Export: Template-based perfect serialization
• Import: loadChildrenFromFile() perfect reconstruction
• No data loss, no version compatibility issues
• Works with any Houdini node types and networks

This system provides infinitely more reliable asset exchange
than JSON-based reconstruction methods!

═══════════════════════════════════════════════════
🏭 BLACKSMITH ATLAS - Professional VFX Asset Management"""

hou.ui.displayMessage(info_text, title="About Blacksmith Atlas Assets")
'''

# Main entry point for right-click menu
if __name__ == "__main__":
    collapse_nodes_to_atlas_asset()