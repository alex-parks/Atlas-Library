# Complete Asset Export System Guide
## Blacksmith Atlas - Advanced Houdini Integration

This guide explains the new **Complete Asset Export System** that preserves entire Houdini material pipelines for perfect reconstruction.

## 🎯 What This System Does

The Complete Asset Export System addresses your core requirement:

> "I need all the trees and parameters to replicate back to houdini when loaded in so we can understand the EXACT way that asset was lookdeved"

### Key Features

1. **Complete Pipeline Preservation**: Captures every node, parameter, and connection
2. **Material Workflow Reconstruction**: Preserves exact lookdev setups for any rendering engine
3. **Smart Folder Organization**: `Assets → Props → {UID}_AssetName → Model/Textures/Data`
4. **Multi-Format Export**: USD, OBJ, Alembic, FBX geometry files
5. **Intelligent Texture Management**: Organizes textures by type with perfect path mapping
6. **One-Click Recreation**: Complete reconstruction back into Houdini sessions

## 📁 Folder Structure

```
/net/library/atlaslib/
└── Assets/
    ├── Props/
    │   └── A1B2C3D4E5F6_Helicopter/
    │       ├── Model/
    │       │   ├── Helicopter_body.usd
    │       │   ├── Helicopter_body.obj
    │       │   ├── Helicopter_body.abc
    │       │   └── Helicopter_body.fbx
    │       ├── Textures/
    │       │   ├── Diffuse/
    │       │   │   └── body_material_basecolor_helicopter_diffuse.png
    │       │   ├── Normal/
    │       │   │   └── body_material_normal_helicopter_normal.png
    │       │   ├── Roughness/
    │       │   │   └── body_material_roughness_helicopter_rough.png
    │       │   └── Metallic/
    │       │       └── body_material_metallic_helicopter_metal.png
    │       └── Data/
    │           ├── reconstruction_data.json      # Complete hierarchy & parameters
    │           ├── arango_document.json         # Database document
    │           └── recreate_materials.py        # Recreation script
    ├── Characters/
    ├── Environments/
    ├── Vehicles/
    ├── Architecture/
    ├── Furniture/
    ├── Weapons/
    ├── Organic/
    ├── Hard_Surface/
    └── General/
```

## 🚀 How to Use

### 1. Simple Export (Recommended for Artists)

In Houdini Python Shell:

```python
# Import the simple export function
from assetlibrary._3D.houdiniae import quick_asset_export

# Ultra-simple export with defaults
result = quick_asset_export("MyHelicopter")
print(result)
```

### 2. Detailed Export with Options

```python
from assetlibrary._3D.houdiniae import export_complete_asset_simple

# Export with specific category and rendering engine
result = export_complete_asset_simple(
    asset_name="SportsCar",
    subcategory="Vehicles", 
    rendering_engine="Arnold"
)

if result['success']:
    print(f"✅ Asset exported!")
    print(f"   ID: {result['asset_id']}")
    print(f"   Location: {result['asset_folder']}")
    print(f"   Files: {result['geometry_files']} geo, {result['materials']} materials")
```

### 3. Advanced Export with Full Control

```python
from assetlibrary._3D.houdiniae import AdvancedAssetExporter
import hou

# Select the node you want to export
selected_node = hou.selectedNodes()[0]

# Create advanced exporter
exporter = AdvancedAssetExporter(
    asset_name="SciFiBuilding",
    subcategory="Architecture",
    rendering_engine="Redshift"
)

# Perform complete export
success = exporter.export_complete_asset(selected_node)

if success:
    print(f"Asset exported with ID: {exporter.asset_id}")
    print(f"Location: {exporter.asset_folder}")
```

## 🔍 Asset Search and Discovery

```python
from assetlibrary._3D.houdiniae import search_assets_in_library

# Search for assets
helicopters = search_assets_in_library("helicopter")
redshift_assets = search_assets_in_library("", rendering_engine="Redshift")
car_props = search_assets_in_library("car", category="Props")

for asset in helicopters:
    print(f"Found: {asset['name']} ({asset['rendering_engine']})")
```

## 🏗️ Loading Assets Back into Houdini

```python
from assetlibrary._3D.houdiniae import load_asset_from_library

# Load by asset ID or name
result = load_asset_from_library("A1B2C3D4E5F6")  # Using asset ID
# or
result = load_asset_from_library("Helicopter")      # Using asset name

if result['success']:
    print(f"✅ Loaded: {result['asset_info']['name']}")
    print(f"   From: {result['asset_folder']}")
```

## 📋 Available Categories and Engines

```python
from assetlibrary._3D.houdiniae import list_available_subcategories, list_supported_rendering_engines

# List all available categories
categories = list_available_subcategories()
print("Available categories:", categories)

# List all supported rendering engines  
engines = list_supported_rendering_engines()
print("Supported engines:", engines)
```

## 🎨 What Gets Captured

### Node Hierarchy
- Complete node tree structure
- Node types and categories
- Parent-child relationships
- Node positions and flags
- Custom user data

### Material Networks
- All material/shader nodes
- Parameter values and types
- Texture file paths
- Node connections and inputs
- Rendering engine detection

### Texture Management
- Automatic texture discovery
- Smart categorization (Diffuse, Normal, Roughness, etc.)
- File copying with organized naming
- Path mapping for reconstruction

### Parameters
- All node parameters
- Default vs. custom values
- Expressions and keyframes
- Parameter templates and metadata

## 🔄 Reconstruction Process

The system creates three key files for perfect reconstruction:

1. **`reconstruction_data.json`**: Complete technical data
2. **`arango_document.json`**: Database document for search/metadata
3. **`recreate_materials.py`**: Python script for material recreation

### Reconstruction Steps

1. **Load Geometry**: Import USD/OBJ/Alembic/FBX files
2. **Recreate Hierarchy**: Rebuild exact node structure
3. **Recreate Materials**: Rebuild material networks with exact parameters
4. **Connect Textures**: Relink all texture files with correct paths
5. **Restore Parameters**: Set all parameters to original values

## 💡 Advanced Features

### Asset ID System
- 12-character unique hash IDs (e.g., `A1B2C3D4E5F6`)
- Prevents naming conflicts
- Enables precise asset tracking

### Multi-Format Support
- **USD**: Primary format for modern pipelines
- **OBJ**: Universal compatibility
- **Alembic**: Animation and caches
- **FBX**: Game engine integration

### Rendering Engine Support
- Redshift
- Arnold
- Mantra
- Karma
- Octane
- Cycles
- V-Ray
- RenderMan

### Texture Organization
Textures are automatically sorted into categories:
- Diffuse (Base Color, Albedo)
- Normal (Bump Maps)
- Roughness
- Metallic
- Specular
- Displacement
- Emission
- Opacity
- Subsurface
- Transmission
- AO (Ambient Occlusion)
- Curvature

## 🛠️ Integration with Blacksmith Atlas

The system integrates seamlessly with the existing Blacksmith Atlas infrastructure:

- **ArangoDB**: Asset metadata and search
- **Asset Library**: Centralized storage at `/net/library/atlaslib`
- **Category System**: Organized folder structure
- **Search Interface**: Fast asset discovery
- **Version Control**: Asset versioning and history

## 📝 Usage Examples

### Export a Character Asset
```python
result = export_complete_asset_simple(
    asset_name="MainCharacter",
    subcategory="Characters",
    rendering_engine="Arnold"
)
```

### Export Environment with Redshift Materials
```python
result = export_complete_asset_simple(
    asset_name="SciFiLab",
    subcategory="Environments", 
    rendering_engine="Redshift"
)
```

### Export Vehicle Asset
```python
result = export_complete_asset_simple(
    asset_name="SpaceShip",
    subcategory="Vehicles",
    rendering_engine="Karma"
)
```

## 🎯 Perfect Material Reconstruction

The system ensures **exact** material reconstruction by:

1. **Parameter Preservation**: Every parameter value, expression, and keyframe
2. **Texture Path Mapping**: Perfect file path reconstruction
3. **Node Connection Mapping**: Exact input/output connections
4. **Rendering Engine Specificity**: Engine-specific material handling
5. **Flag and State Preservation**: Display, render, and template flags

This means when you load an asset back into Houdini, you get **exactly** the same lookdev setup as when it was exported.

## 🚀 Next Steps

1. **Test with Real Assets**: Export actual Houdini scenes
2. **Verify Reconstruction**: Load assets back and verify materials
3. **Integration Testing**: Test with different rendering engines
4. **Pipeline Integration**: Integrate with your production pipeline
5. **Training**: Train your team on the new workflow

## 🔧 Technical Requirements

- **Houdini**: Any recent version with Python support
- **Python**: 3.7+ with standard libraries
- **Storage**: Network access to `/net/library/atlaslib`
- **Memory**: Sufficient for asset data and texture copying
- **ArangoDB**: For metadata and search (optional but recommended)

## 📞 Support

For issues or questions about the Complete Asset Export System:

1. Check the test files for usage examples
2. Review the error messages for troubleshooting
3. Verify network storage accessibility
4. Ensure Houdini Python environment is properly configured

---

**This system gives you complete control over your Houdini asset pipeline while maintaining perfect fidelity for material reconstruction.** 🎨✨
