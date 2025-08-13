#!/usr/bin/env python3
"""
Test script to verify the Atlas Database integration is working correctly
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_database_connection():
    """Test basic database connectivity"""
    print("🔌 Testing database connection...")
    
    try:
        # Import the database service
        from assetlibrary._3D.atlas_database import get_database_service
        
        db_service = get_database_service()
        
        if db_service.is_connected():
            print("✅ Database connection successful!")
            
            # Test collections exist
            try:
                # Try to query assets collection
                collection = db_service.db.collection('assets')
                count = collection.count()
                print(f"✅ Assets collection accessible - {count} assets currently stored")
                
                return True
                
            except Exception as e:
                print(f"❌ Error accessing collections: {e}")
                return False
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database import/connection error: {e}")
        return False

def test_asset_storage():
    """Test storing a sample asset"""
    print("\n📦 Testing asset storage...")
    
    try:
        from assetlibrary._3D.atlas_database import get_database_service
        from datetime import datetime
        
        db_service = get_database_service()
        
        if not db_service.is_connected():
            print("❌ Database not connected")
            return False
        
        # Create test asset data
        test_asset = {
            "_key": "TEST_ASSET_12345",
            "_type": "Asset3D",
            "name": "Test_Cube",
            "category": "Props",
            "tags": ["test", "cube", "geometry"],
            "description": "A test cube asset for database verification",
            "created_by": "test_script",
            "status": "active",
            
            "paths": {
                "asset_folder": "/test/path/TEST_ASSET_12345_Test_Cube",
                "template": "/test/path/TEST_ASSET_12345_Test_Cube/templates/asset.hiptemplate",
                "metadata": "/test/path/TEST_ASSET_12345_Test_Cube/metadata.json"
            },
            
            "geometry": {
                "polycount": 6,
                "vertex_count": 8,
                "node_count": 1,
                "has_uvs": True,
                "has_normals": True
            },
            
            "source": {
                "application": "Houdini",
                "version": "20.0",
                "file": "/test/cube.hip"
            },
            
            "atlas_clipboard": {
                "enabled": True,
                "copy_string_available": True,
                "encryption_enabled": True
            }
        }
        
        # Store the asset
        stored_id = db_service.store_asset(test_asset)
        
        if stored_id:
            print(f"✅ Test asset stored successfully with ID: {stored_id}")
            
            # Try to retrieve it
            try:
                collection = db_service.db.collection('assets')
                retrieved = collection.get(test_asset["_key"])
                
                if retrieved:
                    print(f"✅ Test asset retrieved successfully")
                    print(f"   - Name: {retrieved.get('name', 'Unknown')}")
                    print(f"   - Category: {retrieved.get('category', 'Unknown')}")
                    print(f"   - Tags: {retrieved.get('tags', [])}")
                    
                    # Clean up - delete test asset
                    try:
                        collection.delete(test_asset["_key"])
                        print("✅ Test asset cleaned up")
                    except:
                        print("⚠️ Could not clean up test asset")
                    
                    return True
                else:
                    print("❌ Could not retrieve test asset")
                    return False
                    
            except Exception as e:
                print(f"❌ Error retrieving test asset: {e}")
                return False
        else:
            print("❌ Failed to store test asset")
            return False
            
    except Exception as e:
        print(f"❌ Asset storage test error: {e}")
        return False

def test_search_functionality():
    """Test asset search capabilities"""
    print("\n🔍 Testing search functionality...")
    
    try:
        from assetlibrary._3D.atlas_database import get_database_service
        
        db_service = get_database_service()
        
        if not db_service.is_connected():
            print("❌ Database not connected")
            return False
        
        # Search for any existing assets
        results = db_service.search_assets("*")
        
        print(f"✅ Search completed - found {len(results)} assets")
        
        # Show first few results if any
        for i, asset in enumerate(results[:3]):
            print(f"   Asset {i+1}: {asset.get('name', 'Unknown')} ({asset.get('category', 'Unknown')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Search test error: {e}")
        return False

def main():
    print("🧪 Atlas Database Integration Test")
    print("=" * 50)
    
    # Test connection
    connection_ok = test_database_connection()
    
    if connection_ok:
        # Test asset storage
        storage_ok = test_asset_storage()
        
        # Test search
        search_ok = test_search_functionality()
        
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"   Database Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
        print(f"   Asset Storage: {'✅ PASS' if storage_ok else '❌ FAIL'}")
        print(f"   Search Functionality: {'✅ PASS' if search_ok else '❌ FAIL'}")
        
        if connection_ok and storage_ok and search_ok:
            print("\n🎉 All tests passed! Database integration is working correctly.")
            print("\n📋 Next steps:")
            print("   1. Export a real asset from Houdini to test complete workflow")
            print("   2. Test Atlas Copy functionality to browse library assets")
            print("   3. Test Atlas Paste functionality to import assets")
            return True
        else:
            print("\n⚠️ Some tests failed. Check the error messages above.")
            return False
    else:
        print("\n❌ Database connection failed. Cannot proceed with other tests.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure ArangoDB container is running: docker compose ps")
        print("   2. Check database credentials in config/environments/development.env")
        print("   3. Verify ArangoDB is accessible: curl -u root:atlas_password http://localhost:8529/_api/version")
        return False

if __name__ == "__main__":
    main()
