# Blacksmith Atlas - Load Atlas Asset (Shelf Button)
# Copy this entire script and paste it into a Houdini shelf button

import hou
import sys
from pathlib import Path

def load_atlas_asset():
    """Main function to load an Atlas Asset from the library"""
    
    print("📦 BLACKSMITH ATLAS - LOAD ASSET")
    
    # Get asset name/ID from user
    result = hou.ui.readInput("Enter Atlas Asset Hash_Name (e.g., 148F41BF_MyAtlasAsset):", 
                            initial_contents="",
                            title="Load Atlas Asset")
    if result[0] != 0 or not result[1].strip():
        return
    
    asset_hash_name = result[1].strip()
    
    try:
        # Add backend path
        backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        # Also add the _3D directory path directly
        _3d_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D")
        if str(_3d_path) not in sys.path:
            sys.path.insert(0, str(_3d_path))
        
        # Force reload the module to pick up changes
        import importlib
        
        # Remove from cache if exists
        modules_to_remove = [
            'assetlibrary._3D.houdiniae',
            'houdiniae'
        ]
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Try direct import first
        try:
            import houdiniae
            importlib.reload(houdiniae)
            TemplateAssetImporter = houdiniae.TemplateAssetImporter
            print("🔄 Loaded houdiniae module directly")
        except ImportError:
            # Fallback to full path import
            from assetlibrary._3D import houdiniae
            importlib.reload(houdiniae)
            TemplateAssetImporter = houdiniae.TemplateAssetImporter
            print("🔄 Loaded houdiniae module via assetlibrary path")
        
        print("✅ Successfully imported TemplateAssetImporter")
        
        # Find the asset in the library
        library_root = Path("/net/library/atlaslib/3D/Assets")
        
        # Search in all subcategories for the asset
        asset_folder = None
        for subcategory_folder in library_root.iterdir():
            if subcategory_folder.is_dir():
                potential_asset = subcategory_folder / asset_hash_name
                if potential_asset.exists():
                    asset_folder = potential_asset
                    break
        
        if not asset_folder:
            hou.ui.displayMessage(f"❌ Asset '{asset_hash_name}' not found in library!\n\nSearched in: {library_root}", 
                                severity=hou.severityType.Error)
            return
        
        print(f"📂 Found asset: {asset_folder}")
        
        # Check if template file exists
        template_file = asset_folder / "Data" / "template.hipnc"
        if not template_file.exists():
            hou.ui.displayMessage(f"❌ Template file not found!\n\nExpected: {template_file}", 
                                severity=hou.severityType.Error)
            return
        
        # Get the original export context from metadata
        metadata_file = asset_folder / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Use the original export context if available
        original_context_path = metadata.get('export_context', '/obj')
        target_context = hou.node(original_context_path)
        
        if not target_context:
            # Fallback to /obj if original context doesn't exist
            target_context = hou.node('/obj')
            print(f"⚠️ Original context '{original_context_path}' not found, using /obj")
        
        print(f"📍 Loading into context: {target_context.path()} (original export location)")
        
        # Create importer and load the asset
        importer = TemplateAssetImporter(str(asset_folder))
        
        # Load metadata if available
        print(f"📋 Asset metadata: {metadata.get('name', 'Unknown')} - {metadata.get('description', 'No description')}")
        
        # Load the template as a collapsed subnet
        imported_subnet = importer.import_into_scene(target_context, as_collapsed_subnet=True)
        
        if imported_subnet:
            # Select the imported subnet
            imported_subnet.setSelected(True, clear_all_selected=True)
            
            # Show asset info
            texture_count = len(metadata.get('textures', {}).get('files', []))
            node_count = metadata.get('node_summary', {}).get('total_nodes', 'Unknown')
            
            hou.ui.displayMessage(f"✅ Atlas Asset loaded as collapsed subnet!\n\n"
                                f"Asset: {metadata.get('name', asset_hash_name)}\n"
                                f"Description: {metadata.get('description', 'No description')}\n"
                                f"Nodes: {node_count}\n"
                                f"Textures: {texture_count}\n"
                                f"Subnet: {imported_subnet.path()}\n"
                                f"Location: {asset_folder}\n\n"
                                f"Textures are located in: {asset_folder}/Textures/\n\n"
                                f"💡 Double-click the subnet to edit contents", 
                                title="Asset Loaded")
            
            print(f"✅ Successfully loaded Atlas Asset as subnet: {imported_subnet.path()}")
            
        else:
            hou.ui.displayMessage(f"❌ Failed to load asset: {asset_hash_name}", 
                                severity=hou.severityType.Error)
        
    except Exception as e:
        print(f"❌ Load error: {e}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(f"❌ Load error: {e}", severity=hou.severityType.Error)

# Run the main function
load_atlas_asset()
