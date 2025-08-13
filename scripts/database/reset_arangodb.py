#!/usr/bin/env python3
"""
Reset ArangoDB for Blacksmith Atlas
==================================

This script will:
1. Delete all existing collections from blacksmith_atlas database
2. Create a single Asset_Library collection
3. Set up proper indexes for performance

Usage: python reset_arangodb.py
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
script_dir = Path(__file__).parent
backend_path = script_dir.parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    print("🗄️ BLACKSMITH ATLAS - ARANGODB RESET")
    print("=" * 50)
    
    try:
        # Import ArangoDB client
        from arango import ArangoClient
        
        # Connect to ArangoDB using Docker container credentials
        client = ArangoClient(hosts=['http://localhost:8529'])
        db = client.db(
            'blacksmith_atlas',
            username='root',
            password='atlas_password'
        )
        
        print("✅ Connected to ArangoDB")
        
        # Get all existing collections
        collections = db.collections()
        collection_names = [col['name'] for col in collections if not col['name'].startswith('_')]
        
        if collection_names:
            print(f"\n🗑️ Found {len(collection_names)} existing collections:")
            for name in collection_names:
                print(f"   - {name}")
            
            # Delete all existing collections
            print(f"\n🗑️ Deleting all existing collections...")
            for name in collection_names:
                try:
                    db.delete_collection(name)
                    print(f"   ✅ Deleted: {name}")
                except Exception as e:
                    print(f"   ❌ Failed to delete {name}: {e}")
        else:
            print("\n📭 No existing collections found")
        
        # Create the Asset_Library collection
        print(f"\n📦 Creating Asset_Library collection...")
        try:
            collection = db.create_collection('Asset_Library')
            print("   ✅ Created Asset_Library collection")
            
            # Create indexes for performance
            print("   📊 Creating indexes...")
            
            # Primary search indexes
            collection.add_hash_index(fields=['name'])
            collection.add_hash_index(fields=['asset_type'])
            collection.add_hash_index(fields=['category'])
            collection.add_hash_index(fields=['render_engine'])
            collection.add_hash_index(fields=['status'])
            
            # Hierarchy indexes for frontend filtering
            collection.add_hash_index(fields=['metadata.asset_type'])
            collection.add_hash_index(fields=['metadata.subcategory'])
            collection.add_hash_index(fields=['metadata.render_engine'])
            collection.add_hash_index(fields=['hierarchy.asset_type'])
            collection.add_hash_index(fields=['hierarchy.subcategory'])
            
            # Full-text search indexes
            collection.add_fulltext_index(fields=['name'])
            collection.add_fulltext_index(fields=['description'])
            
            # Time-based indexes
            collection.add_skiplist_index(fields=['created_at'])
            collection.add_skiplist_index(fields=['updated_at'])
            
            print("   ✅ Created performance indexes")
            
            # Insert a test document to verify everything works
            test_doc = {
                "_key": "TEST_ASSET_001",
                "name": "Test Asset",
                "asset_type": "Assets",
                "category": "Test",
                "render_engine": "Redshift",
                "status": "active",
                "description": "Test asset to verify collection setup",
                "metadata": {
                    "asset_type": "Assets",
                    "subcategory": "Test",
                    "render_engine": "Redshift",
                    "created_by": "system"
                },
                "hierarchy": {
                    "dimension": "3D",
                    "asset_type": "Assets",
                    "subcategory": "Test",
                    "render_engine": "Redshift"
                },
                "tags": ["test", "setup"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
            
            result = collection.insert(test_doc)
            print(f"   ✅ Inserted test document: {result['_id']}")
            
            # Verify we can query it
            cursor = collection.find({'name': 'Test Asset'})
            test_results = list(cursor)
            if test_results:
                print(f"   ✅ Query test successful - found {len(test_results)} document(s)")
            else:
                print(f"   ⚠️ Query test failed - no documents found")
            
        except Exception as e:
            print(f"   ❌ Failed to create Asset_Library collection: {e}")
            return 1
        
        # Show final status
        print(f"\n📊 FINAL DATABASE STATUS:")
        final_collections = db.collections()
        final_names = [col['name'] for col in final_collections if not col['name'].startswith('_')]
        print(f"   Collections: {final_names}")
        print(f"   Database: blacksmith_atlas")
        print(f"   Access URL: http://localhost:8529")
        print(f"   Username: root")
        print(f"   Password: atlas_password")
        
        print(f"\n✅ ArangoDB reset complete!")
        print(f"💡 You can now use the Asset_Library collection for all assets")
        
        return 0
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)