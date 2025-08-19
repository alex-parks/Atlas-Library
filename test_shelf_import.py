import sys
print("🧪 TESTING SHELF IMPORT")
print("Python path:")
for p in sys.path:
    print(f"  {p}")

# Add backend path
from pathlib import Path
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
    print(f"Added: {backend_path}")

try:
    from assetlibrary._3D.shelf_create_atlas_asset import main
    print("✅ Successfully imported shelf module")
    main()
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
