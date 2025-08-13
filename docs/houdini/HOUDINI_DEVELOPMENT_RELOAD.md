# Houdini Development - Module Reloading

## Quick Reload Commands

When developing Atlas scripts, paste these into Houdini's Python console to reload modules without restarting:

### Basic Reload
```python
import sys
import importlib
from pathlib import Path

# Add backend path if needed
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Reload Atlas modules
modules_to_reload = [
    'assetlibrary._3D.collapse_to_atlas_script',
    'assetlibrary._3D.right_click_collapse', 
    'assetlibrary._3D.houdiniae'
]

for module_name in modules_to_reload:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f"🔄 Reloaded: {module_name}")

print("✅ All Atlas modules reloaded!")
```

### One-Liner Reload
```python
import sys, importlib; [importlib.reload(sys.modules[m]) for m in ['assetlibrary._3D.collapse_to_atlas_script', 'assetlibrary._3D.right_click_collapse', 'assetlibrary._3D.houdiniae'] if m in sys.modules]; print("✅ Reloaded!")
```

### Create a Shelf Tool for Quick Reload

1. **Create a new shelf tool** in Houdini
2. **Set the label** to "🔄 Reload Atlas"
3. **Paste this script**:

```python
import sys
import importlib
from pathlib import Path

backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

modules = [
    'assetlibrary._3D.collapse_to_atlas_script',
    'assetlibrary._3D.right_click_collapse', 
    'assetlibrary._3D.houdiniae',
    'assetlibrary._3D'
]

for module_name in modules:
    if module_name in sys.modules:
        try:
            importlib.reload(sys.modules[module_name])
            print(f"🔄 Reloaded: {module_name}")
        except Exception as e:
            print(f"⚠️ Failed to reload {module_name}: {e}")

print("✅ Atlas module reload complete!")
hou.ui.displayMessage("Atlas modules reloaded successfully!", title="Atlas Reload")
```

## Alternative: Modify Scripts for Auto-Reload

The right-click menu has been updated to automatically reload modules, so now when you:

1. **Make changes** to your Python files
2. **Right-click** → "🏭 Collapse to Atlas Asset" 
3. **Modules are automatically reloaded** before execution

You'll see reload messages in the console like:
```
🔄 Reloaded: assetlibrary._3D.collapse_to_atlas_script
🔄 Reloaded: assetlibrary._3D.right_click_collapse
🔄 Reloaded: assetlibrary._3D.houdiniae
```

## File Monitoring (Advanced)

For even more automatic reloading, you could set up a file watcher, but the above methods should work well for development!

## Pro Tips

- **Use the shelf tool** for quick manual reloads during development
- **The right-click menu** now auto-reloads, so just use it normally
- **Watch the console** to see which modules are being reloaded
- **Clear Python console** if you get import conflicts: `import sys; sys.modules.clear()`