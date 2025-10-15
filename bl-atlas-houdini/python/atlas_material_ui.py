#!/usr/bin/env python3
"""
Blacksmith Atlas - Material UI and Parameter Creation (Standalone)
================================================================

Contains all the UI parameter creation and main material creation functionality.
Separate from atlas_ui.py to allow independent material export workflow.

Author: Blacksmith VFX
Version: 3.0 (Standalone - Materials)
"""

import os
import sys
import subprocess
import json
import uuid
import re
from pathlib import Path
from datetime import datetime


class TemplateMaterialExporter:
    """
    Export materials using Houdini's template system
    Material ID Structure: 11-character UID + 3-digit version = 14 characters total
    Example: 17EC72A67F4001 (no variants, only versioning)
    """

    def _sanitize_name_for_filesystem(self, name):
        """Sanitize material name for filesystem"""
        sanitized = re.sub(r'[^\w]', '_', name)
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        return sanitized

    def __init__(self, material_name, subcategory="Blacksmith Materials", tags=None, asset_type="Materials",
                 render_engine="Redshift", metadata=None, action="create_new", parent_material_id=None,
                 thumbnail_action="automatic", thumbnail_file_path="", bl_atlas_root=None):
        """
        Initialize Material Exporter

        Args:
            material_name: Name of the material
            action: Either "create_new" or "update_material"
            parent_material_id: For update_material action, the 11-character base UID
        """
        self.material_name = material_name
        self.subcategory = subcategory
        self.tags = tags or []
        self.asset_type = asset_type
        self.render_engine = render_engine
        self.metadata = metadata or {}
        self.action = action
        self.parent_material_id = parent_material_id
        self.thumbnail_action = thumbnail_action
        self.thumbnail_file_path = thumbnail_file_path
        self.bl_atlas_root = bl_atlas_root

        # Generate Material ID based on action
        if action == "create_new":
            # Generate new 11-character base UID + 3-digit version = 14 characters total
            self.base_uid = str(uuid.uuid4()).replace('-', '')[:11].upper()
            self.version = 1
            print(f"🆕 Creating NEW material: {self.base_uid} version {self.version:03d}")

        elif action == "update_material":
            # For update: expects 11-character base UID
            if not parent_material_id or len(parent_material_id) != 11:
                raise ValueError(f"Parent material ID required for update and must be exactly 11 characters (base UID)")
            self.base_uid = parent_material_id.upper()
            # Get next version number by checking existing exports
            self.version = self._get_next_version(self.base_uid)
            print(f"🔄 Updating material: {self.base_uid} to version {self.version:03d}")

        else:
            raise ValueError(f"Invalid action: {action}. Must be 'create_new' or 'update_material'")

        # Create full 14-character material ID (11 base + 3 version)
        self.material_id = f"{self.base_uid}{self.version:03d}"

        print(f"✅ Material ID: {self.material_id} ({len(self.material_id)} characters)")

    def _get_next_version(self, base_uid):
        """Get the next version number for a material base UID"""
        try:
            from config_manager import get_network_config
            config = get_network_config()
            library_path = Path(config.asset_library_3d)

            # Search for existing versions of this material
            material_folder_pattern = f"{base_uid}*"
            max_version = 0

            # Search in Materials category
            materials_path = library_path / "Materials" / self.subcategory
            if materials_path.exists():
                for folder in materials_path.glob(material_folder_pattern):
                    # Extract version from folder name (last 3 characters of 14-char ID)
                    folder_name = folder.name
                    if len(folder_name) >= 14 and folder_name[:11] == base_uid:
                        try:
                            version_str = folder_name[11:14]  # Characters 11-14 are the version
                            version = int(version_str)
                            max_version = max(max_version, version)
                        except (ValueError, IndexError):
                            continue

            next_version = max_version + 1
            print(f"📊 Found {max_version} existing version(s), next version: {next_version:03d}")
            return next_version

        except Exception as e:
            print(f"⚠️  Could not determine version, defaulting to 001: {e}")
            return 1


def copy_selected_to_atlas_material():
    """
    Main function to copy selected material to a subnet and add Atlas export parameters
    """
    try:
        import hou

        print("\n🎨 BLACKSMITH ATLAS: Copy Selected to Atlas Material (Standalone)")
        print("=" * 60)

        # Get selected nodes
        selected_nodes = hou.selectedNodes()

        # Validation
        if not selected_nodes:
            error_msg = "❌ No material selected.\n\nPlease select a material node to create an Atlas Material."
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

        print(f"🎨 Creating subnet from {len(selected_nodes)} material(s) in {parent.path()}")

        # Get material name from user
        result = hou.ui.readInput("Enter name for the Atlas Material:",
                                 buttons=("OK", "Cancel"),
                                 severity=hou.severityType.Message,
                                 title="Atlas Material Name",
                                 initial_contents="MyAtlasMaterial")

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
        user_material_name = text_input.strip() if text_input and text_input.strip() else "atlas_material"

        # Create separate names: one for node (sanitized) and one for parameters (original)
        subnet_node_name = user_material_name.replace(" ", "_")  # Replace spaces with underscores for node name
        material_parameter_name = user_material_name  # Keep original for parameters

        print(f"📝 User entered: '{user_material_name}'")
        print(f"📝 Node name: '{subnet_node_name}'")
        print(f"📝 Parameter name: '{material_parameter_name}'")

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

        print(f"✅ Successfully copied {len(copied_nodes)} material node(s) to subnet")

        # Reposition copied nodes to be centered below subnet inputs
        # Get subnet input nodes positions (Input 1, 2, 3, 4)
        subnet_inputs = [subnet.indirectInputs()[i] for i in range(4) if i < len(subnet.indirectInputs())]

        # Calculate target position (centered below inputs)
        if subnet_inputs:
            # Get the bottom-most input position
            input_y_positions = [inp.position()[1] for inp in subnet_inputs if inp]
            target_y = min(input_y_positions) - 2.0 if input_y_positions else 0.0
        else:
            target_y = -2.0  # Default position below origin

        # Calculate bounding box of copied nodes
        if copied_nodes:
            x_coords = []
            y_coords = []

            for node in copied_nodes:
                pos = node.position()
                x_coords.append(pos[0])
                y_coords.append(pos[1])

            # Calculate center and top of copied nodes
            nodes_center_x = (min(x_coords) + max(x_coords)) / 2
            nodes_top_y = max(y_coords)

            # Calculate offset to position nodes centered below inputs
            offset_x = 0 - nodes_center_x  # Center horizontally at x=0
            offset_y = target_y - nodes_top_y  # Position top of nodes at target_y

            # Apply offset to all copied nodes (maintains relative positions)
            for node in copied_nodes:
                current_pos = node.position()
                new_pos = (current_pos[0] + offset_x, current_pos[1] + offset_y)
                node.setPosition(new_pos)

            print(f"✅ Repositioned nodes: offset=({offset_x:.2f}, {offset_y:.2f})")

        # Add comprehensive export parameters
        success = add_atlas_material_export_parameters(subnet, material_parameter_name)
        if not success:
            print("❌ Failed to add export parameters")
            return False

        print("✅ Atlas Material subnet created successfully!")

        # Select the new subnet and display inside
        subnet.setSelected(True, clear_all_selected=True)

        # Success message
        success_msg = f"""✅ ATLAS MATERIAL SUBNET CREATED!

🎨 Subnet: {subnet.name()}
📁 Location: {subnet.path()}
🎯 Material nodes copied: {len(copied_nodes)}

The subnet now contains:
• Your selected material
• Export parameters for Material Library
• Export button for one-click publishing

Next steps:
1. Configure material details in parameters
2. Click 'Export Atlas Material' button"""

        hou.ui.displayMessage(success_msg, title="🎉 Atlas Material Ready")
        return True

    except Exception as e:
        print(f"❌ Atlas copy operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_atlas_material_export_parameters(subnet, default_name="MyAtlasMaterial"):
    """Add comprehensive export parameters to the material subnet - STANDALONE VERSION (MATERIALS)"""
    try:
        import hou
        print("   🔧 Adding Atlas material export parameters (Standalone)...")

        # Get existing parameter template group
        parm_group = subnet.parmTemplateGroup()

        # Add just the most basic parameters first to test
        print(f"   📋 Current parameter count: {len(parm_group.parmTemplates())}")

        # Create a TAB folder for Atlas Material Export parameters
        atlas_tab = hou.FolderParmTemplate("atlas_material_export_tab", "Atlas Material Export", folder_type=hou.folderType.Tabs)

        # Action dropdown (first parameter in tab)
        action_parm = hou.MenuParmTemplate("action", "Action",
                                          menu_items=("0", "1"),
                                          menu_labels=("Create New Material", "Update Material"),
                                          default_value=0)
        action_parm.setHelp("Choose the type of material creation: New Material or Update existing material")
        atlas_tab.addParmTemplate(action_parm)
        print(f"   ➕ Added action dropdown to tab")

        # === CREATE NEW ASSET PARAMETERS (visible when action == 0) ===

        # Material Name (Create New only)
        material_name = hou.StringParmTemplate("asset_name", "Material Name", 1)
        material_name.setDefaultValue([default_name])
        material_name.setHelp("Enter a unique name for this material")
        material_name.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(material_name)
        print(f"   ➕ Added material name (Create New only)")

        # Subcategory dropdown for Materials
        subcategory_materials = hou.MenuParmTemplate("subcategory_materials", "Subcategory",
                                                    menu_items=("0", "1"),
                                                    menu_labels=("Blacksmith Materials", "Environment"),
                                                    default_value=0)
        subcategory_materials.setHelp("Select the subcategory for this material")
        subcategory_materials.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(subcategory_materials)
        print(f"   ➕ Added material subcategory (Create New only)")

        # Render Engine (Create New only)
        render_engine = hou.MenuParmTemplate("render_engine", "Render Engine",
                                            menu_items=("0", "1"),
                                            menu_labels=("RS Material", "Material X"),
                                            default_value=0)
        render_engine.setHelp("Material type/system used")
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

        # Preview Mesh dropdown (only shown when thumbnail_action is "automatic")
        preview_mesh_parm = hou.MenuParmTemplate("preview_mesh", "Preview Mesh",
                                                 menu_items=("0", "1", "2", "3"),
                                                 menu_labels=("Shader Ball", "Advanced Shader Ball", "Cloth Ball", "Dragon Statue"))
        preview_mesh_parm.setDefaultValue(0)  # Default to Shader Ball
        preview_mesh_parm.setHelp("Select the preview mesh to use for automatic thumbnail rendering")
        preview_mesh_parm.setConditional(hou.parmCondType.HideWhen, "{ thumbnail_action != automatic }")
        thumbnail_folder.addParmTemplate(preview_mesh_parm)

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

        # Separator before Create New export section
        separator_create = hou.SeparatorParmTemplate("create_sep")
        separator_create.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
        atlas_tab.addParmTemplate(separator_create)

        # Export button (Create New only)
        export_button = hou.ButtonParmTemplate("export_atlas_material", "Export Atlas Material")
        export_button.setHelp("Export this material to the Atlas Library with auto-database insertion")
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

        # Insert the tab at the front of the parameter group (before Transform and Subnet tabs)
        # Get the first existing parameter template to insert before it
        first_parm = parm_group.parmTemplates()[0] if parm_group.parmTemplates() else None
        if first_parm:
            parm_group.insertBefore(first_parm, atlas_tab)
            print(f"   📁 Added Atlas Material Export tab at front (before {first_parm.label()})")
        else:
            parm_group.append(atlas_tab)
            print(f"   📁 Added Atlas Material Export tab")

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
            "asset_name", "subcategory_materials", "render_engine", "tags",
            "thumbnail_action", "thumbnail_file", "export_atlas_material"
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
    """Create the export callback script - STANDALONE VERSION (MATERIALS)"""
    return '''
# 🎨 BLACKSMITH ATLAS MATERIAL EXPORT SCRIPT (STANDALONE)
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
        if os.path.exists(os.path.join(test_dir, "python", "atlas_material_ui.py")):
            bl_atlas_root = test_dir
            break

    if not bl_atlas_root:
        raise Exception("Could not find bl-atlas-houdini directory")

    python_path = os.path.join(bl_atlas_root, "python")

    if python_path not in sys.path:
        sys.path.insert(0, python_path)
        print(f"✅ Added to sys.path: {python_path}")

    # Import the standalone modules
    import atlas_material_ui
    import api_client
    import houdiniae

    # Force reload for development
    import importlib
    importlib.reload(atlas_material_ui)
    importlib.reload(api_client)
    importlib.reload(houdiniae)

    print("🚀 BLACKSMITH ATLAS MATERIAL EXPORT INITIATED (STANDALONE)")
    print("=" * 50)

    # Get action parameter
    action_value = int(subnet.parm("action").eval()) if subnet.parm("action") else 0
    action_options = ["create_new", "update_material"]
    action = action_options[action_value] if 0 <= action_value < len(action_options) else "create_new"

    print(f"🎯 Material Action: {action}")

    # Get parameters based on action
    material_name = subnet.parm("asset_name").eval().strip() if subnet.parm("asset_name") else ""
    tags_str = subnet.parm("tags").eval().strip() if subnet.parm("tags") else ""

    # Materials are always in the "Materials" asset type
    asset_type = "Materials"

    # Get subcategory (Blacksmith Materials or Environment)
    subcategory_idx = int(subnet.parm("subcategory_materials").eval()) if subnet.parm("subcategory_materials") else 0
    subcategory_options = ["Blacksmith Materials", "Environment"]
    subcategory = subcategory_options[subcategory_idx] if subcategory_idx < len(subcategory_options) else "Blacksmith Materials"

    # Get render engine (RS Material or Material X)
    render_engine_idx = int(subnet.parm("render_engine").eval()) if subnet.parm("render_engine") else 0
    render_engine_options = ["RS Material", "Material X"]
    render_engine = render_engine_options[render_engine_idx] if render_engine_idx < len(render_engine_options) else "RS Material"

    # Get thumbnail parameters
    thumbnail_action_idx = int(subnet.parm("thumbnail_action").eval()) if subnet.parm("thumbnail_action") else 0
    thumbnail_actions = ["automatic", "choose", "disable"]
    thumbnail_action = thumbnail_actions[thumbnail_action_idx] if thumbnail_action_idx < len(thumbnail_actions) else "automatic"
    thumbnail_file_path = subnet.parm("thumbnail_file").unexpandedString().strip() if subnet.parm("thumbnail_file") else ""

    print(f"🎨 Thumbnail Action: {thumbnail_action}")
    if thumbnail_action == "choose" and thumbnail_file_path:
        print(f"📁 Thumbnail File: {thumbnail_file_path}")

    # For update_material action, get the parent material ID
    parent_material_id = None
    if action == "update_material":
        # TODO: Add UI parameter for parent_material_id in the Update Material section
        # For now, extract from current folder name if it exists
        print("⚠️  Update Material: Parent ID extraction not yet implemented")
        parent_material_id = None  # Will need to be set from a parameter

    # Quick validation
    if not material_name:
        subnet.parm("export_status").set("❌ Missing material name")
        hou.ui.displayMessage("❌ Material name is required!", severity=hou.severityType.Error)
        raise Exception("Material name required")

    # Process tags
    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []

    # Update status
    subnet.parm("export_status").set("🔄 Exporting...")

    print(f"📋 MATERIAL EXPORT CONFIGURATION:")
    print(f"   🎯 Action: {action}")
    print(f"   🎨 Material: {material_name}")
    print(f"   📂 Type: {asset_type}")
    print(f"   📋 Subcategory: {subcategory}")
    print(f"   🛠️  Render Engine: {render_engine}")
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
        "tags": extended_tags,
        "action": action
    }

    # Create TemplateMaterialExporter with new parameters
    exporter = atlas_material_ui.TemplateMaterialExporter(
        material_name=material_name,
        subcategory=subcategory,
        tags=extended_tags,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=hierarchy_metadata,
        action=action,
        parent_material_id=parent_material_id,
        thumbnail_action=thumbnail_action,
        thumbnail_file_path=thumbnail_file_path,
        bl_atlas_root=bl_atlas_root
    )

    print(f"✅ Created material exporter with ID: {exporter.material_id} (14 chars)")
    print(f"📁 Material will be exported (ID structure: 11 UID + 3 version)")

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

                    # Use the standalone API client with network mode
                    api_success = api_client.call_atlas_api_ingestion(metadata_file, use_network=True)

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