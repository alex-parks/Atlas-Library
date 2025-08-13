"""
Atlas Copy Shelf Button

This shelf button browses existing Atlas library assets and retrieves
their pre-generated copy strings for sharing.

Usage: Click Atlas Copy, select asset from library, copy string is placed in clipboard
"""

import hou
import traceback
import os
import json

def atlas_copy_from_library():
    """Browse Atlas library and get copy string for existing asset"""
    try:
        library_path = "/net/library/atlaslib/3D/Assets"
        
        # Check if library exists
        if not os.path.exists(library_path):
            hou.ui.displayMessage(
                f"Atlas library not found at:\n{library_path}\n\nCreate assets first or check library path.",
                severity=hou.severityType.Error,
                title="Atlas Copy - Library Not Found"
            )
            return
        
        print(f"📂 Scanning Atlas library: {library_path}")
        
        # Scan for assets with clipboard systems
        assets_with_clipboard = []
        
        for subcategory in sorted(os.listdir(library_path)):
            subcategory_path = os.path.join(library_path, subcategory)
            if not os.path.isdir(subcategory_path):
                continue
                
            for asset_folder in sorted(os.listdir(subcategory_path)):
                asset_path = os.path.join(subcategory_path, asset_folder)
                if not os.path.isdir(asset_path):
                    continue
                
                # Check for Atlas clipboard system files
                templates_path = os.path.join(asset_path, "templates")
                copy_string_file = os.path.join(templates_path, "ATLAS_COPY_STRING.txt")
                
                if os.path.exists(copy_string_file):
                    # Read the copy string
                    try:
                        with open(copy_string_file, 'r') as f:
                            content = f.read()
                            lines = content.split('\n')
                            copy_string = None
                            for line in lines:
                                line = line.strip()
                                if line.startswith('AtlasAsset_'):
                                    copy_string = line
                                    break
                        
                        if copy_string:
                            # Get metadata if available
                            metadata_file = os.path.join(templates_path, f"{asset_folder.split('_', 1)[1]}_clipboard.json")
                            metadata = {}
                            if os.path.exists(metadata_file):
                                try:
                                    with open(metadata_file, 'r') as f:
                                        metadata = json.load(f)
                                except:
                                    pass
                            
                            assets_with_clipboard.append({
                                'display': f"{subcategory}/{asset_folder}",
                                'asset_path': asset_path,
                                'copy_string': copy_string,
                                'subcategory': subcategory,
                                'folder_name': asset_folder,
                                'metadata': metadata,
                                'templates_path': templates_path
                            })
                    except Exception as e:
                        print(f"   ⚠️ Error reading copy string from {copy_string_file}: {e}")
        
        if not assets_with_clipboard:
            hou.ui.displayMessage(
                f"No Atlas assets with clipboard system found!\n\n"
                f"Library path: {library_path}\n\n"
                f"To enable Atlas Copy/Paste:\n"
                f"1. Create/export assets using Atlas Create button\n"
                f"2. Assets will automatically include copy strings\n"
                f"3. Use Atlas Copy to browse and share them",
                severity=hou.severityType.Warning,
                title="Atlas Copy - No Assets Found"
            )
            return
        
        print(f"✅ Found {len(assets_with_clipboard)} assets with Atlas clipboard system")
        
        # Create selection list
        asset_choices = []
        for asset in assets_with_clipboard:
            # Show asset name and info
            metadata = asset['metadata']
            node_count = metadata.get('node_count', '?')
            encrypted = metadata.get('encrypted', False)
            created = metadata.get('created_date', 'Unknown')[:10] if metadata.get('created_date') else 'Unknown'
            
            choice_text = f"{asset['display']} | Nodes: {node_count} | Encrypted: {'Yes' if encrypted else 'No'} | Created: {created}"
            asset_choices.append(choice_text)
        
        # Show selection dialog
        selected_indices = hou.ui.selectFromList(
            asset_choices,
            message=f"Select Atlas Asset to Copy:\n\nFound {len(assets_with_clipboard)} assets with copy strings",
            title="📋 Atlas Copy - Select Asset",
            column_header="Available Assets (Name | Nodes | Encrypted | Created)",
            num_visible_rows=15
        )
        
        if not selected_indices or len(selected_indices) == 0:
            return  # User cancelled
        
        selected_asset = assets_with_clipboard[selected_indices[0]]
        copy_string = selected_asset['copy_string']
        metadata = selected_asset['metadata']
        
        # Copy to clipboard
        hou.ui.copyTextToClipboard(copy_string)
        
        # Show success message
        asset_name = metadata.get('asset_name', selected_asset['folder_name'])
        uid = metadata.get('uid', 'Unknown')
        encrypted = metadata.get('encrypted', False)
        node_count = metadata.get('node_count', '?')
        
        success_message = f"Atlas Copy successful!\n\n"
        success_message += f"Asset: {asset_name}\n"
        success_message += f"UID: {uid}\n"
        success_message += f"Category: {selected_asset['subcategory']}\n"
        success_message += f"Nodes: {node_count}\n"
        success_message += f"Encrypted: {'Yes' if encrypted else 'No'}\n\n"
        success_message += f"Copy string has been placed in your clipboard:\n"
        success_message += f"{copy_string}\n\n"
        success_message += f"Share this string or use Atlas Paste to import anywhere!"
        
        hou.ui.displayMessage(
            success_message,
            severity=hou.severityType.Message,
            title="Atlas Copy - Success"
        )
        
        # Set status message
        hou.ui.setStatusMessage(f"Atlas Copy: {asset_name} copy string copied to clipboard!")
        
        print(f"📋 Atlas Copy successful: {copy_string}")
        print(f"   Asset: {asset_name}")
        print(f"   Path: {selected_asset['asset_path']}")
        
    except Exception as e:
        error_msg = f"Atlas Copy failed: {str(e)}\n\n"
        error_msg += "Error details:\n"
        error_msg += traceback.format_exc()
        
        hou.ui.displayMessage(
            error_msg,
            severity=hou.severityType.Error,
            title="Atlas Copy - Error"
        )
        
        print(f"❌ Atlas Copy error: {e}")
        print(traceback.format_exc())


def atlas_copy_nodes():
    """Main function for Atlas Copy shelf button"""
    atlas_copy_from_library()


# Module reload support for development
def reload_modules():
    """Reload Atlas clipboard modules for development"""
    import importlib
    import sys
    
    modules_to_reload = [
        'atlas_clipboard_system',
        'houdiniae'
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
            print(f"Reloaded: {module_name}")


if __name__ == "__main__":
    # For development - reload modules and run
    reload_modules()
    atlas_copy_nodes()
