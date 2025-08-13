# Blacksmith Atlas - Permanent Shelf Installation

## Install Atlas Shelf

### Method 1: Copy Shelf File (Recommended)

1. **Copy the shelf file** to your Houdini user directory:
```bash
cp /net/dev/alex.parks/scm/int/Blacksmith-Atlas/docs/houdini_shelves/atlas.shelf /net/users/linux/alex.parks/houdini20.5/toolbar/
```

2. **Restart Houdini** (shelf files are loaded at startup)

3. **Enable the ATLAS shelf**:
   - Right-click on shelf area
   - Select "Shelves" → Check "ATLAS"

### Method 2: Manual Installation

1. **Right-click shelf area** → "New Shelf..."
2. **Name**: `ATLAS`
3. **File Name**: `atlas`
4. **Click OK**

Then add each tool individually:

#### 🏭 Create Atlas Asset
- **Right-click ATLAS shelf** → "New Tool"
- **Name**: `create_atlas_asset`
- **Label**: `🏭 Create`
- **Icon**: `MISC_python`
- **Script**: Copy from `atlas.shelf` file (Create Atlas Asset script section)

#### 📦 Import Atlas Asset  
- **Name**: `import_atlas_asset`
- **Label**: `📦 Import`
- **Icon**: `MISC_python`
- **Script**: Copy from `atlas.shelf` file (Import Atlas Asset script section)

#### 📂 Browse Library
- **Name**: `browse_atlas_library`
- **Label**: `📂 Browse`
- **Icon**: `MISC_python`
- **Script**: Copy from `atlas.shelf` file (Browse Atlas Library script section)

#### ℹ️ Info
- **Name**: `atlas_info`
- **Label**: `ℹ️ Info`
- **Icon**: `MISC_python`
- **Script**: Copy from `atlas.shelf` file (Atlas Info script section)

## Verify Installation

After restart, you should see:
- **ATLAS shelf** in shelf area
- **4 buttons**: 🏭 Create, 📦 Import, 📂 Browse, ℹ️ Info

## Atlas Shelf Tools

### 🏭 Create Atlas Asset
- **Function**: Copy selected nodes into Atlas Asset subnet
- **Usage**: Select nodes → Click button → Configure → Export
- **Features**: Preserves originals, adds export parameters

### 📦 Import Atlas Asset
- **Function**: Browse and import from Atlas library
- **Usage**: Click button → Select asset → Import
- **Location**: `/net/library/atlaslib/3D/Assets/`

### 📂 Browse Library
- **Function**: Open file browser to library location
- **Usage**: Click to explore assets manually

### ℹ️ Info  
- **Function**: Show Atlas system information
- **Usage**: Click for help and workflow info

## File Locations

### Shelf File Location
```
/net/users/linux/alex.parks/houdini20.5/toolbar/atlas.shelf
```

### Library Location
```
/net/library/atlaslib/3D/Assets/
├── Props/
├── Characters/
├── Environments/
├── Vehicles/
└── [other categories]/
```

## Development Features

Each tool automatically:
- **Clears Atlas modules** for fresh imports (no restart needed for development)
- **Uses latest code** from your Python files
- **Shows detailed console output** for debugging

## Usage Workflow

1. **Select nodes** (matnet, geometry, etc.)
2. **Click 🏭 Create** → Creates Atlas subnet with export parameters
3. **Configure parameters** in subnet (name, category, description, tags)  
4. **Click 🚀 Export Atlas Asset** button in subnet parameters
5. **Assets saved** to library with textures and metadata
6. **Click 📦 Import** to browse and import saved assets

## Troubleshooting

### Shelf Not Appearing
- Check file copied to correct location
- Restart Houdini completely
- Right-click shelf area → "Shelves" → Enable "ATLAS"

### Tools Not Working
- Check console output for error messages
- Verify backend path exists: `/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend`
- Check library path exists: `/net/library/atlaslib/3D/Assets/`

### Development Changes
- Tools auto-clear modules, so no restart needed for code changes
- Watch console for "🔄 Cleared X Atlas modules" message

The shelf uses identical logic to what the right-click menu should do!