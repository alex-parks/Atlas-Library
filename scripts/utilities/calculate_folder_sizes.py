#!/usr/bin/env python3
"""
Calculate and update folder sizes for all assets in the database
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from arango import ArangoClient
from backend.assetlibrary.config import BlacksmithAtlasConfig


def get_folder_size(folder_path):
    """Calculate total size of a folder including all subdirectories"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    # Skip files we can't access
                    pass
    except Exception as e:
        print(f"Error calculating folder size for {folder_path}: {e}")
    
    return total_size


def update_asset_sizes():
    """Update all assets with proper folder sizes"""
    print("📊 CALCULATING ASSET FOLDER SIZES")
    print("=" * 60)
    
    try:
        # Get database connection
        environment = os.getenv('ATLAS_ENV', 'development')
        arango_config = BlacksmithAtlasConfig.get_database_config(environment)
        
        client = ArangoClient(hosts=arango_config['hosts'])
        db = client.db(
            arango_config['database'],
            username=arango_config['username'],
            password=arango_config['password']
        )
        
        # Get all assets
        query = "FOR asset IN assets RETURN asset"
        cursor = db.aql.execute(query)
        assets = list(cursor)
        
        print(f"📦 Found {len(assets)} assets to process")
        
        updated_count = 0
        
        for asset in assets:
            asset_id = asset['_key']
            asset_folder = asset.get('asset_folder', '')
            
            print(f"\n🔍 Processing: {asset.get('name', 'Unknown')} (ID: {asset_id})")
            print(f"   📁 Folder: {asset_folder}")
            
            if not asset_folder or not os.path.exists(asset_folder):
                print(f"   ❌ Folder not found or not specified")
                continue
            
            # Calculate folder size
            folder_size = get_folder_size(asset_folder)
            
            print(f"   📏 Total size: {folder_size:,} bytes ({folder_size / (1024**2):.1f} MB)")
            
            # Create detailed file sizes breakdown
            file_sizes = {
                'total_folder_size': folder_size,
                'usd': 0,
                'textures': 0,
                'fbx': 0,
                'abc': 0,
                'hip': 0,
                'other': 0
            }
            
            # Calculate individual file type sizes
            for dirpath, dirnames, filenames in os.walk(asset_folder):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        ext = filename.lower().split('.')[-1]
                        
                        if ext in ['usd', 'usda', 'usdc', 'usdz']:
                            file_sizes['usd'] += file_size
                        elif ext in ['png', 'jpg', 'jpeg', 'exr', 'tiff', 'tif', 'tx', 'rat']:
                            file_sizes['textures'] += file_size
                        elif ext == 'fbx':
                            file_sizes['fbx'] += file_size
                        elif ext == 'abc':
                            file_sizes['abc'] += file_size
                        elif ext in ['hip', 'hipnc', 'hiplc']:
                            file_sizes['hip'] += file_size
                        else:
                            file_sizes['other'] += file_size
                    except:
                        pass
            
            # Update asset in database
            update_query = """
            UPDATE @asset_id WITH {
                file_sizes: @file_sizes
            } IN assets
            RETURN NEW
            """
            
            try:
                result = db.aql.execute(update_query, bind_vars={
                    'asset_id': asset_id,
                    'file_sizes': file_sizes
                })
                
                updated_asset = list(result)[0]
                print(f"   ✅ Updated file sizes in database")
                print(f"      - USD: {file_sizes['usd'] / 1024:.1f} KB")
                print(f"      - Textures: {file_sizes['textures'] / (1024**2):.1f} MB")
                print(f"      - HIP: {file_sizes['hip'] / 1024:.1f} KB")
                updated_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to update database: {e}")
        
        print(f"\n✅ FOLDER SIZE CALCULATION COMPLETE!")
        print(f"📊 Updated {updated_count}/{len(assets)} assets with folder sizes")
        
    except Exception as e:
        print(f"❌ Error updating folder sizes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_asset_sizes()