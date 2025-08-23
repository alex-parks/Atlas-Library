# Blacksmith Atlas HDA Parameter Setup Guide

## 🏗️ HDA Creation Steps

### 1. Create Object-Level HDA
- File → New Asset → Object Level
- Name: `blacksmith_atlas_exporter`
- Label: `Blacksmith Atlas Exporter`

### 2. Add Inputs
- **Input 1**: Geometry stream (for the mesh you want to export)
- **Input 2**: Material Library (optional - for material nodes)

### 3. Add Parameters

Copy this parameter interface definition:

```python
# MAIN EXPORT PARAMETERS
Group: "Export Settings"

1. asset_name (String)
   - Name: "asset_name"
   - Label: "Asset Name" 
   - Default: ""
   - Callback Script: "hou.phm().on_asset_name_changed()"
   - Help: "Name of the asset to export (e.g., 'Helicopter', 'Car')"

2. subcategory (Ordinal/Menu)
   - Name: "subcategory"
   - Label: "Category"
   - Menu Script: "hou.phm().eval_subcategory_menu()"
   - Default: 0 (Props)
   - Callback Script: "hou.phm().on_subcategory_changed()"
   - Help: "Asset category (Props, Characters, Environments, etc.)"

3. rendering_engine (Ordinal/Menu)
   - Name: "rendering_engine" 
   - Label: "Rendering Engine"
   - Menu Script: "hou.phm().eval_rendering_engine_menu()"
   - Default: 0 (Redshift)
   - Help: "Rendering engine used for materials"

# EXPORT CONTROLS
Group: "Export Controls"

4. export_button (Button)
   - Name: "export_button"
   - Label: "🏭 Export Asset"
   - Callback Script: "hou.phm().on_export_button_pressed()"
   - Help: "Export the asset with complete pipeline preservation"

5. search_button (Button)
   - Name: "search_button"
   - Label: "🔍 Check Similar Assets"
   - Callback Script: "hou.phm().search_existing_assets()"
   - Help: "Search for assets with similar names"

6. info_button (Button)
   - Name: "info_button"
   - Label: "ℹ️ Export Info"
   - Callback Script: "hou.phm().show_export_info()"
   - Help: "Show information about the export system"

# STATUS AND RESULTS
Group: "Export Status"

7. validation_status (String)
   - Name: "validation_status"
   - Label: "Validation"
   - Default: ""
   - Disable When: "{ 1 == 1 }" (read-only)
   - Help: "Asset name validation status"

8. preview_path (String)
   - Name: "preview_path"
   - Label: "Preview Path"
   - Default: "Enter asset name to preview path..."
   - Disable When: "{ 1 == 1 }" (read-only)
   - Help: "Preview of where asset will be exported"

9. export_status (String)
   - Name: "export_status"
   - Label: "Export Status"
   - Default: "Ready to export..."
   - Disable When: "{ 1 == 1 }" (read-only)
   - Help: "Current export status"

10. asset_id (String)
    - Name: "asset_id"
    - Label: "Asset ID"
    - Default: ""
    - Disable When: "{ 1 == 1 }" (read-only)
    - Help: "Generated unique asset ID"

11. export_path (String)
    - Name: "export_path"
    - Label: "Export Path"
    - Default: ""
    - Disable When: "{ 1 == 1 }" (read-only)
    - Help: "Full path where asset was exported"

# UTILITY BUTTONS
Group: "Utilities"

12. open_folder_button (Button)
    - Name: "open_folder_button" 
    - Label: "📁 Open Export Folder"
    - Callback Script: "hou.phm().open_export_folder()"
    - Help: "Open the export folder in file manager"

13. reset_button (Button)
    - Name: "reset_button"
    - Label: "🔄 Reset"
    - Callback Script: "hou.phm().reset_export_status()"
    - Help: "Reset export status and clear results"
```

### 4. Alternative Approach - Shelf Tool (Recommended)
**Note:** The HDA approach is legacy. The modern approach uses shelf tools instead.

1. Use the **shelf_create_atlas_asset.py** tool for creating Atlas assets
2. This approach provides the same functionality with better maintainability
3. Right-click context menu integration available

### 4. PyModule Setup (Legacy HDA Approach)
1. Go to **Type Properties → Scripts → PythonModule**
2. Use the `hda_pymodule_template.py` as a reference for custom HDA implementations
3. Make sure the callback scripts match the parameter names above

### 5. Network Setup Inside HDA
```
Input 1 (Geometry) → [Null Node] → Output
                      ↓
              [Material Assignment]
                      ↓  
               [Export Analysis]
```

### 6. Icon and Help
- Icon: Use `$HFS/houdini/help/icons/SHELF/file_cache.svg`
- Help URL: Point to your documentation

## 🎯 Usage Instructions for Artists

### Step 1: Connect Inputs
- **Input 1**: Connect the geometry you want to export
- **Input 2**: Connect material library nodes (optional)

### Step 2: Set Parameters
- **Asset Name**: Enter a descriptive name (e.g., "Helicopter", "Car")
- **Category**: Choose appropriate category (Props, Characters, etc.)
- **Rendering Engine**: Select your rendering engine

### Step 3: Validate and Export
- Click **"🔍 Check Similar Assets"** to avoid duplicates
- Watch the **Validation** field for asset name checks
- Preview the export path
- Click **"🏭 Export Asset"** to export

### Step 4: Results
- **Asset ID**: Generated unique identifier
- **Export Path**: Full path to exported asset
- Click **"📁 Open Export Folder"** to see results

## 🔧 Advanced Features

### Auto-Validation
- Asset name validation happens as you type
- Preview path updates automatically
- Similar asset detection

### Export Process Feedback
- Real-time status updates
- Detailed success/error messages
- Statistics on exported content

### Integration
- Connects to existing Blacksmith Atlas infrastructure
- Uses network storage at `/net/library/atlaslib`
- Compatible with all rendering engines

## 🎨 What Gets Exported

When you click export, the system will:

1. **Analyze Scene**: Deep scan of connected geometry and materials
2. **Export Geometry**: Multiple formats (USD, OBJ, Alembic, FBX)
3. **Organize Textures**: Smart categorization and copying
4. **Capture Materials**: Complete parameter preservation
5. **Create Data**: Reconstruction files for perfect recreation

## 📁 Result Structure
```
/net/library/atlaslib/Assets/{Category}/{UID}_{AssetName}/
├── Model/
│   ├── {AssetName}_geo1.usd
│   ├── {AssetName}_geo1.obj
│   ├── {AssetName}_geo1.abc
│   └── {AssetName}_geo1.fbx
├── Textures/
│   ├── Diffuse/
│   ├── Normal/
│   ├── Roughness/
│   └── Metallic/
└── Data/
    ├── reconstruction_data.json
    ├── arango_document.json
    └── recreate_materials.py
```

This HDA gives you a professional, artist-friendly interface to the complete asset export system! 🎨✨
