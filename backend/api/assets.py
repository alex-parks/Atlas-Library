# backend/api/assets.py - Fixed ArangoDB integration
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import os
import logging
from backend.assetlibrary.config import BlacksmithAtlasConfig

# Setup logging for this module
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["assets"])

def get_asset_queries():
    """Get AssetQueries instance - create fresh connection each time"""
    try:
        from backend.assetlibrary.database.arango_queries import AssetQueries
        environment = os.getenv('ATLAS_ENV', 'development')
        arango_config = BlacksmithAtlasConfig.get_database_config(environment)
        logger.info(f"🔍 Creating AssetQueries with config: {arango_config}")
        queries = AssetQueries(arango_config)
        logger.info(f"✅ AssetQueries created successfully")
        return queries
    except Exception as e:
        logger.error(f"❌ Failed to get asset queries: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None

# Force reload marker

# Docker-friendly asset library base path
ASSET_LIBRARY_BASE = Path(os.getenv('ASSET_LIBRARY_PATH', '/app/assets')) / "3D"

class AssetResponse(BaseModel):
    id: str
    name: str
    category: str
    asset_type: str = "3D"
    paths: dict
    file_sizes: dict = {}
    tags: List[str] = []
    metadata: dict = {}
    created_at: str
    thumbnail_path: Optional[str] = None
    artist: Optional[str] = None
    file_format: str = "USD"
    description: str = ""
    folder_path: Optional[str] = None  # Direct path to asset folder for file manager access
    asset_folder: Optional[str] = None
    class Config:
        populate_by_name = True

class AssetCreateRequest(BaseModel):
    name: str
    category: str
    paths: dict
    metadata: dict = {}
    file_sizes: dict = {}

def find_actual_thumbnail(asset_data: dict) -> Optional[str]:
    asset_id = asset_data.get('_key', asset_data.get('id', ''))
    asset_name = asset_data.get('name', '')
    if not asset_id:
        return None
    if 'paths' in asset_data and 'thumbnail' in asset_data['paths']:
        db_thumbnail_path = asset_data['paths']['thumbnail']
        if db_thumbnail_path and Path(db_thumbnail_path).exists():
            return f"http://localhost:8000/thumbnails/{asset_id}"
    thumbnail_path = asset_data.get('thumbnail_path')
    if thumbnail_path and Path(thumbnail_path).exists():
        return f"http://localhost:8000/thumbnails/{asset_id}"
    folder_patterns = [
        ASSET_LIBRARY_BASE / f"{asset_id}_{asset_name}" / "Thumbnail",
        ASSET_LIBRARY_BASE / asset_id / "Thumbnail",
        ASSET_LIBRARY_BASE / asset_name / "Thumbnail",
    ]
    for folder in folder_patterns:
        if folder.exists() and folder.is_dir():
            for ext in ['.png', '.jpg', '.jpeg']:
                for img_file in folder.glob(f"*{ext}"):
                    return f"http://localhost:8000/thumbnails/{asset_id}"
    return None

def convert_asset_to_response(asset_data: dict) -> AssetResponse:
    thumbnail_url = find_actual_thumbnail(asset_data)
    artist = asset_data.get('metadata', {}).get('created_by', 'Unknown')
    if asset_data.get('created_by'):
        artist = asset_data['created_by']
    description = asset_data.get('metadata', {}).get('description', '')
    if not description and asset_data.get('description'):
        description = asset_data['description']
    if not description:
        description = f"{asset_data.get('category', 'General')} asset created in Houdini"
    paths = asset_data.get('paths', {})
    if not paths or all(v is None for v in paths.values()):
        paths = {
            'usd': asset_data.get('usd_path'),
            'thumbnail': asset_data.get('thumbnail_path'),
            'textures': asset_data.get('textures_path'),
            'fbx': asset_data.get('fbx_path')
        }
    
    # Create comprehensive metadata structure for frontend filtering
    metadata = asset_data.get('metadata', {})
    
    # Debug: Print asset data structure
    logger.info(f"🔍 Raw asset_data keys: {list(asset_data.keys())}")
    logger.info(f"🔍 Raw metadata: {metadata}")
    logger.info(f"🔍 Hierarchy: {asset_data.get('hierarchy', {})}")
    logger.info(f"🔍 Category: {asset_data.get('category')}")
    logger.info(f"🔍 Asset Type: {asset_data.get('asset_type')}")
    
    # Add hierarchy data from top-level fields if metadata is structured
    if isinstance(metadata, dict):
        metadata.update({
            'dimension': asset_data.get('dimension', '3D'),
            'asset_type': asset_data.get('asset_type', metadata.get('asset_type')),
            'subcategory': asset_data.get('hierarchy', {}).get('subcategory') or asset_data.get('category'),
            'render_engine': asset_data.get('render_engine')
        })
        logger.info(f"🔍 Updated metadata: {metadata}")
    
    return AssetResponse(
        id=asset_data.get('_key', asset_data.get('id', '')),
        name=asset_data.get('name', ''),
        category=asset_data.get('category', 'General'),
        asset_type=asset_data.get('asset_type', '3D'),
        paths=paths,
        file_sizes=asset_data.get('file_sizes', {}),
        tags=asset_data.get('tags', []),
        metadata=metadata,  # Now includes hierarchy data
        created_at=asset_data.get('created_at', datetime.now().isoformat()),
        thumbnail_path=thumbnail_url,
        artist=artist,
        file_format="USD",
        description=description,
        folder_path=asset_data.get('folder_path', asset_data.get('paths', {}).get('folder_path'))
    )

@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
        search: Optional[str] = Query(None, description="Search term"),
        category: Optional[str] = Query(None, description="Filter by category"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        limit: int = Query(100, description="Maximum number of results")
):
    """List all assets from ArangoDB"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        logger.error("❌ Database connection failed in list_assets")
        return []
    
    try:
        logger.info(f"🔍 Searching assets: search='{search}', category='{category}', tags={tags}")
        logger.info(f"📊 Asset queries object: {asset_queries}")
        logger.info(f"📊 DB object: {asset_queries.db if asset_queries else 'None'}")
        raw_assets = asset_queries.search_assets(
            search_term=search or "",
            category=category,
            tags=tags
        )
        logger.info(f"✅ Found {len(raw_assets)} raw assets")
        logger.info(f"📊 Raw assets data: {raw_assets}")
        
        assets = []
        for asset_data in raw_assets[:limit]:
            try:
                asset_response = convert_asset_to_response(asset_data)
                assets.append(asset_response)
                logger.info(f"✅ Converted asset: {asset_response.name}")
            except Exception as e:
                logger.error(f"❌ Failed to convert asset: {e}")
                continue
        
        logger.info(f"✅ Returning {len(assets)} assets")
        return assets
        
    except Exception as e:
        logger.error(f"❌ Error in list_assets: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")

@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        asset_data = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        return convert_asset_to_response(asset_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/assets", response_model=AssetResponse)
async def create_asset(asset_request: AssetCreateRequest):
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        import uuid
        asset_id = f"{asset_request.name}_{uuid.uuid4().hex[:8]}"
        
        # Create asset document for ArangoDB
        asset_data = {
            '_key': asset_id,
            'id': asset_id,
            'name': asset_request.name,
            'category': asset_request.category,
            'asset_type': asset_request.metadata.get('hierarchy', {}).get('asset_type', 'Assets'),
            'dimension': '3D',
            'hierarchy': asset_request.metadata.get('hierarchy', {}),
            'metadata': asset_request.metadata,
            'paths': asset_request.paths,
            'file_sizes': asset_request.file_sizes,
            'tags': asset_request.tags if hasattr(asset_request, 'tags') else [],
            'created_at': asset_request.created_at if hasattr(asset_request, 'created_at') else datetime.now().isoformat(),
            'created_by': asset_request.created_by if hasattr(asset_request, 'created_by') else 'unknown',
            'status': 'active'
        }
        
        # Use existing asset queries to insert
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Insert into ArangoDB using collection
        collection = asset_queries.db.collection('Atlas_Library')
        result = collection.insert(asset_data)
        
        logger.info(f"✅ Asset inserted with key: {result['_key']}")
        
        return convert_asset_to_response(asset_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating asset: {str(e)}")

@router.get("/assets/stats/summary")
async def get_asset_stats():
    asset_queries = get_asset_queries()
    if not asset_queries:
        return {
            "total_assets": 0,
            "by_category": {},
            "by_type": {},
            "total_size_gb": 0,
            "assets_this_week": 0,
            "note": "Database not available"
        }
    
    try:
        stats = asset_queries.get_asset_statistics()
        total_size = stats.get('total_size_bytes', 0)
        return {
            "total_assets": stats.get('total_assets', 0),
            "by_category": stats.get('by_category', {}),
            "by_type": stats.get('by_type', {}),
            "total_size_gb": round(total_size / (1024 ** 3), 2),
            "assets_this_week": stats.get('assets_this_week', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/database/status")
async def get_database_status():
    """Get detailed database status and connection information"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        return {
            "status": "disconnected",
            "active_connections": 0,
            "pool_size": 0,
            "max_connections": 0,
            "error": "Database handler not available"
        }
    
    try:
        # Get database connection info
        db_info = asset_queries.db.properties()
        collections = list(asset_queries.db.collections())
        
        return {
            "status": "connected",
            "database_name": db_info.get('name', 'blacksmith_atlas'),
            "database_id": db_info.get('id', 'unknown'),
            "collections_count": len(collections),
            "collections": [c['name'] for c in collections],
            "active_connections": 1,  # ArangoDB HTTP connection
            "pool_size": 1,
            "max_connections": 100,
            "version": db_info.get('version', 'unknown'),
            "engine": "ArangoDB Community Edition"
        }
    except Exception as e:
        return {
            "status": "error",
            "active_connections": 0,
            "pool_size": 0,
            "max_connections": 0,
            "error": str(e)
        }

@router.get("/assets/recent/{limit}")
async def get_recent_assets(limit: int = 10):
    asset_queries = get_asset_queries()
    if not asset_queries:
        return []
    
    try:
        raw_assets = asset_queries.get_recent_assets(limit=limit)
        recent_assets = []
        for asset_data in raw_assets:
            try:
                asset_response = convert_asset_to_response(asset_data)
                recent_assets.append(asset_response)
            except Exception as e:
                continue
        return recent_assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/categories")
async def get_categories():
    asset_queries = get_asset_queries()
    if not asset_queries:
        return {
            "categories": [],
            "count": 0,
            "note": "Database not available"
        }
    
    try:
        stats = asset_queries.get_asset_statistics()
        categories = [c['category'] for c in stats.get('by_category', [])]
        return {
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/debug/test-connection")
async def test_connection():
    """Test database connection and return raw data"""
    try:
        from arango import ArangoClient
        import os
        
        # Direct connection
        client = ArangoClient(hosts=f"http://{os.getenv('ARANGO_HOST', 'arangodb')}:{os.getenv('ARANGO_PORT', '8529')}")
        db = client.db(
            os.getenv('ARANGO_DATABASE', 'blacksmith_atlas'),
            username=os.getenv('ARANGO_USER', 'root'),
            password=os.getenv('ARANGO_PASSWORD', 'atlas_password')
        )
        
        # Test query
        query = "FOR asset IN Asset_Library RETURN asset"
        cursor = db.aql.execute(query)
        assets = list(cursor)
        
        return {
            "status": "success",
            "environment": os.getenv('ATLAS_ENV', 'development'),
            "host": os.getenv('ARANGO_HOST', 'arangodb'),
            "database": os.getenv('ARANGO_DATABASE', 'blacksmith_atlas'),
            "assets_count": len(assets),
            "assets": assets
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/creators")
async def get_creators():
    asset_queries = get_asset_queries()
    if not asset_queries:
        return {
            "creators": [],
            "count": 0,
            "note": "Database not available"
        }
    
    try:
        # This assumes you have a by_creator field in your stats, otherwise adjust accordingly
        stats = asset_queries.get_asset_statistics()
        creators = list(stats.get('by_creator', {}).keys()) if 'by_creator' in stats else []
        return {
            "creators": creators,
            "count": len(creators)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/assets/{asset_id}/open-folder")
async def open_asset_folder(asset_id: str):
    """Open the asset folder in the file system"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get asset data
        asset_data = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        asset_folder = asset_data.get('asset_folder')
        if not asset_folder:
            raise HTTPException(status_code=404, detail="Asset folder path not found")
        
        import subprocess
        import platform
        
        # Check if folder exists
        if not Path(asset_folder).exists():
            raise HTTPException(status_code=404, detail=f"Asset folder does not exist: {asset_folder}")
        
        # Open folder based on operating system
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.Popen(f'explorer "{asset_folder}"')
            elif system == "Darwin":  # macOS
                subprocess.Popen(['open', asset_folder])
            elif system == "Linux":
                subprocess.Popen(['xdg-open', asset_folder])
            else:
                raise HTTPException(status_code=500, detail=f"Unsupported operating system: {system}")
            
            return {
                "success": True,
                "message": f"Opened folder: {asset_folder}",
                "folder_path": asset_folder
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to open folder: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/admin/sync")
async def sync_filesystem_to_database():
    """Scan filesystem for metadata.json files and sync all assets to database"""
    import json
    import uuid
    from datetime import datetime
    
    try:
        # Asset library base path
        library_root = Path("/net/library/atlaslib/3D")
        
        if not library_root.exists():
            raise HTTPException(status_code=404, detail=f"Asset library not found: {library_root}")
        
        logger.info(f"🔄 Starting filesystem to database sync from: {library_root}")
        
        # Get database connection
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Scan for assets
        assets_found = []
        assets_synced = 0
        assets_failed = 0
        
        # Scan asset types: Assets, FX, Materials, HDAs
        asset_types = ["Assets", "FX", "Materials", "HDAs"]
        
        for asset_type in asset_types:
            asset_type_path = library_root / asset_type
            if not asset_type_path.exists():
                continue
                
            logger.info(f"📂 Scanning {asset_type}...")
            
            # Scan subcategories
            for subcategory_path in asset_type_path.iterdir():
                if not subcategory_path.is_dir():
                    continue
                    
                subcategory = subcategory_path.name
                logger.info(f"   📋 Scanning {subcategory}...")
                
                # Scan individual asset folders
                for asset_path in subcategory_path.iterdir():
                    if not asset_path.is_dir():
                        continue
                        
                    # Look for metadata.json
                    metadata_file = asset_path / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            
                            asset_id = metadata.get("asset_id", asset_path.name.split("_")[0])
                            asset_name = metadata.get("name", asset_path.name)
                            
                            # Prepare asset data for database
                            asset_db_data = {
                                "_key": asset_id,
                                "id": asset_id,
                                "name": asset_name,
                                "asset_type": asset_type,
                                "category": subcategory,
                                "render_engine": metadata.get("render_engine", "Redshift"),
                                "metadata": metadata,
                                "tags": metadata.get("tags", []),
                                "description": metadata.get("description", f"{asset_type} asset: {asset_name}"),
                                "created_by": metadata.get("created_by", "unknown"),
                                "created_at": metadata.get("created_at", datetime.now().isoformat()),
                                "status": "active",
                                
                                # Frontend filtering hierarchy
                                "dimension": "3D",
                                "hierarchy": {
                                    "dimension": "3D",
                                    "asset_type": asset_type,
                                    "subcategory": subcategory,
                                    "render_engine": metadata.get("render_engine", "Redshift")
                                },
                                
                                # File paths
                                "paths": {
                                    "asset_folder": str(asset_path),
                                    "metadata": str(metadata_file),
                                    "textures": str(asset_path / "Textures") if (asset_path / "Textures").exists() else None,
                                    "geometry": str(asset_path / "Geometry") if (asset_path / "Geometry").exists() else None,
                                    "template": None
                                },
                                
                                # Find template file
                                "file_sizes": metadata.get("file_sizes", {}),
                                "dependencies": {},
                                "copied_files": []
                            }
                            
                            # Look for template file in Clipboard folder
                            clipboard_folder = asset_path / "Clipboard"
                            if clipboard_folder.exists():
                                for template_file in clipboard_folder.glob("*_template.hip"):
                                    asset_db_data["paths"]["template"] = str(template_file)
                                    break
                            
                            # Store in database using new collection manager
                            from backend.assetlibrary.database.arango_collection_manager import get_collection_manager
                            environment = os.getenv('ATLAS_ENV', 'development')
                            collection_manager = get_collection_manager(environment)
                            
                            # Prepare data for collection manager
                            sync_asset_data = {
                                "asset_id": asset_id,
                                "name": asset_name,
                                "asset_type": asset_type,
                                "category": subcategory,
                                "path": str(asset_path),
                                "metadata_file": str(metadata_file),
                                "metadata": metadata,
                                "last_modified": metadata_file.stat().st_mtime
                            }
                            
                            success = collection_manager.add_asset_to_database(sync_asset_data)
                            if success:
                                assets_synced += 1
                                logger.info(f"      ✅ Synced: {asset_name}")
                            else:
                                assets_failed += 1
                                logger.error(f"      ❌ Failed to sync: {asset_name}")
                            
                            assets_found.append({
                                "name": asset_name,
                                "path": str(asset_path),
                                "asset_type": asset_type,
                                "subcategory": subcategory,
                                "synced": success
                            })
                            
                        except Exception as e:
                            assets_failed += 1
                            logger.error(f"      ❌ Error processing {asset_path.name}: {e}")
                            continue
        
        logger.info(f"🏁 Sync complete: {assets_synced} synced, {assets_failed} failed, {len(assets_found)} total")
        
        return {
            "success": True,
            "message": f"Sync complete: {assets_synced} assets synced, {assets_failed} failed",
            "stats": {
                "assets_found": len(assets_found),
                "assets_synced": assets_synced,
                "assets_failed": assets_failed
            },
            "assets": assets_found
        }
        
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/admin/sync-bidirectional")
async def sync_bidirectional():
    """Perform intelligent bidirectional sync between filesystem and database"""
    try:
        logger.info("🔄 Starting intelligent bidirectional sync...")
        
        # Get collection manager
        from backend.assetlibrary.database.arango_collection_manager import get_collection_manager
        environment = os.getenv('ATLAS_ENV', 'development')
        collection_manager = get_collection_manager(environment)
        
        if not collection_manager.is_connected():
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Perform full bidirectional sync
        stats = collection_manager.full_bidirectional_sync()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return {
            "success": True,
            "message": f"Bidirectional sync complete: {stats['assets_added']} added, {stats['assets_updated']} updated, {stats['assets_removed']} removed",
            "stats": stats,
            "sync_type": "bidirectional",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bidirectional sync failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Bidirectional sync failed: {str(e)}")