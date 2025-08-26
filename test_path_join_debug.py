#!/usr/bin/env python3
"""
Debug path joining with frame variables
"""
from pathlib import Path

def test_path_joining():
    """Test how pathlib handles frame variables during path joining"""
    
    print("🔍 TESTING PATH JOINING WITH FRAME VARIABLES")
    print("=" * 55)
    
    # Simulate the actual values
    asset_folder = Path("/net/library/atlaslib/3D/Assets/BlacksmithAssets/03347063BAA001")
    library_path = "Geometry/bgeo/BEGO_Squence/Library_LibraryExport_v001.${F4}.bgeo.sc"
    
    print(f"Asset folder: {asset_folder}")
    print(f"Library path: {library_path}")
    print()
    
    # Test different ways of joining
    print("🧪 Testing different path joining methods:")
    
    # Method 1: pathlib / operator
    try:
        result1 = asset_folder / library_path
        print(f"1. asset_folder / library_path:")
        print(f"   Result: {result1}")
        print(f"   Type: {type(result1)}")
        print(f"   String: {str(result1)}")
    except Exception as e:
        print(f"1. ERROR with pathlib /: {e}")
    print()
    
    # Method 2: string concatenation
    result2 = f"{asset_folder}/{library_path}"
    print(f"2. f-string concatenation:")
    print(f"   Result: {result2}")
    print()
    
    # Method 3: os.path.join
    import os
    result3 = os.path.join(str(asset_folder), library_path)
    print(f"3. os.path.join:")
    print(f"   Result: {result3}")
    print()
    
    # Check if frame variables are preserved
    for i, result in enumerate([str(result1), result2, result3], 1):
        if "${F4}" in result:
            print(f"✅ Method {i}: Frame variable preserved")
        else:
            print(f"❌ Method {i}: Frame variable LOST")
    print()
    
    # Show what the paths.json mapping should look like
    print("🎯 EXPECTED MAPPING:")
    expected_old = "/net/general/dev_alex.parks_1.1/vfx/asset/Library/lookdev/work/houdini/cache/geo/LibraryExport/${OS}/v001/Library_LibraryExport_v001.${F4}.bgeo.sc"
    expected_new = str(result1)  # This should preserve ${F4}
    
    print(f"old_path: {expected_old}")
    print(f"new_path: {expected_new}")
    
    if "${F4}" in expected_new:
        print("✅ Mapping preserves frame variables!")
    else:
        print("❌ Mapping lost frame variables!")

if __name__ == "__main__":
    test_path_joining()