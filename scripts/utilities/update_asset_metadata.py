#!/usr/bin/env python3
"""
Update existing assets in ArangoDB with proper hierarchy metadata for frontend filtering
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from arango import ArangoClient
from backend.assetlibrary.config import BlacksmithAtlasConfig


def update_asset_metadata():
    """Update existing assets with hierarchy metadata"""
    print("🔄 UPDATING ASSET METADATA FOR FRONTEND FILTERING")
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
        
        print(f"📊 Found {len(assets)} assets to update")
        
        updated_count = 0
        
        for asset in assets:
            asset_id = asset['_key']
            print(f"\n🔍 Processing asset: {asset.get('name', 'Unknown')} (ID: {asset_id})")
            
            # Extract hierarchy info from existing data
            asset_folder = asset.get('asset_folder', '')
            tags = asset.get('tags', [])
            category = asset.get('category', 'Unknown')
            
            # Determine hierarchy from folder path and tags
            dimension = "3D"  # All assets from Houdini are 3D
            asset_type = "Assets"  # Default
            subcategory = "Blacksmith Asset"  # Default
            render_engine = "Redshift"  # Default
            
            # Parse asset type and subcategory from folder path
            if '/Assets/' in asset_folder:
                asset_type = "Assets"
                if '/BlacksmithAssets/' in asset_folder:
                    subcategory = "Blacksmith Asset"
                elif '/Megascans/' in asset_folder:
                    subcategory = "Megascans"
                elif '/Kitbash/' in asset_folder:
                    subcategory = "Kitbash"
            elif '/FX/' in asset_folder:
                asset_type = "FX"
                if '/BlacksmithFX/' in asset_folder:
                    subcategory = "Blacksmith FX"
                elif '/Atmosphere/' in asset_folder:
                    subcategory = "Atmosphere"
                elif '/FLIP/' in asset_folder:
                    subcategory = "FLIP"
                elif '/Pyro/' in asset_folder:
                    subcategory = "Pyro"
            elif '/Materials/' in asset_folder:
                asset_type = "Materials"
                if '/BlacksmithMaterials/' in asset_folder:
                    subcategory = "Blacksmith Materials"
                elif '/Redshift/' in asset_folder:
                    subcategory = "Redshift"
                elif '/Karma/' in asset_folder:
                    subcategory = "Karma"
            elif '/HDAs/' in asset_folder:
                asset_type = "HDAs"
                subcategory = "Blacksmith HDAs"
            
            # Parse render engine from tags
            if 'karma' in tags:
                render_engine = "Karma"
            elif 'redshift' in tags:
                render_engine = "Redshift"
            
            # Create comprehensive metadata
            hierarchy_metadata = {
                "dimension": dimension,
                "asset_type": asset_type,
                "subcategory": subcategory,
                "render_engine": render_engine,
                "export_context": "houdini",
                "houdini_version": "20.0",  # Default
                "export_time": asset.get('created_at', ''),
                "description": asset.get('description', ''),
                "tags": tags,
                "user_metadata": ""
            }
            
            print(f"   📂 Asset Type: {asset_type}")
            print(f"   📋 Subcategory: {subcategory}")
            print(f"   🎨 Render Engine: {render_engine}")
            print(f"   📁 Folder: {asset_folder}")
            
            # Update the asset in database
            update_query = """
            UPDATE @asset_id WITH {
                metadata: @metadata,
                category: @subcategory,
                dimension: @dimension,
                asset_type: @asset_type,
                render_engine: @render_engine,
                hierarchy: {
                    dimension: @dimension,
                    asset_type: @asset_type,
                    subcategory: @subcategory
                }
            } IN assets
            RETURN NEW
            """
            
            try:
                result = db.aql.execute(update_query, bind_vars={
                    'asset_id': asset_id,
                    'metadata': hierarchy_metadata,
                    'subcategory': subcategory,
                    'dimension': dimension,
                    'asset_type': asset_type,
                    'render_engine': render_engine
                })
                
                updated_asset = list(result)[0]
                print(f"   ✅ Updated metadata successfully")
                updated_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to update: {e}")
        
        print(f"\n✅ METADATA UPDATE COMPLETE!")
        print(f"📊 Updated {updated_count}/{len(assets)} assets")
        print(f"🎯 Assets now have hierarchy metadata for frontend filtering")
        
    except Exception as e:
        print(f"❌ Error updating metadata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_asset_metadata()