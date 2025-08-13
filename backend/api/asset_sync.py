# backend/api/asset_sync.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from pathlib import Path
import os
import json
import logging
from datetime import datetime
from backend.assetlibrary.config import BlacksmithAtlasConfig
from backend.assetlibrary.database.arango_queries import AssetQueries
from backend.assetlibrary.database.graph_parser import AtlasGraphParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

def get_asset_queries():
    """Get AssetQueries instance"""
    try:
        environment = os.getenv('ATLAS_ENV', 'development')
        arango_config = BlacksmithAtlasConfig.get_database_config(environment)
        return AssetQueries(arango_config)
    except Exception as e:
        logger.error(f"Failed to get asset queries: {e}")
        return None

def _process_single_asset(asset_dir: Path, asset_id: str, asset_name: str, category_name: str, assets: List[Dict]):
    """Process a single asset directory and add to assets list"""
    # Look for metadata.json or reconstruction_data.json (Houdini export)
    metadata_file = asset_dir / "metadata.json"
    houdini_data_file = asset_dir / "Data" / "reconstruction_data.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                asset_data = {
                    '_key': asset_id,
                    'name': metadata.get('name', asset_name),
                    'category': metadata.get('category', category_name),
                    'asset_type': '3D',
                    'description': metadata.get('description', ''),
                    'tags': metadata.get('tags', []),
                    'created_by': metadata.get('created_by', 'system'),
                    'created_at': metadata.get('created_at', datetime.now().isoformat()),
                    'paths': metadata.get('paths', {}),
                    'file_sizes': metadata.get('file_sizes', {}),
                    'metadata': metadata.get('metadata', {}),
                    'asset_folder': str(asset_dir)
                }
                assets.append(asset_data)
                logger.info(f"Found asset with metadata: {asset_name} in {category_name}")
        except Exception as e:
            logger.error(f"Failed to read metadata for {asset_dir}: {e}")
    elif houdini_data_file.exists():
        try:
            with open(houdini_data_file, 'r') as f:
                houdini_data = json.load(f)
                
                # Parse Houdini export data
                asset_data = {
                    '_key': asset_id,
                    'name': houdini_data.get('asset_name', asset_name),
                    'category': houdini_data.get('subcategory', category_name),
                    'asset_type': '3D',
                    'description': f'Houdini {houdini_data.get("rendering_engine", "Redshift")} asset',
                    'tags': [
                        'houdini',
                        houdini_data.get('rendering_engine', 'redshift').lower(),
                        houdini_data.get('subcategory', category_name).lower()
                    ],
                    'created_by': 'houdini',
                    'created_at': houdini_data.get('creation_timestamp', datetime.now().isoformat()),
                    'version': houdini_data.get('version', '1.0'),
                    'houdini_version': houdini_data.get('export_metadata', {}).get('houdini_version', 'unknown'),
                    'paths': {
                        'asset_folder': str(asset_dir),
                        'data_folder': str(asset_dir / 'Data'),
                        'reconstruction_data': str(houdini_data_file)
                    },
                    'geometry_files': houdini_data.get('geometry_files', {}),
                    'material_network': houdini_data.get('material_network', {}),
                    'export_metadata': houdini_data.get('export_metadata', {}),
                    'file_sizes': {},
                    'metadata': {
                        'source': 'houdini_export',
                        'rendering_engine': houdini_data.get('rendering_engine'),
                        'total_materials': houdini_data.get('export_metadata', {}).get('total_materials', 0),
                        'total_textures': houdini_data.get('export_metadata', {}).get('total_textures', 0),
                        'export_node': houdini_data.get('export_metadata', {}).get('export_node')
                    },
                    'asset_folder': str(asset_dir)
                }
                
                # Check for geometry files
                if 'geometry_files' in houdini_data:
                    for file_type, file_path in houdini_data['geometry_files'].items():
                        if Path(file_path).exists():
                            asset_data['paths'][f'geometry_{file_type}'] = file_path
                            asset_data['file_sizes'][f'geometry_{file_type}'] = Path(file_path).stat().st_size
                
                # Check for textures
                model_folder = asset_dir / "Model"
                textures_folder = asset_dir / "Textures"
                if model_folder.exists():
                    asset_data['paths']['model_folder'] = str(model_folder)
                if textures_folder.exists():
                    asset_data['paths']['textures_folder'] = str(textures_folder)
                    
                assets.append(asset_data)
                logger.info(f"Found Houdini asset: {asset_name} (v{asset_data.get('version')}) in {category_name}")
        except Exception as e:
            logger.error(f"Failed to read Houdini reconstruction data for {asset_dir}: {e}")
    else:
        # Create basic asset data from directory structure
        asset_data = {
            '_key': asset_id,
            'name': asset_name,
            'category': category_name,
            'asset_type': '3D',
            'description': f'{category_name} asset',
            'tags': [category_name.lower()],
            'created_by': 'system',
            'created_at': datetime.now().isoformat(),
            'paths': {
                'asset_folder': str(asset_dir)
            },
            'file_sizes': {},
            'metadata': {},
            'asset_folder': str(asset_dir)
        }
        
        # Check for common files
        template_file = asset_dir / "Data" / "template.hipnc"
        if template_file.exists():
            asset_data['paths']['template'] = str(template_file)
            asset_data['file_sizes']['template'] = template_file.stat().st_size
        
        # Check for thumbnail
        for thumb_name in ['thumbnail.png', 'thumbnail.jpg', 'preview.png']:
            thumb_file = asset_dir / thumb_name
            if thumb_file.exists():
                asset_data['paths']['thumbnail'] = str(thumb_file)
                break
        
        assets.append(asset_data)
        logger.info(f"Found asset without metadata: {asset_name} in {category_name}")

def scan_asset_directory(base_path: Path) -> List[Dict]:
    """Recursively scan directory for all metadata.json files"""
    assets = []
    
    logger.info(f"Recursively scanning for all metadata.json files in: {base_path}")
    
    # Recursively find all metadata.json files
    metadata_files = []
    for metadata_file in base_path.rglob("metadata.json"):
        metadata_files.append(metadata_file)
    
    logger.info(f"Found {len(metadata_files)} metadata.json files")
    
    for metadata_file in metadata_files:
        asset_dir = metadata_file.parent
        logger.info(f"Processing metadata file: {metadata_file}")
        
        # Try to extract asset ID and name from folder structure
        folder_name = asset_dir.name
        if '_' in folder_name:
            asset_id, asset_name = folder_name.split('_', 1)
        else:
            # Use folder name as both ID and name if no underscore
            asset_id = folder_name
            asset_name = folder_name
        
        # Determine category from path structure
        category = "Unknown"
        path_parts = asset_dir.parts
        
        # Look for common category indicators in the path
        for part in reversed(path_parts):
            if part in ['Props', 'Characters', 'Environments', 'Vehicles', 'Effects', 'Materials', 'Textures']:
                category = part
                break
        
        # Process the asset
        _process_single_asset(asset_dir, asset_id, asset_name, category, assets)
    
    return assets

@router.post("/sync")
async def sync_assets():
    """Sync assets from file system to database"""
    try:
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Get asset library path
        asset_path = BlacksmithAtlasConfig.BASE_LIBRARY_PATH
        logger.info(f"Syncing assets from: {asset_path}")
        
        # Scan for assets
        found_assets = scan_asset_directory(asset_path)
        logger.info(f"Found {len(found_assets)} assets in file system")
        
        # Get existing assets from database
        existing_assets = asset_queries.search_assets("", None, None)
        existing_keys = {asset.get('_key') for asset in existing_assets}
        
        # Find assets in DB that are NOT in the file system (for cleanup)
        found_asset_keys = {asset['_key'] for asset in found_assets}
        orphaned_assets = []
        
        logger.info(f"Found asset keys in file system: {found_asset_keys}")
        logger.info(f"Assets in database: {[asset.get('_key') for asset in existing_assets]}")
        
        for existing_asset in existing_assets:
            existing_key = existing_asset.get('_key')
            if existing_key not in found_asset_keys:
                # This asset is in DB but not found in file system
                orphaned_assets.append(existing_key)
                logger.info(f"Detected orphaned asset: {existing_key} (not in file system)")
        
        # Remove orphaned assets (not in library anymore)
        removed_assets = 0
        logger.info(f"Orphaned assets to remove: {orphaned_assets}")
        
        for orphaned_key in orphaned_assets:
            try:
                asset_queries.assets.delete({'_key': orphaned_key})
                removed_assets += 1
                logger.info(f"Successfully removed orphaned asset: {orphaned_key}")
            except Exception as e:
                logger.error(f"Failed to remove orphaned asset {orphaned_key}: {e}")
        
        if removed_assets > 0:
            logger.info(f"Total orphaned assets removed: {removed_assets}")
        
        # Import new assets
        new_assets = 0
        updated_assets = 0
        
        for asset_data in found_assets:
            asset_key = asset_data['_key']
            
            if asset_key not in existing_keys:
                # Insert new asset
                try:
                    asset_queries.assets.insert(asset_data)
                    new_assets += 1
                    logger.info(f"Added new asset: {asset_data['name']}")
                except Exception as e:
                    logger.error(f"Failed to insert asset {asset_key}: {e}")
            else:
                # Update existing asset (optional)
                updated_assets += 1
        
        return {
            "status": "success",
            "found_assets": len(found_assets),
            "new_assets": new_assets,
            "updated_assets": updated_assets,
            "removed_assets": removed_assets,
            "existing_assets": len(existing_assets) - removed_assets,
            "message": f"Sync complete: {new_assets} new assets added, {removed_assets} orphaned assets removed"
        }
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/sync/preview")
async def preview_sync():
    """Preview what would be synced without actually syncing"""
    try:
        # Get asset library path
        asset_path = BlacksmithAtlasConfig.BASE_LIBRARY_PATH
        
        # Scan for assets
        found_assets = scan_asset_directory(asset_path)
        
        # Get existing assets from database
        asset_queries = get_asset_queries()
        if asset_queries:
            existing_assets = asset_queries.search_assets("", None, None)
            existing_keys = {asset.get('_key') for asset in existing_assets}
        else:
            existing_keys = set()
        
        # Categorize assets
        new_assets = []
        existing_in_db = []
        
        for asset in found_assets:
            if asset['_key'] in existing_keys:
                existing_in_db.append({
                    'id': asset['_key'],
                    'name': asset['name'],
                    'category': asset['category'],
                    'path': asset['asset_folder']
                })
            else:
                new_assets.append({
                    'id': asset['_key'],
                    'name': asset['name'],
                    'category': asset['category'],
                    'path': asset['asset_folder']
                })
        
        return {
            "asset_path": str(asset_path),
            "total_found": len(found_assets),
            "new_assets": new_assets,
            "existing_in_db": existing_in_db,
            "would_add": len(new_assets)
        }
        
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.delete("/asset/{asset_id}")
async def delete_asset(asset_id: str):
    """Delete a specific asset from the database"""
    try:
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Check if asset exists
        existing_assets = asset_queries.search_assets("", None, None)
        asset_exists = any(asset.get('_key') == asset_id for asset in existing_assets)
        
        if not asset_exists:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        # Delete the asset
        asset_queries.assets.delete({'_key': asset_id})
        logger.info(f"Deleted asset: {asset_id}")
        
        return {
            "status": "success",
            "message": f"Asset {asset_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/sync-graph")
async def sync_assets_with_graph():
    """Sync assets using advanced ArangoDB graph relationships"""
    try:
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Initialize graph parser
        graph_parser = AtlasGraphParser(asset_queries.db)
        
        # Get asset library path
        asset_path = BlacksmithAtlasConfig.BASE_LIBRARY_PATH
        logger.info(f"Graph syncing assets from: {asset_path}")
        
        # Find all metadata.json files
        metadata_files = []
        for metadata_file in asset_path.rglob("metadata.json"):
            metadata_files.append(metadata_file)
        
        logger.info(f"Found {len(metadata_files)} metadata.json files for graph parsing")
        
        total_stats = {
            'assets_processed': 0,
            'documents_inserted': 0,
            'relationships_inserted': 0,
            'errors': []
        }
        
        # Process each metadata file
        for metadata_file in metadata_files:
            try:
                logger.info(f"Processing metadata file: {metadata_file}")
                
                # Parse metadata into graph structure
                parsed_data = graph_parser.parse_asset_metadata(metadata_file)
                
                # Insert into database
                stats = graph_parser.insert_parsed_data(parsed_data)
                
                total_stats['assets_processed'] += 1
                total_stats['documents_inserted'] += stats['documents_inserted']
                total_stats['relationships_inserted'] += stats['relationships_inserted']
                total_stats['errors'].extend(stats['errors'])
                
                logger.info(f"Processed {metadata_file.name}: {stats['documents_inserted']} docs, {stats['relationships_inserted']} relationships")
                
            except Exception as e:
                error_msg = f"Failed to process {metadata_file}: {e}"
                total_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        return {
            "status": "success",
            "sync_type": "graph",
            "assets_processed": total_stats['assets_processed'],
            "documents_inserted": total_stats['documents_inserted'],
            "relationships_inserted": total_stats['relationships_inserted'],
            "errors": total_stats['errors'][:10],  # Limit error messages
            "message": f"Graph sync complete: {total_stats['assets_processed']} assets processed, "
                      f"{total_stats['documents_inserted']} documents, "
                      f"{total_stats['relationships_inserted']} relationships created"
        }
        
    except Exception as e:
        logger.error(f"Graph sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph sync failed: {str(e)}")

@router.get("/graph-stats")
async def get_graph_statistics():
    """Get ArangoDB graph statistics"""
    try:
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        db = asset_queries.db
        
        # Query collection counts
        collection_stats = {}
        collections = ['Asset_Library', 'textures', 'materials', 'geometry', 'projects', 'users']
        edge_collections = ['asset_uses_texture', 'asset_has_material', 'material_uses_texture', 
                          'asset_uses_geometry', 'project_contains_asset', 'user_created_asset']
        
        for collection_name in collections:
            try:
                collection = db.collection(collection_name)
                if collection:
                    collection_stats[collection_name] = collection.count()
                else:
                    collection_stats[collection_name] = 0
            except:
                collection_stats[collection_name] = 0
        
        relationship_stats = {}
        for edge_collection_name in edge_collections:
            try:
                collection = db.collection(edge_collection_name)
                if collection:
                    relationship_stats[edge_collection_name] = collection.count()
                else:
                    relationship_stats[edge_collection_name] = 0
            except:
                relationship_stats[edge_collection_name] = 0
        
        # Advanced graph queries
        try:
            # Most connected assets
            most_connected_query = """
            FOR asset IN Asset_Library
                LET texture_count = LENGTH(FOR v IN OUTBOUND asset asset_uses_texture RETURN 1)
                LET material_count = LENGTH(FOR v IN OUTBOUND asset asset_has_material RETURN 1)
                LET geometry_count = LENGTH(FOR v IN OUTBOUND asset asset_uses_geometry RETURN 1)
                LET total_connections = texture_count + material_count + geometry_count
                SORT total_connections DESC
                LIMIT 5
                RETURN {
                    asset: asset.name,
                    textures: texture_count,
                    materials: material_count,
                    geometry: geometry_count,
                    total: total_connections
                }
            """
            most_connected = list(db.aql.execute(most_connected_query))
        except:
            most_connected = []
        
        return {
            "status": "success",
            "collection_counts": collection_stats,
            "relationship_counts": relationship_stats,
            "total_documents": sum(collection_stats.values()),
            "total_relationships": sum(relationship_stats.values()),
            "most_connected_assets": most_connected,
            "graph_enabled": True
        }
        
    except Exception as e:
        logger.error(f"Graph stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph stats failed: {str(e)}")

@router.post("/clean-orphans")
async def clean_orphan_assets():
    """Remove assets from database whose paths don't exist in the file system"""
    try:
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Get all assets from database
        existing_assets = asset_queries.search_assets("", None, None)
        removed_count = 0
        removed_assets = []
        
        for asset in existing_assets:
            asset_folder = asset.get('paths', {}).get('asset_folder', '') or asset.get('asset_folder', '')
            
            if asset_folder:
                # Check if the asset folder actually exists
                asset_path = Path(asset_folder)
                if not asset_path.exists():
                    try:
                        asset_queries.assets.delete({'_key': asset.get('_key')})
                        removed_count += 1
                        removed_assets.append({
                            'id': asset.get('_key'),
                            'name': asset.get('name'),
                            'path': asset_folder
                        })
                        logger.info(f"Removed orphaned asset: {asset.get('name')} (path not found: {asset_folder})")
                    except Exception as e:
                        logger.error(f"Failed to remove asset {asset.get('_key')}: {e}")
        
        return {
            "status": "success",
            "removed_count": removed_count,
            "removed_assets": removed_assets,
            "message": f"Removed {removed_count} orphaned assets"
        }
        
    except Exception as e:
        logger.error(f"Clean orphans failed: {e}")
        raise HTTPException(status_code=500, detail=f"Clean orphans failed: {str(e)}")