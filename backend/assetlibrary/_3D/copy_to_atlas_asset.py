#!/usr/bin/env python3
"""
🏭 BLACKSMITH ATLAS: COPY TO ATLAS ASSET TOOL
Enhanced version with full parameter interface and simplified export
"""

import os
import sys
import subprocess
import json
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
                                 initial_contents="MyAtlasAsset")
        
        print(f"🔍 Dialog result: {result}")
        print(f"🔍 Dialog result type: {type(result)}")
        
        # hou.ui.readInput returns (button_index, text_input)
        button_clicked = result[0]  # 0 = OK, 1 = Cancel
        text_input = result[1]      # The actual text entered
        
        print(f"🔍 Button clicked: {button_clicked}")  
        print(f"🔍 Text input: '{text_input}'")
        
        if button_clicked == 1:  # User clicked Cancel
            print("❌ User cancelled operation")
            return False
            
        # Get the user's input
        user_asset_name = text_input.strip() if text_input and text_input.strip() else "atlas_asset"
            
        # Create separate names: one for node (sanitized) and one for parameters (original)
        subnet_node_name = user_asset_name.replace(" ", "_")  # Replace spaces with underscores for node name
        asset_parameter_name = user_asset_name  # Keep original for parameters
        
        print(f"📝 User entered: '{user_asset_name}'")
        print(f"📝 Node name: '{subnet_node_name}'")
        print(f"📝 Parameter name: '{asset_parameter_name}'")
        
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
        subnet = parent.createNode("subnet", subnet_node_name)
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
        success = add_atlas_export_parameters(subnet, asset_parameter_name)
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
    """Add comprehensive export parameters to the subnet - SIMPLIFIED VERSION"""
    try:
        import hou
        print("   🔧 Adding SIMPLIFIED Atlas export parameters...")
        
        # Get existing parameter template group
        parm_group = subnet.parmTemplateGroup()
        
        # Add just the most basic parameters first to test
        print(f"   📋 Current parameter count: {len(parm_group.parmTemplates())}")
        
        # Create a TAB folder for Atlas Export parameters
        atlas_tab = hou.FolderParmTemplate("atlas_export_tab", "Atlas Export", folder_type=hou.folderType.Tabs)
        
        # Action dropdown (first parameter in tab)
        action_parm = hou.MenuParmTemplate("action", "Action",
                                          menu_items=("0", "1", "2"),
                                          menu_labels=("Create New Asset", "Version Up Asset", "Variant Asset"),
                                          default_value=0)
        action_parm.setHelp("Choose the type of asset creation: New Asset, Version of existing asset, or Variant")
        atlas_tab.addParmTemplate(action_parm)
        print(f"   ➕ Added action dropdown to tab")
        
        # === CREATE NEW ASSET PARAMETERS (visible when action == 0) ===
        
        # Asset Name (Create New only)
        asset_name = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name.setDefaultValue([default_name])
        asset_name.setHelp("Enter a unique name for this asset")
        asset_name.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(asset_name)
        print(f"   ➕ Added asset name (Create New only)")
        
        # Asset Type dropdown (Create New only)
        asset_type = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                         menu_items=("0", "1", "2", "3"),
                                         menu_labels=("Assets", "FX", "Materials", "HDAs"),
                                         default_value=0)
        asset_type.setHelp("Select the primary category for this asset")
        asset_type.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(asset_type)
        print(f"   ➕ Added asset type (Create New only)")
        
        # Subcategory dropdowns - one for each asset type (conditional visibility)
        
        # Assets subcategory (visible when asset_type == 0)
        subcategory_assets = hou.MenuParmTemplate("subcategory_assets", "Subcategory",
                                                menu_items=("0", "1", "2"),
                                                menu_labels=("Blacksmith Asset", "Megascans", "Kitbash"),
                                                default_value=0)
        subcategory_assets.setHelp("Select the subcategory for Assets")
        subcategory_assets.setConditional(hou.parmCondType.HideWhen, "{ action != 0 } { asset_type != 0 }")
        atlas_tab.addParmTemplate(subcategory_assets)
        
        # FX subcategory (visible when asset_type == 1)
        subcategory_fx = hou.MenuParmTemplate("subcategory_fx", "Subcategory",
                                            menu_items=("0", "1", "2", "3"),
                                            menu_labels=("Blacksmith FX", "Atmosphere", "FLIP", "Pyro"),
                                            default_value=0)
        subcategory_fx.setHelp("Select the subcategory for FX")
        subcategory_fx.setConditional(hou.parmCondType.HideWhen, "{ action != 0 } { asset_type != 1 }")
        atlas_tab.addParmTemplate(subcategory_fx)
        
        # Materials subcategory (visible when asset_type == 2)
        subcategory_materials = hou.MenuParmTemplate("subcategory_materials", "Subcategory",
                                                    menu_items=("0", "1", "2"),
                                                    menu_labels=("Blacksmith Materials", "Redshift", "Karma"),
                                                    default_value=0)
        subcategory_materials.setHelp("Select the subcategory for Materials")
        subcategory_materials.setConditional(hou.parmCondType.HideWhen, "{ action != 0 } { asset_type != 2 }")
        atlas_tab.addParmTemplate(subcategory_materials)
        
        # HDAs subcategory (visible when asset_type == 3)
        subcategory_hdas = hou.MenuParmTemplate("subcategory_hdas", "Subcategory",
                                              menu_items=("0",),
                                              menu_labels=("Blacksmith HDAs",),
                                              default_value=0)
        subcategory_hdas.setHelp("Select the subcategory for HDAs")
        subcategory_hdas.setConditional(hou.parmCondType.HideWhen, "{ action != 0 } { asset_type != 3 }")
        atlas_tab.addParmTemplate(subcategory_hdas)
        
        print(f"   ➕ Added conditional subcategory dropdowns (Create New only)")
        
        # Render Engine (Create New only)
        render_engine = hou.MenuParmTemplate("render_engine", "Render Engine",
                                            menu_items=("0", "1"),
                                            menu_labels=("Redshift", "Karma"),
                                            default_value=0)
        render_engine.setHelp("Primary render engine for this asset")
        render_engine.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(render_engine)
        print(f"   ➕ Added render engine (Create New only)")
        
        # Tags (Create New only)
        tags = hou.StringParmTemplate("tags", "Tags", 1)
        tags.setDefaultValue([""])
        tags.setHelp("Comma-separated tags for categorization (e.g., 'props, environment, medieval')")
        tags.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(tags)
        print(f"   ➕ Added tags (Create New only)")
        
        # ===== THUMBNAIL SECTION (Create New only) =====
        thumbnail_folder = hou.FolderParmTemplate("thumbnail_folder", "Thumbnail", folder_type=hou.folderType.Collapsible)
        thumbnail_folder.setDefaultValue(1)  # Start expanded
        thumbnail_folder.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        
        # Thumbnail Action dropdown
        thumbnail_action_parm = hou.MenuParmTemplate("thumbnail_action", "Thumbnail Action",
                                                    ["automatic", "choose", "disable"],
                                                    ["Automatic Thumbnail", "Choose Thumbnail", "Disable Thumbnail"])
        thumbnail_action_parm.setDefaultValue(0)  # Default to Automatic Thumbnail
        thumbnail_action_parm.setHelp("Choose how to handle thumbnail generation:\n" +
                                      "• Automatic: Uses HDA to render and submit to farm\n" +
                                      "• Choose: Select existing render sequence to use\n" +
                                      "• Disable: Create text-based thumbnail with asset name")
        thumbnail_folder.addParmTemplate(thumbnail_action_parm)
        
        # File picker for Choose Thumbnail (only shown when thumbnail_action is "choose")
        thumbnail_file_parm = hou.StringParmTemplate("thumbnail_file", "Thumbnail File", 1, 
                                                     string_type=hou.stringParmType.FileReference)
        thumbnail_file_parm.setHelp("Select an image file or sequence to use as thumbnail.\n" +
                                   "Supports PNG, JPG, EXR formats and sequences.")
        thumbnail_file_parm.setConditional(hou.parmCondType.HideWhen, "{ thumbnail_action != choose }")
        thumbnail_file_parm.setFileType(hou.fileType.Image)
        thumbnail_folder.addParmTemplate(thumbnail_file_parm)
        
        atlas_tab.addParmTemplate(thumbnail_folder)
        print(f"   ➕ Added Thumbnail section (Create New only)")
        
        # Advanced section (Create New only) - Collapsible folder
        advanced_folder = hou.FolderParmTemplate("advanced", "Advanced", folder_type=hou.folderType.Collapsible)
        advanced_folder.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        
        # Branded checkbox inside Advanced folder
        branded_checkbox = hou.ToggleParmTemplate("branded", "Branded", default_value=False)
        branded_checkbox.setHelp("Check if this asset is branded by a specific brand/company")
        advanced_folder.addParmTemplate(branded_checkbox)
        
        atlas_tab.addParmTemplate(advanced_folder)
        print(f"   ➕ Added Advanced section with Branded checkbox (Create New only)")
        
        # Separator before Create New export section
        separator_create = hou.SeparatorParmTemplate("create_sep")
        separator_create.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(separator_create)
        
        # Export button (Create New only)
        export_button = hou.ButtonParmTemplate("export_atlas_asset", "Export Atlas Asset")
        export_button.setHelp("Export this asset to the Atlas Library with auto-database insertion")
        export_script = create_export_script()
        export_button.setScriptCallback(export_script)
        export_button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        export_button.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(export_button)
        print(f"   ➕ Added export button (Create New only)")
        
        # === VERSION UP ASSET PARAMETERS (visible when action == 1) ===
        
        # Parent Asset ID (Version Up only) - 13 characters
        parent_asset_id = hou.StringParmTemplate("version_parent_asset_id", "Parent Asset ID", 1)
        parent_asset_id.setDefaultValue([""])
        parent_asset_id.setHelp("Enter the 13-character Asset ID (11 base + 2 variant) of the asset to version up (e.g., A5FF6F3B4R6AA)")
        parent_asset_id.setConditional(hou.parmCondType.HideWhen, "{ action != 1 }")
        atlas_tab.addParmTemplate(parent_asset_id)
        print(f"   ➕ Added parent asset ID (Version Up only)")
        
        # ===== THUMBNAIL SECTION (Version Up) =====
        thumbnail_folder_version = hou.FolderParmTemplate("thumbnail_folder_version", "Thumbnail", folder_type=hou.folderType.Collapsible)
        thumbnail_folder_version.setDefaultValue(1)  # Start expanded
        thumbnail_folder_version.setConditional(hou.parmCondType.HideWhen, "{ action != 1 }")
        
        # Thumbnail Action dropdown for Version Up
        thumbnail_action_version = hou.MenuParmTemplate("thumbnail_action_version", "Thumbnail Action",
                                                        ["automatic", "choose", "disable"],
                                                        ["Automatic Thumbnail", "Choose Thumbnail", "Disable Thumbnail"])
        thumbnail_action_version.setDefaultValue(0)  # Default to Automatic Thumbnail
        thumbnail_action_version.setHelp("Choose how to handle thumbnail generation:\n" +
                                        "• Automatic: Uses HDA to render and submit to farm\n" +
                                        "• Choose: Select existing render sequence to use\n" +
                                        "• Disable: Create text-based thumbnail with asset name")
        thumbnail_folder_version.addParmTemplate(thumbnail_action_version)
        
        # File picker for Choose Thumbnail (Version Up)
        thumbnail_file_version = hou.StringParmTemplate("thumbnail_file_version", "Thumbnail File", 1, 
                                                       string_type=hou.stringParmType.FileReference)
        thumbnail_file_version.setHelp("Select an image file or sequence to use as thumbnail.\n" +
                                     "Supports PNG, JPG, EXR formats and sequences.")
        thumbnail_file_version.setConditional(hou.parmCondType.HideWhen, "{ thumbnail_action_version != choose }")
        thumbnail_file_version.setFileType(hou.fileType.Image)
        thumbnail_folder_version.addParmTemplate(thumbnail_file_version)
        
        atlas_tab.addParmTemplate(thumbnail_folder_version)
        print(f"   ➕ Added Thumbnail section (Version Up only)")
        
        # Separator before Version Up export section
        separator_version = hou.SeparatorParmTemplate("version_sep")
        separator_version.setConditional(hou.parmCondType.HideWhen, "{ action != 1 }")
        atlas_tab.addParmTemplate(separator_version)
        
        # Create New Version button (Version Up only)
        version_button = hou.ButtonParmTemplate("create_new_version", "Create New Version")
        version_button.setHelp("Create a new version of the specified asset")
        version_export_script = create_version_export_script()
        version_button.setScriptCallback(version_export_script)
        version_button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        version_button.setConditional(hou.parmCondType.HideWhen, "{ action != 1 }")
        atlas_tab.addParmTemplate(version_button)
        print(f"   ➕ Added create new version button (Version Up only)")
        
        # === VARIANT ASSET PARAMETERS (visible when action == 2) ===
        
        # Parent Asset ID for Variant (Variant only) - 11 characters only
        variant_parent_id = hou.StringParmTemplate("variant_parent_id", "Parent Asset ID", 1)
        variant_parent_id.setDefaultValue([""])
        variant_parent_id.setHelp("Enter the 11-character base UID of the asset to create variant from (e.g., A5FF6F3B4R6)")
        variant_parent_id.setConditional(hou.parmCondType.HideWhen, "{ action != 2 }")
        atlas_tab.addParmTemplate(variant_parent_id)
        print(f"   ➕ Added variant parent asset ID (Variant only)")
        
        # Variant Name (Variant only)
        variant_name = hou.StringParmTemplate("variant_name", "Variant Name", 1)
        variant_name.setDefaultValue(["default"])
        variant_name.setHelp("Name for this variant (will be stored in variant_name metadata field)")
        variant_name.setConditional(hou.parmCondType.HideWhen, "{ action != 2 }")
        atlas_tab.addParmTemplate(variant_name)
        print(f"   ➕ Added variant name (Variant only)")
        
        # ===== THUMBNAIL SECTION (Variant) =====
        thumbnail_folder_variant = hou.FolderParmTemplate("thumbnail_folder_variant", "Thumbnail", folder_type=hou.folderType.Collapsible)
        thumbnail_folder_variant.setDefaultValue(1)  # Start expanded
        thumbnail_folder_variant.setConditional(hou.parmCondType.HideWhen, "{ action != 2 }")
        
        # Thumbnail Action dropdown for Variant
        thumbnail_action_variant = hou.MenuParmTemplate("thumbnail_action_variant", "Thumbnail Action",
                                                        ["automatic", "choose", "disable"],
                                                        ["Automatic Thumbnail", "Choose Thumbnail", "Disable Thumbnail"])
        thumbnail_action_variant.setDefaultValue(0)  # Default to Automatic Thumbnail
        thumbnail_action_variant.setHelp("Choose how to handle thumbnail generation:\n" +
                                        "• Automatic: Uses HDA to render and submit to farm\n" +
                                        "• Choose: Select existing render sequence to use\n" +
                                        "• Disable: Create text-based thumbnail with asset name")
        thumbnail_folder_variant.addParmTemplate(thumbnail_action_variant)
        
        # File picker for Choose Thumbnail (Variant)
        thumbnail_file_variant = hou.StringParmTemplate("thumbnail_file_variant", "Thumbnail File", 1, 
                                                       string_type=hou.stringParmType.FileReference)
        thumbnail_file_variant.setHelp("Select an image file or sequence to use as thumbnail.\n" +
                                     "Supports PNG, JPG, EXR formats and sequences.")
        thumbnail_file_variant.setConditional(hou.parmCondType.HideWhen, "{ thumbnail_action_variant != choose }")
        thumbnail_file_variant.setFileType(hou.fileType.Image)
        thumbnail_folder_variant.addParmTemplate(thumbnail_file_variant)
        
        atlas_tab.addParmTemplate(thumbnail_folder_variant)
        print(f"   ➕ Added Thumbnail section (Variant only)")
        
        # Separator before Variant export section
        separator_variant = hou.SeparatorParmTemplate("variant_sep")
        separator_variant.setConditional(hou.parmCondType.HideWhen, "{ action != 2 }")
        atlas_tab.addParmTemplate(separator_variant)
        
        # Create Variant button (Variant only)
        variant_button = hou.ButtonParmTemplate("create_variant", "Create Variant")
        variant_button.setHelp("Create a variant of the specified asset")
        variant_export_script = create_variant_export_script()
        variant_button.setScriptCallback(variant_export_script)
        variant_button.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        variant_button.setConditional(hou.parmCondType.HideWhen, "{ action != 2 }")
        atlas_tab.addParmTemplate(variant_button)
        print(f"   ➕ Added create variant button (Variant only)")
        
        # Export status
        export_status = hou.StringParmTemplate("export_status", "Export Status", 1)
        export_status.setDefaultValue(["Ready to export"])
        export_status.setHelp("Current export status")
        atlas_tab.addParmTemplate(export_status)
        print(f"   ➕ Added export status to tab")
        
        # Add the tab to the parameter group
        parm_group.append(atlas_tab)
        print(f"   📁 Added Atlas Export tab")
        
        print(f"   📋 New parameter count: {len(parm_group.parmTemplates())}")
        
        # Apply the parameter group
        print("   💾 Applying parameter template group...")
        subnet.setParmTemplateGroup(parm_group)
        print("   ✅ Parameter template group applied")
        
        # Wait a moment and verify
        import time
        time.sleep(0.1)
        
        # Check if parameters were actually created
        print("   🔍 Checking for created parameters...")
        all_parms = subnet.parms()
        parm_names = [p.name() for p in all_parms]
        print(f"   📋 All subnet parameters: {parm_names}")
        
        # Check for all parameters
        required_params = [
            "action", 
            # Create New Asset parameters
            "asset_name", "asset_type", "subcategory_assets", "subcategory_fx", "subcategory_materials", "subcategory_hdas", "render_engine", "tags", "thumbnail_action", "thumbnail_file", "branded", "export_atlas_asset",
            # Version Up Asset parameters  
            "version_parent_asset_id", "thumbnail_action_version", "thumbnail_file_version", "create_new_version",
            # Variant Asset parameters
            "variant_parent_id", "variant_name", "thumbnail_action_variant", "thumbnail_file_variant", "create_variant"
        ]
        for param in required_params:
            if param in parm_names:
                print(f"   ✅ {param} parameter found!")
            else:
                print(f"   ❌ {param} parameter NOT found!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Parameter addition failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_version_export_script():
    """Create script to lookup version info and perform full asset export"""
    return '''
# 🏭 BLACKSMITH ATLAS VERSION EXPORT SCRIPT
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Import requests with fallback
try:
    import requests
    print("✅ Successfully imported requests module")
except ImportError:
    print("❌ Failed to import requests module")
    import urllib.request
    import urllib.parse
    print("✅ Using urllib as fallback")

def call_atlas_api_ingestion(metadata_file_path):
    """
    Call the Atlas API ingestion script to submit metadata.json via REST API
    """
    try:
        print(f"📡 Starting API ingestion for: {metadata_file_path}")
        
        # Path to the ingestion script
        ingestion_script = "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/scripts/utilities/ingest_metadata_curl.py"
        
        # Check if ingestion script exists
        if not os.path.exists(ingestion_script):
            print(f"❌ Ingestion script not found: {ingestion_script}")
            return False
        
        # Check if metadata file exists
        if not os.path.exists(metadata_file_path):
            print(f"❌ Metadata file not found: {metadata_file_path}")
            return False
            
        print(f"✅ Found ingestion script: {ingestion_script}")
        print(f"✅ Found metadata file: {metadata_file_path}")
        
        # Use system python3
        python_exec = "python3"
        print(f"✅ Using system python3: {python_exec}")
        
        # Prepare the command
        cmd = [
            python_exec,
            ingestion_script,
            metadata_file_path,
            "--api-url", "http://localhost:8000",
            "--verbose"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        # Run the ingestion script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Log the output
        if result.stdout:
            print(f"📄 STDOUT:\\\\n{result.stdout}")
        
        if result.stderr:
            print(f"⚠️ STDERR:\\\\n{result.stderr}")
            
        # Check if successful
        if result.returncode == 0:
            print("✅ API ingestion completed successfully!")
            return True
        else:
            print(f"❌ API ingestion failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API ingestion timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ API ingestion error: {e}")
        import traceback
        traceback.print_exc()
        return False

def lookup_asset_versions(base_uid):
    """
    Look up all versions of an asset by base UID and return version info
    """
    try:
        print(f"🔍 Looking up versions for base UID: {base_uid}")
        
        # Query the Atlas API to get all assets
        api_url = "http://localhost:8000/api/v1/assets"
        print(f"   🌐 Making API request to: {api_url}")
        
        try:
            response = requests.get(api_url, params={"limit": 1000}, timeout=30)
        except Exception as req_error:
            print(f"❌ Request failed: {req_error}")
            return None
        
        print(f"   📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response text: {response.text}")
            return None
        
        assets_data = response.json()
        all_assets = assets_data.get('items', [])
        
        # Filter assets that match the base UID (first 11 characters)
        matching_assets = []
        print(f"   🔍 Checking {len(all_assets)} total assets in database...")
        
        for asset in all_assets:
            asset_id = asset.get('id', '')
            print(f"   🔍 Checking asset: {asset_id}")
            
            if len(asset_id) >= 11 and asset_id[:11].upper() == base_uid.upper():
                matching_assets.append(asset)
                print(f"   ✅ Found matching asset: {asset_id}")
            else:
                if len(asset_id) >= 11:
                    print(f"   ❌ No match: {asset_id[:11]} != {base_uid.upper()}")
                else:
                    print(f"   ❌ Too short: {asset_id}")
        
        print(f"   📊 Total matching assets: {len(matching_assets)}")
        
        if not matching_assets:
            print(f"   ❌ No assets found with base UID: {base_uid}")
            return {
                'base_uid': base_uid,
                'existing_versions': [],
                'next_version': 1,
                'latest_asset': None
            }
        
        # Sort by version number (last 3 characters)
        version_info = []
        print(f"   🔍 Processing {len(matching_assets)} matching assets...")
        
        for asset in matching_assets:
            asset_id = asset.get('id', '')
            print(f"   🔍 Processing asset ID: {asset_id}")
            
            if len(asset_id) == 14:  # Legacy 14-character UIDs (9+2+3)
                try:
                    version_str = asset_id[-3:]
                    version_num = int(version_str)
                    version_info.append({
                        'version': version_num,
                        'asset_id': asset_id,
                        'asset_data': asset
                    })
                    print(f"   ✅ Parsed version {version_num:03d} from {asset_id}")
                except ValueError:
                    print(f"   ⚠️ Invalid version format in asset ID: {asset_id} (last 3: '{asset_id[-3:]}')")
            else:
                print(f"   ⚠️ Asset ID wrong length: {asset_id} (length: {len(asset_id)})")
        
        # Sort by version number
        version_info.sort(key=lambda x: x['version'])
        print(f"   🔍 Sorted version info: {[(v['asset_id'], v['version']) for v in version_info]}")
        
        # Find next version number
        existing_versions = [v['version'] for v in version_info]
        next_version = max(existing_versions) + 1 if existing_versions else 1
        print(f"   📊 Existing versions: {existing_versions}")
        print(f"   🔢 Next version calculated: {next_version}")
        
        # Get latest asset for metadata inheritance
        latest_asset = version_info[-1]['asset_data'] if version_info else None
        
        print(f"   📊 Found {len(existing_versions)} existing versions: {existing_versions}")
        print(f"   🔢 Next version will be: {next_version:03d}")
        
        return {
            'base_uid': base_uid,
            'existing_versions': existing_versions,
            'next_version': next_version,
            'latest_asset': latest_asset,
            'version_info': version_info
        }
        
    except Exception as e:
        print(f"❌ Error looking up asset versions: {e}")
        import traceback
        traceback.print_exc()
        return None

def lookup_asset_versions_v2(asset_base_id):
    """
    Look up all versions of an asset by 13-character asset base ID (11 base + 2 variant) and return version info
    """
    try:
        print(f"🔍 Looking up versions for asset base ID: {asset_base_id}")
        
        # Query the Atlas API to get all assets
        api_url = "http://localhost:8000/api/v1/assets"
        print(f"   🌐 Making API request to: {api_url}")
        
        try:
            response = requests.get(api_url, params={"limit": 1000}, timeout=30)
        except Exception as req_error:
            print(f"❌ Request failed: {req_error}")
            return None
        
        print(f"   📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response text: {response.text}")
            return None
        
        assets_data = response.json()
        all_assets = assets_data.get('items', [])
        
        # Filter assets that match the asset base ID (first 13 characters: 11 base + 2 variant)
        matching_assets = []
        print(f"   🔍 Checking {len(all_assets)} total assets in database...")
        
        for asset in all_assets:
            asset_id = asset.get('id', '')
            print(f"   🔍 Checking asset: {asset_id}")
            
            if len(asset_id) >= 13 and asset_id[:13].upper() == asset_base_id.upper():
                matching_assets.append(asset)
                print(f"   ✅ Found matching asset: {asset_id}")
            else:
                if len(asset_id) >= 13:
                    print(f"   ❌ No match: {asset_id[:13]} != {asset_base_id.upper()}")
                else:
                    print(f"   ❌ Too short: {asset_id} (length: {len(asset_id)})")
        
        print(f"   📊 Total matching assets: {len(matching_assets)}")
        
        if not matching_assets:
            print(f"   ❌ No assets found with asset base ID: {asset_base_id}")
            return None  # Return None to trigger "No Asset Found" error
        
        # Sort by version number (last 3 characters)
        version_info = []
        print(f"   🔍 Processing {len(matching_assets)} matching assets...")
        
        for asset in matching_assets:
            asset_id = asset.get('id', '')
            print(f"   🔍 Processing asset ID: {asset_id}")
            
            if len(asset_id) == 16:  # 16-character UIDs now
                try:
                    version_str = asset_id[-3:]  # Last 3 characters are version
                    version_num = int(version_str)
                    version_info.append({
                        'version': version_num,
                        'asset_id': asset_id,
                        'asset_data': asset
                    })
                    print(f"   ✅ Parsed version {version_num:03d} from {asset_id}")
                except ValueError:
                    print(f"   ⚠️ Invalid version format in asset ID: {asset_id} (last 3: '{asset_id[-3:]}')")
            elif len(asset_id) == 14:  # Legacy 14-character UIDs
                try:
                    version_str = asset_id[-3:]  # Last 3 characters are version
                    version_num = int(version_str)
                    version_info.append({
                        'version': version_num,
                        'asset_id': asset_id,
                        'asset_data': asset
                    })
                    print(f"   ✅ Parsed legacy version {version_num:03d} from {asset_id}")
                except ValueError:
                    print(f"   ⚠️ Invalid version format in legacy asset ID: {asset_id} (last 3: '{asset_id[-3:]}')")
            else:
                print(f"   ⚠️ Asset ID wrong length: {asset_id} (expected 14 or 12, got {len(asset_id)})")
        
        # Sort by version number
        version_info.sort(key=lambda x: x['version'])
        print(f"   🔍 Sorted version info: {[(v['asset_id'], v['version']) for v in version_info]}")
        
        # Find next version number
        existing_versions = [v['version'] for v in version_info]
        next_version = max(existing_versions) + 1 if existing_versions else 1
        print(f"   📊 Existing versions: {existing_versions}")
        print(f"   🔢 Next version calculated: {next_version}")
        
        # Get latest asset for metadata inheritance
        latest_asset = version_info[-1]['asset_data'] if version_info else None
        
        print(f"   📊 Found {len(existing_versions)} existing versions: {existing_versions}")
        print(f"   🔢 Next version will be: {next_version:03d}")
        
        return {
            'asset_base_id': asset_base_id,
            'existing_versions': existing_versions,
            'next_version': next_version,
            'latest_asset': latest_asset,
            'version_info': version_info
        }
        
    except Exception as e:
        print(f"❌ Error looking up asset versions: {e}")
        import traceback
        traceback.print_exc()
        return None

try:
    print("🚀 BLACKSMITH ATLAS VERSION EXPORT INITIATED")
    print("=" * 60)
    
    # Ensure backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Force reload for development
    import importlib
    modules_to_reload = ['assetlibrary.houdini.houdiniae']
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            print(f"🔄 Reloaded: {module_name}")
    
    from assetlibrary.houdini.houdiniae import TemplateAssetExporter
    
    subnet = hou.pwd()
    print(f"📦 Exporting version from subnet: {subnet.path()}")
    
    # Get the base UID from the Asset ID parameter
    base_uid_input = subnet.parm("version_parent_asset_id").eval().strip() if subnet.parm("version_parent_asset_id") else ""
    
    if not base_uid_input:
        subnet.parm("export_status").set("❌ Missing Asset ID")
        hou.ui.displayMessage("❌ Please enter an Asset ID (13-character: 11 base + 2 variant)", severity=hou.severityType.Error)
        raise Exception("Asset ID required")
    
    if len(base_uid_input) != 13:
        subnet.parm("export_status").set("❌ Asset ID wrong length")
        hou.ui.displayMessage(f"❌ Asset ID must be exactly 13 characters (11 base + 2 variant). Got {len(base_uid_input)} characters.", severity=hou.severityType.Error)
        raise Exception("Invalid Asset ID length")
    
    # Use full 13-character asset ID (11 base + 2 variant)
    asset_base_id = base_uid_input[:13].upper()
    base_uid = asset_base_id[:11]  # First 11 characters
    variant_id = asset_base_id[11:13]  # Characters 11-13
    print(f"🎯 Asset Base ID: {asset_base_id} (Base: {base_uid}, Variant: {variant_id})")
    
    # Update status
    subnet.parm("export_status").set("🔄 Looking up versions...")
    
    # Lookup existing versions
    print(f"🔍 Looking up existing versions for asset base ID: {asset_base_id}")
    version_info = lookup_asset_versions_v2(asset_base_id)
    if not version_info:
        subnet.parm("export_status").set("❌ Asset not found")
        hou.ui.displayMessage(f"❌ No Asset Found: {asset_base_id} not found in database", severity=hou.severityType.Error)
        raise Exception("No Asset Found")
    
    next_version = version_info['next_version']
    latest_asset = version_info['latest_asset']
    existing_versions = version_info['existing_versions']
    new_asset_id = f"{base_uid}{variant_id}{next_version:03d}"  # 16-character: 11 base + 2 variant + 3 version
    
    print(f"🔍 VERSION LOOKUP RESULTS:")
    print(f"   Asset Base ID: {asset_base_id} (Base: {base_uid}, Variant: {variant_id})")
    print(f"   Existing versions found: {existing_versions}")
    print(f"   Next version: {next_version}")
    print(f"   New asset ID: {new_asset_id}")
    print(f"   Latest asset exists: {latest_asset is not None}")
    
    if latest_asset:
        print(f"   Latest asset ID: {latest_asset.get('id', 'unknown')}")
        print(f"   Latest asset name: {latest_asset.get('name', 'unknown')}")
    
    # Inherit metadata from latest version if it exists
    if latest_asset:
        print("📋 Inheriting metadata from latest version...")
        hierarchy = latest_asset.get('metadata', {}).get('hierarchy', {})
        inherited_asset_type = hierarchy.get('asset_type', 'Assets')
        inherited_subcategory = hierarchy.get('subcategory', 'Blacksmith Asset')
        inherited_render_engine = hierarchy.get('render_engine', 'Redshift')
        
        # Inherit the original asset name
        inherited_asset_name = latest_asset.get('name', f'Asset_{base_uid}')
        
        print(f"   Asset Type: {inherited_asset_type}")
        print(f"   Subcategory: {inherited_subcategory}")
        print(f"   Render Engine: {inherited_render_engine}")
        print(f"   Asset Name: {inherited_asset_name}")
    else:
        print("📋 No existing versions found, using defaults...")
        inherited_asset_type = "Assets"
        inherited_subcategory = "Blacksmith Asset"
        inherited_render_engine = "Redshift"
        inherited_asset_name = f"Asset_{base_uid}"
    
    # Use the inherited asset name (same as original)
    asset_name = inherited_asset_name
    
    # Update status
    subnet.parm("export_status").set(f"🔄 Creating version {next_version:03d}...")
    
    print(f"📋 VERSION EXPORT CONFIGURATION:")
    print(f"   🎯 Action: version_up")
    print(f"   🏷️ Asset Name: {asset_name}")
    print(f"   🆔 New Asset ID: {new_asset_id}")
    print(f"   📂 Asset Type: {inherited_asset_type}")
    print(f"   📋 Subcategory: {inherited_subcategory}")
    print(f"   🎨 Render Engine: {inherited_render_engine}")
    print(f"   🔢 Version: {next_version}")
    
    # Create extended tags list for version
    extended_tags = ["version", f"version_{next_version:03d}", f"base_{base_uid}"]
    extended_tags.extend([inherited_asset_type.lower(), inherited_subcategory.lower().replace(' ', '_'), inherited_render_engine.lower()])
    
    # Create metadata
    hierarchy_metadata = {
        "dimension": "3D",
        "asset_type": inherited_asset_type,
        "subcategory": inherited_subcategory,
        "render_engine": inherited_render_engine,
        "houdini_version": f"{hou.applicationVersion()[0]}.{hou.applicationVersion()[1]}.{hou.applicationVersion()[2]}",
        "export_time": str(datetime.now()),
        "tags": extended_tags,
        "action": "version_up",
        "parent_asset_id": asset_base_id,  # Pass 13-character asset base ID
        "version": next_version,
        "base_uid": base_uid,
        "variant_id": variant_id,
        "asset_base_id": asset_base_id
    }

    # Create TemplateAssetExporter with inherited parameters
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=inherited_subcategory,
        tags=extended_tags,
        asset_type=inherited_asset_type,
        render_engine=inherited_render_engine,
        metadata=hierarchy_metadata,
        action="version_up",
        parent_asset_id=asset_base_id,  # Pass 13-character asset base ID
        thumbnail_action=thumbnail_action,  # Use thumbnail parameters from UI
        thumbnail_file_path=thumbnail_file_path
    )
    
    print(f"✅ Created exporter with ID: {exporter.asset_id}")
    print(f"📁 Export location: {exporter.asset_folder}")
    
    # Get nodes to export
    nodes_to_export = subnet.children()
    if not nodes_to_export:
        subnet.parm("export_status").set("❌ No nodes to export")
        hou.ui.displayMessage("❌ No nodes found in subnet to export!", severity=hou.severityType.Error)
        raise Exception("No nodes to export")
    else:
        print(f"📦 Found {len(nodes_to_export)} nodes to export:")
        for i, node in enumerate(nodes_to_export, 1):
            print(f"   {i}. {node.name()} ({node.type().name()})")
        
        # CALL EXPORT LOGIC
        print("🚀 Starting template export...")
        success = exporter.export_as_template(subnet, nodes_to_export)
        
        if success:
            subnet.parm("export_status").set("✅ Version export completed!")
            
            # Add to ArangoDB Atlas_Library collection via REST API
            try:
                print("\\\\n🗄️ ADDING TO ATLAS API...")
                print(f"🔍 Looking for metadata in: {exporter.asset_folder}")
                
                # Find the metadata.json file
                metadata_file = os.path.join(exporter.asset_folder, "metadata.json")
                print(f"🔍 Checking metadata file: {metadata_file}")
                
                if os.path.exists(metadata_file):
                    print("✅ Metadata file found! Reading contents...")
                    
                    # Debug: Show metadata contents
                    with open(metadata_file, 'r') as f:
                        metadata_content = f.read()
                    print(f"📄 Metadata content (first 500 chars): {metadata_content[:500]}...")
                    
                    # Use the Atlas REST API ingestion script
                    print("🚀 Calling Atlas API ingestion script...")
                    api_success = call_atlas_api_ingestion(metadata_file)
                    
                    if api_success:
                        print("✅ Successfully added to Atlas Library via REST API!")
                    else:
                        print("❌ Failed to add to Atlas Library via API (check API connection)")
                else:
                    print(f"❌ Metadata file not found: {metadata_file}")
                    
                    # Debug: List what files ARE in the folder
                    try:
                        folder_contents = os.listdir(exporter.asset_folder)
                        print(f"📁 Folder contents: {folder_contents}")
                    except:
                        print(f"📁 Could not list folder contents")
                    
            except Exception as api_error:
                print(f"❌ API ingestion error: {api_error}")
                import traceback
                traceback.print_exc()
                # Don't fail the export if API fails - just log it
            
            success_msg = f\"\"\"✅ ATLAS VERSION EXPORT SUCCESSFUL!
            
🎯 Action: Version Up Asset
🏷️ Asset Name: {asset_name}
🆔 New Asset ID: {exporter.asset_id} (Base: {exporter.base_uid}, Version: {exporter.version:03d})
📂 Category: {inherited_asset_type}/{inherited_subcategory}/
📍 Location: {exporter.asset_folder}

🎯 The new version is now in the Atlas library!
🗄️ Added to Atlas Library via REST API
📋 Inherited metadata from latest version\"\"\"
            
            hou.ui.displayMessage(success_msg, title="🎉 Atlas Version Export Complete")
            print("🎉 VERSION EXPORT SUCCESS!")
            print(f"📍 Location: {exporter.asset_folder}")
        else:
            subnet.parm("export_status").set("❌ Version export failed")
            hou.ui.displayMessage("❌ Version export failed! Check console for details.", severity=hou.severityType.Error)
            print("❌ VERSION EXPORT FAILED - See console")

except Exception as e:
    error_msg = f"Version export error: {str(e)}"
    print(f"❌ {error_msg}")
    
    try:
        hou.pwd().parm("export_status").set("❌ Version export error")
    except:
        pass
    
    hou.ui.displayMessage(f"❌ {error_msg}\\\\n\\\\nCheck console for details.", severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
'''

def create_variant_export_script():
    """Create script for variant asset export with proper parameter handling"""
    return '''
# 🏭 BLACKSMITH ATLAS VARIANT EXPORT SCRIPT
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

def call_atlas_api_ingestion(metadata_file_path):
    """
    Call the Atlas API ingestion script to submit metadata.json via REST API
    """
    try:
        print(f"📡 Starting API ingestion for: {metadata_file_path}")
        
        # Path to the ingestion script
        ingestion_script = "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/scripts/utilities/ingest_metadata_curl.py"
        
        # Check if ingestion script exists
        if not os.path.exists(ingestion_script):
            print(f"❌ Ingestion script not found: {ingestion_script}")
            return False
        
        # Check if metadata file exists
        if not os.path.exists(metadata_file_path):
            print(f"❌ Metadata file not found: {metadata_file_path}")
            return False
            
        print(f"✅ Found ingestion script: {ingestion_script}")
        print(f"✅ Found metadata file: {metadata_file_path}")
        
        # Use system python3
        python_exec = "python3"
        print(f"✅ Using system python3: {python_exec}")
        
        # Prepare the command
        cmd = [
            python_exec,
            ingestion_script,
            metadata_file_path,
            "--api-url", "http://localhost:8000",
            "--verbose"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        # Run the ingestion script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        print(f"📊 Process returned code: {result.returncode}")
        print(f"📤 STDOUT:\\n{result.stdout}")
        
        if result.stderr:
            print(f"⚠️ STDERR:\\n{result.stderr}")
        
        if result.returncode == 0:
            print("✅ API ingestion completed successfully!")
            return True
        else:
            print(f"❌ API ingestion failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API ingestion timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ API ingestion error: {e}")
        import traceback
        traceback.print_exc()
        return False

print("🎭 Starting Variant Asset Export...")

try:
    # Get the node (subnet)
    node = hou.pwd()
    print(f"📦 Working with node: {node.path()}")
    
    # Get variant parameters
    variant_parent_id = node.parm("variant_parent_id").eval().strip()
    variant_name = node.parm("variant_name").eval().strip()
    
    # Validation
    if not variant_parent_id:
        hou.ui.displayMessage("❌ Parent Asset ID is required for variant creation!", severity=hou.severityType.Error)
        raise Exception("Parent Asset ID required")
        
    if len(variant_parent_id) != 11:
        hou.ui.displayMessage("❌ Parent Asset ID must be exactly 11 characters (base UID only)!", severity=hou.severityType.Error)
        raise Exception("Invalid Parent Asset ID length")
        
    if not variant_name:
        variant_name = "default"
    
    # Validation: Don't allow "default" as variant name
    if variant_name.lower() == "default":
        error_msg = '❌ Asset Variant Name has to be different than "default"'
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        if node.parm("export_status"):
            node.parm("export_status").set("❌ Invalid variant name")
        raise Exception(error_msg)
    
    # Validation: Check if parent asset exists in database
    print("🔍 Validating parent asset exists in database...")
    try:
        import urllib.request
        import json
        
        api_url = "http://localhost:8000/api/v1/assets?limit=1000"
        print(f"   🌐 Making API request to: {api_url}")
        
        response = urllib.request.urlopen(api_url, timeout=30)
        assets_data = json.loads(response.read().decode())
        all_assets = assets_data.get('items', [])
        
        # Look for the original asset (AA variant) with the base UID
        target_asset_id = f"{variant_parent_id}AA001"  # Original asset format
        original_asset_found = False
        
        for asset in all_assets:
            if asset.get('id', '') == target_asset_id:
                original_asset_found = True
                print(f"   ✅ Found original asset for variant: {target_asset_id}")
                break
        
        if not original_asset_found:
            error_msg = f"❌ No Asset Found: {variant_parent_id} not found in database"
            print(f"   ❌ {error_msg}")
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            if node.parm("export_status"):
                node.parm("export_status").set("❌ Asset not found")
            raise Exception("No Asset Found")
            
    except urllib.error.URLError as e:
        error_msg = f"❌ Cannot connect to database to validate asset: {e}"
        print(f"   ❌ {error_msg}")
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        if node.parm("export_status"):
            node.parm("export_status").set("❌ Database connection failed")
        raise Exception("Database connection failed")
    except Exception as e:
        if "No Asset Found" in str(e):
            raise  # Re-raise the asset not found error
        error_msg = f"❌ Error validating parent asset: {e}"
        print(f"   ❌ {error_msg}")
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        if node.parm("export_status"):
            node.parm("export_status").set("❌ Validation failed")
        raise Exception("Asset validation failed")
    
    # For variants, pass the variant name as asset_name, but the TemplateAssetExporter
    # will look up the original asset name and use that instead
    variant_asset_name = variant_name  # This will be the variant name, used for metadata
    
    print(f"🎭 Variant Parameters:")
    print(f"   Parent Asset ID: {variant_parent_id}")
    print(f"   Variant Name: {variant_name}")
    print(f"   Asset Name: {variant_asset_name} (from subnet name)")
    
    # Update export status
    if node.parm("export_status"):
        node.parm("export_status").set("🎭 Exporting Variant...")
    
    # Import the exporter
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    from assetlibrary.houdini.houdiniae import TemplateAssetExporter
    
    # Get inheritance data from parent asset (same logic as version_up)
    print("📋 Looking up parent asset for inheritance...")
    base_uid = variant_parent_id  # This is the 11-character base UID
    
    # Query the Atlas API to find the original asset (AA variant)
    target_asset_id = f"{base_uid}AA001"  # Original asset format
    print(f"   🔍 Looking for original asset: {target_asset_id}")
    
    # Initialize defaults
    inherited_asset_type = "Assets"
    inherited_subcategory = "Blacksmith Asset"
    inherited_render_engine = "Redshift"
    inherited_asset_name = f"Asset_{base_uid}"
    
    try:
        import urllib.request
        import json
        
        api_url = "http://localhost:8000/api/v1/assets?limit=1000"
        print(f"   🌐 Making API request to: {api_url}")
        
        response = urllib.request.urlopen(api_url, timeout=30)
        assets_data = json.loads(response.read().decode())
        all_assets = assets_data.get('items', [])
        
        # Find the original asset (AA variant)
        original_asset = None
        for asset in all_assets:
            asset_id = asset.get('id', '')
            if asset_id == target_asset_id:
                original_asset = asset
                print(f"   ✅ Found original asset: {asset_id}")
                break
        
        # Inherit metadata from original asset if found
        if original_asset:
            print("📋 Inheriting metadata from original asset...")
            hierarchy = original_asset.get('metadata', {}).get('hierarchy', {})
            inherited_asset_type = hierarchy.get('asset_type', 'Assets')
            inherited_subcategory = hierarchy.get('subcategory', 'Blacksmith Asset')
            inherited_render_engine = hierarchy.get('render_engine', 'Redshift')
            
            # Inherit the original asset name
            inherited_asset_name = original_asset.get('name', f'Asset_{base_uid}')
            
            print(f"   ✅ Inherited Asset Type: {inherited_asset_type}")
            print(f"   ✅ Inherited Subcategory: {inherited_subcategory}")
            print(f"   ✅ Inherited Render Engine: {inherited_render_engine}")
            print(f"   ✅ Inherited Asset Name: {inherited_asset_name}")
        else:
            print(f"   ⚠️ Original asset not found, using defaults")
    
    except Exception as e:
        print(f"   ⚠️ Error getting parent asset data, using defaults: {e}")
    
    # Create exporter for variant with inherited properties
    exporter = TemplateAssetExporter(
        asset_name=variant_asset_name,
        subcategory=inherited_subcategory,  # Inherit from parent asset
        description="Variant asset",
        tags=[],  # No tags for variants
        asset_type=inherited_asset_type,  # Inherit from parent asset
        render_engine=inherited_render_engine,  # Inherit from parent asset
        metadata="",
        action="variant",
        parent_asset_id=variant_parent_id,
        variant_name=variant_name,
        thumbnail_action=thumbnail_action,  # Use thumbnail parameters from UI
        thumbnail_file_path=thumbnail_file_path
    )
    
    print(f"✅ Created variant exporter with ID: {exporter.asset_id}")
    print(f"   Base UID: {exporter.base_uid}")
    print(f"   Variant ID: {exporter.variant_id}")
    print(f"   Version: {exporter.version:03d}")
    
    # Get children to export
    children = node.children()
    if not children:
        hou.ui.displayMessage("❌ No nodes found inside subnet to export!", severity=hou.severityType.Error)
        raise Exception("No nodes to export")
    
    # Export the variant
    success = exporter.export_as_template(node, children)
    
    if success:
        # Ensure database ingestion by calling API explicitly
        print("📡 Ensuring variant is added to database...")
        metadata_file = exporter.asset_folder / "metadata.json"
        
        if metadata_file.exists():
            try:
                # Call the API ingestion function from the main export script
                api_success = call_atlas_api_ingestion(str(metadata_file))
                if api_success:
                    print("✅ Variant successfully added to database!")
                else:
                    print("⚠️ Database ingestion may have failed, but files were exported")
            except Exception as api_error:
                print(f"⚠️ Database API call failed: {api_error}")
                print("   Files were exported successfully, but may need manual database sync")
        
        # Update export status
        if node.parm("export_status"):
            node.parm("export_status").set("✅ Variant Export Complete!")
        
        success_msg = f"""✅ VARIANT ASSET EXPORT SUCCESSFUL!

🎭 Variant: {variant_name}
📦 Asset: {variant_asset_name}
🆔 ID: {exporter.asset_id}
📁 Base UID: {exporter.base_uid}
🎨 Variant: {exporter.variant_id}
📊 Version: {exporter.version:03d}

🗂️ Location: {exporter.asset_folder}

The variant has been created and linked to the original asset!"""
        
        hou.ui.displayMessage(success_msg, title="🎭 Variant Export Complete")
        print("🎉 Variant export completed successfully!")
        
    else:
        if node.parm("export_status"):
            node.parm("export_status").set("❌ Variant Export Failed")
        hou.ui.displayMessage("❌ Variant export failed! Check console for details.", severity=hou.severityType.Error)
        print("❌ Variant export failed!")

except Exception as e:
    error_msg = f"❌ Variant Export Error: {str(e)}"
    print(error_msg)
    if hou.pwd().parm("export_status"):
        hou.pwd().parm("export_status").set("❌ Variant Export Error")
    hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
'''

def create_export_script():
    """Create the export callback script - FIXED VERSION WITH HDA AUTO-EXECUTION"""
    return '''
# 🏭 BLACKSMITH ATLAS EXPORT SCRIPT
import sys
import os
import subprocess
import json
from pathlib import Path

def call_atlas_api_ingestion(metadata_file_path):
    """
    Call the Atlas API ingestion script to submit metadata.json via REST API
    """
    try:
        print(f"📡 Starting API ingestion for: {metadata_file_path}")
        
        # Path to the ingestion script
        ingestion_script = "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/scripts/utilities/ingest_metadata_curl.py"
        
        # Check if ingestion script exists
        if not os.path.exists(ingestion_script):
            print(f"❌ Ingestion script not found: {ingestion_script}")
            return False
        
        # Check if metadata file exists
        if not os.path.exists(metadata_file_path):
            print(f"❌ Metadata file not found: {metadata_file_path}")
            return False
            
        print(f"✅ Found ingestion script: {ingestion_script}")
        print(f"✅ Found metadata file: {metadata_file_path}")
        
        # Use system python3 to avoid virtual environment conflicts with Houdini
        python_exec = "python3"
        print(f"✅ Using system python3: {python_exec}")
        
        # Prepare the command to run the ingestion script
        cmd = [
            python_exec,
            ingestion_script,
            metadata_file_path,
            "--api-url", "http://localhost:8000",
            "--verbose"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        # Run the ingestion script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Log the output
        if result.stdout:
            print(f"📄 STDOUT:\\n{result.stdout}")
        
        if result.stderr:
            print(f"⚠️ STDERR:\\n{result.stderr}")
            
        # Check if the command was successful
        if result.returncode == 0:
            print("✅ API ingestion completed successfully!")
            return True
        else:
            print(f"❌ API ingestion failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API ingestion timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ API ingestion error: {e}")
        import traceback
        traceback.print_exc()
        return False

try:
    print("🚀 BLACKSMITH ATLAS EXPORT INITIATED")
    print("=" * 50)
    
    # Ensure backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Force reload for development
    import importlib
    modules_to_reload = ['assetlibrary.houdini.houdiniae']
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            print(f"🔄 Reloaded: {module_name}")
    
    from assetlibrary.houdini.houdiniae import TemplateAssetExporter
    
    subnet = hou.pwd()
    print(f"📦 Exporting from subnet: {subnet.path()}")
    
    # Get action parameter
    action_value = int(subnet.parm("action").eval()) if subnet.parm("action") else 0
    action_options = ["create_new", "version_up", "variant"]
    action = action_options[action_value] if 0 <= action_value < len(action_options) else "create_new"
    
    print(f"🎯 Action: {action}")
    
    # Get parameters based on action
    if action == "create_new":
        asset_name = subnet.parm("asset_name").eval().strip() if subnet.parm("asset_name") else ""
        asset_type_idx = int(subnet.parm("asset_type").eval()) if subnet.parm("asset_type") else 0
        tags_str = subnet.parm("tags").eval().strip() if subnet.parm("tags") else ""
        render_engine_idx = int(subnet.parm("render_engine").eval()) if subnet.parm("render_engine") else 0
        parent_asset_id = None
        
        # Get subcategory from the correct parameter based on asset type
        subcategory_parm_names = ["subcategory_assets", "subcategory_fx", "subcategory_materials", "subcategory_hdas"]
        subcategory_parm_name = subcategory_parm_names[asset_type_idx] if asset_type_idx < len(subcategory_parm_names) else subcategory_parm_names[0]
        subcategory_idx = int(subnet.parm(subcategory_parm_name).eval()) if subnet.parm(subcategory_parm_name) else 0
        
        # Get branded checkbox value
        branded = bool(subnet.parm("branded").eval()) if subnet.parm("branded") else False
        
        # Get thumbnail parameters
        thumbnail_action_idx = int(subnet.parm("thumbnail_action").eval()) if subnet.parm("thumbnail_action") else 0
        thumbnail_actions = ["automatic", "choose", "disable"]
        thumbnail_action = thumbnail_actions[thumbnail_action_idx] if thumbnail_action_idx < len(thumbnail_actions) else "automatic"
        # Use unexpandedString to preserve $F variables instead of evaluating them
        thumbnail_file_path = subnet.parm("thumbnail_file").unexpandedString().strip() if subnet.parm("thumbnail_file") else ""
        
        print(f"🎨 Thumbnail Action: {thumbnail_action}")
        if thumbnail_action == "choose" and thumbnail_file_path:
            print(f"📁 Thumbnail File: {thumbnail_file_path}")
    elif action == "version_up":
        parent_asset_id = subnet.parm("version_parent_asset_id").eval().strip() if subnet.parm("version_parent_asset_id") else ""
        # For Version Up, we'll use the subnet name as asset name
        asset_name = subnet.name()
        tags_str = ""  # No tags for version up
        # Default values for version up (we'll inherit from parent asset)
        asset_type_idx = 0  # Default to "Assets"
        render_engine_idx = 0  # Default to "Redshift"
        subcategory_idx = 0  # Default to "Blacksmith Asset"
        branded = False
        
        # Get thumbnail parameters for version up
        thumbnail_action_idx = int(subnet.parm("thumbnail_action_version").eval()) if subnet.parm("thumbnail_action_version") else 0
        thumbnail_actions = ["automatic", "choose", "disable"]
        thumbnail_action = thumbnail_actions[thumbnail_action_idx] if thumbnail_action_idx < len(thumbnail_actions) else "automatic"
        # Use unexpandedString to preserve $F variables instead of evaluating them  
        thumbnail_file_path = subnet.parm("thumbnail_file_version").unexpandedString().strip() if subnet.parm("thumbnail_file_version") else ""
        
        print(f"🎨 Thumbnail Action (Version Up): {thumbnail_action}")
        if thumbnail_action == "choose" and thumbnail_file_path:
            print(f"📁 Thumbnail File: {thumbnail_file_path}")
    elif action == "variant":
        parent_asset_id = subnet.parm("variant_parent_id").eval().strip() if subnet.parm("variant_parent_id") else ""
        # For Variant, we'll use the subnet name as asset name
        asset_name = subnet.name()
        tags_str = ""  # No tags for variant
        # Default values for variant (we'll inherit from parent asset)
        asset_type_idx = 0  # Default to "Assets"
        render_engine_idx = 0  # Default to "Redshift"
        subcategory_idx = 0  # Default to "Blacksmith Asset"
        branded = False
        
        # Get thumbnail parameters for variant
        thumbnail_action_idx = int(subnet.parm("thumbnail_action_variant").eval()) if subnet.parm("thumbnail_action_variant") else 0
        thumbnail_actions = ["automatic", "choose", "disable"]
        thumbnail_action = thumbnail_actions[thumbnail_action_idx] if thumbnail_action_idx < len(thumbnail_actions) else "automatic"
        # Use unexpandedString to preserve $F variables instead of evaluating them
        thumbnail_file_path = subnet.parm("thumbnail_file_variant").unexpandedString().strip() if subnet.parm("thumbnail_file_variant") else ""
        
        print(f"🎨 Thumbnail Action (Variant): {thumbnail_action}")
        if thumbnail_action == "choose" and thumbnail_file_path:
            print(f"📁 Thumbnail File: {thumbnail_file_path}")
    else:
        # Fallback
        asset_name = ""
        asset_type_idx = 0
        tags_str = ""
        render_engine_idx = 0
        parent_asset_id = None
        subcategory_idx = 0
    
    # Quick validation
    if action == "create_new" and not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("❌ Asset name is required for Create New Asset!", severity=hou.severityType.Error)
    elif action in ["version_up", "variant"] and not parent_asset_id:
        subnet.parm("export_status").set("❌ Missing parent asset ID")
        hou.ui.displayMessage(f"❌ Asset ID is required for {action.replace('_', ' ').title()}!", severity=hou.severityType.Error)
    elif action in ["version_up", "variant"] and len(parent_asset_id) < 11:
        subnet.parm("export_status").set("❌ Invalid parent asset ID")
        hou.ui.displayMessage(f"❌ Asset ID must be at least 11 characters for {action.replace('_', ' ').title()}!", severity=hou.severityType.Error)
    else:
        # Convert asset type and get subcategory
        asset_types = ["Assets", "FX", "Materials", "HDAs"]
        asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
        
        # Get the subcategory based on asset type
        subcategory_mapping = {
            "Assets": ["Blacksmith Asset", "Megascans", "Kitbash"],
            "FX": ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"], 
            "Materials": ["Blacksmith Materials", "Redshift", "Karma"],
            "HDAs": ["Blacksmith HDAs"]
        }
        
        subcategory_options = subcategory_mapping.get(asset_type, subcategory_mapping["Assets"])
        subcategory = subcategory_options[subcategory_idx] if subcategory_idx < len(subcategory_options) else subcategory_options[0]
        
        # Get render engine
        render_engines = ["Redshift", "Karma"]
        render_engine = render_engines[render_engine_idx] if render_engine_idx < len(render_engines) else "Redshift"
        
        # Process tags
        tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Update status
        subnet.parm("export_status").set("🔄 Exporting...")
        
        print(f"📋 EXPORT CONFIGURATION:")
        print(f"   🎯 Action: {action}")
        print(f"   🏷️ Asset: {asset_name}")
        print(f"   📂 Asset Type: {asset_type}")
        print(f"   📋 Subcategory: {subcategory}")
        print(f"   🎨 Render Engine: {render_engine}")
        print(f"   🏷️ Tags: {tags_list}")
        if parent_asset_id:
            print(f"   🔗 Parent Asset ID: {parent_asset_id}")
        
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
            "tags": extended_tags,
            "action": action,
            "parent_asset_id": parent_asset_id,
            "branded": branded if action == "create_new" else False
        }

        # Create TemplateAssetExporter with new parameters
        exporter = TemplateAssetExporter(
            asset_name=asset_name,
            subcategory=subcategory,
            tags=extended_tags,
            asset_type=asset_type,
            render_engine=render_engine,
            metadata=hierarchy_metadata,
            action=action,
            parent_asset_id=parent_asset_id,
            thumbnail_action=thumbnail_action,
            thumbnail_file_path=thumbnail_file_path
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
            
            # CALL EXPORT LOGIC (includes HDA loading and dl_Submit auto-execution)
            print("🚀 Starting template export...")
            print("   📋 This includes:")
            print("   • Template file export")  
            print("   • HDA loading and configuration")
            print("   • Auto-execution of dl_Submit button")
            success = exporter.export_as_template(subnet, nodes_to_export)
            
            if success:
                subnet.parm("export_status").set("✅ Export completed!")
                
                # Add to ArangoDB Atlas_Library collection via REST API
                try:
                    print("\\n🗄️ ADDING TO ATLAS API...")
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
                        
                        # Use the Atlas REST API ingestion script
                        print("🚀 Calling Atlas API ingestion script...")
                        api_success = call_atlas_api_ingestion(metadata_file)
                        
                        if api_success:
                            print("✅ Successfully added to Atlas Library via REST API!")
                        else:
                            print("❌ Failed to add to Atlas Library via API (check API connection)")
                    else:
                        print(f"❌ Metadata file not found: {metadata_file}")
                        
                        # Debug: List what files ARE in the folder
                        try:
                            folder_contents = os.listdir(exporter.asset_folder)
                            print(f"📁 Folder contents: {folder_contents}")
                        except:
                            print(f"📁 Could not list folder contents")
                        
                except Exception as api_error:
                    print(f"❌ API ingestion error: {api_error}")
                    import traceback
                    traceback.print_exc()
                    # Don't fail the export if API fails - just log it
                
                success_msg = f"""✅ ATLAS ASSET EXPORT SUCCESSFUL!
                
🎯 Action: {action.replace('_', ' ').title()}
🏷️ Asset: {asset_name}
🆔 Asset ID: {exporter.asset_id} (Base: {exporter.base_uid}, Version: {exporter.version:03d})
📂 Category: Assets/{subcategory}/
📍 Location: {exporter.asset_folder}

🎯 The asset is now in the Atlas library!
🗄️ Added to Atlas Library via REST API"""
                
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
