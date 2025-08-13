#!/usr/bin/env python3
"""
Blacksmith Atlas - Paste Atlas Asset (Shelf Module)
==================================================

This module contains the logic for the "Paste Atlas Asset" shelf button.
Provides a smart paste function that works like Ctrl+V for Atlas assets.
"""

import hou
import sys
from pathlib import Path

def paste_atlas_asset():
    """Main function to paste an Atlas Asset from the system clipboard"""
    
    print("📋 BLACKSMITH ATLAS - SMART PASTE")
    
    try:
        # Add backend path
        backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        # Also add the _3D directory path directly
        _3d_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D")
        if str(_3d_path) not in sys.path:
            sys.path.insert(0, str(_3d_path))
        
        # Import the smart paste function
        from atlas_clipboard_handler import paste_atlas_smart
        
        print("✅ Successfully imported paste_atlas_smart")
        
        # Execute smart paste
        result = paste_atlas_smart()
        
        if result:
            print(f"✅ Successfully pasted Atlas asset")
        else:
            print(f"📋 Smart paste completed")
        
    except Exception as e:
        print(f"❌ Paste error: {e}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(f"❌ Paste error: {e}", severity=hou.severityType.Error)

# Main function to call from shelf button
def main():
    """Main entry point for shelf button"""
    paste_atlas_asset()

if __name__ == "__main__":
    main()
