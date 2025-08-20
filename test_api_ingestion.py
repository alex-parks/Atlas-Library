#!/usr/bin/env python3
"""
Test script for the new API-based ingestion workflow
"""

import sys
import os
from pathlib import Path

# Add the backend path to sys.path
backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Add the _3D path
_3d_path = backend_path / "assetlibrary" / "_3D"
if str(_3d_path) not in sys.path:
    sys.path.insert(0, str(_3d_path))

# Import the function
from copy_to_atlas_asset import call_atlas_api_ingestion

# Test with the existing metadata.json
test_metadata_file = "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/tests/metadata.json"

print("🧪 Testing API ingestion function...")
print(f"📄 Test file: {test_metadata_file}")

if os.path.exists(test_metadata_file):
    print("✅ Test metadata file exists")
    
    # Test the function
    result = call_atlas_api_ingestion(test_metadata_file)
    
    if result:
        print("🎉 API ingestion test PASSED!")
    else:
        print("❌ API ingestion test FAILED!")
        
else:
    print("❌ Test metadata file not found!")
    print("Available files in tests directory:")
    tests_dir = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/tests")
    if tests_dir.exists():
        for f in tests_dir.iterdir():
            print(f"  - {f.name}")