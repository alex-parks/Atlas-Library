# Atlas Clipboard System

## Overview

The Atlas Clipboard System is a web-inspired copy/paste solution for Houdini that adapts HPasteWeb functionality to work with the Atlas asset library filesystem. Instead of using web storage services, it leverages the existing Atlas library structure to enable seamless asset sharing through simple copy strings.

## How It Works

### Atlas Copy Process
1. **Export to Library**: Selected nodes are exported to Atlas library using existing TemplateAssetExporter
2. **Template Creation**: Nodes saved as template file in `{AssetPath}/templates/` directory  
3. **Copy String Generation**: Creates identifier like `"AtlasAsset_Helicopter_DEA80B867493!encryptionkey"`
4. **Clipboard Integration**: Copy string placed in system clipboard for sharing

### Atlas Paste Process
1. **String Parsing**: Parse clipboard to extract asset name, UID, and encryption key
2. **Library Lookup**: Find asset in `/net/library/atlaslib/3D/Assets/{Subcategory}/{UID}_{AssetName}/`
3. **Template Import**: Load template file with optional decryption
4. **Path Remapping**: Use TemplateAssetImporter to remap texture/geometry paths
5. **Node Positioning**: Place imported nodes at cursor location

## Copy String Format

### Basic Format
```
AtlasAsset_{AssetName}_{UID}
```
Example: `AtlasAsset_Helicopter_DEA80B867493`

### Encrypted Format  
```
AtlasAsset_{AssetName}_{UID}!{EncryptionKey}
```
Example: `AtlasAsset_Helicopter_DEA80B867493!x9K2mP1s`

## File Structure

When an Atlas Copy is created, the following structure is generated:

```
/net/library/atlaslib/3D/Assets/{Subcategory}/{UID}_{AssetName}/
├── textures/               # Copied texture files
├── geometry/               # Copied geometry files  
├── templates/              # Clipboard system files
│   ├── {AssetName}_clipboard.hip    # Template file
│   └── {AssetName}_clipboard.json   # Metadata
└── metadata.json           # Standard Atlas metadata
```

## Key Features

### 1. Filesystem-Based Storage
- Uses Atlas library as "storage backend" instead of web services
- No external dependencies or network requirements
- Leverages existing library organization and permissions

### 2. Template-Based Serialization
- Uses Houdini's native `saveChildrenToFile`/`loadChildrenFromFile` methods
- Perfect node reconstruction with all parameters and connections
- Supports all node types including custom HDAs

### 3. Comprehensive File Handling
- Automatic texture detection and copying (including UDIM patterns)
- Geometry file detection (.abc, .fbx, .obj, .bgeo, .vdb)
- Intelligent path remapping during import

### 4. Security Features
- Optional AES encryption with random 16-character keys
- Encryption key embedded in copy string
- Data integrity verification with checksums

### 5. Context Awareness
- Automatic context detection (SOP/OBJ/etc.)
- Smart error handling for context mismatches
- Automatic geo node creation when needed

## Shelf Buttons

### Atlas Copy
- **Function**: Export selected nodes and generate copy string
- **Usage**: Select nodes → Click Atlas Copy → Enter name/subcategory → Copy string to clipboard
- **Features**: Encryption option, progress feedback, comprehensive error handling

### Atlas Paste  
- **Function**: Import asset from clipboard copy string
- **Usage**: Copy Atlas string → Navigate to target → Click Atlas Paste → Confirm import
- **Features**: Asset preview, automatic path remapping, cursor positioning

### Atlas Inspect
- **Function**: Analyze copy string without importing
- **Usage**: Copy Atlas string → Click Atlas Inspect → View asset information
- **Features**: Format validation, library lookup, encryption status

## Integration with Existing Atlas System

### Reuses Existing Components
- **TemplateAssetExporter**: For texture/geometry file processing
- **TemplateAssetImporter**: For path remapping during import
- **Library Structure**: Same folder organization and naming conventions
- **Metadata System**: Compatible with existing Atlas metadata

### Extends Current Workflow
- **Frontend Integration**: Copy strings can be generated from web UI
- **Library Management**: Assets remain fully manageable through existing tools
- **Version Compatibility**: Works with current Atlas export/import system

## Technical Implementation

### Core Classes

#### AtlasClipboardCopy
- Handles export and copy string generation
- Manages encryption and template file creation
- Integrates with existing TemplateAssetExporter

#### AtlasClipboardPaste  
- Parses copy strings and locates assets
- Handles decryption and template import
- Integrates with existing TemplateAssetImporter

### Error Handling
- **AtlasAssetNotFoundError**: Asset not in library
- **AtlasEncryptionError**: Encryption/decryption failures
- **Context validation**: Wrong node context handling
- **Format validation**: Invalid copy string detection

### Development Features
- Module reloading for development workflow
- Comprehensive logging and debug output
- Demo script for testing functionality
- Unit tests for copy string parsing

## Usage Examples

### Basic Copy/Paste
```python
# Copy selected nodes
from atlas_clipboard_system import atlas_copy_selected
copy_string = atlas_copy_selected("MyAsset", "Props")
# Result: "AtlasAsset_MyAsset_ABC123DEF456"

# Paste from clipboard
from atlas_clipboard_system import atlas_paste_from_clipboard  
nodes = atlas_paste_from_clipboard()
```

### Encrypted Copy/Paste
```python
# Create encrypted copy
copy_string = atlas_copy_selected("SecretAsset", "Props", use_encryption=True)
# Result: "AtlasAsset_SecretAsset_XYZ789!randomkey12345"

# Paste handles decryption automatically
nodes = atlas_paste_from_clipboard()  # Decrypts using embedded key
```

### Manual Operations
```python
# Advanced copy with custom options
from atlas_clipboard_system import AtlasClipboardCopy
copier = AtlasClipboardCopy()
copy_string = copier.atlas_copy(
    nodes=hou.selectedNodes(),
    asset_name="ComplexAsset", 
    subcategory="Environments",
    use_encryption=True
)

# Advanced paste with target specification
from atlas_clipboard_system import AtlasClipboardPaste
paster = AtlasClipboardPaste()
nodes = paster.atlas_paste(
    copy_string="AtlasAsset_ComplexAsset_DEF456!key123",
    target_parent=hou.node('/obj'),
    network_editor=hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
)
```

## Benefits Over HPasteWeb

### 1. Local Filesystem Storage
- No external web service dependencies
- Faster access and higher reliability
- Works in isolated/offline environments
- Better security for proprietary assets

### 2. Atlas Integration
- Seamless integration with existing library
- Maintains asset organization and metadata
- Compatible with current workflow and tools
- Leverages existing texture/geometry handling

### 3. Persistent Asset Management
- Assets remain permanently in library
- Can be managed through existing Atlas tools
- Supports versioning and metadata updates
- Integrates with web frontend for sharing

### 4. Enhanced File Handling
- Comprehensive texture detection (UDIM support)
- Geometry file handling beyond just nodes
- Intelligent path remapping system
- Maintains library organization standards

## Future Enhancements

### Planned Features
- **Version Management**: Support for multiple template versions per asset
- **Dependency Tracking**: Track and resolve asset dependencies
- **Batch Operations**: Copy/paste multiple assets simultaneously
- **Web Integration**: Generate copy strings from web frontend
- **Asset Validation**: Verify asset integrity before paste
- **Custom Metadata**: Support for additional clipboard metadata

### Integration Opportunities
- **Slack/Discord Bots**: Share copy strings through messaging
- **Database Integration**: Track copy/paste usage statistics
- **Asset Marketplace**: Enable easy asset sharing between users
- **Pipeline Tools**: Integrate with existing production pipelines

## Installation & Setup

### File Locations
```
backend/assetlibrary/_3D/
├── atlas_clipboard_system.py      # Core system
├── shelf_atlas_copy.py            # Copy shelf button
├── shelf_atlas_paste.py           # Paste shelf button  
├── atlas_clipboard_demo.py        # Demo/test script
└── atlas_clipboard_shelf.xml      # Shelf button definitions
```

### Shelf Installation
1. Copy shelf button definitions to your existing `atlas.shelf` file
2. Ensure Python modules are in Houdini's Python path
3. Test functionality with demo script

### Dependencies
- **Existing Atlas System**: Requires TemplateAssetExporter/Importer
- **PyCrypto** (optional): For encryption support
- **Houdini 16+**: For modern serialization methods

## Conclusion

The Atlas Clipboard System provides a powerful, filesystem-based alternative to web clipboard solutions, offering seamless integration with the existing Atlas library while maintaining the ease-of-use and sharing capabilities that make HPasteWeb so popular. By adapting the proven HPasteWeb workflow to work with local storage, it delivers the best of both worlds: reliable local performance with the convenience of simple copy/paste sharing.
