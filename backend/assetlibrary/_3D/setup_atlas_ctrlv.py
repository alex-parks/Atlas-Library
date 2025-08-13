#!/usr/bin/env python3
"""
Blacksmith Atlas - Ctrl+V Setup
===============================

This script helps set up Ctrl+V functionality for Atlas assets.
It creates the necessary hotkey overrides and provides instructions.
"""

import hou
import os
from pathlib import Path

def setup_atlas_ctrlv():
    """Set up Ctrl+V for Atlas assets"""
    try:
        print("🔧 Setting up Atlas Ctrl+V functionality...")
        
        # Get Houdini user directory
        user_dir = Path(hou.homeHoudiniDirectory())
        print(f"📂 Houdini user directory: {user_dir}")
        
        # Create the keymap override content
        keymap_content = '''# Blacksmith Atlas - Ctrl+V Override
# This overrides Ctrl+V in Network Editor to handle Atlas assets

# Override Ctrl+V to use Atlas smart paste
h.pane.netwview.paste "Ctrl+V" {
    python -c "
import sys
from pathlib import Path

# Add Atlas paths
backend_path = Path('/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend')
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

_3d_path = Path('/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D')
if str(_3d_path) not in sys.path:
    sys.path.insert(0, str(_3d_path))

try:
    from atlas_clipboard_handler import paste_atlas_smart
    result = paste_atlas_smart()
    if result is None:
        # No Atlas asset, try normal paste
        import hou
        try:
            pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            if pane and hasattr(pane, 'paste'):
                pane.paste()
        except:
            pass
except Exception as e:
    print(f'Atlas Ctrl+V error: {e}')
    # Fallback to normal paste
    try:
        import hou
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if pane and hasattr(pane, 'paste'):
            pane.paste()
    except:
        pass
"
}'''
        
        # Write to keymap override file
        keymap_file = user_dir / "Houdini.keymap.overrides"
        
        # Check if file exists
        if keymap_file.exists():
            print(f"⚠️ Keymap override file already exists: {keymap_file}")
            print("📝 You may need to manually add the Atlas Ctrl+V override")
            
            # Read existing content
            with open(keymap_file, 'r') as f:
                existing_content = f.read()
            
            if "Atlas" in existing_content or "BLATLAS" in existing_content:
                print("✅ Atlas override already appears to be present")
            else:
                print("📝 Adding Atlas override to existing keymap file...")
                with open(keymap_file, 'a') as f:
                    f.write("\n\n" + keymap_content)
                print("✅ Atlas override added to existing keymap file")
        else:
            print(f"📝 Creating new keymap override file: {keymap_file}")
            with open(keymap_file, 'w') as f:
                f.write(keymap_content)
            print("✅ Keymap override file created")
        
        # Show instructions
        hou.ui.displayMessage(f"🔧 Atlas Ctrl+V Setup Complete!\n\n"
                            f"📂 Keymap file: {keymap_file}\n\n"
                            f"🔄 RESTART HOUDINI for changes to take effect.\n\n"
                            f"After restart:\n"
                            f"1. Use 'Create Atlas Asset' to copy an asset\n"
                            f"2. Go to any network editor\n"
                            f"3. Press Ctrl+V to paste with pre-mapped paths!\n\n"
                            f"💡 If Ctrl+V doesn't work, use the 'Paste Atlas Asset' shelf button instead.",
                            title="Setup Complete - Restart Required")
        
        print("✅ Setup complete! Restart Houdini to enable Ctrl+V for Atlas assets.")
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(f"❌ Setup error: {e}\n\n"
                            f"You can still use the 'Paste Atlas Asset' shelf button.",
                            severity=hou.severityType.Error)

def remove_atlas_ctrlv():
    """Remove Atlas Ctrl+V setup"""
    try:
        user_dir = Path(hou.homeHoudiniDirectory())
        keymap_file = user_dir / "Houdini.keymap.overrides"
        
        if keymap_file.exists():
            with open(keymap_file, 'r') as f:
                content = f.read()
            
            # Remove Atlas sections
            lines = content.split('\n')
            filtered_lines = []
            skip_until_end = False
            
            for line in lines:
                if "Blacksmith Atlas" in line or "Atlas Ctrl+V" in line:
                    skip_until_end = True
                elif skip_until_end and line.strip() == '}':
                    skip_until_end = False
                    continue
                elif not skip_until_end:
                    filtered_lines.append(line)
            
            new_content = '\n'.join(filtered_lines).strip()
            
            if new_content:
                with open(keymap_file, 'w') as f:
                    f.write(new_content)
                print("✅ Atlas Ctrl+V override removed")
            else:
                keymap_file.unlink()
                print("✅ Empty keymap file removed")
            
            hou.ui.displayMessage("Atlas Ctrl+V override removed.\n\nRestart Houdini for changes to take effect.",
                                title="Removal Complete")
        else:
            print("⚠️ No keymap override file found")
            hou.ui.displayMessage("No keymap override file found.", severity=hou.severityType.Warning)
            
    except Exception as e:
        print(f"❌ Removal error: {e}")
        hou.ui.displayMessage(f"❌ Removal error: {e}", severity=hou.severityType.Error)

if __name__ == "__main__":
    setup_atlas_ctrlv()
