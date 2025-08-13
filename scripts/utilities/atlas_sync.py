#!/usr/bin/env python3
"""
Atlas Asset Sync Utility
========================

Standalone utility for synchronizing Blacksmith Atlas assets between
filesystem and ArangoDB database. Can be run manually or scheduled.

Usage:
    python atlas_sync.py                    # Full bidirectional sync
    python atlas_sync.py --add-only         # Only add new assets
    python atlas_sync.py --remove-orphans   # Only remove deleted assets
    python atlas_sync.py --check-only       # Dry run - show what would change
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to Python path
script_dir = Path(__file__).parent
backend_path = script_dir.parent / "backend"
sys.path.insert(0, str(backend_path))


def main():
    parser = argparse.ArgumentParser(description="Blacksmith Atlas Asset Sync Utility")
    parser.add_argument("--add-only", action="store_true", help="Only add new assets to database")
    parser.add_argument("--remove-orphans", action="store_true", help="Only remove orphaned assets from database")
    parser.add_argument("--check-only", action="store_true", help="Dry run - show what would change")
    parser.add_argument("--environment", default="development", help="Environment (development/production)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🏭 BLACKSMITH ATLAS - ASSET SYNC UTILITY")
    print("=" * 50)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Environment: {args.environment}")
    print()
    
    try:
        # Import collection manager
        from assetlibrary.database.arango_collection_manager import get_collection_manager
        
        # Get collection manager
        manager = get_collection_manager(args.environment)
        
        if not manager.is_connected():
            print("❌ Database connection failed!")
            print("   Check if ArangoDB is running and accessible")
            return 1
        
        print("✅ Database connection successful")
        print()
        
        if args.check_only:
            print("🔍 DRY RUN - Checking what would change...")
            
            # Get current state
            filesystem_assets = manager.scan_filesystem_assets()
            database_assets = manager.get_database_assets()
            
            filesystem_ids = set(filesystem_assets.keys())
            database_ids = set(database_assets.keys())
            
            assets_to_add = filesystem_ids - database_ids
            assets_to_remove = database_ids - filesystem_ids
            assets_to_check = filesystem_ids & database_ids
            
            print(f"📊 SYNC ANALYSIS:")
            print(f"   📁 Filesystem assets: {len(filesystem_assets)}")
            print(f"   🗄️ Database assets: {len(database_assets)}")
            print(f"   ➕ Would add to database: {len(assets_to_add)}")
            print(f"   ➖ Would remove from database: {len(assets_to_remove)}")
            print(f"   🔍 Would check for updates: {len(assets_to_check)}")
            
            if assets_to_add:
                print(f"\n   ASSETS TO ADD:")
                for asset_id in sorted(list(assets_to_add)[:10]):  # Show first 10
                    asset = filesystem_assets[asset_id]
                    print(f"      ➕ {asset['name']} ({asset['asset_type']}/{asset['category']})")
                if len(assets_to_add) > 10:
                    print(f"      ... and {len(assets_to_add) - 10} more")
            
            if assets_to_remove:
                print(f"\n   ASSETS TO REMOVE:")
                for asset_id in sorted(list(assets_to_remove)[:10]):  # Show first 10
                    asset = database_assets[asset_id]
                    print(f"      ➖ {asset.get('name', 'Unknown')} (ID: {asset_id})")
                if len(assets_to_remove) > 10:
                    print(f"      ... and {len(assets_to_remove) - 10} more")
            
            print(f"\n💡 To perform actual sync, run without --check-only")
            
        elif args.add_only:
            print("➕ ADD-ONLY MODE - Adding new assets to database...")
            
            filesystem_assets = manager.scan_filesystem_assets()
            database_assets = manager.get_database_assets()
            
            assets_to_add = set(filesystem_assets.keys()) - set(database_assets.keys())
            
            print(f"   Found {len(assets_to_add)} new assets to add...")
            
            added_count = 0
            for asset_id in assets_to_add:
                asset_data = filesystem_assets[asset_id]
                if manager.add_asset_to_database(asset_data):
                    added_count += 1
                    print(f"   ✅ Added: {asset_data['name']}")
                else:
                    print(f"   ❌ Failed: {asset_data['name']}")
            
            print(f"\n📊 RESULTS: {added_count}/{len(assets_to_add)} assets added successfully")
            
        elif args.remove_orphans:
            print("➖ REMOVE-ORPHANS MODE - Removing deleted assets from database...")
            
            filesystem_assets = manager.scan_filesystem_assets()
            database_assets = manager.get_database_assets()
            
            assets_to_remove = set(database_assets.keys()) - set(filesystem_assets.keys())
            
            print(f"   Found {len(assets_to_remove)} orphaned assets to remove...")
            
            removed_count = 0
            for asset_id in assets_to_remove:
                asset_data = database_assets[asset_id]
                asset_name = asset_data.get('name', 'Unknown')
                if manager.remove_asset_from_database(asset_id, asset_name):
                    removed_count += 1
                    print(f"   ✅ Removed: {asset_name}")
                else:
                    print(f"   ❌ Failed: {asset_name}")
            
            print(f"\n📊 RESULTS: {removed_count}/{len(assets_to_remove)} assets removed successfully")
            
        else:
            print("🔄 FULL BIDIRECTIONAL SYNC - Synchronizing all changes...")
            
            # Perform full sync
            stats = manager.full_bidirectional_sync()
            
            if "error" in stats:
                print(f"❌ Sync failed: {stats['error']}")
                return 1
            
            print(f"\n📊 SYNC COMPLETE:")
            print(f"   ➕ Assets added: {stats['assets_added']}")
            print(f"   🔄 Assets updated: {stats['assets_updated']}")
            print(f"   ➖ Assets removed: {stats['assets_removed']}")
            print(f"   ➡️ Assets unchanged: {stats['assets_unchanged']}")
            print(f"   ❌ Errors: {stats['errors']}")
            
            if stats['errors'] > 0:
                print(f"\n⚠️ Some operations failed - check logs for details")
        
        print(f"\n🏁 Sync utility completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
        
    except Exception as e:
        print(f"❌ Sync utility failed: {e}")
        import traceback
        if args.verbose:
            print(f"\nFull error traceback:")
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)