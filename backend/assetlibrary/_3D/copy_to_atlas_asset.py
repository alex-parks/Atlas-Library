#!/usr/bin/env python3
"""
Blacksmith Atlas - Copy to Atlas Asset (No Collapse)
====================================================

Copy selected nodes into a new Atlas Asset subnet while preserving the originals.
This script creates a subnet with comprehensive export parameters.
"""

import hou

def copy_selected_to_atlas_asset():
    """Copy selected nodes into Atlas Asset subnet (preserve originals)"""
    
    print("🏭 BLACKSMITH ATLAS - COPY TO ASSET")
    print("=" * 60)
    
    try:
        # Get selected nodes
        selected_nodes = hou.selectedNodes()
        if not selected_nodes:
            hou.ui.displayMessage("❌ Please select nodes to copy into Atlas Asset.", 
                                severity=hou.severityType.Warning, 
                                title="Atlas Asset")
            return False
        
        print(f"📦 Processing {len(selected_nodes)} selected nodes:")
        for i, node in enumerate(selected_nodes, 1):
            print(f"   {i}. {node.path()} ({node.type().name()})")
        
        # Verify all nodes have same parent
        parent = selected_nodes[0].parent()
        invalid_nodes = [node.path() for node in selected_nodes[1:] if node.parent() != parent]
        
        if invalid_nodes:
            error_msg = f"❌ All selected nodes must be in the same network.\n\n"
            error_msg += f"Parent: {parent.path()}\nInvalid nodes:\n"
            for node_path in invalid_nodes:
                error_msg += f"• {node_path}\n"
            
            hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Atlas Asset Error")
            return False
        
        print(f"✅ All nodes in context: {parent.path()}")
        
        # Get asset name
        if len(selected_nodes) == 1:
            default_name = f"{selected_nodes[0].name()}_Atlas"
        else:
            default_name = f"{len(selected_nodes)}Nodes_Atlas"
        
        try:
            result = hou.ui.readInput("Enter Atlas Asset Name:", initial_contents=default_name)
            if result[0] != 0:
                print("❌ User cancelled")
                return False
            asset_name = result[1].strip()
            if not asset_name:
                asset_name = default_name
        except:
            asset_name = default_name
        
        print(f"🏷️ Asset name: '{asset_name}'")
        
        # Create subnet and copy nodes
        print("📦 Creating Atlas Asset subnet...")
        subnet = parent.createNode("subnet", asset_name)
        subnet.setComment("🏭 Blacksmith Atlas Asset\\n(Copied Nodes - Originals Preserved)")
        subnet.setColor(hou.Color(0.2, 0.6, 1.0))  # Atlas blue
        
        print(f"✅ Created subnet: {subnet.path()}")
        
        # Copy nodes into subnet
        print(f"📋 Copying {len(selected_nodes)} nodes...")
        copied_nodes = []
        
        for node in selected_nodes:
            try:
                copied_node = subnet.copyItems([node])[0]
                copied_nodes.append(copied_node)
                print(f"   ✅ Copied: {node.name()} -> {copied_node.name()}")
            except Exception as e:
                print(f"   ⚠️ Failed to copy {node.name()}: {e}")
        
        # Reconnect copied nodes
        print("🔗 Reconnecting copied nodes...")
        connection_count = 0
        for i, original_node in enumerate(selected_nodes):
            if i < len(copied_nodes):
                copied_node = copied_nodes[i]
                
                try:
                    # Get input connections
                    for input_idx in range(len(original_node.inputs())):
                        input_connections = original_node.inputConnections()
                        if input_connections and input_idx < len(input_connections):
                            input_connection = input_connections[input_idx]
                            input_node = input_connection.inputNode()
                            
                            # If input node is also in our selection, connect to its copy
                            if input_node in selected_nodes:
                                input_node_idx = selected_nodes.index(input_node)
                                if input_node_idx < len(copied_nodes):
                                    copied_input = copied_nodes[input_node_idx]
                                    copied_node.setInput(input_idx, copied_input)
                                    connection_count += 1
                                    print(f"   🔗 {copied_input.name()} -> {copied_node.name()}")
                except Exception as e:
                    print(f"   ⚠️ Connection error: {e}")
        
        print(f"✅ Made {connection_count} connections between copied nodes")
        
        # Layout subnet contents
        try:
            subnet.layoutChildren()
            print("📐 Laid out subnet contents")
        except:
            pass
        
        # Add Atlas export parameters
        print("⚙️ Adding Atlas export parameters...")
        try:
            param_success = add_atlas_export_parameters(subnet, asset_name)
            
            if param_success:
                print("✅ Export parameters added successfully!")
                
                # Verify parameters were actually added
                if subnet.parm("asset_name"):
                    print("✅ Verified: asset_name parameter exists")
                else:
                    print("❌ asset_name parameter missing after addition!")
                    
                if subnet.parm("export_atlas_asset"):  
                    print("✅ Verified: export button exists")
                else:
                    print("❌ Export button missing after addition!")
                    
            else:
                print("❌ add_atlas_export_parameters() returned False")
                
        except Exception as param_error:
            print(f"❌ Exception adding parameters: {param_error}")
            import traceback
            traceback.print_exc()
            param_success = False
        
        # Position subnet near original nodes
        if selected_nodes:
            first_pos = selected_nodes[0].position()
            subnet.setPosition([first_pos[0] + 4, first_pos[1]])
        
        # Select the new subnet
        subnet.setSelected(True, clear_all_selected=True)
        
        # Success message
        success_msg = f"""✅ Atlas Asset Created Successfully!

🏷️ Asset: {asset_name}
📦 Subnet: {subnet.path()}
📋 Copied: {len(copied_nodes)} nodes
🔧 Export Parameters: {'✅ Added' if param_success else '❌ Failed'}

ORIGINAL NODES PRESERVED ✅

NEXT STEPS:
1. Configure asset parameters in the subnet
2. Click '🚀 Export Atlas Asset' button
3. Asset will be saved to Atlas library

The subnet contains copies - originals are untouched!"""
        
        hou.ui.displayMessage(success_msg, title="🎉 Atlas Asset Ready")
        
        print("🎉 Atlas Asset creation complete!")
        print(f"📍 Subnet: {subnet.path()}")
        print(f"📋 Original nodes preserved")
        print(f"🚀 Ready for export!")
        
        return True
        
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error, title="Atlas Asset Error")
        return False

def add_atlas_export_parameters(subnet, asset_name):
    """Add comprehensive Atlas export parameters to subnet"""
    try:
        print(f"   📋 Adding export parameters to {subnet.name()}...")
        
        ptg = subnet.parmTemplateGroup()
        
        # Create individual parameters first
        parameters = []
        
        # Asset name
        asset_name_parm = hou.StringParmTemplate("asset_name", "Asset Name", 1)
        asset_name_parm.setDefaultValue([asset_name])
        parameters.append(asset_name_parm)
        
        # Asset Type
        asset_type_parm = hou.MenuParmTemplate("asset_type", "Asset Type", 
                                              ["assets", "fx", "materials", "hdas"],
                                              ["Assets", "FX", "Materials", "HDAs"])
        asset_type_parm.setDefaultValue(0)  # Default to Assets
        parameters.append(asset_type_parm)
        
        # Subcategory (dynamic based on Asset Type)
        subcategory_parm = hou.MenuParmTemplate("subcategory", "Subcategory", 
                                               ["blacksmith_asset", "megascans", "kitbash"],  # Default for Assets
                                               ["Blacksmith Asset", "Megascans", "Kitbash"])
        subcategory_parm.setDefaultValue(0)  # Default to first option
        subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 0 }")  # Show for Assets
        parameters.append(subcategory_parm)
        
        # FX Subcategory
        fx_subcategory_parm = hou.MenuParmTemplate("fx_subcategory", "Subcategory", 
                                                  ["blacksmith_fx", "atmosphere", "flip", "pyro"],
                                                  ["Blacksmith FX", "Atmosphere", "FLIP", "Pyro"])
        fx_subcategory_parm.setDefaultValue(0)
        fx_subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 1 }")  # Show for FX
        parameters.append(fx_subcategory_parm)
        
        # Materials Subcategory
        materials_subcategory_parm = hou.MenuParmTemplate("materials_subcategory", "Subcategory", 
                                                         ["blacksmith_materials", "redshift", "karma"],
                                                         ["Blacksmith Materials", "Redshift", "Karma"])
        materials_subcategory_parm.setDefaultValue(0)
        materials_subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 2 }")  # Show for Materials
        parameters.append(materials_subcategory_parm)
        
        # HDAs Subcategory
        hdas_subcategory_parm = hou.MenuParmTemplate("hdas_subcategory", "Subcategory", 
                                                    ["blacksmith_hdas"],
                                                    ["Blacksmith HDAs"])
        hdas_subcategory_parm.setDefaultValue(0)
        hdas_subcategory_parm.setConditional(hou.parmCondType.DisableWhen, "{ asset_type != 3 }")  # Show for HDAs
        parameters.append(hdas_subcategory_parm)
        
        # Render Engine
        render_engine_parm = hou.MenuParmTemplate("render_engine", "Render Engine", 
                                                 ["redshift", "karma"],
                                                 ["Redshift", "Karma"])
        render_engine_parm.setDefaultValue(0)  # Default to Redshift
        parameters.append(render_engine_parm)
        
        # Description
        description_parm = hou.StringParmTemplate("description", "Description", 1)
        description_parm.setDefaultValue([f"Atlas asset: {asset_name}"])
        parameters.append(description_parm)
        
        # Metadata Text Area
        metadata_parm = hou.StringParmTemplate("metadata", "Metadata (for search)", 5)  # 5 lines
        metadata_parm.setStringType(hou.stringParmType.Regular)
        metadata_parm.setDefaultValue(["Enter searchable metadata keywords, descriptions, or notes here..."])
        parameters.append(metadata_parm)
        
        # Tags
        tags_parm = hou.StringParmTemplate("tags", "Search Tags", 1)
        tags_parm.setDefaultValue(["helicopter, vehicle"])
        parameters.append(tags_parm)
        
        # Export status
        status_parm = hou.StringParmTemplate("export_status", "Export Status", 1)
        status_parm.setDefaultValue(["Ready to export"])
        status_parm.setReadOnly(True)
        parameters.append(status_parm)
        
        # Export button - THE MAIN EXPORT FUNCTIONALITY
        export_btn = hou.ButtonParmTemplate("export_atlas_asset", "🚀 Export Atlas Asset")
        export_btn.setScriptCallback(create_comprehensive_export_script())
        export_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        parameters.append(export_btn)
        
        # Info button
        info_btn = hou.ButtonParmTemplate("atlas_info", "ℹ️ About Atlas")
        info_btn.setScriptCallback('''
info_text = """🏭 BLACKSMITH ATLAS EXPORT

WORKFLOW:
1. Configure asset name, category, description
2. Add search tags (comma-separated)
3. Click '🚀 Export Atlas Asset' button
4. Asset saved with textures and metadata

FEATURES:
• Template-based perfect reconstruction  
• Automatic texture extraction from materials
• Multiple export formats (HIP, ABC, FBX)
• Organized library structure

LOCATION: /net/library/atlaslib/3D/Assets/{category}/

Click the Export button to save this asset!"""

hou.ui.displayMessage(info_text, title="Atlas Export Info")
''')
        info_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
        parameters.append(info_btn)
        
        # Create folder with the parameter list - correct syntax
        atlas_folder = hou.FolderParmTemplate("atlas_export", "🏭 Atlas Export", parameters, hou.folderType.Collapsible)
        atlas_folder.setDefaultValue(1)  # Open by default
        
        # Add folder to parameter group
        ptg.addParmTemplate(atlas_folder)
        subnet.setParmTemplateGroup(ptg)
        
        print(f"   ✅ Added Atlas export parameters successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Parameter addition failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_comprehensive_export_script():
    """Create the export callback script that calls your houdiniae.py logic"""
    return '''
# 🏭 BLACKSMITH ATLAS EXPORT SCRIPT
import sys
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
    
    from assetlibrary._3D.houdiniae import TemplateAssetExporter
    
    subnet = hou.pwd()
    print(f"📦 Exporting from subnet: {subnet.path()}")
    
    # Get parameters from subnet
    asset_name = subnet.parm("asset_name").eval().strip()
    asset_type_idx = int(subnet.parm("asset_type").eval())
    description = subnet.parm("description").eval().strip()
    metadata = subnet.parm("metadata").eval().strip()
    tags_str = subnet.parm("tags").eval().strip()
    render_engine_idx = int(subnet.parm("render_engine").eval())
    
    # Validation
    if not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("❌ Asset name is required!", severity=hou.severityType.Error)
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
    
    # Process tags
    tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    # Update status
    subnet.parm("export_status").set("🔄 Exporting...")
    
    print(f"📋 EXPORT CONFIGURATION:")
    print(f"   🏷️ Asset: {asset_name}")
    print(f"   📂 Asset Type: {asset_type}")
    print(f"   📋 Subcategory: {subcategory}")
    print(f"   🎨 Render Engine: {render_engine}")
    print(f"   📝 Description: {description}")
    print(f"   📄 Metadata: {metadata[:100]}..." if len(metadata) > 100 else f"📄 Metadata: {metadata}")
    print(f"   🏷️ Tags: {tags_list}")
    
    # Create extended tags list including metadata for search
    extended_tags = tags_list.copy()
    extended_tags.extend([asset_type.lower(), subcategory.lower().replace(' ', '_'), render_engine.lower()])
    if metadata and metadata != "Enter searchable metadata keywords, descriptions, or notes here...":
        # Add metadata words as tags
        metadata_words = [word.strip().lower() for word in metadata.split() if len(word.strip()) > 2]
        extended_tags.extend(metadata_words)
    
    # Create comprehensive metadata for frontend filtering  
    from datetime import datetime
    hierarchy_metadata = {
        "dimension": "3D",  # Always 3D from Houdini
        "asset_type": asset_type,  # Assets, FX, Materials, HDAs
        "subcategory": subcategory,  # Blacksmith Asset, Megascans, etc.
        "render_engine": render_engine,
        "houdini_version": f"{hou.applicationVersion()[0]}.{hou.applicationVersion()[1]}.{hou.applicationVersion()[2]}",
        "export_time": str(datetime.now()),
        "description": description,
        "tags": extended_tags,
        "user_metadata": metadata  # Original user metadata
    }

    # Create your TemplateAssetExporter
    exporter = TemplateAssetExporter(
        asset_name=asset_name,
        subcategory=subcategory,  # Just the subcategory name (e.g. "Blacksmith Asset")
        description=description,
        tags=extended_tags,
        asset_type=asset_type,
        render_engine=render_engine,
        metadata=hierarchy_metadata  # Pass structured metadata
    )
    
    print(f"✅ Created exporter with ID: {exporter.asset_id}")
    print(f"📁 Export location: {exporter.asset_folder}")
    
    # Get nodes to export (children of subnet)
    nodes_to_export = subnet.children()
    if not nodes_to_export:
        subnet.parm("export_status").set("❌ No nodes to export")
        hou.ui.displayMessage("❌ No nodes found in subnet to export!", 
                            severity=hou.severityType.Error)
        raise Exception("No nodes to export")
    
    print(f"📦 Found {len(nodes_to_export)} nodes to export:")
    for i, node in enumerate(nodes_to_export, 1):
        print(f"   {i}. {node.name()} ({node.type().name()})")
    
    # CALL YOUR EXISTING EXPORT LOGIC
    print("🚀 Starting template export with texture scanning...")
    success = exporter.export_as_template(subnet, nodes_to_export)
    
    if success:
        subnet.parm("export_status").set("✅ Export completed!")
        
        success_msg = f"""✅ ATLAS ASSET EXPORT SUCCESSFUL!

🏷️ Asset: {asset_name}  
🆔 Asset ID: {exporter.asset_id}
📂 Category: Assets/{subcategory}/
📍 Location: {exporter.asset_folder}

📦 EXPORTED FILES:
• Template: Perfect reconstruction with saveChildrenToFile()
• Textures: Comprehensive material scanning & copying
• Metadata: Searchable asset information
• ABC/FBX: Cross-DCC compatibility

🎯 The asset is now in the Atlas library!"""
        
        hou.ui.displayMessage(success_msg, title="🎉 Atlas Export Complete")
        print("🎉 EXPORT SUCCESS!")
        print(f"📍 Location: {exporter.asset_folder}")
        
    else:
        subnet.parm("export_status").set("❌ Export failed")
        hou.ui.displayMessage("❌ Export failed! Check console for details.", 
                            severity=hou.severityType.Error)
        print("❌ EXPORT FAILED - See console")

except Exception as e:
    error_msg = f"Export error: {str(e)}"
    print(f"❌ {error_msg}")
    
    try:
        hou.pwd().parm("export_status").set("❌ Export error")
    except:
        pass
    
    hou.ui.displayMessage(f"❌ {error_msg}\\n\\nCheck console for details.", 
                        severity=hou.severityType.Error)
    import traceback
    traceback.print_exc()
'''

# Main function
if __name__ == "__main__":
    copy_selected_to_atlas_asset()

print("📦 Atlas copy-to-asset script loaded")
print("💡 Run: copy_selected_to_atlas_asset()")