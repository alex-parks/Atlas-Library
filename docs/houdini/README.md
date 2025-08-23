# Blacksmith Atlas 3D Module

**Template-Based Asset Management for Houdini**

This folder contains the core files for the Blacksmith Atlas template-based 3D asset system.

## 📁 Files

### Core System Files
- **`houdiniae.py`** - Main module containing `TemplateAssetExporter` and `TemplateAssetImporter` classes
- **`shelf_create_atlas_asset.py`** - Shelf tool for creating Atlas assets from selected nodes (modern approach)
- **`__init__.py`** - Python package initialization

### Documentation & Examples  
- **`demo_template_workflow.py`** - Demonstration script showing template workflow
- **`README.md`** - This file

## 🎯 Key Approach

This system uses Houdini's native `saveChildrenToFile()` and `loadChildrenFromFile()` methods for perfect asset reconstruction, completely replacing the previous complex JSON-based approach.

## 🚀 Usage

### Export Asset as Template
```python
from assetlibrary._3D.houdiniae import TemplateAssetExporter

exporter = TemplateAssetExporter("MyAsset", "Props", "Description")
success = exporter.export_as_template(parent_node, nodes_to_export)
```

### Import Asset from Template  
```python
from assetlibrary._3D.houdiniae import TemplateAssetImporter

importer = TemplateAssetImporter()
success = importer.import_from_template("/path/to/template.hip", parent_node)
```

### Simple Template Operations
```python
import hou
from assetlibrary._3D.houdiniae import save_template, load_template

# Save nodes as template
matnet = hou.node("/obj/matnet1")
save_template(matnet, "/tmp/my_template.hip")

# Load template 
new_context = hou.node("/obj")
load_template(new_context, "/tmp/my_template.hip")
```

## 📋 Benefits

- ✅ **Perfect Reconstruction**: Uses Houdini's proven serialization
- ✅ **Extreme Simplicity**: Export/import in one line each  
- ✅ **Universal Compatibility**: Works with any Houdini nodes
- ✅ **Reliability**: No more broken reconstructions
- ✅ **Future-Proof**: No version compatibility issues

---
*Total file count: 4 files (down from 20+ research/analysis files)*
