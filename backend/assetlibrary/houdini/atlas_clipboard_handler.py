#!/usr/bin/env python3
"""
Blacksmith Atlas - Clipboard Handler
===================================

This module provides Atlas clipboard functionality that integrates with Houdini.
Instead of overriding Ctrl+V globally, it provides seamless integration through
the network editor right-click menu and paste functions.
"""

import hou
import sys
from pathlib import Path

def is_atlas_in_clipboard():
    """Check if there's an Atlas asset in the clipboard"""
    try:
        clipboard_text = hou.ui.getTextFromClipboard()
        return clipboard_text and clipboard_text.startswith("BLATLAS:")
    except:
        return False

def paste_atlas_smart():
    """Smart paste function that handles both Atlas assets and normal clipboard content"""
    try:
        # Add paths
        backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        _3d_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D")
        if str(_3d_path) not in sys.path:
            sys.path.insert(0, str(_3d_path))
        
        # Check what's in clipboard
        clipboard_text = hou.ui.getTextFromClipboard()
        
        if clipboard_text and clipboard_text.startswith("BLATLAS:"):
            print("📋 Atlas asset detected - pasting...")
            
            # Import and reload
            import importlib
            modules_to_remove = ['assetlibrary._3D.houdiniae', 'houdiniae']
            for mod in modules_to_remove:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            try:
                import houdiniae
                importlib.reload(houdiniae)
                paste_function = houdiniae.paste_atlas_from_clipboard
            except ImportError:
                from assetlibrary._3D import houdiniae
                importlib.reload(houdiniae)
                paste_function = houdiniae.paste_atlas_from_clipboard
            
            # Find current network editor
            current_network_editor = None
            for pane in hou.ui.paneTabs():
                if pane.type() == hou.paneTabType.NetworkEditor and pane.isCurrentTab():
                    current_network_editor = pane
                    break
            
            # Paste Atlas asset
            return paste_function(network_editor=current_network_editor)
            
        else:
            print("📋 No Atlas asset in clipboard - use normal Houdini paste (Ctrl+V)")
            hou.ui.displayMessage("No Atlas asset in clipboard.\n\n"
                                "Use 'Create Atlas Asset' to copy an asset first,\n"
                                "or use normal Houdini Ctrl+V for regular clipboard content.",
                                severity=hou.severityType.Message)
            return None
        
    except Exception as e:
        print(f"❌ Smart paste error: {e}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(f"❌ Paste error: {e}", severity=hou.severityType.Error)
        return None

def setup_atlas_menu_integration():
    """Set up Atlas paste in the network editor right-click menu"""
    print("📋 Atlas clipboard integration ready!")
    print("💡 Atlas assets will be automatically detected in clipboard")
    print("🎯 Use 'Create Atlas Asset' then paste with the Atlas Paste function")

# Auto-setup when module is imported
setup_atlas_menu_integration()
