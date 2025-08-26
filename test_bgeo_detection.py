#!/usr/bin/env python3
"""Test BGEO sequence detection logic"""

import sys
from pathlib import Path

# Test the improved BGEO detection logic
def test_bgeo_detection():
    test_files = [
        "Library_LibraryExport_v001.${F4}.bgeo.sc",
        "test_file.1001.bgeo.sc",
        "sequence.${F}.bgeo",
        "single_file.bgeo.sc",
        "not_bgeo.abc"
    ]
    
    print("Testing BGEO file detection:")
    for filename in test_files:
        # Test the improved detection logic
        filename_lower = filename.lower()
        is_bgeo = (filename_lower.endswith('.bgeo') or 
                   filename_lower.endswith('.bgeo.sc'))
        
        # Test for sequence variables
        frame_vars = ['${F4}', '${F}', '${FF}', '$F4', '$F']
        has_frame_var = any(var in filename for var in frame_vars)
        
        print(f"  File: {filename}")
        print(f"    Is BGEO: {is_bgeo}")
        print(f"    Has frame var: {has_frame_var}")
        print(f"    -> {'BGEO SEQUENCE' if is_bgeo and has_frame_var else 'INDIVIDUAL BGEO' if is_bgeo else 'NOT BGEO'}")
        print()

if __name__ == "__main__":
    test_bgeo_detection()