#!/usr/bin/env python3
"""
Test Auto-Insert Functionality
=============================

Test the complete workflow from metadata.json creation to ArangoDB insertion.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def create_test_metadata():
    """Create a test metadata.json file"""
    
    test_asset_folder = Path("/tmp/test_asset_export")
    test_asset_folder.mkdir(exist_ok=True)
    
    # Create test metadata matching Houdini export format
    test_metadata = {
        "id": "TEST001",
        "name": "Test Pig Asset",
        "asset_type": "Assets",
        "subcategory": "Characters",
        "render_engine": "Redshift",
        "created_by": "test_user",
        "created_at": datetime.now().isoformat(),
        "template_file": "/tmp/test_asset_export/Data/template.hipnc",
        "source_hip_file": "/path/to/source.hip",
        "houdini_version": "20.0.547",
        "export_context": "template_export",
        "export_time": datetime.now().isoformat(),
        "description": "Test pig character asset for ArangoDB integration",
        "tags": ["test", "character", "pig", "demo"],
        "asset_folder": str(test_asset_folder),
        "metadata_file": str(test_asset_folder / "metadata.json"),
        "file_sizes": {
            "template": 1024,
            "textures": 2048,
            "total": 3072
        },
        "dependencies": {
            "textures": ["pig_diffuse.jpg", "pig_normal.jpg"],
            "geometry": ["pig_mesh.usd"]
        }
    }
    
    # Write metadata file
    metadata_file = test_asset_folder / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(test_metadata, f, indent=2)
    
    print(f"✅ Created test metadata: {metadata_file}")
    return str(metadata_file)

def test_auto_insert():
    """Test the auto-insert functionality"""
    
    print("🧪 TESTING AUTO-INSERT WORKFLOW")
    print("=" * 50)
    
    try:
        # Create test metadata
        metadata_file = create_test_metadata()
        
        # Test the auto-insert function
        from backend.assetlibrary._3D.auto_arango_insert import auto_insert_on_export
        
        print(f"\n🚀 Testing auto-insert with: {metadata_file}")
        success = auto_insert_on_export(metadata_file)
        
        if success:
            print("✅ Auto-insert test PASSED!")
            
            # Test API endpoint to verify data is accessible
            print("\n🔍 Testing API endpoint...")
            from backend.assetlibrary.database.arango_queries import AssetQueries
            from backend.assetlibrary.config import BlacksmithAtlasConfig
            
            environment = 'development'
            arango_config = BlacksmithAtlasConfig.get_database_config(environment)
            queries = AssetQueries(arango_config)
            
            # Search for our test asset
            results = queries.search_assets(search_term="Test Pig")
            if results:
                print(f"✅ Found {len(results)} matching assets in database")
                for asset in results:
                    print(f"   - {asset.get('name', 'Unknown')} ({asset.get('_key', 'No key')})")
            else:
                print("⚠️ No matching assets found in database")
            
            # Get statistics
            stats = queries.get_asset_statistics()
            print(f"\n📊 Database Statistics:")
            print(f"   Total assets: {stats.get('total_assets', 0)}")
            print(f"   Total size: {stats.get('total_size_gb', 0):.2f} GB")
            
        else:
            print("❌ Auto-insert test FAILED!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_compatibility():
    """Test that the data structure is compatible with frontend expectations"""
    
    print("\n🖥️ TESTING FRONTEND COMPATIBILITY")
    print("=" * 40)
    
    try:
        from backend.api.assets import get_asset_queries, convert_asset_to_response
        
        asset_queries = get_asset_queries()
        if not asset_queries:
            print("❌ Database connection failed")
            return False
        
        # Get recent assets
        recent_assets = asset_queries.get_recent_assets(limit=5)
        print(f"📋 Found {len(recent_assets)} recent assets")
        
        if recent_assets:
            # Test conversion to frontend format
            for asset_data in recent_assets[:2]:  # Test first 2
                try:
                    frontend_asset = convert_asset_to_response(asset_data)
                    print(f"✅ Converted asset: {frontend_asset.name}")
                    print(f"   ID: {frontend_asset.id}")
                    print(f"   Category: {frontend_asset.category}")
                    print(f"   Type: {frontend_asset.asset_type}")
                except Exception as e:
                    print(f"❌ Conversion failed for {asset_data.get('name', 'Unknown')}: {e}")
                    return False
        
        print("✅ Frontend compatibility test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Frontend compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    
    print("🧪 BLACKSMITH ATLAS - AUTO-INSERT TESTING")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Auto-insert functionality
    if not test_auto_insert():
        all_passed = False
    
    # Test 2: Frontend compatibility
    if not test_frontend_compatibility():
        all_passed = False
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 20)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n💡 Ready for production use:")
        print("   1. Houdini exports will auto-insert into Asset_Library collection")
        print("   2. Frontend will display assets from ArangoDB")
        print("   3. Sync workflow is fully automated")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the error messages above for details")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)