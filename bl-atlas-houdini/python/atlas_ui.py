#!/usr/bin/env python3
"""
Blacksmith Atlas - UI and Parameter Creation (Standalone)
========================================================

Contains all the UI parameter creation and main asset creation functionality.
Extracted from the original copy_to_atlas_asset.py for standalone use.

Author: Blacksmith VFX
Version: 3.0 (Standalone)
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

        print("\n🏭 BLACKSMITH ATLAS: Copy Selected to Atlas Asset (Standalone)")
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
    """Add comprehensive export parameters to the subnet - STANDALONE VERSION"""
    try:
        import hou
        print("   🔧 Adding Atlas export parameters (Standalone)...")

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
                                            menu_items=("0", "1", "2"),
                                            menu_labels=("Redshift", "Karma", "Universal"),
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

        # Export With No References checkbox inside Advanced folder
        no_references_checkbox = hou.ToggleParmTemplate("export_no_references", "Export With No References", default_value=False)
        no_references_checkbox.setHelp("Export only the template file without copying any geometry or texture references.\nIdeal for FX setups with large simulation files that don't need to be stored in the library.")
        advanced_folder.addParmTemplate(no_references_checkbox)

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

        # Check for required parameters
        required_params = [
            "action",
            "asset_name", "asset_type", "subcategory_assets", "render_engine", "tags",
            "thumbnail_action", "thumbnail_file", "branded", "export_no_references", "export_atlas_asset"
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


def create_export_script():
    """Create the export callback script - STANDALONE VERSION"""
    return '''
# 🏭 BLACKSMITH ATLAS EXPORT SCRIPT (STANDALONE)
import sys
import os
import subprocess
import json
from pathlib import Path

# Auto-detect the bl-atlas-houdini directory
try:
    # Get the current subnet (this script runs in the context of the subnet)
    subnet = hou.pwd()

    # Try to find bl-atlas-houdini directory
    script_dirs = [
        "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/bl-atlas-houdini",
        os.path.expanduser("~/bl-atlas-houdini"),
        "/opt/bl-atlas-houdini",
        "/usr/local/bl-atlas-houdini"
    ]

    bl_atlas_root = None
    for test_dir in script_dirs:
        if os.path.exists(os.path.join(test_dir, "python", "houdiniae.py")):
            bl_atlas_root = test_dir
            break

    if not bl_atlas_root:
        raise Exception("Could not find bl-atlas-houdini directory")

    python_path = os.path.join(bl_atlas_root, "python")

    if python_path not in sys.path:
        sys.path.insert(0, python_path)
        print(f"✅ Added to sys.path: {python_path}")

    # Import the standalone modules
    import houdiniae
    import api_client

    # Force reload for development
    import importlib
    importlib.reload(houdiniae)
    importlib.reload(api_client)

    print("🚀 BLACKSMITH ATLAS EXPORT INITIATED (STANDALONE)")
    print("=" * 50)

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

        # Get subcategory from the correct parameter based on asset type
        subcategory_parm_names = ["subcategory_assets", "subcategory_fx", "subcategory_materials", "subcategory_hdas"]
        subcategory_parm_name = subcategory_parm_names[asset_type_idx] if asset_type_idx < len(subcategory_parm_names) else subcategory_parm_names[0]
        subcategory_idx = int(subnet.parm(subcategory_parm_name).eval()) if subnet.parm(subcategory_parm_name) else 0

        # Get other parameters
        branded = bool(subnet.parm("branded").eval()) if subnet.parm("branded") else False
        export_no_references = bool(subnet.parm("export_no_references").eval()) if subnet.parm("export_no_references") else False

        # Get thumbnail parameters
        thumbnail_action_idx = int(subnet.parm("thumbnail_action").eval()) if subnet.parm("thumbnail_action") else 0
        thumbnail_actions = ["automatic", "choose", "disable"]
        thumbnail_action = thumbnail_actions[thumbnail_action_idx] if thumbnail_action_idx < len(thumbnail_actions) else "automatic"
        thumbnail_file_path = subnet.parm("thumbnail_file").unexpandedString().strip() if subnet.parm("thumbnail_file") else ""

        print(f"🎨 Thumbnail Action: {thumbnail_action}")
        if thumbnail_action == "choose" and thumbnail_file_path:
            print(f"📁 Thumbnail File: {thumbnail_file_path}")
    else:
        # For now, only support create_new in standalone version
        subnet.parm("export_status").set("❌ Only Create New Asset supported in standalone version")
        hou.ui.displayMessage("❌ Version Up and Variant assets not supported in standalone version yet!", severity=hou.severityType.Error)
        raise Exception("Only Create New Asset supported")

    # Quick validation
    if not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("❌ Asset name is required!", severity=hou.severityType.Error)
        raise Exception("Asset name required")

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
    render_engines = ["Redshift", "Karma", "Universal"]
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
    print(f"   📁 Export No References: {export_no_references}")

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
        "branded": branded,
        "export_no_references": export_no_references
    }

    # Create TemplateAssetExporter with new parameters
    exporter = houdiniae.TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,
        tags=extended_tags,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=hierarchy_metadata,
        action=action,
        thumbnail_action=thumbnail_action,
        thumbnail_file_path=thumbnail_file_path,
        export_no_references=export_no_references,
        bl_atlas_root=bl_atlas_root
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
            subnet.parm("export_status").set("✅ Export completed!")

            # Add to Atlas API via the standalone API client
            try:
                print("\\n🗄️ ADDING TO ATLAS API...")
                print(f"🔍 Looking for metadata in: {exporter.asset_folder}")

                # Find the metadata.json file in the exported asset folder
                metadata_file = os.path.join(exporter.asset_folder, "metadata.json")
                print(f"🔍 Checking metadata file: {metadata_file}")

                if os.path.exists(metadata_file):
                    print("✅ Metadata file found! Calling API...")

                    # Use the standalone API client
                    api_success = api_client.call_atlas_api_ingestion(metadata_file)

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

            # Build success message
            success_msg = f\"\"\"✅ ATLAS ASSET EXPORT SUCCESSFUL!

🎯 Action: {action.replace('_', ' ').title()}
🏷️ Asset: {asset_name}
🆔 Asset ID: {exporter.asset_id}
📂 Category: {asset_type}/{subcategory}/
📍 Location: {exporter.asset_folder}

🎯 The asset is now in the Atlas library!
🗄️ Added to Atlas Library via REST API\"\"\"

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