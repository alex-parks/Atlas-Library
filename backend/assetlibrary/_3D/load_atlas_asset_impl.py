#!/usr/bin/env python3
"""
Blacksmith Atlas - Load Atlas Asset Implementation
================================================

Loads Atlas assets from clipboard-based Asset IDs with context-aware template selection.
"""

import os
import sys
import json
from pathlib import Path

# Try to import Houdini
try:
    import hou
except ImportError:
    print("❌ This script must be run inside Houdini")
    sys.exit(1)

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
    """Validate that the asset ID is in correct format (14 characters)"""
    if not asset_id:
        return False, "No Asset ID found in clipboard"
    
    # Remove any whitespace
    asset_id = asset_id.strip()
    
    # Check length
    if len(asset_id) != 14:
        return False, f"Invalid Asset ID length: {len(asset_id)} (expected 14 characters)"
    
    # Check if it's alphanumeric
    if not asset_id.isalnum():
        return False, "Asset ID must contain only letters and numbers"
    
    return True, asset_id.upper()

def get_asset_info_from_api(asset_id):
    """Query the Atlas API to get asset information"""
    try:
        import urllib.request
        import urllib.error
        
        api_url = f"http://localhost:8000/api/v1/assets/{asset_id}"
        print(f"   🌐 Querying API: {api_url}")
        
        try:
            response = urllib.request.urlopen(api_url, timeout=10)
            asset_data = json.loads(response.read().decode())
            
            print(f"   ✅ Found asset: {asset_data.get('name', 'Unknown')}")
            return True, asset_data
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"   ❌ Asset not found via API, trying direct database lookup...")
                # Fallback: Try to get asset info directly from the list endpoint
                return get_asset_info_from_list(asset_id)
            else:
                return False, f"API error: {e.code} {e.reason}"
        except Exception as e:
            return False, f"API connection error: {e}"
            
    except Exception as e:
        return False, f"Error querying API: {e}"

def get_asset_info_from_list(asset_id):
    """Fallback: Get asset info by searching the assets list"""
    try:
        import urllib.request
        
        # Get all assets and find the one with matching ID
        api_url = "http://localhost:8000/api/v1/assets?limit=1000"
        print(f"   🔄 Fallback: Searching asset list: {api_url}")
        
        response = urllib.request.urlopen(api_url, timeout=30)
        data = json.loads(response.read().decode())
        
        assets = data.get('items', [])
        print(f"   📊 Found {len(assets)} total assets, searching for {asset_id}")
        
        for asset in assets:
            if asset.get('id') == asset_id:
                print(f"   ✅ Found asset via list search: {asset.get('name', 'Unknown')}")
                return True, asset
        
        print(f"   ❌ Asset {asset_id} not found in {len(assets)} assets")
        return False, f"Asset {asset_id} not found in database"
        
    except Exception as e:
        print(f"   ❌ Fallback search failed: {e}")
        return False, f"Database search error: {e}"

def determine_render_engine_from_context():
    """Determine which render engine template to load based on current context"""
    try:
        current_node = hou.pwd()
        current_path = current_node.path()
        current_type = current_node.type().name()
        
        print(f"   📍 Current location: {current_path}")
        print(f"   📍 Node type: {current_type}")
        
        # Check if we're in LOPs/Stage context
        if current_path.startswith("/stage") or current_type == "lopnet" or "lop" in current_type.lower():
            print("   🎨 Detected LOP/Stage context → Using Karma template")
            return "karma"
        else:
            print("   🎨 Detected OBJ context → Using Redshift template")
            return "redshift"
            
    except Exception as e:
        print(f"   ⚠️ Error detecting context: {e}, defaulting to Redshift")
        return "redshift"

def build_asset_folder_path(asset_data):
    """Build the asset folder path from asset data"""
    try:
        # Get hierarchy information
        hierarchy = asset_data.get('hierarchy', {})
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

def load_template_file(template_path):
    """Load the template file into the current network"""
    try:
        current_network = hou.pwd()
        print(f"   📥 Loading template into: {current_network.path()}")
        
        # Load the template
        current_network.loadChildrenFromFile(str(template_path))
        
        print(f"   ✅ Template loaded successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error loading template: {e}")
        return False

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
        
        # Query API for asset info
        print("\n🔍 LOOKING UP ASSET...")
        api_success, api_result = get_asset_info_from_api(asset_id)
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
        render_engine = determine_render_engine_from_context()
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
        if load_template_file(template_path):
            # Success message
            success_msg = f"""✅ ATLAS ASSET LOADED!

🏷️ Asset: {asset_name}
🆔 ID: {asset_id}
🎨 Template: {render_engine.title()}
📍 Loaded into: {hou.pwd().path()}

The asset nodes have been added to your current network."""
            
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

# For testing
if __name__ == "__main__":
    load_asset_from_clipboard()