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
    metadata = subnet.parm("metadata").eval().strip()
    tags_str = subnet.parm("tags").eval().strip()
    render_engine_idx = int(subnet.parm("render_engine").eval())
    
    # Quick validation check
    if not asset_name:
        subnet.parm("export_status").set("❌ Missing asset name")
        hou.ui.displayMessage("❌ Asset name is required!", severity=hou.severityType.Error)
    else:
        # Convert asset type and get subcategory
        asset_types = ["Assets", "FX", "Materials", "HDAs"]
        asset_type = asset_types[asset_type_idx] if asset_type_idx < len(asset_types) else "Assets"
        
        # Get the subcategory - simplified single parameter approach
        subcategory_idx = int(subnet.parm("subcategory").eval())
        
        # Define subcategory options for each asset type
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
            "tags": extended_tags,
            "user_metadata": metadata  # Original user metadata
        }

        # Create your TemplateAssetExporter
        exporter = TemplateAssetExporter(
            asset_name=asset_name,
            subcategory=subcategory,  # Just the subcategory name (e.g. "Blacksmith Asset")
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
        else:
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
