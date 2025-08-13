# Blacksmith Atlas - Houdini Right-Click Menu Setup

## Overview

This guide will set up a right-click context menu in Houdini that allows you to select nodes and collapse them into Blacksmith Atlas Assets with full export functionality.

## Features

- **Right-click Integration**: Select nodes and right-click → "Blacksmith Atlas" → "Collapse into Atlas Asset"
- **Automated Export**: Complete export pipeline with texture copying, ABC/FBX generation, and metadata
- **Template-based Fidelity**: Uses Houdini's native `saveChildrenToFile()` for perfect reconstruction
- **User-friendly Interface**: Comprehensive parameter interface with export controls and status

## Installation Steps

### 1. Copy Menu Configuration

Copy the menu XML file to your Houdini preferences directory:

```bash
# Find your Houdini user preferences directory:
# Linux/macOS: ~/houdini20.0/
# Windows: %USERPROFILE%\Documents\houdini20.0\

# Copy the menu file
cp /net/dev/alex.parks/scm/int/Blacksmith-Atlas/docs/houdini_menus/MainMenuCommon.xml ~/houdini20.0/
```

**Alternative Manual Installation:**

1. Navigate to your Houdini user preferences directory:
   - **Linux**: `~/houdini20.0/`
   - **macOS**: `~/Library/Preferences/houdini/20.0/`
   - **Windows**: `%USERPROFILE%\Documents\houdini20.0\`

2. Copy `MainMenuCommon.xml` from `docs/houdini_menus/` to this directory

3. If you already have a `MainMenuCommon.xml` file, you'll need to merge the Blacksmith Atlas sections manually

### 2. Verify Python Path Access

The menu system needs access to the Blacksmith Atlas backend. Ensure the backend path is accessible:

```python
# Test in Houdini Python Shell:
import sys
from pathlib import Path

backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Test import
from assetlibrary._3D.collapse_to_atlas_script import collapse_selected_to_atlas_asset
print("✅ Backend accessible")
```

### 3. Restart Houdini

After copying the menu file, restart Houdini completely for the menu changes to take effect.

### 4. Verify Installation

1. Open Houdini
2. Create some geometry nodes (e.g., Box, Sphere)
3. Select multiple nodes
4. Right-click in the viewport
5. Look for "🏭 Blacksmith Atlas" submenu
6. Click "Collapse into Atlas Asset"

## Usage Workflow

### Basic Workflow

1. **Select Nodes**: Select one or more nodes in Houdini that you want to collapse into an Atlas Asset
2. **Right-click**: Right-click in the viewport to bring up the context menu
3. **Choose Atlas Option**: Navigate to "🏭 Blacksmith Atlas" → "Collapse into Atlas Asset"
4. **Name Your Asset**: Enter a descriptive name for the Atlas Asset
5. **Configure Parameters**: In the created subnet, configure:
   - Asset Name
   - Category (Props, Characters, Environments, etc.)
   - Description
   - Search Tags
6. **Export**: Click the "🚀 Export Atlas Asset" button
7. **Success**: Asset is saved to the Atlas library with full metadata

### Advanced Options

The created Atlas Asset subnet includes advanced options:

- **Export Formats**: Toggle ABC, FBX, texture copying
- **Version Control**: Set asset version numbers
- **Status Monitoring**: Real-time export status updates
- **Info System**: Built-in help and documentation

## Menu Structure

The right-click menu adds these options:

```
Right-click Context Menu
└── 🏭 Blacksmith Atlas
    ├── Collapse into Atlas Asset    (Main function)
    ├── About Atlas Assets          (Information)
    ├── ──────────────────         (Separator)
    └── Load Atlas Asset...         (Future: Asset browser)
```

## File Locations

### Generated Files

When you export an Atlas Asset, files are created in:

```
/net/library/atlaslib/3D/Assets/{Category}/{AssetID}_{AssetName}/
├── Data/
│   └── template.hipnc              # Perfect reconstruction template
├── Textures/
│   ├── {MaterialName}/             # Organized by material
│   │   ├── diffuse.jpg
│   │   ├── normal.jpg
│   │   └── ...
│   └── ...
└── metadata.json                   # Searchable asset information
```

### Library Structure

```
/net/library/atlaslib/3D/Assets/
├── Props/
├── Characters/
├── Environments/
├── Vehicles/
├── Architecture/
├── Furniture/
├── Weapons/
├── Organic/
├── Hard_Surface/
├── FX/
└── General/
```

## Technical Details

### Export Process

The right-click workflow performs these steps:

1. **Node Validation**: Ensures all selected nodes are in the same network context
2. **Subnet Creation**: Uses Houdini's `collapseIntoSubnet()` for proper node organization
3. **Parameter Addition**: Adds comprehensive Atlas export parameters to the subnet
4. **Template Export**: Uses `saveChildrenToFile()` for perfect node serialization
5. **Texture Processing**: Comprehensive scanning of VOP, SHOP, and MatNet nodes
6. **Metadata Generation**: Creates searchable JSON metadata with keywords
7. **Library Organization**: Files organized by category in the Atlas library structure

### Texture Discovery

The system performs comprehensive texture discovery:

- **VOP Nodes**: Scans all parameter values for texture file paths
- **SHOP Materials**: Extracts texture references from traditional Houdini materials
- **MatNet Networks**: Recursively scans material networks for texture nodes
- **UDIM Support**: Handles UDIM texture sequences and patterns
- **Path Resolution**: Expands Houdini variables and validates file existence

## Troubleshooting

### Menu Not Appearing

1. **Check File Location**: Ensure `MainMenuCommon.xml` is in the correct Houdini preferences directory
2. **Restart Required**: Menu changes require a complete Houdini restart
3. **XML Syntax**: Verify the XML file is valid and properly formatted
4. **Permissions**: Ensure you have write access to the Houdini preferences directory

### Import Errors

```python
# Test Python imports in Houdini:
import sys
print(sys.path)

# Add backend path manually if needed:
sys.path.insert(0, "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
```

### Export Failures

1. **Library Path**: Verify `/net/library/atlaslib/3D/` exists and is writable
2. **Node Context**: Ensure all selected nodes are in the same network level
3. **Python Console**: Check Houdini's Python console for detailed error messages
4. **File Permissions**: Verify write access to the export destination

### Network Path Issues

For network paths, ensure:

- Network drives are properly mounted
- Path accessibility from Houdini's Python environment
- Proper escaping of path separators on Windows

## Customization

### Modifying Categories

Edit the subcategory list in `right_click_collapse.py`:

```python
subcategories = ["Props", "Characters", "Environments", "Vehicles", 
                "Architecture", "Furniture", "Weapons", "Organic", 
                "Hard_Surface", "FX", "General", "YourCustomCategory"]
```

### Changing Library Path

Modify the library root in `houdiniae.py`:

```python
self.library_root = Path("/your/custom/library/path/3D")
```

### Menu Customization

Edit `MainMenuCommon.xml` to:
- Change menu labels
- Add additional options
- Modify keyboard shortcuts
- Customize menu organization

## Integration with Existing Workflows

### Shelf Tools

The right-click menu complements existing shelf tools. You can continue using shelf buttons for other Atlas operations while using the right-click menu for node collapse workflows.

### Pipeline Integration

The system integrates with:
- Asset management systems
- Version control workflows
- Automated build processes
- Studio pipeline tools

## Future Enhancements

Planned features:
- **Asset Browser**: Right-click "Load Atlas Asset" will open a visual asset browser
- **Version Management**: Enhanced versioning with diff capabilities  
- **Collaborative Features**: Multi-user asset development workflows
- **Cloud Integration**: Support for cloud-based asset libraries
- **AI Integration**: Automated tagging and categorization

---

## Support

For issues or questions:

1. Check the Houdini Python console for error messages
2. Verify file paths and permissions
3. Test Python imports manually
4. Check the troubleshooting section above

The system provides comprehensive error handling and user feedback to help diagnose and resolve issues quickly.