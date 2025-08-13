"""
Atlas Paste Shelf Button

This shelf button reads an Atlas copy string from the clipboard and imports
the asset with automatic texture/geometry path remapping.

Usage: Copy Atlas copy string to clipboard, click Atlas Paste, nodes are imported
"""

import hou
import traceback

def atlas_paste_nodes():
    """Main function for Atlas Paste shelf button"""
    try:
        # Get clipboard content
        try:
            clipboard_text = hou.ui.getTextFromClipboard()
        except:
            # Fallback for older Houdini versions
            from PySide2.QtWidgets import QApplication
            qapp = QApplication.instance()
            clipboard_text = qapp.clipboard().text()
        
        if not clipboard_text:
            hou.ui.displayMessage(
                "Clipboard is empty!\n\nPlease copy an Atlas copy string to your clipboard first.",
                severity=hou.severityType.Error,
                title="Atlas Paste"
            )
            return
        
        clipboard_text = clipboard_text.strip()
        
        # Validate Atlas copy string format
        if not clipboard_text.startswith('AtlasAsset_'):
            hou.ui.displayMessage(
                "Clipboard does not contain a valid Atlas copy string!\n\n"
                f"Expected format: AtlasAsset_AssetName_UID[!encryption_key]\n"
                f"Found: {clipboard_text[:50]}{'...' if len(clipboard_text) > 50 else ''}",
                severity=hou.severityType.Error,
                title="Atlas Paste"
            )
            return
        
        # Parse copy string to show preview
        try:
            from atlas_clipboard_system import AtlasClipboardPaste
        except ImportError:
            # Fallback import
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            from atlas_clipboard_system import AtlasClipboardPaste
        
        paster = AtlasClipboardPaste()
        
        try:
            asset_name, uid, identifier, encryption_key = paster.parse_copy_string(clipboard_text)
        except Exception as e:
            hou.ui.displayMessage(
                f"Invalid Atlas copy string format!\n\n"
                f"Error: {str(e)}\n\n"
                f"Copy string: {clipboard_text}",
                severity=hou.severityType.Error,
                title="Atlas Paste"
            )
            return
        
        # Show asset info and confirm
        info_message = f"Atlas Paste Preview:\n\n"
        info_message += f"Asset Name: {asset_name}\n"
        info_message += f"Asset UID: {uid}\n"
        info_message += f"Encrypted: {'Yes' if encryption_key else 'No'}\n\n"
        info_message += f"This will import the asset into the current network location.\n"
        info_message += f"Continue with Atlas Paste?"
        
        confirm = hou.ui.displayMessage(
            info_message,
            buttons=("Paste Asset", "Cancel"),
            default_choice=0,
            close_choice=1,
            title="Atlas Paste - Confirm"
        )
        
        if confirm != 0:
            return  # User cancelled
        
        # Check if we can find the asset
        try:
            asset_path, subcategory = paster.find_asset_in_library(asset_name, uid)
        except Exception as e:
            hou.ui.displayMessage(
                f"Asset not found in Atlas library!\n\n"
                f"Asset: {asset_name} ({uid})\n"
                f"Error: {str(e)}\n\n"
                f"Make sure the asset exists in your Atlas library.",
                severity=hou.severityType.Error,
                title="Atlas Paste - Asset Not Found"
            )
            return
        
        # Show progress and perform paste
        with hou.InterruptableOperation("Atlas Paste", open_interrupt_dialog=True) as operation:
            operation.updateProgress(0.1, "Loading asset from library...")
            
            try:
                # Perform Atlas Paste
                new_nodes = paster.atlas_paste(clipboard_text)
                
                operation.updateProgress(0.9, "Finalizing import...")
                
            except Exception as e:
                # Handle specific encryption errors
                if "encryption" in str(e).lower() or "decrypt" in str(e).lower():
                    hou.ui.displayMessage(
                        f"Encryption error!\n\n"
                        f"This asset is encrypted and requires the correct encryption key.\n"
                        f"Make sure you copied the complete Atlas copy string including the key.\n\n"
                        f"Error: {str(e)}",
                        severity=hou.severityType.Error,
                        title="Atlas Paste - Encryption Error"
                    )
                    return
                else:
                    raise  # Re-raise other errors
        
        # Success message
        success_message = f"Atlas Paste successful!\n\n"
        success_message += f"Asset: {asset_name}\n"
        success_message += f"Subcategory: {subcategory}\n"
        success_message += f"Nodes imported: {len(new_nodes)}\n"
        success_message += f"Source: {asset_path}\n\n"
        success_message += f"All texture and geometry file paths have been automatically remapped to the Atlas library."
        
        hou.ui.displayMessage(
            success_message,
            severity=hou.severityType.Message,
            title="Atlas Paste - Success"
        )
        
        # Set status message
        hou.ui.setStatusMessage(f"Atlas Paste: {asset_name} imported successfully!")
        
        # Select imported nodes for user convenience
        if new_nodes:
            for node in hou.selectedNodes():
                node.setSelected(False)
            for node in new_nodes:
                node.setSelected(True)
        
        print(f"Atlas Paste successful: {len(new_nodes)} nodes imported from {asset_name}")
        
    except Exception as e:
        error_msg = f"Atlas Paste failed: {str(e)}\n\n"
        error_msg += "Error details:\n"
        error_msg += traceback.format_exc()
        
        hou.ui.displayMessage(
            error_msg,
            severity=hou.severityType.Error,
            title="Atlas Paste - Error"
        )
        
        print(f"Atlas Paste error: {e}")
        print(traceback.format_exc())


def atlas_paste_inspect():
    """Inspect Atlas copy string from clipboard without importing"""
    try:
        # Get clipboard content
        try:
            clipboard_text = hou.ui.getTextFromClipboard()
        except:
            from PySide2.QtWidgets import QApplication
            qapp = QApplication.instance()
            clipboard_text = qapp.clipboard().text()
        
        if not clipboard_text:
            hou.ui.displayMessage(
                "Clipboard is empty!",
                severity=hou.severityType.Error,
                title="Atlas Inspect"
            )
            return
        
        clipboard_text = clipboard_text.strip()
        
        if not clipboard_text.startswith('AtlasAsset_'):
            hou.ui.displayMessage(
                f"Clipboard does not contain Atlas copy string.\n\nContent: {clipboard_text[:100]}",
                severity=hou.severityType.Error,
                title="Atlas Inspect"
            )
            return
        
        # Import system
        try:
            from atlas_clipboard_system import AtlasClipboardPaste
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            from atlas_clipboard_system import AtlasClipboardPaste
        
        paster = AtlasClipboardPaste()
        
        # Parse and inspect
        asset_name, uid, identifier, encryption_key = paster.parse_copy_string(clipboard_text)
        
        # Try to find asset
        try:
            asset_path, subcategory = paster.find_asset_in_library(asset_name, uid)
            asset_found = True
        except:
            asset_found = False
            asset_path = "Not found"
            subcategory = "Unknown"
        
        # Show detailed info
        info = f"Atlas Copy String Inspector\n\n"
        info += f"Asset Name: {asset_name}\n"
        info += f"Asset UID: {uid}\n"
        info += f"Encrypted: {'Yes' if encryption_key else 'No'}\n"
        if encryption_key:
            info += f"Encryption Key: {encryption_key}\n"
        info += f"Subcategory: {subcategory}\n"
        info += f"Asset Found: {'Yes' if asset_found else 'No'}\n"
        info += f"Asset Path: {asset_path}\n\n"
        info += f"Copy String: {clipboard_text}"
        
        hou.ui.displayMessage(
            info,
            title="Atlas Inspect"
        )
        
    except Exception as e:
        hou.ui.displayMessage(
            f"Atlas Inspect failed: {str(e)}",
            severity=hou.severityType.Error,
            title="Atlas Inspect"
        )


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
    atlas_paste_nodes()
