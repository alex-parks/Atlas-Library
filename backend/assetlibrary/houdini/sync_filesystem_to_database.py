#!/usr/bin/env python3
"""
Sync Filesystem Assets to Database
=================================

This script scans the Atlas asset library filesystem and syncs all assets
to the ArangoDB database. Use this to manually sync assets that were 
exported but didn't get added to the database.

Usage:
1. From terminal: python sync_filesystem_to_database.py
2. From Houdini: exec(open('sync_filesystem_to_database.py').read())
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

def scan_asset_library():
    """Scan the Atlas asset library for all exported assets"""
    library_root = Path("/net/library/atlaslib/3D")
    
    if not library_root.exists():
        print(f"❌ Library root not found: {library_root}")
        return []
    
    print(f"🔍 Scanning asset library: {library_root}")
    
    assets_found = []
    asset_types = ["Assets", "FX", "Materials", "HDAs"]
    
    for asset_type in asset_types:
        asset_type_path = library_root / asset_type
        if not asset_type_path.exists():
            continue
            
        print(f"   📂 Scanning {asset_type}...")
        
        # Look for subcategory folders
        for subcategory_path in asset_type_path.iterdir():
            if not subcategory_path.is_dir():
                continue
                
            subcategory = subcategory_path.name
            print(f"      📋 Scanning {subcategory}...")
            
            # Look for asset folders (format: ID_AssetName)
            for asset_path in subcategory_path.iterdir():
                if not asset_path.is_dir():
                    continue
                    
                # Check if it has a metadata.json file
                metadata_file = asset_path / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            
                        asset_info = {
                            "path": asset_path,
                            "metadata": metadata,
                            "asset_type": asset_type,
                            "subcategory": subcategory,
                            "asset_id": metadata.get("asset_id", asset_path.name.split("_")[0]),
                            "name": metadata.get("name", asset_path.name),
                        }
                        assets_found.append(asset_info)
                        print(f"         ✅ Found: {asset_info['name']}")
                        
                    except Exception as e:
                        print(f"         ❌ Error reading metadata for {asset_path.name}: {e}")
                else:
                    print(f"         ⚠️ No metadata.json in {asset_path.name}")
    
    print(f"\n📊 Total assets found: {len(assets_found)}")
    return assets_found

def sync_asset_to_database(asset_info):
    """Sync a single asset to the database"""
    try:
        from assetlibrary._3D.atlas_database import get_database_service
        
        db_service = get_database_service()
        if not db_service.is_connected():
            print("❌ Database not connected")
            return False
            
        metadata = asset_info["metadata"]
        asset_path = asset_info["path"]
        
        # Prepare asset data for database
        asset_db_data = {
            "_key": asset_info["asset_id"],
            "_type": "Asset3D",
            "name": asset_info["name"],
            "asset_type": asset_info["asset_type"],
            "category": asset_info["subcategory"],
            "render_engine": metadata.get("render_engine", "Redshift"),
            "metadata": metadata,
            "tags": metadata.get("tags", []),
            "description": metadata.get("description", ""),
            "created_by": metadata.get("created_by", "unknown"),
            "status": "active",
            "created_at": metadata.get("created_at", datetime.now().isoformat()),
            
            # Frontend filtering hierarchy
            "dimension": "3D",
            "hierarchy": {
                "dimension": "3D",
                "asset_type": asset_info["asset_type"],
                "subcategory": asset_info["subcategory"],
                "render_engine": metadata.get("render_engine", "Redshift")
            },
            
            # File paths
            "paths": {
                "asset_folder": str(asset_path),
                "metadata": str(asset_path / "metadata.json"),
                "textures": str(asset_path / "Textures") if (asset_path / "Textures").exists() else None,
                "geometry": str(asset_path / "Geometry") if (asset_path / "Geometry").exists() else None
            },
            
            # Find template file
            "template_path": None
        }
        
        # Look for template file
        clipboard_folder = asset_path / "Clipboard"
        if clipboard_folder.exists():
            for template_file in clipboard_folder.glob("*_template.hip"):
                asset_db_data["template_path"] = str(template_file)
                break
        
        # Store in database
        result = db_service.store_asset(asset_db_data)
        if result:
            print(f"   ✅ Synced to database: {asset_info['name']}")
            return True
        else:
            print(f"   ❌ Failed to sync: {asset_info['name']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error syncing {asset_info['name']}: {e}")
        return False

def main():
    """Main sync function"""
    print("🔄 ATLAS FILESYSTEM TO DATABASE SYNC")
    print("=" * 50)
    
    # Test database connection first
    try:
        from assetlibrary._3D.atlas_database import get_database_service
        
        db_service = get_database_service()
        if not db_service.is_connected():
            print("❌ Database connection failed - cannot sync")
            print("   Check if ArangoDB is running and accessible")
            return
        else:
            print("✅ Database connection successful")
            
    except Exception as e:
        print(f"❌ Database service error: {e}")
        return
    
    # Scan filesystem for assets
    assets = scan_asset_library()
    
    if not assets:
        print("📭 No assets found to sync")
        return
    
    # Sync each asset
    print(f"\n🔄 Syncing {len(assets)} assets to database...")
    success_count = 0
    
    for asset_info in assets:
        print(f"🔄 Syncing: {asset_info['name']} ({asset_info['asset_type']}/{asset_info['subcategory']})")
        if sync_asset_to_database(asset_info):
            success_count += 1
    
    print(f"\n📊 SYNC COMPLETE:")
    print(f"   ✅ Successfully synced: {success_count}")
    print(f"   ❌ Failed to sync: {len(assets) - success_count}")
    print(f"   📁 Total assets: {len(assets)}")

if __name__ == "__main__":
    main()