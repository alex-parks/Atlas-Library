# Blacksmith Atlas HDA - Import by Name Setup Guide
## 🎯 Complete Parameter Configuration

### 📋 Required HDA Parameters

#### Import Section
Add these parameters to your HDA's parameter interface:

```
FOLDER: "Import Asset"
├── STRING: "import_name" 
│   ├── Label: "Asset Name"
│   ├── Help: "Type asset name or ID (e.g., DEA80B867493_Helicopter)"
│   ├── Callback Script: hou.phm().on_import_name_changed()
│   └── Callback Language: Python
│
├── BUTTON: "import_button"
│   ├── Label: "Import Asset"
│   ├── Help: "Import and reconstruct the asset"
│   ├── Callback Script: hou.phm().import_asset()
│   └── Callback Language: Python
│
└── BUTTON: "search_button" (Optional)
    ├── Label: "Search Assets"
    ├── Help: "Search for matching assets"
    ├── Callback Script: hou.phm().search_assets_by_pattern()
    └── Callback Language: Python
```

### 🔧 Callback Functions Setup

Add these functions to your HDA's PyModule (they're already in the provided code):

```python
# Main import function
def import_asset()              # Imports asset by name or path
def on_import_name_changed()    # Validates name as user types
def search_assets_by_pattern()  # Shows matching assets
def validate_import_name()      # Internal validation
def find_asset_by_name()        # Internal search function
```

### 🎯 User Workflow

#### Step 1: Type Asset Name
User types in the `import_name` field:
- `DEA80B867493_Helicopter` (full folder name)
- `Helicopter` (asset name only)  
- `DEA80B867493` (ID only)
- `heli` (partial match, case-insensitive)

#### Step 2: Automatic Validation
As the user types, the system:
- Searches the Atlas library automatically
- Prints validation results to Houdini console
- Shows asset details when found
- Provides feedback for asset search

#### Step 3: Import Asset
User clicks "Import Asset" button:
- System loads reconstruction data
- Executes appropriate construction script
- Creates geometry node: `{AssetName}_Import`
- Creates material library: `{AssetName}_MatLib`
- Rebuilds complete material networks

### 📁 Asset Search Logic

The system searches for assets in this priority:

1. **Exact folder name match**: `DEA80B867493_Helicopter`
2. **Contains search term**: `Helicopter` → finds `DEA80B867493_Helicopter`
3. **Starts with search term**: `DEA8` → finds `DEA80B867493_Helicopter`
4. **Case-insensitive matching**: `helicopter` → finds `DEA80B867493_Helicopter`

### 🎨 Real-time Feedback

The interface provides immediate feedback in the Houdini console:

```
# User types: "DEA80B867493_Helicopter"
# Console output:
🔍 Validating asset name: DEA80B867493_Helicopter
✅ Asset found: Helicopter (DEA80B867493)
   📁 Location: /net/library/atlaslib/Assets/Props/DEA80B867493_Helicopter
   🎨 Engine: Redshift
   🎭 Materials: 2
   📂 Category: Props
```

### 🔍 Search Feature

The "Search Assets" button shows all matching assets:
- Lists assets containing the search term
- Shows asset details (name, ID, category, engine)
- Provides exact folder names for copy/paste

### ⚡ Quick Setup Checklist

- [ ] Add `import_name` string parameter with callback
- [ ] Add `import_button` button with callback
- [ ] Add `search_button` button with callback (optional)
- [ ] Place provided PyModule code in HDA PyModule section
- [ ] Test with asset name: `DEA80B867493_Helicopter`

### 🎉 Expected Results

When working correctly:
1. User types asset name → instant validation in console
2. Console shows asset found with details
3. Import button creates perfect reconstruction

### 🔧 Troubleshooting

**Asset not found?**
- Check Atlas library exists: `/net/library/atlaslib/Assets/`
- Verify reconstruction data exists: `{AssetFolder}/Data/reconstruction_data.json`
- Try partial names: `Heli` instead of full name

**Validation not updating?**
- Verify callback is set: `hou.phm().on_import_name_changed()`
- Check PyModule code is in place
- Check Houdini console for validation feedback
- Ensure parameter name is exactly `import_name`

**Import fails?**
- Check construction script exists: `Construction_{RenderingEngine}.py`
- Verify file permissions on Atlas library
- Check Houdini console for error details

---

🎯 **Your import by name system is now ready! Users can simply type `DEA80B867493_Helicopter` and the system will automatically find and import the asset with complete material reconstruction.**
