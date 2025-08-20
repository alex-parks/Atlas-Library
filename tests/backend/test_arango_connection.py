#!/usr/bin/env python3
"""
Test ArangoDB Connection and Auto-Insert
=========================================

This script tests the connection to ArangoDB and tries to insert a test asset
to help debug the auto-insert issue.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_direct_connection():
    """Test direct connection to ArangoDB"""
    print("🔌 Testing direct ArangoDB connection...")
    
    try:
        from arango import ArangoClient
        
        # Get connection details from environment/config
        host = os.getenv('ARANGO_HOST', 'localhost')
        port = os.getenv('ARANGO_PORT', '8529')
        database = os.getenv('ARANGO_DATABASE', 'blacksmith_atlas')
        username = os.getenv('ARANGO_USER', 'root')
        password = os.getenv('ARANGO_PASSWORD', 'atlas_password')
        
        print(f"   Host: {host}:{port}")
        print(f"   Database: {database}")
        print(f"   User: {username}")
        
        # Create client
        client = ArangoClient(hosts=[f"http://{host}:{port}"])
        
        # Connect to database
        db = client.db(database, username=username, password=password)
        
        # Test connection
        info = db.properties()
        print(f"✅ Connected to database: {info.get('name')}")
        
        # Check for Atlas_Library collection
        if db.has_collection('Atlas_Library'):
            collection = db.collection('Atlas_Library')
            count = collection.count()
            print(f"✅ Atlas_Library collection found with {count} documents")
            
            # Show some sample documents
            if count > 0:
                print("📋 Sample documents:")
                for doc in collection.all(limit=3):
                    print(f"   • {doc.get('name', 'Unknown')} ({doc.get('asset_type', 'Unknown')})")
            
            return True, collection
        else:
            print("❌ Atlas_Library collection not found")
            return False, None
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, None

def test_config_connection():
    """Test connection using Atlas config"""
    print("\n🔧 Testing Atlas config connection...")
    
    try:
        from assetlibrary.config import BlacksmithAtlasConfig
        
        # Get config
        db_config = BlacksmithAtlasConfig.get_database_config('development')
        print(f"   Config hosts: {db_config['hosts']}")
        print(f"   Config database: {db_config['database']}")
        print(f"   Config user: {db_config['username']}")
        
        from arango import ArangoClient
        
        # Create client using config
        client = ArangoClient(hosts=db_config['hosts'])
        db = client.db(
            db_config['database'],
            username=db_config['username'],
            password=db_config['password']
        )
        
        # Test connection
        info = db.properties()
        print(f"✅ Config connection successful: {info.get('name')}")
        
        return True, db
        
    except Exception as e:
        print(f"❌ Config connection failed: {e}")
        return False, None

def test_collection_manager():
    """Test the collection manager"""
    print("\n🗄️ Testing collection manager...")
    
    try:
        from assetlibrary.database.arango_collection_manager import get_collection_manager
        
        manager = get_collection_manager('development')
        
        if manager.is_connected():
            print("✅ Collection manager connected")
            
            # Test scanning (but limit to avoid long output)
            print("🔍 Testing filesystem scan...")
            filesystem_assets = manager.scan_filesystem_assets()
            print(f"   Found {len(filesystem_assets)} assets in filesystem")
            
            print("🗄️ Testing database scan...")
            database_assets = manager.get_database_assets()
            print(f"   Found {len(database_assets)} assets in database")
            
            return True, manager
        else:
            print("❌ Collection manager not connected")
            return False, None
            
    except Exception as e:
        print(f"❌ Collection manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_auto_insert():
    """Test the auto-insert functionality"""
    print("\n🚀 Testing auto-insert functionality...")
    
    try:
        from assetlibrary._3D.auto_arango_insert import AutoArangoAssetInserter
        
        # Create test metadata
        test_metadata = {
            "id": "TEST123",
            "name": "Test_Asset_Connection",
            "asset_type": "Assets",
            "subcategory": "BlacksmithAssets",
            "render_engine": "Redshift", 
            "created_by": "test_script",
            "created_at": datetime.now().isoformat(),
            "description": "Test asset for connection verification",
            "tags": ["test", "connection"],
            "folder_path": "/test/path",
            "template_file": "test.hip",
            "source_hip_file": "test_scene.hip",
            "houdini_version": "20.0.547",
            "export_context": "/obj",
            "export_time": datetime.now().isoformat()
        }
        
        # Save test metadata to temp file
        temp_file = Path("/tmp/test_metadata.json")
        with open(temp_file, 'w') as f:
            json.dump(test_metadata, f, indent=2)
        
        print(f"📄 Created test metadata: {temp_file}")
        
        # Test inserter
        inserter = AutoArangoAssetInserter('development')
        
        if inserter.is_connected():
            print("✅ Auto-inserter connected")
            
            # Try to insert
            success = inserter.insert_asset(str(temp_file))
            
            if success:
                print("✅ Test asset inserted successfully!")
                
                # Try to find it in the database
                if inserter.asset_collection:
                    try:
                        doc = inserter.asset_collection.get("TEST123_Test_Asset_Connection")
                        if doc:
                            print(f"✅ Test asset found in database: {doc.get('name')}")
                        else:
                            print("⚠️ Test asset not found in database")
                    except:
                        print("⚠️ Could not retrieve test asset")
                
                return True
            else:
                print("❌ Test asset insertion failed")
                return False
        else:
            print("❌ Auto-inserter not connected")
            return False
            
    except Exception as e:
        print(f"❌ Auto-insert test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            temp_file.unlink()
        except:
            pass

def main():
    """Run all tests"""
    print("🧪 ARANGODB CONNECTION TEST")
    print("=" * 50)
    
    # Test 1: Direct connection
    direct_success, collection = test_direct_connection()
    
    # Test 2: Config connection
    config_success, db = test_config_connection()
    
    # Test 3: Collection manager
    manager_success, manager = test_collection_manager()
    
    # Test 4: Auto-insert
    insert_success = test_auto_insert()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"Direct Connection: {'✅' if direct_success else '❌'}")
    print(f"Config Connection: {'✅' if config_success else '❌'}")
    print(f"Collection Manager: {'✅' if manager_success else '❌'}")
    print(f"Auto-Insert: {'✅' if insert_success else '❌'}")
    
    if all([direct_success, config_success, manager_success, insert_success]):
        print("\n🎉 All tests passed! Auto-insert should work from Houdini.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
        
        # Provide solutions
        print("\n🔧 POTENTIAL SOLUTIONS:")
        if not direct_success:
            print("   • Check if ArangoDB container is running: docker ps")
            print("   • Check if ArangoDB is healthy: docker logs blacksmith-atlas-db")
            print("   • Verify connection settings in .env file")
        
        if not config_success:
            print("   • Check Atlas configuration in backend/assetlibrary/config.py")
            print("   • Verify environment variables are set correctly")
        
        if not manager_success:
            print("   • Check if collection manager imports are working")
            print("   • Verify Atlas_Library collection exists")
        
        if not insert_success:
            print("   • Check auto-insert module dependencies")
            print("   • Verify ArangoDB permissions for the user")

if __name__ == "__main__":
    main()
