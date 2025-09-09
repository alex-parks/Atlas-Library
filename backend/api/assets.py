# backend/api/assets.py - Fixed ArangoDB integration
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import os
import sys
import logging
from backend.core.config_manager import config as atlas_config

# Setup logging for this module
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["assets"])

def get_asset_queries():
    """Get AssetQueries instance - create fresh connection each time"""
    try:
        from backend.assetlibrary.database.arango_queries import AssetQueries
        environment = os.getenv('ATLAS_ENV', 'development')
        
        # Use new Atlas config for database settings
        db_config = atlas_config.get('api.database', {})
        arango_config = {
            'hosts': [f"http://{db_config.get('host', 'localhost')}:{db_config.get('port', '8529')}"],
            'database': db_config.get('name', 'blacksmith_atlas'),
            'username': db_config.get('username', 'root'),
            'password': db_config.get('password', 'atlas_password'),
            'collections': {
                'assets': 'Atlas_Library'
            }
        }
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
    variant_id: Optional[str] = None  # 2-character variant ID (AA, AB, etc.)
    variant_name: Optional[str] = None  # Human-readable variant name
    paths: dict
    file_sizes: dict = {}
    tags: List[str] = []
    metadata: dict = {}
    created_at: str
    thumbnail_path: Optional[str] = None
    thumbnail_frame: Optional[int] = None  # Frame number to show when not hovering
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
    tags: List[str] = []
    created_at: Optional[str] = None
    created_by: Optional[str] = None

def find_actual_thumbnail(asset_data: dict) -> Optional[str]:
    # Prioritize 'id' field over '_key' since 'id' has the correct format
    asset_id = asset_data.get('id', asset_data.get('_key', ''))
    asset_name = asset_data.get('name', '')
    if not asset_id:
        return None
    
    # Check existing thumbnail paths first
    if 'paths' in asset_data and 'thumbnail' in asset_data['paths']:
        db_thumbnail_path = asset_data['paths']['thumbnail']
        if db_thumbnail_path and Path(db_thumbnail_path).exists():
            return f"http://localhost:8000/thumbnails/{asset_id}"
    
    thumbnail_path = asset_data.get('thumbnail_path')
    if thumbnail_path and Path(thumbnail_path).exists():
        return f"http://localhost:8000/thumbnails/{asset_id}"
    
    # Check folder_path from metadata (most accurate path)
    folder_path = asset_data.get('folder_path')
    if folder_path:
        # Convert network path to container path if needed
        if folder_path.startswith('/net/library/atlaslib/'):
            container_folder = folder_path.replace('/net/library/atlaslib/', '/app/assets/')
            thumbnail_folder = Path(container_folder) / "Thumbnail"
        else:
            thumbnail_folder = Path(folder_path) / "Thumbnail"
        
        if thumbnail_folder.exists() and thumbnail_folder.is_dir():
            for ext in ['.png', '.jpg', '.jpeg']:
                for img_file in thumbnail_folder.glob(f"*{ext}"):
                    return f"http://localhost:8000/thumbnails/{asset_id}"
    
    # Check paths.folder_path as well
    paths_folder_path = asset_data.get('paths', {}).get('folder_path')
    if paths_folder_path and paths_folder_path != folder_path:
        if paths_folder_path.startswith('/net/library/atlaslib/'):
            container_folder = paths_folder_path.replace('/net/library/atlaslib/', '/app/assets/')
            thumbnail_folder = Path(container_folder) / "Thumbnail"
        else:
            thumbnail_folder = Path(paths_folder_path) / "Thumbnail"
        
        if thumbnail_folder.exists() and thumbnail_folder.is_dir():
            for ext in ['.png', '.jpg', '.jpeg']:
                for img_file in thumbnail_folder.glob(f"*{ext}"):
                    return f"http://localhost:8000/thumbnails/{asset_id}"
    
    # Fallback to pattern-based search
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
    logger.info(f"🔍 Created at value: {asset_data.get('created_at')} (type: {type(asset_data.get('created_at'))})")
    logger.info(f"🔍 Created by value: {asset_data.get('created_by')} (type: {type(asset_data.get('created_by'))})")
    
    # Add hierarchy data from top-level fields if metadata is structured
    if isinstance(metadata, dict):
        try:
            hierarchy = asset_data.get('hierarchy', {})
            if not isinstance(hierarchy, dict):
                logger.warning(f"⚠️ Hierarchy is not a dict: {type(hierarchy)} = {hierarchy}")
                hierarchy = {}
            
            metadata.update({
                'dimension': asset_data.get('dimension', '3D'),
                'asset_type': asset_data.get('asset_type', metadata.get('asset_type')),
                'subcategory': hierarchy.get('subcategory') or asset_data.get('category'),
                'render_engine': asset_data.get('render_engine')
            })
            logger.info(f"🔍 Updated metadata: {metadata}")
        except Exception as e:
            logger.error(f"❌ Error updating metadata: {e}")
            logger.error(f"❌ asset_data type: {type(asset_data)}")
            logger.error(f"❌ asset_data keys: {list(asset_data.keys()) if isinstance(asset_data, dict) else 'not a dict'}")
            raise
    # Extract variant information from asset ID and metadata
    # Prioritize 'id' field over '_key' since 'id' has the correct format
    asset_id = asset_data.get('id', asset_data.get('_key', ''))
    variant_id = None
    variant_name = None
    
    # Extract variant_id from asset ID (characters 11-13 in a 16-character ID)
    logger.info(f"🔍 Extracting variant info from asset_id: '{asset_id}' (length: {len(asset_id)})")
    if len(asset_id) >= 13:
        variant_id = asset_id[11:13]  # Characters 11-13 for 11-char base UID system
        logger.info(f"🔍 Extracted variant_id: '{variant_id}'")
    
    # Extract variant_name from metadata (check export_metadata first, then other locations)
    if isinstance(metadata, dict):
        variant_name = (asset_data.get('variant_name') or 
                       metadata.get('variant_name') or
                       metadata.get('export_metadata', {}).get('variant_name') or
                       asset_data.get('metadata', {}).get('variant_name') or
                       asset_data.get('metadata', {}).get('export_metadata', {}).get('variant_name'))
        logger.info(f"🔍 Extracted variant_name: '{variant_name}'")
    
    
    thumbnail_frame_value = asset_data.get('thumbnail_frame')
    
    return AssetResponse(
        id=asset_id,
        name=asset_data.get('name', ''),
        category=asset_data.get('category', 'General'),
        asset_type=asset_data.get('asset_type', '3D'),
        variant_id=variant_id,
        variant_name=variant_name,
        paths=paths,
        file_sizes=asset_data.get('file_sizes', {}),
        tags=asset_data.get('tags', []),
        metadata=metadata,  # Now includes hierarchy data
        created_at=asset_data.get('created_at') or datetime.now().isoformat(),
        thumbnail_path=thumbnail_url,
        thumbnail_frame=thumbnail_frame_value,
        artist=artist,
        file_format="USD",
        description=description,
        folder_path=asset_data.get('folder_path', asset_data.get('paths', {}).get('folder_path'))
    )

class PaginationResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

@router.get("/assets/debug/test-endpoint")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "status": "ok"}

@router.get("/assets/{asset_id}/thumbnail-frame")
async def get_thumbnail_frame(asset_id: str):
    """Get thumbnail frame for an asset"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Direct AQL query to get just the thumbnail_frame
        query = "FOR asset IN Atlas_Library FILTER asset._key == @asset_id RETURN asset.thumbnail_frame"
        cursor = asset_queries.db.aql.execute(query, bind_vars={'asset_id': asset_id})
        result = list(cursor)
        
        if not result:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"asset_id": asset_id, "thumbnail_frame": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/assets/debug/raw/{asset_id}")
async def debug_raw_asset(asset_id: str):
    """Debug endpoint to see raw asset data from database"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        return {"error": "Database not available"}
    
    try:
        result = asset_queries.get_asset_with_dependencies(asset_id)
        return {
            "raw_result": result,
            "asset_thumbnail_frame": result.get('asset', {}).get('thumbnail_frame') if result.get('asset') else None
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/assets", response_model=PaginationResponse)
async def list_assets(
        search: Optional[str] = Query(None, description="Search term"),
        category: Optional[str] = Query(None, description="Filter by category"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
        offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """List all assets from ArangoDB with pagination"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        logger.error("❌ Database connection failed in list_assets")
        return PaginationResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)
    
    try:
        logger.info(f"🔍 Searching assets: search='{search}', category='{category}', tags={tags}, limit={limit}, offset={offset}")
        
        # Get all matching assets
        raw_assets = asset_queries.search_assets(
            search_term=search or "",
            category=category,
            tags=tags
        )
        
        total_count = len(raw_assets)
        logger.info(f"✅ Found {total_count} total assets")
        
        # Apply pagination
        paginated_assets = raw_assets[offset:offset + limit]
        
        assets = []
        for asset_data in paginated_assets:
            try:
                asset_response = convert_asset_to_response(asset_data)
                assets.append(asset_response)
            except Exception as e:
                logger.error(f"❌ Failed to convert asset: {e}")
                continue
        
        has_more = (offset + limit) < total_count
        
        logger.info(f"✅ Returning {len(assets)} assets (page {offset//limit + 1})")
        
        return PaginationResponse(
            items=assets,
            total=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
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
        import re
        
        # Extract ID and name from metadata
        metadata_id = asset_request.metadata.get('id') if asset_request.metadata else None
        asset_name = asset_request.name
        
        # DEBUG: Log the received metadata_id and its properties
        logger.info(f"🔍 DEBUG: Received metadata_id = '{metadata_id}' (type: {type(metadata_id)}, length: {len(metadata_id) if metadata_id else 'None'})")
        logger.info(f"🔍 DEBUG: Asset name = '{asset_name}'")
        if asset_request.metadata:
            logger.info(f"🔍 DEBUG: Full metadata keys: {list(asset_request.metadata.keys())}")
        else:
            logger.info(f"🔍 DEBUG: No metadata provided")
        
        if metadata_id:
            # For new Houdini exports: metadata_id is just the UID (e.g., "B6A48C5B")
            # For legacy exports: metadata_id might be the full format (e.g., "B6A48C5B_atlas_asset")
            
            # New versioning system: metadata_id is the full 16-character UID 
            # Use the 16-character UID directly as both _key and id
            if len(metadata_id) == 16:
                # New 16-character UID system (11 base + 2 variant + 3 version)
                asset_key = metadata_id  # Use 16-char UID directly as _key
                asset_id = metadata_id   # Use 16-char UID as document id
                logger.info(f"🔍 DEBUG: Using 16-char UID path - asset_key = '{asset_key}', asset_id = '{asset_id}'")
            elif len(metadata_id) == 17:
                # Previous 17-character UID system (12 base + 2 variant + 3 version) - still support for existing assets
                asset_key = metadata_id  # Use 17-char UID directly as _key
                asset_id = metadata_id   # Use 17-char UID as document id
                logger.info(f"🔍 DEBUG: Using 17-char UID path - asset_key = '{asset_key}', asset_id = '{asset_id}'")
            elif len(metadata_id) == 14:
                # Previous 14-character UID system (9 base + 2 variant + 3 version) - still support for existing assets
                asset_key = metadata_id  # Use 14-char UID directly as _key
                asset_id = metadata_id   # Use 14-char UID as document id
                logger.info(f"🔍 DEBUG: Using 14-char UID path - asset_key = '{asset_key}', asset_id = '{asset_id}'")
            elif len(metadata_id) == 12:
                # Legacy 12-character UID system (9 base + 3 version) - still support for existing assets
                asset_key = metadata_id  # Use 12-char UID directly as _key
                asset_id = metadata_id   # Use 12-char UID as document id
                logger.info(f"🔍 DEBUG: Using legacy 12-char UID path - asset_key = '{asset_key}', asset_id = '{asset_id}'")
            elif '_' in metadata_id:
                # Legacy format: UID_Name
                uid_part = metadata_id.split('_')[0]
                asset_key = metadata_id  # Use full format for _key (legacy)
                asset_id = uid_part      # Use just UID for document id
                logger.info(f"🔍 DEBUG: Using legacy UID_Name path - asset_key = '{asset_key}', asset_id = '{asset_id}'")
            else:
                # Old format: just UID (use UID only for both key and ID)
                asset_key = metadata_id  # Use UID only as _key (no name suffix)
                asset_id = metadata_id   # Use UID for document id
                logger.info(f"🔍 DEBUG: Using old UID path - asset_key = '{asset_key}', asset_id = '{asset_id}'")
        else:
            # Generate new asset ID and key (use UID only, no name suffix)
            uid = uuid.uuid4().hex[:11].upper()
            asset_key = uid  # Use UID only as _key
            asset_id = uid   # Use UID as document id
            logger.info(f"🔍 DEBUG: Generated new UID - asset_key = '{asset_key}', asset_id = '{asset_id}'")
        
        # Create asset document for ArangoDB
        asset_data = {
            '_key': asset_key,
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
            'created_at': getattr(asset_request, 'created_at', None) or datetime.now().isoformat(),
            'created_by': getattr(asset_request, 'created_by', None) or 'unknown',
            'status': 'active'
        }
        
        # DEBUG: Log the final database document structure
        logger.info(f"🔍 DEBUG: Final asset_data._key = '{asset_data['_key']}'")
        logger.info(f"🔍 DEBUG: Final asset_data.id = '{asset_data['id']}'")
        logger.info(f"🔍 DEBUG: Final asset_data.name = '{asset_data['name']}'")
        logger.info(f"🔍 DEBUG: Final asset_data.category = '{asset_data['category']}'")
        
        # Use existing asset queries to insert
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Insert into ArangoDB using collection
        collection = asset_queries.db.collection('Atlas_Library')
        result = collection.insert(asset_data)
        
        logger.info(f"✅ Asset inserted with key: {result['_key']}")
        
        # Get the inserted document from database for proper response
        inserted_asset = collection.get(result['_key'])
        
        return convert_asset_to_response(inserted_asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating asset: {str(e)}")

@router.put("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, asset_request: AssetCreateRequest):
    """Full update of an asset - replaces entire document"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Check if asset exists
        collection = asset_queries.db.collection('Atlas_Library')
        if not collection.has(asset_id):
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        # Get existing asset for metadata preservation
        existing_asset = collection.get(asset_id)
        
        # Create updated asset document
        asset_data = {
            '_key': asset_id,  # Keep existing _key
            'id': asset_request.metadata.get('id') if asset_request.metadata else asset_id,
            'name': asset_request.name,
            'category': asset_request.category,
            'asset_type': asset_request.metadata.get('hierarchy', {}).get('asset_type', 'Assets'),
            'dimension': '3D',
            'hierarchy': asset_request.metadata.get('hierarchy', {}),
            'metadata': asset_request.metadata,
            'paths': asset_request.paths,
            'file_sizes': asset_request.file_sizes,
            'tags': asset_request.tags if hasattr(asset_request, 'tags') else [],
            'created_at': existing_asset.get('created_at', datetime.now().isoformat()),
            'created_by': existing_asset.get('created_by', 'unknown'),
            'updated_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Replace document in ArangoDB
        result = collection.replace(asset_id, asset_data)
        
        logger.info(f"✅ Asset {asset_id} updated successfully")
        
        return convert_asset_to_response(asset_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating asset: {str(e)}")

@router.patch("/assets/{asset_id}")
async def patch_asset(asset_id: str, asset_update: dict):
    """Partial update of an asset - updates only provided fields"""
    try:
        logger.info(f"🔍 PATCH Debug: Received PATCH request for asset {asset_id}")
        logger.info(f"🔍 PATCH Debug: Update data: {asset_update}")
        if 'thumbnail_frame' in asset_update:
            logger.info(f"🔍 PATCH Debug: thumbnail_frame in update: {asset_update['thumbnail_frame']}, type: {type(asset_update['thumbnail_frame'])}")
        
        # Get database connection
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Check if asset exists and update
        collection = asset_queries.db.collection('Atlas_Library')
        if not collection.has(asset_id):
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        # Get current asset data for comparison
        current_asset = collection.get(asset_id)
        logger.info(f"🔍 PATCH Debug: Current thumbnail_frame in DB: {current_asset.get('thumbnail_frame')}")
        
        # Add update timestamp
        asset_update['updated_at'] = datetime.now().isoformat()
        
        # Use AQL for reliable updates (collection.update has issues)
        aql_query = """
            FOR doc IN Atlas_Library
            FILTER doc._key == @asset_id
            UPDATE doc WITH @updates IN Atlas_Library
            RETURN NEW
        """
        bind_vars = {'asset_id': asset_id, 'updates': asset_update}
        
        cursor = asset_queries.db.aql.execute(aql_query, bind_vars=bind_vars)
        result_list = list(cursor)
        
        if not result_list:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found or update failed")
        
        logger.info(f"✅ Asset {asset_id} updated with fields: {list(asset_update.keys())}")
        
        return {
            "success": True,
            "message": f"Asset {asset_id} updated successfully",
            "updated_fields": list(asset_update.keys()),
            "asset_id": asset_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Error in patch_asset: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating asset: {str(e)}")

def is_safe_asset_folder(folder_path: str) -> bool:
    """
    Security check: Verify that the folder path represents a valid asset folder
    that is safe to move to TrashBin. NEVER allow deletion/moving of core folders.
    Handles both host paths (/net/library/atlaslib/...) and container paths (/app/assets/...).
    """
    import re
    from pathlib import Path
    
    if not folder_path:
        return False
    
    path = Path(folder_path).resolve()
    path_str = str(path)
    
    # Convert container path to host path for consistent security checking
    if path_str.startswith('/app/assets/'):
        # Convert container path to host path for validation using config
        host_path_str = path_str.replace('/app/assets/', f"{atlas_config.asset_library_root}/")
        logger.info(f"🔄 SECURITY: Converted container path for validation: {path_str} -> {host_path_str}")
    else:
        host_path_str = path_str
    
    # CRITICAL SECURITY: Protected folders that should NEVER be moved/deleted (host paths)
    # Get paths from Atlas configuration
    asset_lib_root = atlas_config.asset_library_root
    asset_lib_3d = atlas_config.asset_library_3d
    asset_lib_2d = atlas_config.asset_library_2d
    
    protected_folders = [
        asset_lib_root,
        asset_lib_3d, 
        asset_lib_2d,
        f"{asset_lib_3d}/Assets",
        f"{asset_lib_3d}/FX", 
        f"{asset_lib_3d}/Materials",
        f"{asset_lib_3d}/HDAs",
        f"{asset_lib_3d}/Textures",
        f"{asset_lib_3d}/HDRI",
        f"{asset_lib_2d}/Textures",
        f"{asset_lib_2d}/References", 
        f"{asset_lib_2d}/UI"
    ]
    
    # Add subcategory folders to protected list using config paths
    subcategory_patterns = [
        rf"{re.escape(asset_lib_3d)}/Assets/[^/]+$",           # e.g. /3D/Assets/BlacksmithAssets
        rf"{re.escape(asset_lib_3d)}/FX/[^/]+$",              # e.g. /3D/FX/Pyro  
        rf"{re.escape(asset_lib_3d)}/Materials/[^/]+$",       # e.g. /3D/Materials/Redshift
        rf"{re.escape(asset_lib_3d)}/HDAs/[^/]+$",            # e.g. /3D/HDAs/BlacksmithHDAs
        rf"{re.escape(asset_lib_2d)}/[^/]+/[^/]+$"            # e.g. /2D/Textures/Metals
    ]
    
    # Check exact matches against protected folders (use host path for consistency)
    for protected in protected_folders:
        if host_path_str == str(Path(protected).resolve()):
            logger.error(f"🚫 SECURITY: Attempted to delete protected folder: {host_path_str} (original: {path_str})")
            return False
    
    # Check pattern matches for subcategory folders  
    for pattern in subcategory_patterns:
        if re.match(pattern, host_path_str):
            logger.error(f"🚫 SECURITY: Attempted to delete subcategory folder: {host_path_str} (original: {path_str})")
            return False
    
    # Validate this looks like an asset folder (should contain asset ID)
    folder_name = path.name
    
    # Asset folders should match pattern: {ID}_{name} or just {ID}
    # Updated to support 14-character asset IDs (base_uid + variant_id + version)
    asset_id_pattern = r'^[A-Z0-9]{6,14}(_.*)?$'
    if not re.match(asset_id_pattern, folder_name):
        logger.error(f"🚫 SECURITY: Folder name doesn't match asset pattern: {folder_name}")
        return False
    
    # Must be within atlaslib structure (check both host and container paths)
    asset_lib_prefix = f"{atlas_config.asset_library_root}/"
    if asset_lib_prefix not in host_path_str and "/app/assets/" not in path_str:
        logger.error(f"🚫 SECURITY: Folder not within atlaslib: {path_str}")
        return False
    
    # Must be at least 4 levels deep (e.g. /atlaslib/3D/Assets/Subcategory/AssetFolder)
    if asset_lib_prefix in host_path_str:
        atlaslib_relative = host_path_str.split(asset_lib_prefix)[1]
    elif "/app/assets/" in path_str:
        atlaslib_relative = path_str.split("/app/assets/")[1]
    else:
        logger.error(f"🚫 SECURITY: Invalid path format: {path_str}")
        return False
    
    path_parts = atlaslib_relative.split("/")
    if len(path_parts) < 4:
        logger.error(f"🚫 SECURITY: Path not deep enough to be asset folder: {path_str}")
        return False
    
    logger.info(f"✅ SECURITY: Path validated as safe asset folder: {path_str} (host equivalent: {host_path_str})")
    return True

def ensure_trashbin_structure():
    """Create TrashBin folder structure if it doesn't exist"""
    # Use container path for TrashBin
    trashbin_base = Path("/app/assets/TrashBin")
    trashbin_3d = trashbin_base / "3D" 
    trashbin_2d = trashbin_base / "2D"
    
    try:
        trashbin_base.mkdir(exist_ok=True)
        trashbin_3d.mkdir(exist_ok=True)
        trashbin_2d.mkdir(exist_ok=True)
        logger.info(f"✅ TrashBin structure ensured: {trashbin_base}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create TrashBin structure: {e}")
        return False

def move_asset_to_trashbin(asset_folder_path: str, dimension: str = "3D") -> dict:
    """
    Safely move an asset folder to TrashBin with timestamp.
    Returns dict with success status and details.
    """
    import shutil
    from datetime import datetime
    
    if not is_safe_asset_folder(asset_folder_path):
        return {
            "success": False,
            "error": "Security validation failed - folder not safe to move",
            "folder_path": asset_folder_path
        }
    
    try:
        # Ensure TrashBin exists
        if not ensure_trashbin_structure():
            return {
                "success": False, 
                "error": "Failed to create TrashBin structure",
                "folder_path": asset_folder_path
            }
        
        source_path = Path(asset_folder_path)
        if not source_path.exists():
            return {
                "success": False,
                "error": "Asset folder does not exist",
                "folder_path": asset_folder_path  
            }
        
        # Preserve original folder name, only add timestamp if conflict exists
        folder_name = source_path.name
        trashbin_path = Path(f"/app/assets/TrashBin/{dimension}/{folder_name}")
        timestamp = None  # Initialize timestamp variable
        
        # Only add timestamp if a folder with the same name already exists in TrashBin
        if trashbin_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trashbin_folder_name = f"{folder_name}_{timestamp}"
            trashbin_path = Path(f"/app/assets/TrashBin/{dimension}/{trashbin_folder_name}")
            logger.info(f"🔄 Conflict detected, using timestamped name: {trashbin_folder_name}")
        else:
            logger.info(f"✅ Using original folder name: {folder_name}")
        
        # Move the folder
        shutil.move(str(source_path), str(trashbin_path))
        
        logger.info(f"✅ Asset folder moved to TrashBin: {source_path} -> {trashbin_path}")
        
        return {
            "success": True,
            "message": f"Asset folder moved to TrashBin",
            "source_path": str(source_path),
            "trashbin_path": str(trashbin_path),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to move asset to TrashBin: {e}")
        return {
            "success": False,
            "error": f"Failed to move folder: {str(e)}",
            "folder_path": asset_folder_path
        }

@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """
    Securely delete an asset: remove from database and move folder to TrashBin.
    NEVER permanently deletes folders - always moves to TrashBin for recovery.
    """
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get asset data before deletion
        collection = asset_queries.db.collection('Atlas_Library')
        if not collection.has(asset_id):
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        asset_data = collection.get(asset_id)
        asset_name = asset_data.get('name', 'Unknown')
        
        # DEBUG: Log the entire asset data structure to understand what's available
        logger.info(f"🔍 FULL ASSET DATA STRUCTURE:")
        logger.info(f"🔍 Asset ID: {asset_id}")
        logger.info(f"🔍 Asset Name: {asset_name}")
        logger.info(f"🔍 All Keys: {list(asset_data.keys())}")
        for key, value in asset_data.items():
            if isinstance(value, dict):
                logger.info(f"🔍 {key}: {value}")
            else:
                logger.info(f"🔍 {key}: {value}")
        
        # Get folder path for moving to TrashBin - PRIORITY: folder_path field
        asset_folder_path = None
        dimension = asset_data.get('dimension', '3D')
        
        # Check ALL possible field names where folder path might be stored
        possible_paths = [
            asset_data.get('folder_path'),
            asset_data.get('asset_folder'),
            asset_data.get('paths', {}).get('asset_folder') if 'paths' in asset_data else None,
            asset_data.get('paths', {}).get('folder_path') if 'paths' in asset_data else None,
            asset_data.get('asset_folder_path'),
            asset_data.get('directory'),
            asset_data.get('path'),
        ]
        
        # SPECIAL CASE: Extract folder path from original_metadata_file field
        original_metadata_file = asset_data.get('metadata', {}).get('original_metadata_file')
        if original_metadata_file:
            # Extract folder path from metadata file path
            # e.g. '{asset_library_root}/3D/Assets/BlacksmithAssets/6F950393_atlas_asset/metadata.json'
            # becomes '{asset_library_root}/3D/Assets/BlacksmithAssets/6F950393_atlas_asset'
            from pathlib import Path
            folder_from_metadata = str(Path(original_metadata_file).parent)
            possible_paths.insert(0, folder_from_metadata)  # Add as first priority
            logger.info(f"🔍 Extracted folder from original_metadata_file: {folder_from_metadata}")
        
        logger.info(f"🔍 All possible folder paths found:")
        for i, path in enumerate(possible_paths):
            logger.info(f"🔍   Option {i+1}: {path}")
            
        # Use the first non-None path found
        for path in possible_paths:
            if path and isinstance(path, str) and path.strip():
                asset_folder_path = path.strip()
                logger.info(f"✅ Selected folder path: {asset_folder_path}")
                break
        
        if not asset_folder_path:
            logger.error(f"❌ NO FOLDER PATH FOUND in any field!")
            logger.info(f"🔍 Full asset data: {asset_data}")
        else:
            logger.info(f"✅ Final asset_folder_path: {asset_folder_path}")
        
        # STRICT POLICY: Only delete from database if folder is found AND successfully moved
        if not asset_folder_path:
            logger.error(f"❌ CRITICAL: No folder path found for asset {asset_id}. REFUSING to delete from database.")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete asset: No folder path found in database. Please check the asset data structure. Asset will NOT be removed from database without folder path."
            )
        
        # CONTAINER PATH TRANSLATION: Convert host network path to container mount path
        def translate_to_container_path(host_path: str) -> str:
            """
            Translate network path to container mount path.
            Host: /net/library/atlaslib/3D/Assets/... 
            Container: /app/assets/3D/Assets/...
            """
            asset_lib_prefix = f"{atlas_config.asset_library_root}/"
            if host_path.startswith(asset_lib_prefix):
                container_path = host_path.replace(asset_lib_prefix, '/app/assets/')
                logger.info(f"🔄 Path translation: {host_path} -> {container_path}")
                return container_path
            else:
                logger.info(f"🔄 Path already container-compatible: {host_path}")
                return host_path
        
        # Translate path for container access
        container_folder_path = translate_to_container_path(asset_folder_path)
        
        # Check if folder actually exists before attempting move
        from pathlib import Path
        folder_path = Path(container_folder_path)
        folder_moved = False
        folder_move_result = None
        
        if not folder_path.exists():
            logger.warning(f"⚠️ Folder does not exist at container path: {container_folder_path} (original: {asset_folder_path})")
            logger.info(f"🧹 Treating as orphaned database entry - will delete from database without folder move")
            folder_moved = False
            folder_move_result = {"success": False, "message": "Folder did not exist - orphaned database entry"}
        elif not folder_path.is_dir():
            logger.error(f"❌ CRITICAL: Path exists but is not a directory: {container_folder_path} (original: {asset_folder_path})")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete asset: Path is not a directory: {asset_folder_path}. Asset will NOT be removed from database."
            )
        else:
            # Folder exists, attempt to move it to TrashBin
            logger.info(f"🗑️ Attempting to move asset folder to TrashBin: {container_folder_path} (original: {asset_folder_path})")
            folder_move_result = move_asset_to_trashbin(container_folder_path, dimension)
            
            if not folder_move_result["success"]:
                # If folder move fails, don't delete from database
                logger.error(f"❌ FOLDER MOVE FAILED: {folder_move_result.get('error', 'Unknown error')}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"FOLDER MOVE FAILED: {folder_move_result.get('error', 'Unknown error')}. Asset will NOT be removed from database without successful folder move."
                )
            else:
                logger.info(f"✅ SUCCESS: Folder successfully moved to TrashBin at: {folder_move_result.get('trashbin_path')}")
                folder_moved = True
        
        logger.info(f"🗑️ Now proceeding to delete from database...")
        
        # Delete from database ONLY after confirmed successful folder move
        try:
            result = collection.delete(asset_id)
            logger.info(f"✅ Database deletion successful for asset {asset_id}")
        except Exception as db_error:
            logger.error(f"❌ Database deletion failed: {db_error}")
            # NOTE: Folder was already moved to TrashBin, so we have a problem
            # We should probably move the folder back from TrashBin in this case
            raise HTTPException(
                status_code=500, 
                detail=f"CRITICAL: Folder was moved to TrashBin but database deletion failed: {db_error}. Manual recovery may be needed."
            )
        
        logger.info(f"✅ Asset {asset_id} ({asset_name}) deleted successfully from database")
        
        return {
            "success": True,
            "message": f"Asset '{asset_name}' deleted successfully",
            "deleted_id": asset_id,
            "deleted_name": asset_name,
            "folder_moved": folder_moved,
            "folder_move_details": folder_move_result,
            "dimension": dimension
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting asset {asset_id}: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error deleting asset: {str(e)}")

@router.get("/assets/{asset_id}/expand")
async def expand_asset(
    asset_id: str,
    relations: Optional[List[str]] = Query(None, description="Relations to expand (e.g., dependencies, materials, textures)"),
    depth: int = Query(1, ge=1, le=3, description="Depth of graph traversal")
):
    """Get asset with expanded relationships using ArangoDB graph traversal"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get the main asset
        asset_data = asset_queries.get_asset_with_dependencies(asset_id)
        if not asset_data or not asset_data.get('asset'):
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        expanded_result = {
            "asset": convert_asset_to_response(asset_data['asset']),
            "relations": {}
        }
        
        # If no specific relations requested, return all available
        if not relations:
            relations = ["dependencies", "materials", "textures", "geometry"]
        
        # Get related assets based on requested relations
        for relation in relations:
            if relation == "dependencies" and asset_data.get('dependencies'):
                expanded_result["relations"]["dependencies"] = [
                    convert_asset_to_response(dep) for dep in asset_data['dependencies']
                ]
            
            elif relation in ["materials", "textures", "geometry"]:
                # Query for related assets based on paths or metadata
                query = f"""
                FOR related IN Atlas_Library
                    FILTER related.category == @relation OR 
                           related.asset_type == @relation OR
                           CONTAINS(related.tags, @relation)
                    FILTER related._key IN @asset.metadata.related_assets OR
                           @asset._key IN related.metadata.parent_assets
                    LIMIT 50
                    RETURN related
                """
                
                cursor = asset_queries.db.aql.execute(
                    query,
                    bind_vars={
                        'relation': relation,
                        'asset': asset_data['asset']
                    }
                )
                
                related_assets = list(cursor)
                if related_assets:
                    expanded_result["relations"][relation] = [
                        convert_asset_to_response(asset) for asset in related_assets
                    ]
        
        # Add graph statistics
        expanded_result["graph_info"] = {
            "depth": depth,
            "relations_queried": relations,
            "total_related_assets": sum(
                len(assets) for assets in expanded_result["relations"].values()
            )
        }
        
        return expanded_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in expand_asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error expanding asset: {str(e)}")

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
    """Open asset folder in system file manager"""
    import subprocess
    import platform
    
    # Get asset from database
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        asset_data = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Get folder path from asset data
        folder_path = asset_data.get('folder_path') or asset_data.get('paths', {}).get('folder_path')
        
        if not folder_path:
            raise HTTPException(status_code=404, detail="Asset folder path not configured")
        
        # Convert network path to container mount path if needed
        asset_lib_prefix = f"{atlas_config.asset_library_root}/"
        if folder_path.startswith(asset_lib_prefix):
            # Convert host path to container mount path
            container_path = folder_path.replace(asset_lib_prefix, '/app/assets/')
            logger.info(f"Converted path: {folder_path} -> {container_path}")
        else:
            container_path = folder_path
        
        # Verify folder exists (check container path)
        from pathlib import Path
        if not Path(container_path).exists():
            # Try original path as fallback
            if not Path(folder_path).exists():
                raise HTTPException(status_code=404, detail=f"Asset folder not found at {folder_path} or {container_path}")
            else:
                # Use original path if container path doesn't exist
                folder_path = folder_path
        else:
            # Use container path
            folder_path = container_path
        
        logger.info(f"Opening folder: {folder_path}")
        
        # In containerized environment, we can't directly open GUI applications
        # Instead, we'll verify the folder exists and return success
        # In production, this would need a different approach (e.g., mounting host X11 socket)
        
        logger.info(f"✅ Folder verified accessible: {folder_path}")
        
        # For now, just return success since we've verified the folder exists
        # TODO: In production, implement proper folder opening mechanism
        # (e.g., via host system integration or remote desktop protocols)
        
        return {
            "success": True, 
            "message": f"Folder verified and accessible: {folder_path}",
            "note": "Folder opening in containerized environment requires host system integration",
            "folder_path": folder_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error opening folder for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to open folder: {str(e)}")

@router.post("/admin/sync")
async def sync_filesystem_to_database():
    """Scan filesystem for metadata.json files and sync all assets to database"""
    import json
    import uuid
    from datetime import datetime
    
    try:
        # Asset library base path from Atlas config
        library_root = Path(atlas_config.asset_library_3d)
        
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

def convert_hdr_to_exact_png(hdr_path, png_path):
    """Proper EXR to PNG conversion with automatic exposure adjustment"""
    try:
        logger.info(f"🔧 Converting EXR to PNG: {hdr_path} -> {png_path}")
        
        # Method 1: Try ImageIO first (excellent EXR support)
        try:
            import imageio.v3 as iio
            import numpy as np
            from PIL import Image
            
            logger.info(f"🔧 Using ImageIO for EXR conversion")
            
            # Read EXR image
            image_array = iio.imread(str(hdr_path))
            if image_array is None:
                raise Exception(f"Could not read {hdr_path}")
            
            height, width = image_array.shape[:2]
            channels = image_array.shape[2] if len(image_array.shape) > 2 else 1
            
            logger.info(f"📏 Original EXR dimensions: {width}x{height} ({channels} channels)")
            logger.info(f"📊 Value range: min={np.min(image_array):.3f}, max={np.max(image_array):.3f}")
            
            # Handle negative values and infinities
            image_array = np.nan_to_num(image_array, nan=0.0, posinf=1.0, neginf=0.0)
            image_array = np.maximum(image_array, 0.0)  # Remove negative values
            
            # Automatic exposure adjustment based on image content
            # Find a reasonable exposure level by looking at the 95th percentile
            if np.max(image_array) > 1.0:
                p95 = np.percentile(image_array[image_array > 0], 95)
                if p95 > 1.0:
                    # Scale down so 95th percentile maps to ~0.8
                    exposure_scale = 0.8 / p95
                    image_array = image_array * exposure_scale
                    logger.info(f"🔧 Applied exposure scale: {exposure_scale:.3f}")
            
            # Soft clamp to avoid hard cutoffs
            image_array = image_array / (image_array + 1.0)  # Soft compression
            image_array = np.clip(image_array, 0.0, 1.0)
            
            # Convert to 8-bit
            image_array = (image_array * 255).astype(np.uint8)
            
            # Handle channel configuration
            if channels >= 4:
                # RGBA
                image_array = image_array[:, :, :4]
                mode = 'RGBA'
            elif channels == 3:
                # RGB - add alpha channel
                alpha_channel = np.ones((height, width, 1), dtype=np.uint8) * 255
                image_array = np.concatenate([image_array, alpha_channel], axis=2)
                mode = 'RGBA'
            else:
                # Grayscale
                if len(image_array.shape) == 2:
                    # Convert to RGBA
                    gray_rgb = np.repeat(image_array[:, :, np.newaxis], 3, axis=2)
                    alpha_channel = np.ones((height, width, 1), dtype=np.uint8) * 255
                    image_array = np.concatenate([gray_rgb, alpha_channel], axis=2)
                else:
                    # Single channel with shape (h, w, 1)
                    gray_rgb = np.repeat(image_array[:, :, :1], 3, axis=2)
                    alpha_channel = np.ones((height, width, 1), dtype=np.uint8) * 255
                    image_array = np.concatenate([gray_rgb, alpha_channel], axis=2)
                mode = 'RGBA'
            
            # Create and save PNG
            pil_image = Image.fromarray(image_array, mode)
            pil_image.save(png_path, 'PNG')
            logger.info(f"✅ Converted EXR to PNG: {width}x{height} -> {png_path}")
            return True
            
        except ImportError:
            logger.info(f"   ℹ️ ImageIO not available")
        except Exception as e:
            logger.info(f"   ⚠️ ImageIO conversion failed: {e}")
        
        # Method 2: Try OpenCV fallback
        try:
            import cv2
            import numpy as np
            from PIL import Image
            
            logger.info(f"🔧 Using OpenCV for EXR conversion")
            
            # Read EXR file
            img = cv2.imread(str(hdr_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                raise Exception(f"Could not read {hdr_path}")
            
            original_height, original_width = img.shape[:2]
            logger.info(f"📏 Original EXR dimensions: {original_width}x{original_height}")
            
            # Convert BGR to RGB if needed
            if len(img.shape) == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            elif len(img.shape) == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            
            # Handle negative values and infinities
            img = np.nan_to_num(img, nan=0.0, posinf=1.0, neginf=0.0)
            img = np.maximum(img, 0.0)
            
            # Automatic exposure adjustment
            if np.max(img) > 1.0:
                p95 = np.percentile(img[img > 0], 95)
                if p95 > 1.0:
                    exposure_scale = 0.8 / p95
                    img = img * exposure_scale
                    logger.info(f"🔧 Applied exposure scale: {exposure_scale:.3f}")
            
            # Soft compression and clamp
            img = img / (img + 1.0)
            img = np.clip(img, 0.0, 1.0)
            img = (img * 255).astype(np.uint8)
            
            # Ensure RGBA format
            if len(img.shape) == 2:
                # Grayscale to RGBA
                gray = img[:, :, np.newaxis]
                rgb = np.repeat(gray, 3, axis=2)
                alpha = np.ones((img.shape[0], img.shape[1], 1), dtype=np.uint8) * 255
                img = np.concatenate([rgb, alpha], axis=2)
            elif len(img.shape) == 3 and img.shape[2] == 3:
                # RGB to RGBA
                alpha = np.ones((img.shape[0], img.shape[1], 1), dtype=np.uint8) * 255
                img = np.concatenate([img, alpha], axis=2)
            
            # Save as PNG
            pil_image = Image.fromarray(img, 'RGBA')
            pil_image.save(png_path, 'PNG')
            logger.info(f"✅ Converted EXR to PNG: {original_width}x{original_height} -> {png_path}")
            return True
            
        except ImportError:
            logger.info(f"   ℹ️ OpenCV not available")
        except Exception as e:
            logger.info(f"   ⚠️ OpenCV conversion failed: {e}")
        
        logger.error(f"❌ All EXR conversion methods failed")
        return False
            
    except Exception as e:
        logger.error(f"❌ EXR conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Upload Asset Request Model
class UploadAssetRequest(BaseModel):
    asset_type: str  # 'Textures' or 'HDRI'
    name: str
    file_path: str
    description: Optional[str] = ""
    dimension: str = "3D"
    created_by: str = "web_uploader"

@router.post("/assets/upload", response_model=AssetResponse)
async def upload_asset(upload_request: UploadAssetRequest):
    """Upload a Texture or HDRI asset to the Atlas library"""
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        import uuid
        import shutil
        from datetime import datetime
        from pathlib import Path
        
        logger.info(f"🔧 Processing upload request: {upload_request.dict()}")
        
        # Validate asset type
        if upload_request.asset_type not in ['Textures', 'HDRI']:
            raise HTTPException(status_code=400, detail="Asset type must be 'Textures' or 'HDRI'")
        
        # Validate file path exists (now accessible via Docker mount)
        source_file = Path(upload_request.file_path)
        if not source_file.exists():
            # Provide helpful error with mount information
            error_msg = f"Source file not found: {upload_request.file_path}\n\n"
            error_msg += "Available mounted paths in container:\n"
            error_msg += "- /app/assets (atlas library)\n"
            error_msg += "- /net/general (general network drive)\n"
            error_msg += "\nMake sure the file path starts with one of these mounted directories."
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check if file is a supported image format
        supported_extensions = {'.exr', '.hdr', '.hdri', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}
        if source_file.suffix.lower() not in supported_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {source_file.suffix}. Supported: {', '.join(supported_extensions)}"
            )
        
        # Clean and validate asset name
        clean_asset_name = upload_request.name.strip()
        if not clean_asset_name:
            raise HTTPException(status_code=400, detail="Asset name cannot be empty")
        
        # Generate unique asset ID using same convention as houdiniae.py
        # 11-character base UID + 2-character variant (AA) + 3-character version (001) = 16 characters total
        base_uid = str(uuid.uuid4()).replace('-', '')[:11].upper()
        variant_id = "AA"  # Always start with AA variant for new assets
        version = 1
        asset_id = f"{base_uid}{variant_id}{version:03d}"  # 16-character ID
        asset_base_id = f"{base_uid}{variant_id}"  # 13-character base ID
        
        # Create folder structure for uploaded asset
        # Structure: /app/assets/3D/{Textures|HDRI}/ASSETID_AssetName/
        #   ├── Asset/          # ACTUAL asset file (original .exr/.hdr/etc)  
        #   ├── Thumbnail/      # Converted PNG for web (EXACT aspect ratio)
        #   └── metadata.json   # Database entry
        asset_library_path = Path(os.getenv('ASSET_LIBRARY_PATH', '/app/assets'))
        category_path = asset_library_path / "3D" / upload_request.asset_type
        asset_folder = category_path / f"{asset_id}_{clean_asset_name}"
        
        # Ensure category directory exists
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Create asset folder
        if asset_folder.exists():
            raise HTTPException(status_code=400, detail=f"Asset folder already exists: {asset_folder}")
        
        asset_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created asset folder: {asset_folder}")
        
        # Create subfolders for Textures/HDRI structure
        asset_subfolder = asset_folder / "Asset"  # This holds the ACTUAL asset file
        thumbnail_folder = asset_folder / "Thumbnail"
        asset_subfolder.mkdir(exist_ok=True)
        thumbnail_folder.mkdir(exist_ok=True)
        
        # Copy the actual asset file to the Asset folder (same for both Textures and HDRI)
        target_file = asset_subfolder / source_file.name
        shutil.copy2(source_file, target_file)
        logger.info(f"📋 Copied {upload_request.asset_type.lower()} file to Asset folder: {source_file} -> {target_file}")
        
        # Create thumbnail from the copied file (inside container where libraries work)
        thumbnail_created = False
        thumbnail_file = thumbnail_folder / f"{clean_asset_name}_thumbnail.png"
        
        if target_file.suffix.lower() in {'.exr', '.hdr', '.hdri', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}:
            try:
                if target_file.suffix.lower() in {'.exr', '.hdr', '.hdri'}:
                    # Use the copied file (inside container) for EXR conversion with existing libraries
                    logger.info(f"🔧 Converting EXR from copied file: {target_file}")
                    success = convert_hdr_to_exact_png(target_file, thumbnail_file)
                    if success:
                        thumbnail_created = True
                        logger.info(f"✅ Created exact aspect ratio thumbnail from copied {upload_request.asset_type}: {thumbnail_file}")
                else:
                    # For regular image formats, convert to PNG preserving EXACT dimensions and aspect ratio
                    from PIL import Image
                    with Image.open(target_file) as img:  # Use copied file
                        # Convert to RGBA to ensure transparency support
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        
                        # NO RESIZING - preserve exact dimensions and aspect ratio
                        img.save(thumbnail_file, 'PNG')
                        thumbnail_created = True
                        logger.info(f"✅ Created exact thumbnail from copied image ({img.width}x{img.height}): {thumbnail_file}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to create thumbnail from copied file: {e}")
                logger.info(f"💡 Thumbnail creation failed but continuing with upload...")
                thumbnail_created = False
        
        # Create metadata.json file
        metadata = {
            "id": asset_id,
            "name": clean_asset_name,
            "asset_type": upload_request.asset_type,
            "dimension": upload_request.dimension,
            "created_by": upload_request.created_by,
            "created_at": datetime.now().isoformat(),
            "description": upload_request.description,
            "file_info": {
                "original_path": str(source_file),
                "filename": source_file.name,
                "size_bytes": source_file.stat().st_size,
                "extension": source_file.suffix
            },
            "paths": {
                "asset_folder": str(asset_folder),
                "asset_subfolder": str(asset_subfolder),
                "main_file": str(target_file),
                "thumbnail": str(thumbnail_file) if thumbnail_created else None
            }
        }
        
        metadata_file = asset_folder / "metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"📄 Created metadata file: {metadata_file}")
        
        # Create asset document for database
        asset_doc = {
            "_key": asset_id,
            "id": asset_id,
            "name": clean_asset_name,
            "category": upload_request.asset_type,
            "dimension": upload_request.dimension,
            "asset_type": upload_request.asset_type,
            "hierarchy": {
                "dimension": upload_request.dimension,
                "asset_type": upload_request.asset_type,
                "subcategory": "Uploaded"
            },
            "metadata": metadata,
            "paths": {
                "folder_path": str(asset_folder),
                "asset_folder": str(asset_folder),
                "asset_subfolder": str(asset_subfolder),
                "main_file": str(target_file),
                "thumbnail": str(thumbnail_file) if thumbnail_created else None
            },
            "file_sizes": {
                "main_file": source_file.stat().st_size,
                "estimated_total_size": source_file.stat().st_size
            },
            "tags": ["uploaded", upload_request.asset_type.lower()],
            "created_at": datetime.now().isoformat(),
            "created_by": upload_request.created_by,
            "status": "active",
            "folder_path": str(asset_folder)  # For compatibility with existing frontend
        }
        
        # Insert into database using the same AssetQueries method as elsewhere
        try:
            # Use the same database connection as other endpoints
            result = asset_queries.create_asset(asset_doc)
            logger.info(f"✅ Inserted asset into database: {result}")
            
        except Exception as db_error:
            # If database insert fails, clean up created files
            logger.error(f"❌ Database insert failed: {db_error}")
            logger.error(f"❌ Database error type: {type(db_error)}")
            import traceback
            logger.error(f"❌ Database traceback: {traceback.format_exc()}")
            try:
                shutil.rmtree(asset_folder)
                logger.info(f"🧹 Cleaned up asset folder after database failure: {asset_folder}")
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to cleanup asset folder: {cleanup_error}")
            
            raise HTTPException(status_code=500, detail=f"Database insert failed: {str(db_error)}")
        
        logger.info(f"✅ Successfully uploaded {upload_request.asset_type} asset: {clean_asset_name} (ID: {asset_id})")
        
        # Return asset response
        return convert_asset_to_response(asset_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")