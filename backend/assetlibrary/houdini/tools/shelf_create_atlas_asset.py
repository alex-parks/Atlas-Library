#!/usr/bin/env python3
"""
Blacksmith Atlas - Create Atlas Asset (Shelf Module)
==================================================

This module contains the logic for the "Create Atlas Asset" shelf button.
The shelf button just imports and calls the main function from this module.
"""

import hou
import sys
from pathlib import Path

def create_atlas_asset():
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
    
    # Sanitize the asset name for use as node name (remove spaces, special chars)
    node_name = asset_name.replace(" ", "_").replace("-", "_")
    # Remove any characters that aren't alphanumeric or underscore
    import re
    node_name = re.sub(r'[^\w]', '_', node_name)
    
    print(f"📝 Original name: '{asset_name}'")
    print(f"📝 Node name: '{node_name}'")
    
    try:
        # Create an empty subnet first with sanitized node name
        subnet = parent.createNode("subnet", node_name)
        subnet.setComment("Blacksmith Atlas Asset - Ready for Export")
        subnet.setColor(hou.Color(0.2, 0.6, 1.0))  # Blue
        
        print(f"📦 Created subnet: {subnet.path()}")
        print(f"📦 Actual subnet name: {subnet.name()}")
        
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
        
        # Add Atlas parameters (use original asset_name for parameters)
        add_atlas_parameters(subnet, asset_name)
        
        print(f"📋 Set parameter default to: '{asset_name}'")
        
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
    
    # Create main Atlas folder
    main_folder = hou.FolderParmTemplate("atlas_folder", "🏭 Atlas Export")
    
    # ===== ACTION DROPDOWN =====
    action_parm = hou.MenuParmTemplate("action", "Action",
                                    ["create_new", "version_up", "variant"],
                                    ["Create New Asset", "Version Up Asset", "Variant Asset"])
    action_parm.setDefaultValue(0)
    action_parm.setHelp("Choose the type of asset creation: New Asset, Version of existing asset, or Variant")
    main_folder.addParmTemplate(action_parm)
    
    # ===== CREATE NEW ASSET FOLDER =====
    create_folder = hou.FolderParmTemplate("create_folder", "Create New Asset Parameters", folder_type=hou.folderType.Simple)
    create_folder.setConditional(hou.parmCondType.HideWhen, "{ action != 0 }")
    
    # Asset name
    asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
    asset_name_parm.setDefaultValue([asset_name])
    create_folder.addParmTemplate(asset_name_parm)
    
    # Asset Type
    asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                          ["assets", "fx", "materials", "hdas"],
                                          ["Assets", "FX", "Materials", "HDAs"])
    asset_type_parm.setDefaultValue(0)  # Default to Assets
    create_folder.addParmTemplate(asset_type_parm)
    asset_type_parm.setScriptCallback('''
node = hou.pwd()
asset_type = node.parm("asset_type").eval()

# Define subcategory options for each asset type
subcategory_options = {
    0: (["blacksmith_asset", "megascans", "kitbash"], ["Blacksmith Asset", "Megascans", "Kitbash"]),
    1: (["blacksmith_fx", "atmosphere", "flip", "pyro"], ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"]),
    2: (["blacksmith_materials", "redshift_mat", "karma_mat"], ["Blacksmith Materials", "Redshift", "Karma"]),
    3: (["blacksmith_hdas"], ["Blacksmith HDAs"])
}

# Get the parameter template group
ptg = node.parmTemplateGroup()

# Find the subcategory parameter
subcategory_parm = ptg.find("subcategory")
if subcategory_parm:
    # Get the new menu items for the selected asset type
    menu_items, menu_labels = subcategory_options.get(asset_type, (["blacksmith_asset"], ["Blacksmith Asset"]))
    
    # Update the subcategory parameter with new menu items
    subcategory_parm.setMenuItems(menu_items)
    subcategory_parm.setMenuLabels(menu_labels)
    subcategory_parm.setDefaultValue(0)
    
    # Replace the parameter template
    ptg.replace(subcategory_parm.name(), subcategory_parm)
    node.setParmTemplateGroup(ptg)
    
    # Reset the subcategory parameter to first option
    node.parm("subcategory").set(0)
''')
    asset_type_parm.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    
    # Dynamic Subcategory dropdown (starts with Assets options)
    subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                           ["blacksmith_asset", "megascans", "kitbash"],
                                           ["Blacksmith Asset", "Megascans", "Kitbash"])
    subcategory_parm.setDefaultValue(0)
    
    # Render Engine
    render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine", 
                                             ["redshift", "karma"],
                                             ["Redshift", "Karma"])
    render_engine_parm.setDefaultValue(0)  # Default to Redshift
    
    # Tags
    tags_parm = hou.StringParmTemplate("tags", "Search Tags", 1)
    tags_parm.setDefaultValue([""])
    
    # Export status
    status_parm = hou.StringParmTemplate("export_status", "Status", 1)
    status_parm.setDefaultValue(["Ready to export"])
    status_parm.setTags({"editor": "readonly"})
    
    # Add remaining parameters to create folder
    create_folder.addParmTemplate(subcategory_parm)
    create_folder.addParmTemplate(render_engine_parm)
    create_folder.addParmTemplate(tags_parm)
    
    main_folder.addParmTemplate(create_folder)
    
    # ===== VERSION UP FOLDER =====
    version_folder = hou.FolderParmTemplate("version_folder", "Version Up Parameters", folder_type=hou.folderType.Simple)
    version_folder.setConditional(hou.parmCondType.HideWhen, "{ action != 1 }")
    
    # Parent Asset ID for version up
    version_parent_id = hou.StringParmTemplate("version_parent_asset_id", "Parent Asset ID", 1)
    version_parent_id.setHelp("Enter the 13-character Asset ID (11 base + 2 variant) of the asset to version up (e.g., A5FF6F3B4R6AA)")
    version_folder.addParmTemplate(version_parent_id)
    
    # Asset Name for version
    version_asset_name = hou.StringParmTemplate("version_asset_name", "Asset Name", 1)
    version_asset_name.setDefaultValue([asset_name + "_v2"])
    version_folder.addParmTemplate(version_asset_name)
    
    # Version Tags
    version_tags = hou.StringParmTemplate("version_tags", "Tags", 1)
    version_tags.setHelp("Comma-separated tags for searching")
    version_folder.addParmTemplate(version_tags)
    
    main_folder.addParmTemplate(version_folder)
    
    # ===== VARIANT FOLDER =====
    variant_folder = hou.FolderParmTemplate("variant_folder", "Variant Parameters", folder_type=hou.folderType.Simple)
    variant_folder.setConditional(hou.parmCondType.HideWhen, "{ action != 2 }")
    
    # Parent Asset ID for variant (11 characters: base UID only)
    variant_parent_id = hou.StringParmTemplate("variant_parent_asset_id", "Parent Asset ID", 1)
    variant_parent_id.setHelp("Enter the 11-character base UID of the asset to create variant from (e.g., A5FF6F3B4R6)")
    variant_folder.addParmTemplate(variant_parent_id)
    
    # Variant Name (new parameter)
    variant_name_param = hou.StringParmTemplate("variant_name", "Variant Name", 1)
    variant_name_param.setDefaultValue(["default"])
    variant_name_param.setHelp("Name for this variant (will be stored in variant_name metadata field)")
    variant_folder.addParmTemplate(variant_name_param)
    
    # Asset Name for variant
    variant_asset_name = hou.StringParmTemplate("variant_asset_name", "Asset Name", 1)
    variant_asset_name.setDefaultValue([asset_name + "_variant"])
    variant_folder.addParmTemplate(variant_asset_name)
    
    # Variant Tags
    variant_tags = hou.StringParmTemplate("variant_tags", "Tags", 1)
    variant_tags.setHelp("Comma-separated tags for searching")
    variant_folder.addParmTemplate(variant_tags)
    
    main_folder.addParmTemplate(variant_folder)
    
    # Export status and button
    status_parm = hou.StringParmTemplate("export_status", "Status", 1)
    status_parm.setDefaultValue(["Ready to export"])
    status_parm.setTags({"editor": "readonly"})
    main_folder.addParmTemplate(status_parm)
    
    # Export button
    export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
    export_btn.setScriptCallback(get_export_script())
    export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    main_folder.addParmTemplate(export_btn)
    
    ptg.addParmTemplate(main_folder)
    subnet.setParmTemplateGroup(ptg)

def get_export_script():
    """Return the export script for the button"""
    return '''
print("🚀 Export button clicked!")
try:
    import sys
    from pathlib import Path
    
    print("📥 Setting up paths...")
    
    # Add backend path
    backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Also add the _3D directory path directly
    _3d_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D")
    if str(_3d_path) not in sys.path:
        sys.path.insert(0, str(_3d_path))
    
    print("📦 Loading modules...")
    
    # Force reload the module to pick up changes
    import importlib
    
    # Remove from cache if exists
    modules_to_remove = [
        'assetlibrary.houdini.houdiniae',
        'houdiniae'
    ]
    for mod in modules_to_remove:
        if mod in sys.modules:
            del sys.modules[mod]
    
    # Try direct import first
    try:
        import houdiniae
        importlib.reload(houdiniae)
        TemplateAssetExporter = houdiniae.TemplateAssetExporter
        print("✅ Loaded houdiniae module directly")
    except ImportError as e:
        print(f"⚠️ Direct import failed: {e}")
        # Fallback to full path import
        from assetlibrary._3D import houdiniae
        importlib.reload(houdiniae)
        TemplateAssetExporter = houdiniae.TemplateAssetExporter
        print("✅ Loaded houdiniae module via assetlibrary path")
    
    print("📋 Getting subnet parameters...")
    subnet = hou.pwd()
    
    # Get action parameter to determine which set of parameters to use
    action_value = subnet.parm("action").eval() if subnet.parm("action") else 0
    action_options = ["create_new", "version_up", "variant"]
    action = action_options[int(action_value)] if 0 <= int(action_value) < len(action_options) else "create_new"
    
    print(f"🎯 Action: {action}")
    
    # Get parameters based on action
    if action == "create_new":
        asset_name = subnet.parm("asset_name").eval().strip()
        asset_type_idx = int(subnet.parm("asset_type").eval())
        subcategory_idx = int(subnet.parm("subcategory").eval())
        tags_str = subnet.parm("tags").eval().strip()
        render_engine_idx = int(subnet.parm("render_engine").eval())
        parent_asset_id = None
        variant_name = "default"
    elif action == "version_up":
        parent_asset_id = subnet.parm("version_parent_asset_id").eval().strip() if subnet.parm("version_parent_asset_id") else ""
        asset_name = subnet.parm("version_asset_name").eval().strip() if subnet.parm("version_asset_name") else "Versioned Asset"
        tags_str = subnet.parm("version_tags").eval().strip() if subnet.parm("version_tags") else ""
        # For version up, use default values for missing parameters
        asset_type_idx = 0  # Default to Assets
        subcategory_idx = 0  # Default to first subcategory
        render_engine_idx = 0  # Default to Redshift
        variant_name = None  # Will be looked up from parent
    elif action == "variant":
        parent_asset_id = subnet.parm("variant_parent_asset_id").eval().strip() if subnet.parm("variant_parent_asset_id") else ""
        asset_name = subnet.parm("variant_asset_name").eval().strip() if subnet.parm("variant_asset_name") else "Variant Asset"
        tags_str = subnet.parm("variant_tags").eval().strip() if subnet.parm("variant_tags") else ""
        variant_name = subnet.parm("variant_name").eval().strip() if subnet.parm("variant_name") else "default"
        
        # Validation: Don't allow "default" as variant name
        if variant_name.lower() == "default":
            error_msg = '❌ Asset Variant Name has to be different than "default"'
            print(f"❌ {error_msg}")
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            subnet.parm("export_status").set("❌ Invalid variant name")
            raise Exception(error_msg)
        
        # Validation: Check if parent asset exists in database
        print("🔍 Validating parent asset exists in database...")
        original_asset_found = False
        try:
            # Query the Atlas API to find the original asset (AA variant)
            target_asset_id = f"{parent_asset_id}AA001"  # Original asset format
            print(f"   🔍 Looking for original asset: {target_asset_id}")
            
            api_url = "http://localhost:8000/api/v1/assets?limit=1000"
            response = urllib.request.urlopen(api_url, timeout=30)
            assets_data = json.loads(response.read().decode())
            all_assets = assets_data.get('items', [])
            
            # Find the original asset (AA variant)
            for asset in all_assets:
                if asset.get('id', '') == target_asset_id:
                    original_asset_found = True
                    print(f"   ✅ Found original asset for variant: {target_asset_id}")
                    break
            
            if not original_asset_found:
                error_msg = f"❌ No Asset Found: {parent_asset_id} not found in database"
                print(f"   ❌ {error_msg}")
                hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
                subnet.parm("export_status").set("❌ Asset not found")
                raise Exception("No Asset Found")
                
        except urllib.error.URLError as e:
            error_msg = f"❌ Cannot connect to database to validate asset: {e}"
            print(f"   ❌ {error_msg}")
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            subnet.parm("export_status").set("❌ Database connection failed")
            raise Exception("Database connection failed")
        except Exception as e:
            if "No Asset Found" in str(e):
                raise  # Re-raise the asset not found error
            error_msg = f"❌ Error validating parent asset: {e}"
            print(f"   ❌ {error_msg}")
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
            subnet.parm("export_status").set("❌ Validation failed")
            raise Exception("Asset validation failed")
        
        # For variant, inherit properties from parent asset
        asset_type_idx = 0  # Default to Assets
        subcategory_idx = 0  # Default to first subcategory
        render_engine_idx = 0  # Default to Redshift
        
        # Try to inherit from parent asset
        if parent_asset_id and len(parent_asset_id) == 11:
            try:
                import urllib.request
                import json
                
                # Query the Atlas API to find the original asset (AA variant)
                target_asset_id = f"{parent_asset_id}AA001"  # Original asset format
                print(f"   🔍 Looking for original asset for inheritance: {target_asset_id}")
                
                api_url = "http://localhost:8000/api/v1/assets?limit=1000"
                response = urllib.request.urlopen(api_url, timeout=30)
                assets_data = json.loads(response.read().decode())
                all_assets = assets_data.get('items', [])
                
                # Find the original asset (AA variant)
                for asset in all_assets:
                    if asset.get('id', '') == target_asset_id:
                        print(f"   ✅ Found original asset for inheritance: {target_asset_id}")
                        hierarchy = asset.get('metadata', {}).get('hierarchy', {})
                        inherited_asset_type = hierarchy.get('asset_type', 'Assets')
                        inherited_subcategory = hierarchy.get('subcategory', 'Blacksmith Asset')
                        inherited_render_engine = hierarchy.get('render_engine', 'Redshift')
                        
                        # Map back to indices
                        asset_types = ["Assets", "FX", "Materials", "HDAs"]
                        if inherited_asset_type in asset_types:
                            asset_type_idx = asset_types.index(inherited_asset_type)
                        
                        subcategory_options = {
                            0: ["Blacksmith Asset", "Megascans", "Kitbash"],
                            1: ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"],
                            2: ["Blacksmith Materials", "Redshift", "Karma"],
                            3: ["Blacksmith HDAs"]
                        }
                        available_subcategories = subcategory_options.get(asset_type_idx, ["Blacksmith Asset"])
                        if inherited_subcategory in available_subcategories:
                            subcategory_idx = available_subcategories.index(inherited_subcategory)
                        
                        render_engines = ["Redshift", "Karma"]
                        if inherited_render_engine in render_engines:
                            render_engine_idx = render_engines.index(inherited_render_engine)
                        
                        print(f"   ✅ Inherited Asset Type: {inherited_asset_type} (index: {asset_type_idx})")
                        print(f"   ✅ Inherited Subcategory: {inherited_subcategory} (index: {subcategory_idx})")
                        print(f"   ✅ Inherited Render Engine: {inherited_render_engine} (index: {render_engine_idx})")
                        break
                else:
                    print(f"   ⚠️ Original asset not found, using defaults")
                    
            except Exception as e:
                print(f"   ⚠️ Error getting parent asset data for inheritance, using defaults: {e}")
    else:
        # Fallback to create_new
        asset_name = subnet.parm("asset_name").eval().strip() if subnet.parm("asset_name") else "Asset"
        asset_type_idx = 0
        subcategory_idx = 0
        tags_str = ""
        render_engine_idx = 0
        parent_asset_id = None
        variant_name = "default"
    
    if not asset_name:
        print("❌ No asset name provided")
        hou.ui.displayMessage("Asset name required!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("No asset name")
        raise Exception("Asset name required")
        
    # Validate parent asset ID for version/variant actions
    if action == "version_up" and (not parent_asset_id or len(parent_asset_id) != 13):
        error_msg = "Version Up requires 13-character Parent Asset ID (11 base + 2 variant)"
        print(f"❌ {error_msg}")
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        subnet.parm("export_status").set("Invalid Parent ID")
        raise Exception(error_msg)
        
    if action == "variant" and (not parent_asset_id or len(parent_asset_id) != 11):
        error_msg = "Variant creation requires 11-character Parent Asset ID (base UID only)"
        print(f"❌ {error_msg}")
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        subnet.parm("export_status").set("Invalid Parent ID")
        raise Exception(error_msg)
    
    # Convert asset type
    asset_types = ["Assets", "FX", "Materials", "HDAs"]
    asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
    
    # Get subcategory based on asset type and current selection
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
    
    print(f"📋 Asset: {asset_name}")
    print(f"📂 Asset Type: {asset_type}")
    print(f"📋 Subcategory: {subcategory}")
    print(f"🎨 Render Engine: {render_engine}")
    print(f"🏷️ Tags: {tags_list}")
    print(f"🎯 Action: {action}")
    if parent_asset_id:
        print(f"🔗 Parent Asset ID: {parent_asset_id}")
    if variant_name and variant_name != "default":
        print(f"🎭 Variant Name: {variant_name}")
    
    subnet.parm("export_status").set("Exporting...")
    
    # Debug: Check for materials before export
    print("🔍 Checking nodes for materials...")
    nodes_to_export = subnet.children()
    material_count = 0
    
    for node in nodes_to_export:
        print(f"   Node: {node.name()} ({node.type().name()})")
        
        # Check shop_materialpath
        if node.parm("shop_materialpath"):
            mat_path = node.parm("shop_materialpath").eval()
            if mat_path:
                print(f"   Material: {mat_path}")
                material_count += 1
            else:
                print("   No material assigned")
        else:
            print("   No shop_materialpath parameter")
    
    print(f"Found {material_count} material assignments before export")
    
    # Store the export context in metadata
    export_context = subnet.parent().path()
    print(f"📍 Export context: {export_context}")
    
    print("🏭 Creating exporter...")
    
    # Create extended tags list for search
    extended_tags = tags_list.copy()
    extended_tags.extend([asset_type.lower(), subcategory.lower().replace(' ', '_'), render_engine.lower()])
    
    # Create comprehensive metadata for frontend filtering
    from datetime import datetime
    hierarchy_metadata = {
        "dimension": "3D",  # Always 3D from Houdini
        "asset_type": asset_type,  # Assets, FX, Materials, HDAs
        "subcategory": subcategory,  # Blacksmith Asset, Megascans, etc.
        "render_engine": render_engine,
        "export_context": export_context,
        "houdini_version": f"{hou.applicationVersion()[0]}.{hou.applicationVersion()[1]}.{hou.applicationVersion()[2]}",
        "export_time": str(datetime.now()),
        "tags": extended_tags
    }
    
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,  # Just the subcategory name (e.g. "Blacksmith Asset")
        description=f"Atlas {asset_type} asset: {asset_name}",  # Auto-generate description
        tags=extended_tags,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=hierarchy_metadata,  # Pass structured metadata instead of empty string
        action=action,  # Pass the action (create_new, version_up, variant)
        parent_asset_id=parent_asset_id,  # Pass parent asset ID for versioning/variants
        variant_name=variant_name  # Pass variant name
    )
    
    if not nodes_to_export:
        print("❌ No nodes to export")
        hou.ui.displayMessage("No nodes to export!", severity=hou.severityType.Error)
        subnet.parm("export_status").set("No nodes")
        raise Exception("No nodes to export")
    
    print(f"🚀 Starting export of {len(nodes_to_export)} nodes...")
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        print("✅ Export successful!")
        
        # Update metadata file to ensure hierarchy data is preserved
        metadata_file = exporter.asset_folder / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            # Ensure hierarchy metadata is present for frontend filtering
            metadata.update(hierarchy_metadata)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"📝 Updated metadata with hierarchy data for frontend filtering")
            print(f"   📊 Dimension: {hierarchy_metadata['dimension']}")
            print(f"   📂 Asset Type: {hierarchy_metadata['asset_type']}")
            print(f"   📋 Subcategory: {hierarchy_metadata['subcategory']}")
        
        subnet.parm("export_status").set("Exported!")
        
        # Show enhanced success message with template file info
        template_file = exporter.clipboard_folder / f"{asset_name}_template.hip"
        success_message = ("Atlas Asset exported successfully!\\n\\n" +
                          "Location: " + str(exporter.asset_folder) + "\\n\\n" +
                          "TEMPLATE FILE READY!\\n" +
                          "A template file has been created with pre-mapped paths:\\n" +
                          str(template_file) + "\\n\\n" +
                          "To use in any scene:\\n" +
                          "1. Navigate to desired context (e.g., inside geo node)\\n" +
                          "2. Python Console: parent_node.loadChildrenFromFile('" + str(template_file) + "')\\n" +
                          "   OR File > Merge and select the template file\\n\\n" +
                          "All paths are already mapped - it just works!")
        
        hou.ui.displayMessage(success_message, title="Export Complete - Template Ready!")
    else:
        print("❌ Export failed")
        subnet.parm("export_status").set("Export failed")
        hou.ui.displayMessage("Export failed!", severity=hou.severityType.Error)

except Exception as e:
    print(f"❌ Export error: {e}")
    import traceback
    traceback.print_exc()
    try:
        hou.pwd().parm("export_status").set("Error: " + str(e))
    except:
        pass
    hou.ui.displayMessage("Export error: " + str(e), severity=hou.severityType.Error)
'''

# Main function to call from shelf button
def main():
    """Main entry point for shelf button"""
    create_atlas_asset()

if __name__ == "__main__":
    main()
