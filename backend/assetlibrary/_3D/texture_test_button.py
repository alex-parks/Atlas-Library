# Texture Copying Test Button
# Add this as a shelf button to test texture detection

import sys
import importlib
from pathlib import Path

# Add backend path
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/_3D")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Force reload the module to pick up changes
try:
    import test_texture_copying
    importlib.reload(test_texture_copying)
    print("🔄 Reloaded test_texture_copying module")
except:
    import test_texture_copying
    print("📦 Imported test_texture_copying module")

# Run the test
test_texture_copying.test_texture_copying()
