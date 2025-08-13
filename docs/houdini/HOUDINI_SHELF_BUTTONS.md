# Blacksmith Atlas - Shelf Buttons for Testing

Create these shelf buttons for easy testing of the Atlas system.

## Create Atlas Asset Shelf Button

**Name**: Create Atlas Asset  
**Label**: 🏭 Create  
**Script**:

```python
# Blacksmith Atlas - Create Atlas Asset (Shelf Button)
import sys
from pathlib import Path

# Add backend path
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Clear Atlas modules for fresh imports (development)
atlas_modules = [k for k in list(sys.modules.keys()) if 'assetlibrary' in k]
for module_name in atlas_modules:
    del sys.modules[module_name]
if atlas_modules:
    print(f"🔄 Cleared {len(atlas_modules)} Atlas modules")

try:
    from assetlibrary._3D.copy_to_atlas_asset import copy_selected_to_atlas_asset
    print("✅ Atlas create script loaded")
    copy_selected_to_atlas_asset()
except Exception as e:
    hou.ui.displayMessage(f"Atlas Create Error: {e}", severity=hou.severityType.Error)
    print(f"❌ Atlas Create Error: {e}")
    import traceback
    traceback.print_exc()
```

## Import Atlas Asset Shelf Button

**Name**: Import Atlas Asset  
**Label**: 📦 Import  
**Script**:

```python
# Blacksmith Atlas - Import Atlas Asset (Shelf Button)
import sys
from pathlib import Path

# Add backend path  
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Clear Atlas modules for fresh imports
atlas_modules = [k for k in list(sys.modules.keys()) if 'assetlibrary' in k]
for module_name in atlas_modules:
    del sys.modules[module_name]
if atlas_modules:
    print(f"🔄 Cleared {len(atlas_modules)} Atlas modules")

try:
    # Simple file browser to select Atlas asset
    import os
    library_path = "/net/library/atlaslib/3D/Assets"
    
    # Check if library path exists
    if not os.path.exists(library_path):
        hou.ui.displayMessage(f"Atlas library not found at:\n{library_path}\n\nCreate the library directory first.", 
                            severity=hou.severityType.Warning, title="Library Not Found")
        print(f"❌ Library path not found: {library_path}")
    else:
        # For now, show available assets
        assets = []
        for category in os.listdir(library_path):
            category_path = os.path.join(library_path, category)
            if os.path.isdir(category_path):
                for asset_folder in os.listdir(category_path):
                    if os.path.isdir(os.path.join(category_path, asset_folder)):
                        assets.append(f"{category}/{asset_folder}")
        
        if assets:
            # Show asset selection dialog
            selected = hou.ui.selectFromList(assets, 
                                           message="Select Atlas Asset to Import:", 
                                           title="Import Atlas Asset",
                                           column_header="Available Assets")
            if selected:
                selected_asset = assets[selected[0]]
                hou.ui.displayMessage(f"Selected: {selected_asset}\n\nImport functionality coming soon!\n\nAsset location:\n{library_path}/{selected_asset}", 
                                    title="Atlas Import")
                print(f"📦 Selected asset: {selected_asset}")
            else:
                print("❌ No asset selected")
        else:
            hou.ui.displayMessage(f"No Atlas assets found in library.\n\nCreate some assets first using the Create Atlas Asset button.", 
                                title="No Assets Found")
            print("📋 No assets found in library")

except Exception as e:
    hou.ui.displayMessage(f"Atlas Import Error: {e}", severity=hou.severityType.Error)
    print(f"❌ Atlas Import Error: {e}")
    import traceback
    traceback.print_exc()
```

## How to Create Shelf Buttons

1. **Right-click on shelf** → "New Tool"
2. **Set Name** and **Label** as above
3. **Copy/paste the script** into the Script field
4. **Set Script Language** to Python
5. **Click Accept**

## Testing Workflow

1. **Select nodes** (matnet + geometry)
2. **Click "🏭 Create"** shelf button
3. **Verify subnet is created with export parameters**
4. **Configure asset parameters and export**
5. **Click "📦 Import"** to browse created assets

Once these work perfectly, we'll copy the exact same logic to the right-click menu!