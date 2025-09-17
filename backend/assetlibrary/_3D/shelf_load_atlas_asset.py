#!/usr/bin/env python3
"""
Blacksmith Atlas - Load Atlas Asset (Self-Contained Shelf Module)
================================================================

This module contains ALL the logic for the "Load Atlas Asset" shelf button.
Everything is self-contained for Houdini shelf compatibility.
"""

import hou
import os
import sys
import json
from pathlib import Path

def get_clipboard_text():
    """Get text from clipboard using Houdini's method"""
    try:
        # Houdini's clipboard access
        clipboard_text = hou.ui.getTextFromClipboard()
        return clipboard_text.strip() if clipboard_text else None
    except Exception as e:
        print(f"❌ Error reading clipboard: {e}")
        return None

def validate_asset_id(asset_id):
    """Validate that the asset ID is in correct format (16 characters)"""
    if not asset_id:
        return False, "No Asset ID found in clipboard"
    
    # Remove any whitespace
    asset_id = asset_id.strip()
    
    # Check length
    if len(asset_id) != 16:
        return False, f"Invalid Asset ID length: {len(asset_id)} (expected 16 characters)"
    
    # Check if it's alphanumeric
    if not asset_id.isalnum():
        return False, "Asset ID must contain only letters and numbers"
    
    return True, asset_id.upper()

def get_asset_info_from_list(asset_id):
    """Get asset info by searching the assets list"""
    try:
        import urllib.request
        
        # Get all assets and find the one with matching ID
        api_url = "http://localhost:8000/api/v1/assets?limit=1000"
        print(f"   🔄 Searching asset list: {api_url}")
        
        response = urllib.request.urlopen(api_url, timeout=30)
        data = json.loads(response.read().decode())
        
        assets = data.get('items', [])
        print(f"   📊 Found {len(assets)} total assets, searching for {asset_id}")
        
        for asset in assets:
            if asset.get('id') == asset_id:
                print(f"   ✅ Found asset: {asset.get('name', 'Unknown')}")
                return True, asset
        
        print(f"   ❌ Asset {asset_id} not found in {len(assets)} assets")
        return False, f"Asset {asset_id} not found in database"
        
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return False, f"Database search error: {e}"

def determine_render_engine_from_context():
    """Determine which render engine template to load based on current context"""
    try:
        current_node = hou.pwd()
        current_path = current_node.path()
        current_type = current_node.type().name()
        
        print(f"   📍 Current location: {current_path}")
        print(f"   📍 Node type: {current_type}")
        print(f"   📍 Node name: {current_node.name()}")
        
        # Try to get the network editor context
        network_path = current_path
        try:
            pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            if pane:
                network_node = pane.pwd()
                network_path = network_node.path()
                print(f"   📍 Network Editor path: {network_path}")
                print(f"   📍 Network Editor node type: {network_node.type().name()}")
        except Exception as ne_error:
            print(f"   📍 Could not get network editor context: {ne_error}")
        
        # If we're at root, try to use /obj as default for Redshift
        if network_path == "/":
            print("   📍 At root level - defaulting to OBJ/Redshift context")
            network_path = "/obj"
        
        # Check if we're in LOPs/Stage context
        if network_path.startswith("/stage") or current_type == "lopnet" or "lop" in current_type.lower():
            print("   🎨 Detected LOP/Stage context → Using Karma template")
            return "karma", network_path
        else:
            print("   🎨 Detected OBJ context → Using Redshift template")
            return "redshift", network_path
            
    except Exception as e:
        print(f"   ⚠️ Error detecting context: {e}, defaulting to Redshift")
        import traceback
        print(f"   ⚠️ Traceback: {traceback.format_exc()}")
        return "redshift", "/obj"

def build_asset_folder_path(asset_data):
    """Build the asset folder path from asset data"""
    try:
        # First try to get from paths.folder_path
        folder_path = asset_data.get('paths', {}).get('folder_path')
        if folder_path and os.path.exists(folder_path):
            return Path(folder_path)
        
        # Fallback: Get hierarchy information and build path
        hierarchy = asset_data.get('metadata', {}).get('hierarchy', {})
        asset_type = hierarchy.get('asset_type', 'Assets')
        subcategory = hierarchy.get('subcategory', 'Blacksmith Asset')
        
        # Convert subcategory names to folder names (matching the export logic)
        subcategory_folder_map = {
            "Blacksmith Asset": "BlacksmithAssets",
            "Megascans": "Megascans", 
            "Kitbash": "Kitbash",
            "Blacksmith FX": "BlacksmithFX",
            "Atmosphere": "Atmosphere",
            "FLIP": "FLIP", 
            "Pyro": "Pyro",
            "Blacksmith Materials": "BlacksmithMaterials",
            "Redshift": "Redshift",
            "Karma": "Karma",
            "Blacksmith HDAs": "BlacksmithHDAs"
        }
        
        subcategory_folder = subcategory_folder_map.get(subcategory, subcategory.replace(" ", ""))
        
        # Build full path
        library_root = Path("/net/library/atlaslib/3D")
        asset_folder = library_root / asset_type / subcategory_folder / asset_data['id']
        
        return asset_folder
        
    except Exception as e:
        print(f"   ❌ Error building asset path: {e}")
        return None

def sanitize_node_name(name):
    """Sanitize asset name for use as Houdini node name"""
    import re
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^\w]', '_', name)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"asset_{sanitized}"
    return sanitized if sanitized else "atlas_asset"

def load_template_file(template_path, target_network_path, asset_name):
    """Load the template file into the specified network and wrap in named subnet"""
    try:
        print(f"   📄 Template file: {template_path}")
        print(f"   📊 File size: {template_path.stat().st_size} bytes")
        print(f"   🎯 Target network: {target_network_path}")
        
        # Get the target network node
        try:
            target_network = hou.node(target_network_path)
            if not target_network:
                error_msg = f"Target network not found: {target_network_path}"
                print(f"   ❌ {error_msg}")
                hou.ui.displayMessage(f"❌ {error_msg}", severity=hou.severityType.Error)
                return False
        except Exception as e:
            error_msg = f"Error accessing target network {target_network_path}: {e}"
            print(f"   ❌ {error_msg}")
            hou.ui.displayMessage(f"❌ {error_msg}", severity=hou.severityType.Error)
            return False
        
        print(f"   📥 Loading template into: {target_network.path()}")
        
        # Check if we can read the file
        if not template_path.is_file():
            print(f"   ❌ Not a file: {template_path}")
            return False
            
        if not os.access(template_path, os.R_OK):
            print(f"   ❌ No read permission: {template_path}")
            return False
        
        # Create a subnet to contain the asset first
        # Sanitize the asset name for use as node name
        sanitized_name = sanitize_node_name(asset_name)
        print(f"   🔧 Sanitized node name: '{asset_name}' → '{sanitized_name}'")
        subnet = target_network.createNode("subnet", sanitized_name)
        print(f"   📦 Created subnet: {subnet.name()}")
        
        # Load the template directly into the subnet
        print(f"   🔄 Loading template into subnet...")
        subnet.loadChildrenFromFile(str(template_path))
        
        # Position the subnet nicely
        subnet.moveToGoodPosition()
        
        # Check if anything was loaded
        loaded_children = len(subnet.children())
        print(f"   📦 Loaded {loaded_children} nodes into subnet")
        
        if loaded_children > 0:
            print(f"   ✅ Asset loaded as subnet: {asset_name}")
            return True, subnet.name()
        else:
            print(f"   ⚠️ No nodes were loaded from template")
            # Clean up empty subnet
            subnet.destroy()
            return True, None
        
    except hou.LoadWarning as e:
        print(f"   ⚠️ Load warning: {e}")
        print(f"   ✅ Template loaded with warnings!")
        return True, None
        
    except Exception as e:
        print(f"   ❌ Error loading template: {e}")
        print(f"   ❌ Error type: {type(e).__name__}")
        import traceback
        print(f"   ❌ Traceback: {traceback.format_exc()}")
        return False, None

def load_asset_from_clipboard():
    """Main function to load asset from clipboard ID"""
    try:
        print("\n📋 READING CLIPBOARD...")
        
        # Get clipboard text
        clipboard_text = get_clipboard_text()
        if not clipboard_text:
            hou.ui.displayMessage("❌ No text found in clipboard!\n\nPlease copy an Asset ID first.", 
                                severity=hou.severityType.Error)
            return False
        
        print(f"   📋 Clipboard content: '{clipboard_text}'")
        
        # Validate asset ID
        is_valid, result = validate_asset_id(clipboard_text)
        if not is_valid:
            hou.ui.displayMessage(f"❌ {result}\n\nClipboard content: '{clipboard_text}'", 
                                severity=hou.severityType.Error)
            return False
        
        asset_id = result
        print(f"   ✅ Valid Asset ID: {asset_id}")
        
        # Get asset info directly from list (skip individual API)
        print("\n🔍 LOOKING UP ASSET...")
        api_success, api_result = get_asset_info_from_list(asset_id)
        if not api_success:
            hou.ui.displayMessage(f"❌ {api_result}\n\nAsset ID: {asset_id}", 
                                severity=hou.severityType.Error)
            return False
        
        asset_data = api_result
        asset_name = asset_data.get('name', 'Unknown Asset')
        
        # Build asset folder path
        asset_folder = build_asset_folder_path(asset_data)
        if not asset_folder:
            hou.ui.displayMessage("❌ Could not determine asset folder path", 
                                severity=hou.severityType.Error)
            return False
        
        print(f"   📁 Asset folder: {asset_folder}")
        
        # Determine which template to load based on context
        render_engine, target_network_path = determine_render_engine_from_context()
        template_filename = f"template_{render_engine}.hip"
        template_path = asset_folder / template_filename
        
        print(f"\n🎯 LOADING TEMPLATE...")
        print(f"   📄 Looking for: {template_filename}")
        print(f"   📍 Full path: {template_path}")
        
        # Check if template exists
        if not template_path.exists():
            error_msg = f"Can't find {render_engine.title()} version of this asset"
            hou.ui.displayMessage(f"❌ {error_msg}\n\nLooking for: {template_path}\n\nAsset: {asset_name}", 
                                severity=hou.severityType.Error)
            print(f"   ❌ {error_msg}")
            return False
        
        # Load the template
        load_result = load_template_file(template_path, target_network_path, asset_name)
        if load_result[0]:  # Success
            subnet_name = load_result[1]
            
            # Success message
            if subnet_name:
                success_msg = f"""✅ ATLAS ASSET LOADED!

🏷️ Asset: {asset_name}
🆔 ID: {asset_id}
🎨 Template: {render_engine.title()}
📍 Loaded into: {target_network_path}
📦 Subnet: {subnet_name}

The asset has been loaded as a subnet container in the {render_engine.title()} network."""
            else:
                success_msg = f"""✅ ATLAS ASSET LOADED!

🏷️ Asset: {asset_name}
🆔 ID: {asset_id}
🎨 Template: {render_engine.title()}
📍 Loaded into: {target_network_path}

The asset nodes have been added to the {render_engine.title()} network."""
            
            hou.ui.displayMessage(success_msg, title="🎉 Atlas Asset Loaded")
            print("\n🎉 ASSET LOAD COMPLETE!")
            return True
        else:
            hou.ui.displayMessage("❌ Failed to load template file", 
                                severity=hou.severityType.Error)
            return False
            
    except Exception as e:
        error_msg = f"Load error: {str(e)}"
        print(f"❌ {error_msg}")
        hou.ui.displayMessage(f"❌ {error_msg}", severity=hou.severityType.Error)
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point for shelf button"""
    
    print("🏭 BLACKSMITH ATLAS - LOAD ATLAS ASSET")
    print("=" * 60)
    
    try:
        # Call the main function
        success = load_asset_from_clipboard()
        
        if success:
            print("✅ Atlas asset loading completed successfully!")
        else:
            print("⚠️ Atlas asset loading completed with warnings")
            
        return success
            
    except Exception as e:
        error_msg = f"❌ Error: {e}"
        print(error_msg)
        hou.ui.displayMessage(error_msg, severity=hou.severityType.Error)
        import traceback
        traceback.print_exc()
        return False

# Legacy function name for compatibility
def load_atlas_asset():
    """Legacy function name - calls main()"""
    return main()

if __name__ == "__main__":
    main()