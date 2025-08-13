#!/usr/bin/env python3
"""
Test if Houdini export is calling auto-insert
============================================

This script will process any existing metadata.json files and attempt to insert them into ArangoDB.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def process_existing_exports():
    """Process all existing Houdini exports and insert them into ArangoDB"""
    
    print("🔍 PROCESSING EXISTING HOUDINI EXPORTS")
    print("=" * 50)
    
    # Find all metadata.json files in the atlas library
    library_root = Path("/net/library/atlaslib/3D")
    
    if not library_root.exists():
        print(f"❌ Library not found: {library_root}")
        return
    
    metadata_files = list(library_root.rglob("metadata.json"))
    print(f"📋 Found {len(metadata_files)} metadata files")
    
    if not metadata_files:
        print("❌ No metadata files found - no exports have been made")
        return
    
    # Import auto-insert functionality
    try:
        from backend.assetlibrary._3D.auto_arango_insert import auto_insert_on_export
        print("✅ Auto-insert module loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import auto-insert module: {e}")
        return
    
    # Process each metadata file
    successful_inserts = 0
    failed_inserts = 0
    
    for metadata_file in metadata_files:
        try:
            print(f"\n📁 Processing: {metadata_file.parent.name}")
            print(f"   File: {metadata_file}")
            
            # Check if file was recently modified (within last hour as a test)
            mtime = datetime.fromtimestamp(metadata_file.stat().st_mtime)
            print(f"   Modified: {mtime}")
            
            # Read and validate metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            asset_name = metadata.get('name', 'Unknown')
            asset_id = metadata.get('id', 'Unknown')
            asset_type = metadata.get('asset_type', 'Unknown')
            subcategory = metadata.get('subcategory', 'Unknown')
            
            print(f"   Asset: {asset_name} ({asset_id})")
            print(f"   Type: {asset_type}/{subcategory}")
            
            # Attempt auto-insert
            success = auto_insert_on_export(str(metadata_file))
            
            if success:
                print(f"   ✅ Successfully inserted into ArangoDB")
                successful_inserts += 1
            else:
                print(f"   ❌ Failed to insert into ArangoDB")
                failed_inserts += 1
                
        except Exception as e:
            print(f"   ❌ Error processing {metadata_file}: {e}")
            failed_inserts += 1
    
    # Summary
    print(f"\n📊 PROCESSING SUMMARY")
    print(f"   ✅ Successful inserts: {successful_inserts}")
    print(f"   ❌ Failed inserts: {failed_inserts}")
    print(f"   📁 Total processed: {len(metadata_files)}")
    
    if successful_inserts > 0:
        print(f"\n🎉 SUCCESS! Assets are now in ArangoDB")
        print(f"   Check your Asset Library frontend - you should see {successful_inserts} assets")
    else:
        print(f"\n⚠️ No assets were successfully inserted")
        print(f"   This suggests there may be a connection or configuration issue")

def check_database_connection():
    """Test database connection"""
    print("\n🔗 TESTING DATABASE CONNECTION")
    print("=" * 40)
    
    try:
        from backend.assetlibrary._3D.auto_arango_insert import get_arango_inserter
        
        inserter = get_arango_inserter()
        if inserter.is_connected():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 HOUDINI AUTO-INSERT DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Check database connection first
    if not check_database_connection():
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("   1. Make sure Docker containers are running:")
        print("      docker compose ps")
        print("   2. Check ArangoDB is accessible:")
        print("      curl http://localhost:8529/_api/version")
        print("   3. Verify credentials in docker-compose.yml")
        return 1
    
    # Process existing exports
    process_existing_exports()
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Check your Asset Library frontend at http://localhost:3011")
    print(f"   2. Try exporting a new asset from Houdini")
    print(f"   3. The new export should automatically appear in the frontend")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)