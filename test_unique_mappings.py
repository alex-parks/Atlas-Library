#!/usr/bin/env python3
"""
Test that individual files and pattern mappings have unique original_path values
"""

def test_unique_original_paths():
    """Test that sequence files and pattern mappings don't conflict"""
    
    print("🧪 TESTING UNIQUE ORIGINAL PATHS")
    print("=" * 40)
    
    # Simulate the sequence detection
    parm_value = "/net/general/.../LibraryExport/${OS}/v001/Library_LibraryExport_v001.${F4}.bgeo.sc"
    node_name = "BEGO_Squence"
    
    # Simulated sequence files that were found on disk
    sequence_files = [
        "/net/general/.../LibraryExport/BEGO_Squence/v001/Library_LibraryExport_v001.1001.bgeo.sc",
        "/net/general/.../LibraryExport/BEGO_Squence/v001/Library_LibraryExport_v001.1002.bgeo.sc",
        "/net/general/.../LibraryExport/BEGO_Squence/v001/Library_LibraryExport_v001.1100.bgeo.sc"
    ]
    
    print(f"📄 Pattern parameter: {parm_value}")
    print(f"📁 Found {len(sequence_files)} sequence files")
    print()
    
    # Simulate the NEW logic - individual files use actual paths
    geometry_info = []
    
    print("📋 Individual sequence files:")
    for seq_file in sequence_files:
        info = {
            'file': seq_file,
            'original_path': seq_file,  # NEW: Use actual file path
            'is_pattern_mapping': False
        }
        geometry_info.append(info)
        print(f"   File: {seq_file.split('/')[-1]}")
        print(f"   original_path: {info['original_path'].split('/')[-1]}")
        print()
    
    # Pattern mapping uses the pattern
    print("🔗 Pattern mapping:")
    library_pattern_path = f"Geometry/bgeo/{node_name}/{parm_value.split('/')[-1]}"
    pattern_info = {
        'file': parm_value,
        'original_path': parm_value,  # Pattern with frame variables
        'library_path': library_pattern_path,
        'is_pattern_mapping': True
    }
    geometry_info.append(pattern_info)
    print(f"   original_path: {pattern_info['original_path'].split('/')[-1]}")
    print(f"   library_path: {pattern_info['library_path']}")
    print()
    
    # Test path mappings building
    print("🗂️ BUILDING PATH MAPPINGS:")
    print("=" * 30)
    
    mappings = {}
    asset_folder = "/net/library/atlaslib/3D/Assets/BlacksmithAssets/TEST123"
    
    for geo_info in geometry_info:
        original_path = geo_info.get('original_path')
        library_path = geo_info.get('library_path')
        is_pattern = geo_info.get('is_pattern_mapping', False)
        
        if original_path and library_path:
            full_library_path = f"{asset_folder}/{library_path}"
            mappings[original_path] = full_library_path
            
            if is_pattern:
                print(f"🔗 Pattern mapping:")
                print(f"   {original_path.split('/')[-1]}")
                print(f"   → {full_library_path.split('/')[-1]}")
                if "${F4}" in full_library_path:
                    print("   ✅ Frame variable preserved!")
                else:
                    print("   ❌ Frame variable LOST!")
            else:
                print(f"📄 Individual file mapping:")
                print(f"   {original_path.split('/')[-1]}")
                print(f"   → (no library_path set yet)")
        elif original_path:
            print(f"📄 Individual file (no library_path yet):")
            print(f"   {original_path.split('/')[-1]}")
            print(f"   → (will be set during copying)")
        print()
    
    print(f"📊 SUMMARY:")
    print(f"   Total mappings: {len(mappings)}")
    pattern_mappings = [k for k in mappings.keys() if "${F4}" in k]
    print(f"   Pattern mappings: {len(pattern_mappings)}")
    print(f"   Individual file mappings: {len(mappings) - len(pattern_mappings)}")
    
    if pattern_mappings:
        pattern_key = pattern_mappings[0]
        pattern_value = mappings[pattern_key]
        if "${F4}" in pattern_value:
            print("🎉 SUCCESS: Pattern mapping preserved frame variables!")
        else:
            print("❌ FAILED: Pattern mapping lost frame variables!")

if __name__ == "__main__":
    test_unique_original_paths()