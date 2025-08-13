#!/usr/bin/env python3
"""
Blacksmith Atlas - Load Atlas Asset (Shelf Module)
=================================================

This module contains the logic for the "Load Atlas Asset" shelf button.
The shelf button just imports and calls the main function from this module.
"""

import hou
import sys
import os
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
        
        # Debug: Check template file size and readability
        template_file_path = asset_folder / "Data" / "template.hipnc"
        print(f"🔍 Template file debug:")
        print(f"   📄 File: {template_file_path}")
        print(f"   📊 Size: {template_file_path.stat().st_size} bytes")
        print(f"   🔐 Readable: {template_file_path.is_file() and os.access(template_file_path, os.R_OK)}")
        
        # CHECK IF CLIPBOARD VERSION EXISTS
        clipboard_folder = asset_folder / "Clipboard"
        clipboard_file = clipboard_folder / "atlas_asset.cpio"
        
        if clipboard_file.exists():
            print(f"� Found existing clipboard file: {clipboard_file}")
            print(f"📏 Clipboard file size: {clipboard_file.stat().st_size / 1024:.1f} KB")
            
            # Copy the clipboard file to a temp location that Houdini can access
            import tempfile
            import shutil
            
            with tempfile.NamedTemporaryFile(suffix='.cpio', delete=False) as temp_file:
                temp_clipboard_path = temp_file.name
                
            # Copy the clipboard file to temp location
            shutil.copy2(str(clipboard_file), temp_clipboard_path)
            
            # Load from clipboard file using Houdini's clipboard system
            try:
                print(f"📋 Loading clipboard file into Houdini...")
                
                # Use Houdini's loadItemsFromFile to load the clipboard data
                items = hou.loadItemsFromFile(temp_clipboard_path)
                
                if items:
                    print(f"✅ Successfully loaded {len(items)} items from clipboard")
                    
                    # Place items in the target context
                    placed_items = target_context.pasteItems(items)
                    
                    if placed_items:
                        # Select the first placed item
                        if placed_items[0]:
                            placed_items[0].setSelected(True, clear_all_selected=True)
                        
                        texture_count = len(metadata.get('textures', {}).get('files', []))
                        node_count = metadata.get('node_summary', {}).get('total_nodes', 'Unknown')
                        
                        hou.ui.displayMessage(f"✅ Atlas Asset pasted from clipboard!\n\n"
                                            f"Asset: {metadata.get('name', asset_hash_name)}\n"
                                            f"Description: {metadata.get('description', 'No description')}\n"
                                            f"Nodes: {node_count}\n"
                                            f"Textures: {texture_count}\n"
                                            f"Location: {asset_folder}\n\n"
                                            f"🎯 All file paths are pre-mapped to library locations!\n"
                                            f"📋 Clipboard system test successful!", 
                                            title="Clipboard Asset Loaded")
                        
                        print(f"✅ Successfully pasted Atlas Asset from clipboard")
                    else:
                        print(f"❌ Failed to paste items")
                        hou.ui.displayMessage("❌ Failed to paste clipboard items", 
                                            severity=hou.severityType.Error)
                else:
                    print(f"❌ No items loaded from clipboard file")
                    hou.ui.displayMessage("❌ No items found in clipboard file", 
                                        severity=hou.severityType.Error)
                
            except Exception as clipboard_error:
                print(f"❌ Clipboard loading error: {clipboard_error}")
                import traceback
                traceback.print_exc()
                hou.ui.displayMessage(f"❌ Clipboard loading error: {clipboard_error}", 
                                    severity=hou.severityType.Error)
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_clipboard_path)
                except:
                    pass
            
        else:
            print(f"⚠️ No clipboard version found at: {clipboard_file}")
            print(f"📋 Will need to create clipboard version for this asset")
            
            hou.ui.displayMessage(f"⚠️ No clipboard version found!\n\n"
                                f"This asset doesn't have a clipboard version yet.\n"
                                f"Expected: {clipboard_file}\n\n"
                                f"💡 You need to re-export this asset to create a clipboard version.", 
                                title="No Clipboard Version")
            return
        
    except Exception as e:
        print(f"❌ Load error: {e}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(f"❌ Load error: {e}", severity=hou.severityType.Error)

# Main function to call from shelf button
def main():
    """Main entry point for shelf button"""
    load_atlas_asset()

if __name__ == "__main__":
    main()
