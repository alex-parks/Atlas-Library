#!/usr/bin/env python3
"""
Test BGEO sequence pattern mapping logic
"""

def test_pattern_mapping_logic():
    """Test the pattern mapping creation and usage"""
    
    print("🧪 TESTING BGEO PATTERN MAPPING LOGIC")
    print("=" * 50)
    
    # Simulate the pattern mapping creation (from _process_bgeo_sequence)
    parm_value = "/net/general/dev_alex.parks_1.1/vfx/asset/Library/lookdev/work/houdini/cache/geo/LibraryExport/${OS}/v001/Library_LibraryExport_v001.${F4}.bgeo.sc"
    node_name = "BEGO_Squence"
    
    print(f"📄 Original parameter value: {parm_value}")
    print(f"🎯 Node name: {node_name}")
    print()
    
    # Create pattern mapping (as done in the code)
    library_pattern_path = f"Geometry/bgeo/{node_name}/{parm_value.split('/')[-1]}"
    
    print(f"✨ Pattern mapping created:")
    print(f"   Original: {parm_value}")
    print(f"   Library:  {library_pattern_path}")
    print()
    
    # Simulate the asset folder path conversion
    asset_folder = "/net/library/atlaslib/3D/Assets/BlacksmithAssets/TEST123456"
    full_library_path = f"{asset_folder}/{library_pattern_path}"
    
    print(f"🏠 Asset folder: {asset_folder}")
    print(f"📍 Full library path: {full_library_path}")
    print()
    
    # Test path mappings dictionary (as built in build_path_mappings_from_copied_files)
    path_mappings = {parm_value: full_library_path}
    
    print("🗂️ Path mappings dictionary:")
    for original, library in path_mappings.items():
        print(f"   '{original}'")
        print(f"   → '{library}'")
    print()
    
    # Test parameter remapping logic
    print("🔄 PARAMETER REMAPPING TEST:")
    print("=" * 30)
    
    # Simulate what would happen in update_node_parameters_with_library_paths
    test_unexpanded_values = [
        parm_value,  # This should match
        "/some/other/path/${F4}.bgeo.sc",  # This should not match
        "/net/general/dev_alex.parks_1.1/vfx/asset/Library/lookdev/work/houdini/cache/geo/LibraryExport/BEGO_Squence/v001/Library_LibraryExport_v001.1001.bgeo.sc"  # Expanded version, should not match
    ]
    
    for i, test_value in enumerate(test_unexpanded_values, 1):
        print(f"Test {i}: {test_value}")
        if test_value in path_mappings:
            mapped_path = path_mappings[test_value]
            print(f"   ✅ MATCH! Would remap to: {mapped_path}")
        else:
            print(f"   ❌ No match in path_mappings")
        print()
    
    # Verify the final expected result
    print("🎯 EXPECTED RESULT:")
    print("=" * 20)
    expected_result = f"{asset_folder}/Geometry/bgeo/{node_name}/Library_LibraryExport_v001.${{F4}}.bgeo.sc"
    print(f"The Houdini parameter should be remapped to:")
    print(f"   {expected_result}")
    print()
    print("This preserves the frame variable ${F4} but points to the library location!")

if __name__ == "__main__":
    test_pattern_mapping_logic()