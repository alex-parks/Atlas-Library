"""
Atlas Clipboard System - Demo & Test Script

This script demonstrates the complete Atlas Copy/Paste workflow and
provides testing functions to validate the system.

Run this script in Houdini to test the Atlas clipboard functionality.
"""

import hou
import os
import tempfile

def demo_atlas_clipboard_workflow():
    """
    Complete demonstration of Atlas Copy/Paste workflow
    """
    print("=" * 60)
    print("ATLAS CLIPBOARD SYSTEM DEMO")
    print("=" * 60)
    
    try:
        # Step 1: Create some test nodes
        print("\n1. Creating test nodes...")
        
        obj_context = hou.node('/obj')
        
        # Create a geometry object
        geo_node = obj_context.createNode('geo', 'demo_atlas_asset')
        
        # Add some SOP nodes inside
        box = geo_node.createNode('box')
        mountain = geo_node.createNode('mountain')
        material = geo_node.createNode('material')
        
        # Connect them
        mountain.setInput(0, box)
        material.setInput(0, mountain)
        
        # Set some parameters
        box.parm('sizex').set(2.0)
        box.parm('sizey').set(1.5)
        box.parm('sizez').set(3.0)
        
        mountain.parm('height').set(0.2)
        mountain.parm('rough').set(0.8)
        
        # Set display flag
        material.setDisplayFlag(True)
        
        # Layout nodes
        box.setPosition([0, 0])
        mountain.setPosition([2, 0])
        material.setPosition([4, 0])
        
        print(f"   Created test asset with {len(geo_node.children())} SOP nodes")
        
        # Step 2: Test Atlas Copy
        print("\n2. Testing Atlas Copy...")
        
        # Import the Atlas clipboard system
        from atlas_clipboard_system import AtlasClipboardCopy, AtlasClipboardPaste
        
        # Create copier
        copier = AtlasClipboardCopy()
        
        # Test copy (with encryption)
        nodes_to_copy = [geo_node]
        asset_name = "DemoAsset_Test"
        subcategory = "Props"
        
        copy_string = copier.atlas_copy(
            nodes=nodes_to_copy,
            asset_name=asset_name,
            subcategory=subcategory,
            use_encryption=True  # Test encryption
        )
        
        print(f"   Atlas Copy successful!")
        print(f"   Copy string: {copy_string}")
        
        # Step 3: Verify asset was created in library
        print("\n3. Verifying asset in library...")
        
        # Parse copy string to get asset info
        paster = AtlasClipboardPaste()
        parsed_name, parsed_uid, identifier, encryption_key = paster.parse_copy_string(copy_string)
        
        print(f"   Parsed asset name: {parsed_name}")
        print(f"   Parsed UID: {parsed_uid}")
        print(f"   Encryption key: {'Present' if encryption_key else 'None'}")
        
        # Find asset in library
        asset_path, found_subcategory = paster.find_asset_in_library(parsed_name, parsed_uid)
        print(f"   Found asset at: {asset_path}")
        print(f"   Subcategory: {found_subcategory}")
        
        # Check files exist
        templates_path = os.path.join(asset_path, "templates")
        template_file = os.path.join(templates_path, f"{parsed_name}_clipboard.hip")
        metadata_file = os.path.join(templates_path, f"{parsed_name}_clipboard.json")
        
        print(f"   Template file exists: {os.path.exists(template_file)}")
        print(f"   Metadata file exists: {os.path.exists(metadata_file)}")
        
        # Step 4: Test different context (simulate different scene)
        print("\n4. Testing Atlas Paste...")
        
        # Delete original nodes to simulate clean scene
        geo_node.destroy()
        print("   Deleted original nodes")
        
        # Perform Atlas Paste
        pasted_nodes = paster.atlas_paste(copy_string)
        
        print(f"   Atlas Paste successful!")
        print(f"   Imported {len(pasted_nodes)} nodes")
        
        for node in pasted_nodes:
            print(f"     - {node.name()} ({node.type().name()})")
        
        # Step 5: Verify node structure
        print("\n5. Verifying pasted node structure...")
        
        if pasted_nodes:
            pasted_geo = pasted_nodes[0]
            if pasted_geo.type().name() == 'geo':
                sop_children = pasted_geo.children()
                print(f"   Pasted geo has {len(sop_children)} child nodes:")
                for child in sop_children:
                    print(f"     - {child.name()} ({child.type().name()})")
                    
                    # Check some parameters
                    if child.type().name() == 'box':
                        sizex = child.parm('sizex').eval()
                        print(f"       sizex parameter: {sizex}")
        
        # Step 6: Test copy string manipulation
        print("\n6. Testing copy string utilities...")
        
        # Test clipboard functions
        hou.ui.copyTextToClipboard(copy_string)
        print("   Copy string placed in clipboard")
        
        retrieved_text = hou.ui.getTextFromClipboard()
        print(f"   Retrieved from clipboard: {retrieved_text == copy_string}")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\nDEMO FAILED: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_copy_string_parsing():
    """Test copy string parsing with various formats"""
    print("\n" + "=" * 40)
    print("TESTING COPY STRING PARSING")
    print("=" * 40)
    
    from atlas_clipboard_system import AtlasClipboardPaste
    paster = AtlasClipboardPaste()
    
    test_cases = [
        "AtlasAsset_Helicopter_DEA80B867493",
        "AtlasAsset_Helicopter_DEA80B867493!x9K2mP1s",
        "AtlasAsset_Complex_Asset_Name_ABC123DEF456",
        "AtlasAsset_Simple_123ABC",
        "AtlasAsset_Test_Asset_XYZ789!encryptionkey123"
    ]
    
    for i, test_string in enumerate(test_cases, 1):
        try:
            asset_name, uid, identifier, key = paster.parse_copy_string(test_string)
            print(f"{i}. ✓ {test_string}")
            print(f"   Asset: {asset_name}, UID: {uid}, Key: {key}")
        except Exception as e:
            print(f"{i}. ✗ {test_string}")
            print(f"   Error: {e}")
    
    print("Parsing tests completed.")


def test_encryption_system():
    """Test the encryption/decryption system"""
    print("\n" + "=" * 40)
    print("TESTING ENCRYPTION SYSTEM")
    print("=" * 40)
    
    try:
        from atlas_clipboard_system import AtlasClipboardCopy, AtlasClipboardPaste
        
        # Test data
        test_data = b"This is test data for encryption testing!"
        test_key = "testkey123456789"  # 16 chars
        
        # Test encryption
        copier = AtlasClipboardCopy()
        encrypted_data = copier.encrypt_data(test_data, test_key)
        
        print(f"Original data length: {len(test_data)}")
        print(f"Encrypted data length: {len(encrypted_data)}")
        print(f"Encryption successful: {len(encrypted_data) > len(test_data)}")
        
        # Test decryption
        paster = AtlasClipboardPaste()
        decrypted_data = paster.decrypt_data(encrypted_data, test_key)
        
        print(f"Decrypted data length: {len(decrypted_data)}")
        print(f"Decryption successful: {decrypted_data == test_data}")
        
        if decrypted_data == test_data:
            print("✓ Encryption/Decryption system working correctly")
        else:
            print("✗ Encryption/Decryption system failed")
            
    except Exception as e:
        print(f"✗ Encryption test failed: {e}")


def cleanup_demo_assets():
    """Clean up demo assets from library"""
    print("\n" + "=" * 40)
    print("CLEANING UP DEMO ASSETS")
    print("=" * 40)
    
    library_root = "/net/library/atlaslib/3D/Assets"
    demo_patterns = ["DemoAsset", "Test", "ClipboardAsset"]
    
    import shutil
    import glob
    
    for subcategory in ["Props", "Environments", "Characters", "Vehicles"]:
        subcategory_path = os.path.join(library_root, subcategory)
        if not os.path.exists(subcategory_path):
            continue
            
        for pattern in demo_patterns:
            pattern_path = os.path.join(subcategory_path, f"*{pattern}*")
            matching_dirs = glob.glob(pattern_path)
            
            for dir_path in matching_dirs:
                if os.path.isdir(dir_path):
                    try:
                        shutil.rmtree(dir_path)
                        print(f"   Removed: {os.path.basename(dir_path)}")
                    except Exception as e:
                        print(f"   Failed to remove {dir_path}: {e}")
    
    print("Cleanup completed.")


if __name__ == "__main__":
    print("Atlas Clipboard System - Demo Script")
    print("Choose an option:")
    print("1. Run full demo workflow")
    print("2. Test copy string parsing")
    print("3. Test encryption system")
    print("4. Clean up demo assets")
    
    # For now, just run the full demo
    print("\nRunning full demo workflow...")
    
    # Test individual components first
    test_copy_string_parsing()
    test_encryption_system()
    
    # Run main demo
    demo_atlas_clipboard_workflow()
    
    print("\nDemo script completed.")
