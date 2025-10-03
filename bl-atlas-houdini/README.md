# Blacksmith Atlas - Standalone Houdini Tools

**Version 3.0 (Standalone)**

This package provides standalone Houdini tools for creating and importing assets to the Blacksmith Atlas library without requiring the full Atlas development environment.

## 📁 Package Structure

```
bl-atlas-houdini/
├── shelftools/              # Houdini shelf tool scripts
│   ├── create_atlas_asset.py    # Create new Atlas assets
│   └── import_atlas_asset.py    # Import assets from library
├── python/                  # Python modules
│   ├── __init__.py              # Package initialization
│   ├── houdiniae.py             # Core asset exporter
│   ├── atlas_ui.py              # UI and parameter creation
│   ├── api_client.py            # API communication
│   └── config_manager.py        # Configuration management
├── otls/                    # Houdini Digital Assets
│   └── atlas_thumbnail.hda     # Thumbnail generation HDA
├── config/                  # Configuration files
│   └── atlas_config.json       # Main configuration
└── README.md               # This file
```

## 🚀 Installation

### 1. Copy Package to Your Machine

Copy the entire `bl-atlas-houdini` folder to your local machine. Recommended locations:

- **Windows**: `C:\Users\YourName\bl-atlas-houdini`
- **Linux**: `~/bl-atlas-houdini`
- **Mac**: `~/bl-atlas-houdini`

### 2. Create Houdini Shelf Buttons

#### Method 1: Manual Shelf Button Creation

1. Open Houdini
2. Right-click on any shelf and select **"New Tool..."**
3. Fill in the tool details:

**Create Atlas Asset Tool:**
- **Name**: `create_atlas_asset`
- **Label**: `Create Atlas Asset`
- **Icon**: Choose an appropriate icon
- **Script**: Copy the entire contents of `shelftools/create_atlas_asset.py`

**Import Atlas Asset Tool:**
- **Name**: `import_atlas_asset`
- **Label**: `Import Atlas Asset`
- **Icon**: Choose an appropriate icon
- **Script**: Copy the entire contents of `shelftools/import_atlas_asset.py`

#### Method 2: Script-Based Installation

1. Open Houdini's Python Shell
2. Run the following script (adjust the path as needed):

```python
import hou
from pathlib import Path

# Adjust this path to where you copied bl-atlas-houdini
bl_atlas_path = Path("C:/Users/YourName/bl-atlas-houdini")  # Windows
# bl_atlas_path = Path("~/bl-atlas-houdini").expanduser()  # Linux/Mac

# Create shelf
shelf = hou.shelves.newShelf(name="atlas_tools", label="Atlas Tools")

# Create Atlas Asset tool
create_script = (bl_atlas_path / "shelftools" / "create_atlas_asset.py").read_text()
create_tool = hou.shelves.newTool(
    name="create_atlas_asset",
    label="Create Atlas Asset",
    script=create_script,
    language=hou.scriptLanguage.Python
)
shelf.setTools([create_tool])

# Import Atlas Asset tool
import_script = (bl_atlas_path / "shelftools" / "import_atlas_asset.py").read_text()
import_tool = hou.shelves.newTool(
    name="import_atlas_asset",
    label="Import Atlas Asset",
    script=import_script,
    language=hou.scriptLanguage.Python
)
shelf.setTools(shelf.tools() + (import_tool,))

print("✅ Atlas Tools shelf created successfully!")
```

## 🎯 Usage

### Creating Atlas Assets

1. **Select nodes** in Houdini that you want to turn into an Atlas asset
2. **Click the "Create Atlas Asset" shelf button**
3. **Enter an asset name** when prompted
4. **Configure the created subnet parameters**:
   - Asset Type (Assets, FX, Materials, HDAs)
   - Subcategory (varies by asset type)
   - Render Engine (Redshift, Karma, Universal)
   - Tags (comma-separated)
   - Thumbnail settings
5. **Click "Export Atlas Asset"** button in the subnet parameters

### Importing Atlas Assets

1. **Click the "Import Atlas Asset" shelf button**
2. **Select an asset** from the library browser
3. **The asset will be imported** into your current context

## ⚙️ Configuration

The tools are pre-configured to work with the Blacksmith network Atlas database:

- **API URL**: `http://library.blacksmith.tv:8000`
- **Database URL**: `http://library.blacksmith.tv:8529`
- **Asset Library**: `/net/library/atlaslib/3D`

### Customizing Configuration

If you need to modify the configuration, edit `config/atlas_config.json`:

```json
{
  "api_base_url": "http://library.blacksmith.tv:8000",
  "database_url": "http://library.blacksmith.tv:8529",
  "asset_library_3d": "/net/library/atlaslib/3D",
  "houdini_hda_path": "../otls/atlas_thumbnail.hda",
  "houdini_hda_type": "Object/AtlasThumbnail::1.0",
  "version": "3.0",
  "description": "Blacksmith Atlas Standalone Configuration"
}
```

## 📋 Features

### Create Atlas Asset Tool
- ✅ Creates subnet from selected nodes
- ✅ Adds comprehensive export parameters
- ✅ Supports multiple asset types (Assets, FX, Materials, HDAs)
- ✅ Automatic file reference processing
- ✅ Thumbnail generation options
- ✅ Direct database integration
- ✅ Version control ready

### Import Atlas Asset Tool
- ✅ Browse entire Atlas library
- ✅ Filter by category and subcategory
- ✅ One-click import to current context
- ✅ Automatic node selection and framing

### Supported Asset Types

**Assets**
- Blacksmith Asset (studio originals)
- Megascans (Quixel library assets)
- Kitbash (modular construction)

**FX**
- Blacksmith FX (custom VFX)
- Atmosphere (environmental effects)
- FLIP (fluid simulations)
- Pyro (fire, smoke, explosions)

**Materials**
- Blacksmith Materials (custom shaders)
- Redshift (Redshift renderer)
- Karma (Karma renderer)

**HDAs**
- Blacksmith HDAs (custom digital assets)

## 🔧 Troubleshooting

### Common Issues

**"Atlas Import Error: Atlas config file not found"**
- Ensure `config/atlas_config.json` exists in the bl-atlas-houdini directory
- Check that the file paths in your shelf scripts are correct

**"No Atlas assets found in the library"**
- Verify network access to `/net/library/atlaslib/3D`
- Check that you're connected to the Blacksmith network

**"API ingestion error"**
- Verify network connection to `library.blacksmith.tv:8000`
- Check that the Atlas API server is running
- Ensure firewall isn't blocking the connection

**"Module import errors"**
- Ensure the `python/` directory contains all required modules
- Check that the path detection in shelf scripts is working correctly

### Debug Mode

To enable verbose debugging, add this to the beginning of any shelf script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

For support:
1. Check the Houdini Python Shell for detailed error messages
2. Verify all file paths in the configuration
3. Test network connectivity to the Atlas servers
4. Contact the Blacksmith VFX team for Atlas-specific issues

## 📝 Version History

**Version 3.0 (Standalone)**
- Standalone package creation
- Removed dependencies on main Atlas codebase
- Simplified installation process
- Pre-configured for Blacksmith network

**Version 2.1 (Original)**
- Full Atlas integration with main codebase
- Development environment required

## 🏭 Blacksmith VFX

This tool is part of the Blacksmith Atlas Asset Management System.

**Author**: Blacksmith VFX
**Version**: 3.0 (Standalone)
**Date**: 2025

For more information about Blacksmith VFX, visit: [blacksmith.tv](http://blacksmith.tv)