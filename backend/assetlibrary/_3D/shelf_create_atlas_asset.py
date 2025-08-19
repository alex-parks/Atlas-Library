#!/usr/bin/env python3
"""
Blacksmith Atlas - Create Atlas Asset (Shelf Module)
==================================================

This module contains the logic for the "Create Atlas Asset" shelf button.
The shelf button imports and calls the main function from this module.
"""

import hou
import sys
from pathlib import Path

def main():
    """Main entry point for shelf button - calls the working implementation"""
    
    print("🏭 BLACKSMITH ATLAS - CREATE ATLAS ASSET")
    print("=" * 60)
    
    try:
        # Import the working implementation
        import copy_to_atlas_asset
        
        # Call the working function
        success = copy_to_atlas_asset.copy_selected_to_atlas_asset()
        
        if success:
            print("✅ Atlas asset creation completed successfully!")
        else:
            print("⚠️ Atlas asset creation completed with warnings")
            
        return success
            
    except ImportError as e:
        error_msg = f"❌ Failed to import copy_to_atlas_asset: {e}"
        print(error_msg)
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        return False
        
    except Exception as e:
        error_msg = f"❌ Error: {e}"
        print(error_msg)
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        return False

# Legacy function name for compatibility
def create_atlas_asset():
    """Legacy function name - calls main()"""
    return main()

if __name__ == "__main__":
    main()
