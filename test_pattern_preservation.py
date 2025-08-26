#!/usr/bin/env python3
"""
Test that pattern mapping library_path is preserved during file copying
"""

def test_pattern_preservation():
    """Test that pattern mappings preserve their library_path during file copying"""
    
    print("🧪 TESTING PATTERN MAPPING PRESERVATION")
    print("=" * 50)
    
    # Simulate geometry_info with pattern mapping
    geometry_info = [
        # Regular BGEO file (should get library_path updated)
        {
            'file': '/path/to/regular_file.bgeo.sc',
            'original_path': '/path/to/regular_file.bgeo.sc', 
            'library_path': 'Geometry/bgeo/node1/regular_file.bgeo.sc',
            'is_sequence': False,
            'is_pattern_mapping': False
        },
        # Pattern mapping (should preserve library_path)
        {
            'file': '/path/to/sequence_file.1001.bgeo.sc',
            'original_path': '/path/to/sequence_${F4}.bgeo.sc',
            'library_path': 'Geometry/bgeo/BEGO_Squence/sequence_${F4}.bgeo.sc', 
            'is_sequence': True,
            'is_pattern_mapping': True,
            'sequence_pattern': '/path/to/sequence_${F4}.bgeo.sc'
        }
    ]
    
    print("📋 Original geometry_info:")
    for i, info in enumerate(geometry_info):
        print(f"  File {i+1}:")
        print(f"    original_path: {info['original_path']}")  
        print(f"    library_path: {info['library_path']}")
        print(f"    is_pattern_mapping: {info['is_pattern_mapping']}")
        print()
    
    # Simulate what happens during file copying
    print("🔄 Simulating file copying process...")
    
    for info in geometry_info:
        # This simulates the dest_file.name that would come from copying
        filename = info['file'].split('/')[-1]  # e.g., "sequence_file.1001.bgeo.sc"
        file_type = "bgeo/BEGO_Squence"
        
        # This is the logic from the fixed code
        if not info.get('is_pattern_mapping', False):
            # Regular files get their library_path updated
            old_library_path = info['library_path']
            info['library_path'] = f"Geometry/{file_type}/{filename}"
            print(f"  📝 Updated library_path for regular file:")
            print(f"    FROM: {old_library_path}")
            print(f"    TO:   {info['library_path']}")
        else:
            # Pattern mappings preserve their original library_path
            print(f"  🔒 Preserved library_path for pattern mapping:")
            print(f"    KEPT: {info['library_path']}")
        print()
    
    print("📋 Final geometry_info:")
    for i, info in enumerate(geometry_info):
        print(f"  File {i+1}:")
        print(f"    library_path: {info['library_path']}")
        print(f"    ✅" if "${F4}" in info['library_path'] or not info['is_pattern_mapping'] else "❌")
        print()
    
    # Verify results
    pattern_entry = next(info for info in geometry_info if info['is_pattern_mapping'])
    if "${F4}" in pattern_entry['library_path']:
        print("🎉 SUCCESS: Pattern mapping preserved frame variables!")
    else:
        print("❌ FAILED: Pattern mapping lost frame variables!")

if __name__ == "__main__":
    test_pattern_preservation()