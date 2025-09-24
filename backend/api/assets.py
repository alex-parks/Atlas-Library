# backend/api/assets.py - Fixed ArangoDB integration
from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import os
import sys
import logging
import hashlib
import shutil
import tempfile
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


def generate_texture_tags(
    asset_name: str,
    subcategory: str,
    alpha_subcategory: Optional[str] = None,
    texture_set_paths: Optional[dict] = None,
    texture_type: Optional[str] = None,
    seamless: Optional[bool] = None,
    uv_tile: Optional[bool] = None,
    resolution_info: Optional[dict] = None
) -> List[str]:
    """Generate comprehensive tags for texture assets"""
    tags = set()
    
    # 1. Basic texture category tags
    tags.add("texture")
    tags.add("material")
    
    # 2. Subcategory tags
    if subcategory:
        tags.add(subcategory.lower().replace(' ', '_'))
        
        # Special subcategory-specific tags
        if subcategory == 'Texture Sets':
            tags.add("texture_set")
            tags.add("material_set")
            tags.add("multi_channel")
        else:
            tags.add("single_texture")
    
    # 3. Alpha subcategory tags
    if alpha_subcategory:
        tags.add(alpha_subcategory.lower().replace(' ', '_'))
    
    # 4. Texture type tags (already handled above but included for completeness)
    if texture_type:
        tags.add(texture_type.lower())
    
    if seamless:
        tags.add("tileable")
        tags.add("repeatable")
    
    if uv_tile:
        tags.add("udim")
        tags.add("uv_tiles")
    
    # 5. Channel-specific tags for texture sets
    if texture_set_paths:
        available_channels = []
        channel_mapping = {
            'baseColor': ['base_color', 'albedo', 'diffuse'],
            'metallic': ['metallic', 'metalness', 'metal'],
            'roughness': ['roughness', 'rough'],
            'normal': ['normal', 'bump', 'normal_map'],
            'displacement': ['displacement', 'height', 'disp'],
            'opacity': ['opacity', 'alpha', 'transparency']
        }
        
        for channel_key, channel_tags in channel_mapping.items():
            if texture_set_paths.get(channel_key) and texture_set_paths[channel_key].strip():
                available_channels.extend(channel_tags)
                tags.add(f"has_{channel_tags[0]}")
        
        # Add all channel tags
        tags.update(available_channels)
        
        # Add combined channel tags for common combinations
        if texture_set_paths.get('baseColor') and texture_set_paths.get('normal'):
            tags.add("pbr_ready")
        
        if texture_set_paths.get('metallic') and texture_set_paths.get('roughness'):
            tags.add("metallic_workflow")
    
    # 6. Asset name word tags (for searchability)
    for word in asset_name.lower().replace('_', ' ').split():
        word = word.strip()
        if word and len(word) > 2:  # Skip very short words
            # Filter out common texture terms that aren't useful for search
            skip_words = {'texture', 'material', 'map', 'set', 'asset', 'file'}
            if word not in skip_words:
                tags.add(word)
    
    # 7. Resolution tags
    if resolution_info:
        resolution = resolution_info.get('resolution', '')
        if resolution:
            # Extract resolution quality tags
            if '4096' in resolution or '4K' in resolution.upper():
                tags.add("4k")
                tags.add("high_res")
            elif '2048' in resolution or '2K' in resolution.upper():
                tags.add("2k")
                tags.add("medium_res")
            elif '1024' in resolution or '1K' in resolution.upper():
                tags.add("1k")
                tags.add("low_res")
            elif '8192' in resolution or '8K' in resolution.upper():
                tags.add("8k")
                tags.add("ultra_high_res")
        
        # Add aspect ratio tags
        width = resolution_info.get('width', 0)
        height = resolution_info.get('height', 0)
        if width and height:
            if width == height:
                tags.add("square")
            elif width > height * 1.5:
                tags.add("wide")
            elif height > width * 1.5:
                tags.add("tall")
    
    # 8. File format tags (can be inferred from common texture formats)
    common_formats = ['jpg', 'png', 'exr', 'tiff', 'tga', 'hdr']
    for fmt in common_formats:
        # This would require checking the actual file paths, but we can add logic later
        pass
    
    # Convert to lowercase and return as sorted list
    return sorted([tag.lower() for tag in tags])


# Force reload marker

# Docker-friendly asset library base path
ASSET_LIBRARY_BASE = Path(os.getenv('ASSET_LIBRARY_PATH', '/app/assets')) / "3D"

# Network library base path (actual path that external applications use)
NETWORK_LIBRARY_BASE = Path("/net/library/atlaslib/3D")

def convert_to_network_path(container_path: str) -> str:
    """Convert container mount path to network library path"""
    container_path_str = str(container_path)
    if '/app/assets/' in container_path_str:
        return container_path_str.replace('/app/assets/', '/net/library/atlaslib/')
    return container_path_str

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
    🚫 PROTECTION: Will NOT move files from protected mount areas.
    """
    import shutil
    from datetime import datetime
    from backend.core.config_manager import config as atlas_config
    
    # 🚫 PROTECTION CHECK: Validate against protected mount areas first
    is_safe, reason = atlas_config.validate_safe_operation('move', asset_folder_path)
    if not is_safe:
        logger.error(f"❌ {reason}")
        return {
            "success": False,
            "error": reason,
            "folder_path": asset_folder_path
        }
    
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
    🚫 PROTECTION: Will NOT delete assets from protected mount areas.
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
        
        # 🚫 PROTECTION CHECK: Validate that we're not trying to delete from protected mount areas
        from backend.core.config_manager import config as atlas_config
        is_safe, reason = atlas_config.validate_safe_operation('delete', container_folder_path)
        if not is_safe:
            logger.error(f"❌ {reason}")
            raise HTTPException(
                status_code=403, 
                detail=f"Operation denied: {reason}. Assets in protected mount areas cannot be deleted for safety."
            )
        
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

@router.post("/assets/{asset_id}/copy-folder-path")
async def copy_asset_folder_path(asset_id: str):
    """Get asset folder path for copying to clipboard"""
    
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
        
        # Convert container mount path back to real network path
        if folder_path.startswith('/app/assets/'):
            # Convert container mount path back to real network path
            real_network_path = folder_path.replace('/app/assets/', '/net/library/atlaslib/')
            logger.info(f"Converting container path to network path: {folder_path} -> {real_network_path}")
            folder_path = real_network_path
        
        # Verify folder exists (check both network path and container mount)
        from pathlib import Path
        folder_exists = False
        
        if Path(folder_path).exists():
            folder_exists = True
            logger.info(f"✅ Folder exists at network path: {folder_path}")
        else:
            # Try container mount path as fallback for verification
            container_fallback = folder_path.replace('/net/library/atlaslib/', '/app/assets/')
            if Path(container_fallback).exists():
                folder_exists = True
                logger.info(f"✅ Folder exists at container mount: {container_fallback}, using network path: {folder_path}")
        
        if not folder_exists:
            logger.warning(f"⚠️ Folder not found at {folder_path} or container mount")
        
        logger.info(f"📋 Returning folder path for clipboard: {folder_path}")
        
        return {
            "success": True, 
            "folder_path": folder_path,
            "folder_exists": folder_exists,
            "asset_id": asset_id,
            "asset_name": asset_data.get('name', 'Unknown'),
            "message": f"Folder path ready for clipboard: {folder_path}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder path for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get folder path: {str(e)}")

@router.get("/assets/{asset_id}/texture-images")
async def get_texture_images(asset_id: str):
    """Get list of texture images for navigation"""
    
    # Get asset from database
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        asset_data = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if this is a texture asset
        asset_type = asset_data.get('asset_type') or asset_data.get('category')
        if asset_type != 'Textures':
            return {"images": [], "resolutions": {}}
        
        # Get folder path
        folder_path = asset_data.get('folder_path') or asset_data.get('paths', {}).get('folder_path')
        if not folder_path:
            return {"images": [], "resolutions": {}}
        
        # Convert container mount path if needed
        if folder_path.startswith('/app/assets/'):
            folder_path = folder_path.replace('/app/assets/', '/net/library/atlaslib/')
        
        # Check if folder exists
        from pathlib import Path
        folder = Path(folder_path)
        if not folder.exists():
            # Try container mount as fallback
            container_folder = Path(folder_path.replace('/net/library/atlaslib/', '/app/assets/'))
            if container_folder.exists():
                folder = container_folder
            else:
                return {"images": [], "resolutions": {}}
        
        # Look for original texture files in the asset subfolder (for copying)
        # Use asset_subfolder from metadata if available, otherwise fallback to "Assets"
        asset_subfolder_path = asset_data.get('paths', {}).get('asset_subfolder')
        if asset_subfolder_path:
            # Extract just the subfolder name from the full path
            assets_folder = Path(asset_subfolder_path)
        else:
            # Fallback to hardcoded "Assets" for legacy assets
            assets_folder = folder / "Assets"
        preview_folder = folder / "Preview"
        images = []
        resolutions = {}
        
        # First, check if there's a preview image
        preview_files = (asset_data.get('paths', {}).get('preview_files', []) or 
                        asset_data.get('metadata', {}).get('paths', {}).get('preview_files', []))
        
        preview_found = False
        if preview_files and len(preview_files) > 0:
            # Add preview image as the first image (use container path directly)
            preview_path = Path(preview_files[0])
            if preview_path.exists():
                # For the API response, convert to network path for external access
                network_path = str(preview_path).replace('/app/assets/', '/net/library/atlaslib/')
                images.append({
                    "filename": "Preview.png",
                    "path": network_path,
                    "relative_path": "Preview/Preview.png",
                    "is_original": False,
                    "is_preview": True
                })
                resolutions[0] = asset_data.get('metadata', {}).get('resolution', 'Unknown')
                logger.info(f"🖼️ Added preview image from database: {preview_path}")
                preview_found = True
        
        # Fallback: Scan Preview folder directly if not found in database
        if not preview_found and (folder / "Preview").exists():
            preview_folder = folder / "Preview"
            for file_path in preview_folder.iterdir():
                if file_path.is_file() and file_path.name.lower() == 'preview.png':
                    # Convert to network path for external access
                    network_path = str(file_path).replace('/app/assets/', '/net/library/atlaslib/')
                    images.append({
                        "filename": "Preview.png",
                        "path": network_path,
                        "relative_path": "Preview/Preview.png",
                        "is_original": False,
                        "is_preview": True
                    })
                    resolutions[0] = asset_data.get('metadata', {}).get('resolution', 'Unknown')
                    logger.info(f"🖼️ Added preview image from filesystem scan: {file_path}")
                    preview_found = True
                    break
        
        # Then, get thumbnail files from the database (NOT copied_files)
        thumbnail_files = asset_data.get('paths', {}).get('thumbnails', [])
        
        if thumbnail_files:
            logger.info(f"🖼️ Using thumbnails from database: {len(thumbnail_files)} files")
            for i, file_path in enumerate(thumbnail_files):
                file_path_obj = Path(file_path)
                # Offset index by 1 if preview was actually found and added
                res_index = i + 1 if preview_found else i
                
                # Extract original filename from thumbnail name for texture slot mapping
                thumbnail_name = file_path_obj.name
                original_filename = thumbnail_name
                
                # For texture sets, map thumbnail to original using texture_set_info
                if '_thumbnail' in thumbnail_name:
                    texture_set_info = asset_data.get('metadata', {}).get('texture_set_info', {})
                    texture_slots = texture_set_info.get('texture_slots', {})

                    # Parse thumbnail name to extract position and type
                    # Example: Faux_2_0_BaseColor_thumbnail.png -> position=0, type=BaseColor
                    # We need to find the position digit that comes BEFORE a texture type keyword
                    name_without_ext = thumbnail_name.replace('_thumbnail.png', '')
                    name_parts = name_without_ext.split('_')

                    # Known texture type keywords
                    texture_types = ['BaseColor', 'Metallic', 'Roughness', 'Normal', 'Opacity', 'Displacement']

                    # Find position and type by looking for texture type keywords
                    found_position = None
                    found_type = None
                    for i, part in enumerate(name_parts):
                        if part in texture_types:
                            found_type = part
                            # Position should be the previous part if it's a digit
                            if i > 0 and name_parts[i-1].isdigit():
                                found_position = name_parts[i-1]
                            break

                    # Find matching texture slot using position
                    if found_position is not None:
                        for slot_key, slot_info in texture_slots.items():
                            if str(slot_info.get('position', '')) == found_position:
                                original_filename = slot_info.get('original_filename', thumbnail_name)
                                logger.debug(f"Mapped thumbnail position {found_position} to original: {original_filename}")
                                break
                    else:
                        logger.warning(f"Could not parse position from thumbnail: {thumbnail_name}")
                
                images.append({
                    "filename": original_filename,
                    "path": str(file_path),  # Full path to thumbnail file
                    "relative_path": f"Thumbnail/{file_path_obj.name}",
                    "is_original": False,  # These are thumbnails, not originals
                    "is_thumbnail": True,
                    "is_preview": False
                })
                resolutions[res_index] = asset_data.get('metadata', {}).get('resolution', 'Unknown')
        
        # Fallback: Scan Thumbnail folder if no thumbnails in database
        elif (folder / "Thumbnail").exists():
            thumbnail_folder = folder / "Thumbnail"
            logger.info(f"🖼️ Scanning Thumbnail folder: {thumbnail_folder}")
            image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tga', '.exr', '.tif'}
            
            for file_path in thumbnail_folder.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    # Extract original filename from thumbnail name
                    original_filename = file_path.name.replace('_thumbnail', '') if '_thumbnail' in file_path.name else file_path.name
                    
                    images.append({
                        "filename": original_filename,
                        "path": str(file_path),  # Full path to thumbnail file
                        "relative_path": str(file_path.relative_to(folder)),
                        "is_original": False,
                        "is_thumbnail": True,
                        "is_preview": False
                    })
                    # Try to get resolution from asset metadata
                    resolutions[len(images) - 1] = asset_data.get('metadata', {}).get('resolution', 'Unknown')
        
        # If no images found, return empty result
        else:
            logger.warning(f"⚠️ No Preview or Thumbnail files found for {asset_id}")
            return {"images": [], "resolutions": {}}
        
        # Sort images by position using explicit texture set mappings first, then filename fallback
        def get_texture_position(image_info):
            # Preview images always come first
            if image_info.get('is_preview', False):
                return -1  # Preview comes before all texture maps

            filename = image_info['filename'].lower()

            # For texture sets, use explicit mapping from metadata instead of guessing from filename
            texture_set_info = asset_data.get('metadata', {}).get('texture_set_info', {})
            if texture_set_info and texture_set_info.get('type') == 'texture_set':
                provided_paths = texture_set_info.get('provided_paths', {})
                texture_slots = texture_set_info.get('texture_slots', {})

                # First, try to match by original filename from texture slots
                for slot_key, slot_info in texture_slots.items():
                    if slot_info.get('original_filename', '').lower() == image_info['filename'].lower():
                        slot_position = int(slot_info.get('position', 99))
                        logger.info(f"📍 Matched {image_info['filename']} to slot {slot_key} at position {slot_position}")
                        return slot_position

                # Second, try to match by checking if the image filename appears in any provided path
                for slot_key, file_path in provided_paths.items():
                    if file_path and Path(file_path).name.lower() == image_info['filename'].lower():
                        # Get position from the defined texture order
                        texture_order = {
                            'baseColor': 0,
                            'metallic': 1,
                            'roughness': 2,
                            'normal': 3,
                            'opacity': 4,
                            'displacement': 5
                        }
                        slot_position = texture_order.get(slot_key, 99)
                        logger.info(f"📍 Matched {image_info['filename']} to provided path {slot_key} at position {slot_position}")
                        return slot_position

            # Fallback to filename-based position pattern for legacy assets: Name_Position_Type_
            parts = filename.split('_')
            for i, part in enumerate(parts):
                if part.isdigit() and i > 0:  # Position should not be the first part
                    # Check if next part matches texture type
                    if i + 1 < len(parts):
                        next_part = parts[i + 1]
                        if any(tex_type in next_part for tex_type in ['basecolor', 'metallic', 'roughness', 'normal', 'opacity', 'displacement']):
                            return int(part)

            # Final fallback to texture type priority for files without position numbers
            texture_priority = {
                'basecolor': 0, 'albedo': 0, 'diffuse': 0,
                'metallic': 1, 'metalness': 1, 'metal': 1,
                'roughness': 2, 'rough': 2,
                'normal': 3, 'bump': 3,
                'opacity': 4, 'alpha': 4, 'transparency': 4,
                'displacement': 5, 'height': 5, 'disp': 5
            }

            for tex_type, position in texture_priority.items():
                if tex_type in filename:
                    logger.info(f"📍 Fallback: Matched {image_info['filename']} to texture type {tex_type} at position {position}")
                    return position

            # Unknown texture types go last
            logger.info(f"📍 Unknown texture type for {image_info['filename']}, assigning position 99")
            return 99
            
        images.sort(key=get_texture_position)
        
        # Debug logging to verify order
        for i, img in enumerate(images):
            is_preview = img.get('is_preview', False)
            logger.info(f"📸 Image {i}: {img.get('filename')} (preview: {is_preview})")
        
        logger.info(f"📸 Found {len(images)} texture images for asset {asset_id}")
        
        return {
            "images": images,
            "resolutions": resolutions,
            "asset_id": asset_id,
            "asset_name": asset_data.get('name', 'Unknown'),
            "total_images": len(images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting texture images for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get texture images: {str(e)}")

@router.get("/assets/{asset_id}/texture-image/{image_index}")
async def get_texture_image_by_index(asset_id: str, image_index: int):
    """Serve a specific texture image by index - uses same ordering as texture-images endpoint"""
    
    # Get asset from database
    asset_queries = get_asset_queries()
    if not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        asset_data = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if this is a texture asset
        asset_type = asset_data.get('asset_type') or asset_data.get('category')
        if asset_type != 'Textures':
            raise HTTPException(status_code=404, detail="Not a texture asset")
        
        # Use same image gathering logic as get_texture_images endpoint
        images = []
        
        # Get folder path for fallback scanning
        folder_path = asset_data.get('folder_path') or asset_data.get('paths', {}).get('folder_path')
        if not folder_path:
            raise HTTPException(status_code=404, detail="Asset folder path not found")
            
        # Convert container mount path if needed
        if folder_path.startswith('/app/assets/'):
            folder_path = folder_path.replace('/app/assets/', '/net/library/atlaslib/')
            
        # Check if folder exists
        from pathlib import Path
        folder = Path(folder_path)
        if not folder.exists():
            # Try container mount as fallback
            container_folder = Path(folder_path.replace('/net/library/atlaslib/', '/app/assets/'))
            if container_folder.exists():
                folder = container_folder
            else:
                raise HTTPException(status_code=404, detail="Asset folder not found")
        
        # First, check if there's a preview image
        preview_files = (asset_data.get('paths', {}).get('preview_files', []) or 
                        asset_data.get('metadata', {}).get('paths', {}).get('preview_files', []))
        
        preview_found = False
        if preview_files and len(preview_files) > 0:
            # Add preview image as the first image (use container path directly)
            preview_path = Path(preview_files[0])
            if preview_path.exists():
                images.append({
                    "filename": "Preview.png", 
                    "path": str(preview_path),
                    "is_preview": True
                })
                preview_found = True
                
        # Fallback: Scan Preview folder directly if not found in database
        if not preview_found and (folder / "Preview").exists():
            preview_folder = folder / "Preview"
            for file_path in preview_folder.iterdir():
                if file_path.is_file() and file_path.name.lower() == 'preview.png':
                    images.append({
                        "filename": "Preview.png",
                        "path": str(file_path),  # Use actual file path for serving
                        "is_preview": True
                    })
                    preview_found = True
                    break
        
        # Then add texture images from thumbnails (NOT copied_files)
        thumbnail_files = asset_data.get('paths', {}).get('thumbnails', [])
        if thumbnail_files:
            for file_path_str in thumbnail_files:
                file_path = Path(file_path_str)
                if file_path.exists():
                    # Map thumbnail name back to original filename for frontend consistency
                    thumbnail_name = file_path.name
                    
                    # Extract original filename using texture slot mapping
                    original_filename = thumbnail_name
                    if '_thumbnail' in thumbnail_name:
                        texture_set_info = asset_data.get('metadata', {}).get('texture_set_info', {})
                        texture_slots = texture_set_info.get('texture_slots', {})
                        
                        # Parse thumbnail name to extract position (Stone_Wall_0_BaseColor_thumbnail.png -> position=0)
                        name_parts = thumbnail_name.replace('_thumbnail.png', '').split('_')
                        found_position = None
                        for part in name_parts:
                            if part.isdigit():
                                found_position = part
                                break
                        
                        # Find matching texture slot using position
                        if found_position is not None:
                            for slot_key, slot_info in texture_slots.items():
                                if str(slot_info.get('position', '')) == found_position:
                                    original_filename = slot_info.get('original_filename', thumbnail_name)
                                    break
                    
                    images.append({
                        "filename": original_filename,
                        "path": str(file_path),  # Path to thumbnail file
                        "is_preview": False,
                        "is_thumbnail": True
                    })
        
        # Sort images by position using explicit texture set mappings first, then filename fallback
        def get_texture_position(image_info):
            # Preview images always come first
            if image_info.get('is_preview', False):
                return -1  # Preview comes before all texture maps

            filename = image_info['filename'].lower()

            # For texture sets, use explicit mapping from metadata instead of guessing from filename
            texture_set_info = asset_data.get('metadata', {}).get('texture_set_info', {})
            if texture_set_info and texture_set_info.get('type') == 'texture_set':
                provided_paths = texture_set_info.get('provided_paths', {})
                texture_slots = texture_set_info.get('texture_slots', {})

                # First, try to match by original filename from texture slots
                for slot_key, slot_info in texture_slots.items():
                    if slot_info.get('original_filename', '').lower() == image_info['filename'].lower():
                        slot_position = int(slot_info.get('position', 99))
                        return slot_position

                # Second, try to match by checking if the image filename appears in any provided path
                for slot_key, file_path in provided_paths.items():
                    if file_path and Path(file_path).name.lower() == image_info['filename'].lower():
                        # Get position from the defined texture order
                        texture_order = {
                            'baseColor': 0,
                            'metallic': 1,
                            'roughness': 2,
                            'normal': 3,
                            'opacity': 4,
                            'displacement': 5
                        }
                        slot_position = texture_order.get(slot_key, 99)
                        return slot_position

            # Fallback to filename-based position pattern for legacy assets: Name_Position_Type_
            parts = filename.split('_')
            for i, part in enumerate(parts):
                if part.isdigit() and i > 0:  # Position should not be the first part
                    # Check if next part matches texture type
                    if i + 1 < len(parts):
                        next_part = parts[i + 1]
                        if any(tex_type in next_part for tex_type in ['basecolor', 'metallic', 'roughness', 'normal', 'opacity', 'displacement']):
                            return int(part)

            # Final fallback to texture type priority for files without position numbers
            texture_priority = {
                'basecolor': 0, 'albedo': 0, 'diffuse': 0,
                'metallic': 1, 'metalness': 1, 'metal': 1,
                'roughness': 2, 'rough': 2,
                'normal': 3, 'bump': 3,
                'opacity': 4, 'alpha': 4, 'transparency': 4,
                'displacement': 5, 'height': 5, 'disp': 5
            }

            for tex_type, position in texture_priority.items():
                if tex_type in filename:
                    return position

            # Unknown texture types go last
            return 99
        
        images.sort(key=get_texture_position)
        
        # Check if image_index is valid
        if image_index < 0 or image_index >= len(images):
            raise HTTPException(status_code=404, detail=f"Image index {image_index} out of range (0-{len(images)-1})")
        
        selected_image = images[image_index]
        image_path = Path(selected_image["path"])
        
        # Determine content type based on file extension
        if image_path.suffix.lower() == '.png':
            content_type = "image/png"
        elif image_path.suffix.lower() in ['.jpg', '.jpeg']:
            content_type = "image/jpeg"
        elif image_path.suffix.lower() == '.exr':
            content_type = "image/x-exr"
        else:
            content_type = "image/png"  # Default
        
        # Since we're now using thumbnail paths directly, just serve the file
        if image_path.exists():
            logger.info(f"🖼️ ✅ Serving image: {image_path}")
            try:
                import mimetypes
                from fastapi.responses import FileResponse
                
                # Use FileResponse for better file serving
                return FileResponse(
                    path=str(image_path),
                    media_type=content_type,
                    filename=selected_image["filename"],
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET",
                        "Access-Control-Allow-Headers": "*"
                    }
                )
            except Exception as e:
                logger.error(f"❌ Error serving image file: {e}")
                # Fallback to manual file reading
                pass
        
        # Fallback: serve file manually if FileResponse fails
        if image_path.exists():
            try:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                from fastapi.responses import Response
                return Response(
                    content=image_data,
                    media_type=content_type,
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Content-Disposition": f'inline; filename="{selected_image["filename"]}"'
                    }
                )
            except Exception as e:
                logger.error(f"❌ Error reading image file: {e}")
                raise HTTPException(status_code=500, detail=f"Error reading image file: {str(e)}")
        else:
            logger.error(f"❌ Image file not found: {image_path}")
            raise HTTPException(status_code=404, detail=f"Image file not found: {selected_image['filename']}")
        
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving texture image {image_index} for asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve texture image: {str(e)}")

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
    """Proper HDRI EXR to PNG conversion with tone mapping using oiiotool
    Returns: tuple (success: bool, resolution: dict)
    """
    try:
        logger.info(f"🔧 Converting EXR to PNG: {hdr_path} -> {png_path}")
        resolution_info = {}
        
        # Method 1: Try oiiotool first (BEST for HDR tone mapping)
        try:
            import subprocess
            import os
            
            logger.info(f"🔧 Using oiiotool for EXR conversion with proper tone mapping")
            
            # Check if oiiotool is available
            result = subprocess.run(['which', 'oiiotool'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("oiiotool not found in PATH")
            
            # Use oiiotool with color space conversion for proper tone mapping
            cmd = [
                'oiiotool',
                str(hdr_path),
                '--colorconvert', 'linear', 'srgb',  # Convert from linear to sRGB for proper display
                '-o', str(png_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully converted EXR with tone mapping using oiiotool")
                
                # Get image dimensions using oiiotool
                info_cmd = ['oiiotool', '--info', str(hdr_path)]
                info_result = subprocess.run(info_cmd, capture_output=True, text=True)
                
                if info_result.returncode == 0:
                    # Parse output for dimensions
                    output = info_result.stdout
                    # Look for pattern like "2048 x 1024"
                    import re
                    match = re.search(r'(\d+)\s*x\s*(\d+)', output)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        resolution_info = {
                            "width": width,
                            "height": height,
                            "resolution": f"{width}x{height}",
                            "channels": 4  # Default to 4 for PNG output
                        }
                        logger.info(f"📏 Extracted resolution: {resolution_info['resolution']}")
                
                return True, resolution_info
            else:
                logger.warning(f"⚠️ oiiotool conversion failed: {result.stderr}")
                raise Exception(f"oiiotool failed: {result.stderr}")
                
        except Exception as e:
            logger.info(f"   ℹ️ oiiotool not available or failed: {e}")
        
        # Method 2: Try ImageIO fallback (excellent EXR support)
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
            
            # Store resolution information
            resolution_info = {
                "width": int(width),
                "height": int(height),
                "resolution": f"{width}x{height}",
                "channels": int(channels)
            }
            
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
            return True, resolution_info
            
        except ImportError:
            logger.info(f"   ℹ️ ImageIO not available")
        except Exception as e:
            logger.info(f"   ⚠️ ImageIO conversion failed: {e}")
        
        # Method 3: Try OpenCV fallback
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
            channels = img.shape[2] if len(img.shape) > 2 else 1
            
            # Store resolution information for OpenCV branch
            resolution_info = {
                "width": int(original_width),
                "height": int(original_height),
                "resolution": f"{original_width}x{original_height}",
                "channels": int(channels)
            }
            
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
            return True, resolution_info
            
        except ImportError:
            logger.info(f"   ℹ️ OpenCV not available")
        except Exception as e:
            logger.info(f"   ⚠️ OpenCV conversion failed: {e}")
        
        logger.error(f"❌ All EXR conversion methods failed")
        return False, {}
            
    except Exception as e:
        logger.error(f"❌ EXR conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

def convert_texture_exr_to_png(exr_path, png_path):
    """Convert texture EXR to PNG WITHOUT tone mapping (for textures only)
    Returns: tuple (success: bool, resolution: dict)
    """
    try:
        logger.info(f"🔧 Converting texture EXR to PNG (no tone mapping): {exr_path} -> {png_path}")
        
        # Try oiiotool first (without tone mapping for textures)
        try:
            import subprocess
            
            # Check if oiiotool is available
            result = subprocess.run(['which', 'oiiotool'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("oiiotool not found in PATH")
            
            # Get original dimensions first to calculate proper resize without upscaling
            info_cmd = ['oiiotool', '--info', str(exr_path)]
            info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=10)
            
            resize_arg = '1024x1024'  # Default fallback
            if info_result.returncode == 0:
                import re
                match = re.search(r'(\d+)\s*x\s*(\d+)', info_result.stdout)
                if match:
                    original_width = int(match.group(1))
                    original_height = int(match.group(2))
                    max_dimension = 1024
                    
                    # Don't downscale if either dimension is already below 1028
                    if original_width <= 1028 or original_height <= 1028:
                        # Keep original size - one dimension is already small enough
                        new_width = original_width
                        new_height = original_height
                        scale_factor = 1.0
                        resize_arg = f'{new_width}x{new_height}'
                        logger.info(f"📏 EXR: Keeping original size - one dimension already <= 1028")
                    else:
                        # Calculate scale factor to never upscale
                        scale_factor = min(
                            max_dimension / original_width,
                            max_dimension / original_height,
                            1.0  # Never exceed original size
                        )
                        
                        new_width = int(original_width * scale_factor)
                        new_height = int(original_height * scale_factor)
                        resize_arg = f'{new_width}x{new_height}'
                    
                    logger.info(f"📏 EXR oiiotool: {original_width}x{original_height} -> {resize_arg} (scale: {scale_factor:.3f})")

            # Use oiiotool WITHOUT color conversion but resize appropriately
            cmd = [
                'oiiotool',
                str(exr_path),
                '--resize', resize_arg,
                '-o', str(png_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully converted texture EXR without tone mapping using oiiotool")
                return True, {}
            else:
                logger.warning(f"⚠️ oiiotool failed for texture EXR: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"⚠️ oiiotool not available for texture conversion: {e}")
        
        # Fallback to PIL/OpenCV for texture EXR conversion
        try:
            from PIL import Image
            import numpy as np
            
            # Try OpenCV for EXR reading
            try:
                import cv2
                img_array = cv2.imread(str(exr_path), cv2.IMREAD_UNCHANGED)
                if img_array is not None:
                    # Convert to RGB and normalize for PNG
                    if img_array.dtype == np.float32:
                        # Clamp values to 0-1 range without tone mapping
                        img_array = np.clip(img_array, 0, 1)
                        img_array = (img_array * 255).astype(np.uint8)
                    
                    # Convert BGR to RGB
                    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                    
                    img = Image.fromarray(img_array)
                    img.save(png_path, 'PNG')
                    logger.info(f"✅ Successfully converted texture EXR using OpenCV fallback")
                    return True, {}
            except ImportError:
                logger.warning("⚠️ OpenCV not available for texture EXR conversion")
            
            # Final fallback - try PIL directly 
            with Image.open(exr_path) as img:
                img = img.convert('RGBA')
                img.save(png_path, 'PNG')
                logger.info(f"✅ Successfully converted texture EXR using PIL fallback")
                return True, {}
                
        except Exception as fallback_error:
            logger.error(f"❌ All texture EXR conversion methods failed: {fallback_error}")
            return False, {}
            
    except Exception as e:
        logger.error(f"❌ Texture EXR conversion error: {e}")
        return False, {}

# Helper functions for texture processing
def get_texture_position_and_type_from_slot(texture_slot_key):
    """Get position and type for texture thumbnails based on the upload slot the user chose"""
    # Map texture slots to position and display name
    slot_mapping = {
        'baseColor': ('0', 'BaseColor'),
        'metallic': ('1', 'Metallic'), 
        'roughness': ('2', 'Roughness'),
        'normal': ('3', 'Normal'),
        'opacity': ('4', 'Opacity'),
        'displacement': ('5', 'Displacement')
    }
    
    return slot_mapping.get(texture_slot_key, ('9', 'Unknown'))

async def generate_texture_thumbnail(source_file, thumbnail_file):
    """Generate thumbnail for texture files, handling EXR conversion WITHOUT tone mapping"""
    try:
        source_path = Path(source_file)
        
        if source_path.suffix.lower() in {'.exr'}:
            # Use NEW texture EXR conversion WITHOUT tone mapping
            logger.info(f"🔧 Converting texture EXR to PNG (no tone mapping): {source_path}")
            success, _ = convert_texture_exr_to_png(source_path, thumbnail_file)
            if success:
                logger.info(f"✅ Created EXR texture thumbnail: {thumbnail_file}")
                return True
            else:
                logger.warning(f"⚠️ Failed to convert texture EXR: {source_path}")
                return False
                
        elif source_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}:
            # Resize texture images preserving aspect ratio, max dimension 1024
            logger.info(f"🔧 Resizing texture image (preserving aspect ratio): {source_path} -> {thumbnail_file}")
            
            # Check original file size first
            try:
                original_size = source_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"📏 Original file size: {original_size:.1f} MB")
            except:
                pass
                
            try:
                # First try with oiiotool for better quality
                import subprocess
                # Get original dimensions first to calculate proper resize without upscaling
                info_cmd = ['oiiotool', '--info', str(source_path)]
                info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=10)
                
                resize_arg = '1024x1024'  # Default fallback
                if info_result.returncode == 0:
                    import re
                    match = re.search(r'(\d+)\s*x\s*(\d+)', info_result.stdout)
                    if match:
                        original_width = int(match.group(1))
                        original_height = int(match.group(2))
                        max_dimension = 1024
                        
                        # Don't downscale if either dimension is already below 1028
                        if original_width <= 1028 or original_height <= 1028:
                            # Keep original size - one dimension is already small enough
                            new_width = original_width
                            new_height = original_height
                            scale_factor = 1.0
                            logger.info(f"📏 Keeping original size - one dimension already <= 1028")
                        else:
                            # Calculate scale factor to never upscale, only downscale large images
                            scale_factor = min(
                                max_dimension / original_width,
                                max_dimension / original_height,
                                1.0  # Never exceed original size
                            )
                            
                            new_width = int(original_width * scale_factor)
                            new_height = int(original_height * scale_factor)
                        resize_arg = f'{new_width}x{new_height}'
                        
                        logger.info(f"📏 oiiotool: {original_width}x{original_height} -> {resize_arg} (scale: {scale_factor:.3f})")
                
                cmd = [
                    'oiiotool',
                    str(source_path),
                    '--resize', resize_arg,
                    '--colorconvert', 'sRGB', 'sRGB',
                    '-o', str(thumbnail_file)
                ]
                
                logger.info(f"🔧 Running oiiotool command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Check resulting file size
                    try:
                        final_size = Path(thumbnail_file).stat().st_size / (1024 * 1024)  # MB
                        logger.info(f"✅ Created resized thumbnail with oiiotool: {thumbnail_file} ({final_size:.1f} MB)")
                    except:
                        logger.info(f"✅ Created resized thumbnail with oiiotool: {thumbnail_file}")
                    return True
                else:
                    logger.warning(f"⚠️ oiiotool failed: {result.stderr}")
                    logger.warning(f"⚠️ oiiotool stdout: {result.stdout}")
                    
                    # Fallback to PIL
                    logger.info("🔄 Falling back to PIL for resizing...")
                    from PIL import Image
                    with Image.open(source_path) as img:
                        logger.info(f"📏 Original PIL image size: {img.size}")
                        
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                            logger.info(f"🎨 Converted image mode from {img.mode} to RGB")
                        
                        # Calculate new size preserving aspect ratio, max dimension 1024 (never upscale)
                        original_width, original_height = img.size
                        max_dimension = 1024
                        
                        # Don't downscale if either dimension is already below 1028
                        if original_width <= 1028 or original_height <= 1028:
                            # Keep original size - one dimension is already small enough
                            new_width = original_width
                            new_height = original_height
                            scale_factor = 1.0
                            logger.info(f"📏 PIL: Keeping original size - one dimension already <= 1028")
                        else:
                            # Find the scaling factor needed - only downscale, never upscale
                            scale_factor = min(
                                max_dimension / original_width,
                                max_dimension / original_height,
                                1.0  # Never exceed original size (no upscaling)
                            )
                            
                            new_width = int(original_width * scale_factor)
                            new_height = int(original_height * scale_factor)
                        
                        logger.info(f"📏 Scale factor: {scale_factor:.3f} ({original_width}x{original_height} -> {new_width}x{new_height})")
                        
                        # Resize preserving aspect ratio
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        logger.info(f"📏 Resized image from {original_width}x{original_height} to: {img.size} (aspect ratio preserved)")
                        
                        # Save as PNG for thumbnails
                        img.save(thumbnail_file, 'PNG', optimize=True)
                        
                        # Check resulting file size
                        try:
                            final_size = Path(thumbnail_file).stat().st_size / (1024 * 1024)  # MB
                            logger.info(f"✅ Created resized thumbnail with PIL: {thumbnail_file} ({final_size:.1f} MB)")
                        except:
                            logger.info(f"✅ Created resized thumbnail with PIL: {thumbnail_file}")
                        return True
                        
            except Exception as e:
                logger.error(f"❌ Failed to resize texture image: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                
                # Final fallback - just copy the original
                logger.warning(f"⚠️ Falling back to copying original file")
                import shutil
                shutil.copy2(source_path, thumbnail_file)
                
                try:
                    final_size = Path(thumbnail_file).stat().st_size / (1024 * 1024)  # MB
                    logger.warning(f"⚠️ Using original size as thumbnail: {thumbnail_file} ({final_size:.1f} MB)")
                except:
                    logger.warning(f"⚠️ Using original size as thumbnail: {thumbnail_file}")
                return True
            
        else:
            logger.warning(f"⚠️ Unsupported texture format for thumbnail: {source_path.suffix}")
            return False
                
    except Exception as e:
        logger.warning(f"⚠️ Failed to generate thumbnail: {e}")
        return False

async def extract_image_info(image_file):
    """Extract resolution and channel info from image files"""
    try:
        image_path = Path(image_file)
        
        if image_path.suffix.lower() in {'.exr', '.hdr', '.hdri'}:
            # For EXR files, try to get info using imageio
            try:
                import imageio.v3 as iio
                import numpy as np
                image_array = iio.imread(str(image_path))
                if image_array is not None:
                    height, width = image_array.shape[:2]
                    channels = image_array.shape[2] if len(image_array.shape) > 2 else 1
                    return {
                        "width": int(width),
                        "height": int(height),
                        "resolution": f"{width}x{height}",
                        "channels": int(channels)
                    }
            except ImportError:
                logger.info("ImageIO not available for EXR info extraction")
        else:
            # Regular image files
            from PIL import Image
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "resolution": f"{img.width}x{img.height}",
                    "channels": len(img.getbands()) if hasattr(img, 'getbands') else 4
                }
                
    except Exception as e:
        logger.warning(f"⚠️ Failed to extract image info: {e}")
    
    return {
        "width": 1024,
        "height": 1024,
        "resolution": "1024x1024",
        "channels": 4
    }

# Upload Asset Request Model
class UploadAssetRequest(BaseModel):
    asset_type: str  # 'Textures' or 'HDRI'
    name: str
    file_path: Optional[str] = None  # Optional for texture sets, required for single files
    preview_path: Optional[str] = None  # Optional preview JPEG/PNG for HDRIs
    preview_image_path: Optional[str] = None  # Optional preview image for texture badge display
    description: Optional[str] = ""
    dimension: str = "3D"
    created_by: str = "web_uploader"
    subcategory: Optional[str] = None  # For HDRI/Texture categories
    alpha_subcategory: Optional[str] = None  # For Alpha texture subcategories
    texture_set_paths: Optional[dict] = None  # For texture sets with multiple files
    # Texture type metadata
    texture_type: Optional[str] = None  # 'seamless' or 'uv_tile'
    seamless: Optional[bool] = None  # True if texture is seamless
    uv_tile: Optional[bool] = None  # True if texture uses UV tiles

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
        
        # Separate validation logic for HDRI vs Textures
        if upload_request.asset_type == 'HDRI':
            # HDRI uploads: Always require a file_path
            if not upload_request.file_path or not upload_request.file_path.strip():
                raise HTTPException(status_code=400, detail="File path is required for HDRI uploads")
            
            source_file = Path(upload_request.file_path)
            if not source_file.exists():
                # Provide helpful error with mount information
                error_msg = f"HDRI source file not found: {upload_request.file_path}\n\n"
                error_msg += "Available mounted paths in container:\n"
                error_msg += "- /app/assets (atlas library - output only)\n"
                error_msg += "- /net/general (general network drive - READ ONLY)\n"
                error_msg += "- /net/library/library (library drive - READ ONLY)\n"
                error_msg += "\nMake sure the file path starts with one of these mounted directories."
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Check if file is a supported HDRI format
            hdri_extensions = {'.exr', '.hdr', '.hdri'}
            if source_file.suffix.lower() not in hdri_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported HDRI file format: {source_file.suffix}. Supported: {', '.join(hdri_extensions)}"
                )
            
            logger.info(f"📋 HDRI upload validated: {source_file}")
            
        elif upload_request.asset_type == 'Textures':
            # Handle different texture subcategories
            if upload_request.subcategory == 'Texture Sets' and upload_request.texture_set_paths:
                # Texture Sets: Validate texture_set_paths
                if not any(path and path.strip() for path in upload_request.texture_set_paths.values()):
                    raise HTTPException(status_code=400, detail="At least one texture file path must be provided for texture sets")
                
                # Validate each provided texture file
                texture_extensions = {'.exr', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}
                for key, file_path in upload_request.texture_set_paths.items():
                    if file_path and file_path.strip():
                        source_file = Path(file_path.strip())
                        if not source_file.exists():
                            raise HTTPException(status_code=400, detail=f"{key.title()} texture file not found: {file_path}")
                        
                        if source_file.suffix.lower() not in texture_extensions:
                            raise HTTPException(
                                status_code=400, 
                                detail=f"Unsupported file format for {key} texture: {source_file.suffix}. Supported: {', '.join(texture_extensions)}"
                            )
                
                logger.info(f"📋 Texture set upload validated: {len([p for p in upload_request.texture_set_paths.values() if p and p.strip()])} texture files provided")
                
            else:
                # Single Textures (Alpha, Base Color, etc.): Require file_path (optional now)
                if upload_request.file_path and upload_request.file_path.strip():
                    source_file = Path(upload_request.file_path)
                    if not source_file.exists():
                        error_msg = f"Texture source file not found: {upload_request.file_path}\n\n"
                        error_msg += "Available mounted paths in container:\n"
                        error_msg += "- /app/assets (atlas library - output only)\n"
                        error_msg += "- /net/general (general network drive - READ ONLY)\n"
                        error_msg += "- /net/library/library (library drive - READ ONLY)\n"
                        error_msg += "\nMake sure the file path starts with one of these mounted directories."
                        raise HTTPException(status_code=400, detail=error_msg)
                    
                    # Check if file is a supported texture format
                    texture_extensions = {'.exr', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}
                    if source_file.suffix.lower() not in texture_extensions:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Unsupported texture file format: {source_file.suffix}. Supported: {', '.join(texture_extensions)}"
                        )
                    
                    logger.info(f"📋 Single texture upload validated: {source_file}")
        
        else:
            raise HTTPException(status_code=400, detail="Asset type must be 'HDRI' or 'Textures'")
        
        # Clean and validate asset name
        clean_asset_name = upload_request.name.strip()
        if not clean_asset_name:
            raise HTTPException(status_code=400, detail="Asset name cannot be empty")
        
        # Generate unique asset ID for HDRI and Texture uploads
        # Simple 10-character UID based on time (different from Houdini 3D assets)
        import time
        timestamp = str(int(time.time() * 1000))  # Millisecond timestamp for uniqueness
        hash_input = f"{upload_request.name}_{upload_request.asset_type}_{timestamp}".encode()
        asset_id = hashlib.md5(hash_input).hexdigest()[:10].upper()  # 10-character UID
        asset_base_id = asset_id  # Same as asset_id since no variants/versions
        
        # Create folder structure for uploaded asset
        # Structure: /app/assets/3D/{Textures|HDRI}/{Subcategory}/{10_CHAR_UID}/
        # Examples: /app/assets/3D/HDRI/Outdoor/A1B2C3D4E5/
        #          /app/assets/3D/Textures/Alpha/F8A2B7E9D1/
        #   ├── Asset/          # ACTUAL asset file (original .exr/.hdr/etc)  
        #   ├── Thumbnail/      # Converted PNG for web (EXACT aspect ratio)
        #   └── metadata.json   # Database entry
        asset_library_path = Path(os.getenv('ASSET_LIBRARY_PATH', '/app/assets'))
        # Place assets in their subcategory folders: HDRI/Outdoor, Textures/Alpha, etc.
        category_path = asset_library_path / "3D" / upload_request.asset_type / upload_request.subcategory
        # For HDRI and Texture uploads: folder name is just the UID (no asset name)
        asset_folder = category_path / asset_id
        
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
        preview_folder = asset_folder / "Preview"  # This holds the preview image for texture badge display
        asset_subfolder.mkdir(exist_ok=True)
        thumbnail_folder.mkdir(exist_ok=True)
        preview_folder.mkdir(exist_ok=True)
        
        # Handle file copying and thumbnail generation based on asset type
        copied_files = []
        thumbnails_created = []
        preview_files_created = []
        resolution_info = None
        
        if upload_request.asset_type == 'HDRI':
            # HDRI Logic: Single file handling
            target_file = asset_subfolder / source_file.name
            shutil.copy2(source_file, target_file)
            copied_files.append(convert_to_network_path(str(target_file)))
            logger.info(f"📋 Copied HDRI file to Asset folder: {source_file} -> {target_file}")
            
            # First, extract resolution from the EXR HDRI file (this is the real resolution)
            try:
                resolution_info = await extract_image_info(target_file)
                logger.info(f"📏 Extracted EXR resolution: {resolution_info}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract EXR resolution, using defaults: {e}")
                resolution_info = {
                    "width": 4096,
                    "height": 2048,
                    "resolution": "4096x2048",
                    "channels": 4
                }

            # Handle HDRI preview/thumbnail - downscale to match EXR resolution
            thumbnail_file = thumbnail_folder / f"{clean_asset_name}_thumbnail.png"
            if upload_request.preview_path:
                try:
                    preview_source = Path(upload_request.preview_path)
                    if preview_source.exists():
                        # Get EXR dimensions for target resize
                        exr_width = resolution_info.get("width", 4096)
                        exr_height = resolution_info.get("height", 2048)
                        
                        # Resize the preview/thumbnail to match EXR resolution
                        from PIL import Image
                        with Image.open(preview_source) as preview_img:
                            logger.info(f"📏 Original preview size: {preview_img.size}")
                            
                            # Resize to match EXR dimensions exactly
                            resized_preview = preview_img.resize((exr_width, exr_height), Image.Resampling.LANCZOS)
                            resized_preview.save(thumbnail_file, 'PNG', optimize=True)
                            
                            logger.info(f"✅ Resized HDRI preview to match EXR: {preview_source} -> {thumbnail_file} ({exr_width}x{exr_height})")
                            
                        thumbnails_created.append(str(thumbnail_file))
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process HDRI preview: {e}")
        
        elif upload_request.asset_type == 'Textures':
            # Texture Logic: Handle single files or texture sets
            if upload_request.subcategory == 'Texture Sets' and upload_request.texture_set_paths:
                # Texture Set: Multiple files
                texture_paths = upload_request.texture_set_paths
                # Process textures in priority order: BC → M → R → N → O → D
                from collections import OrderedDict
                texture_map = OrderedDict([
                    ('baseColor', 'Base_Color'),
                    ('metallic', 'Metallic'), 
                    ('roughness', 'Roughness'),
                    ('normal', 'Normal'),
                    ('opacity', 'Opacity'),
                    ('displacement', 'Displacement')
                ])
                
                for key, display_name in texture_map.items():
                    file_path = texture_paths.get(key)
                    if file_path and file_path.strip():
                        try:
                            source_path = Path(file_path.strip())
                            if source_path.exists():
                                # Copy texture file to Asset folder (preserve original filename)
                                target_file = asset_subfolder / source_path.name
                                shutil.copy2(source_path, target_file)
                                copied_files.append(convert_to_network_path(str(target_file)))
                                logger.info(f"📋 Copied {display_name} texture: {source_path} -> {target_file}")
                                
                                # Generate thumbnail with asset name, position, and type based on upload slot
                                position, texture_type = get_texture_position_and_type_from_slot(key)
                                # Clean asset name - replace spaces with underscores
                                clean_asset_name_for_thumbnail = clean_asset_name.replace(' ', '_')
                                thumbnail_file = thumbnail_folder / f"{clean_asset_name_for_thumbnail}_{position}_{texture_type}_thumbnail.png"
                                if await generate_texture_thumbnail(target_file, thumbnail_file):
                                    thumbnails_created.append(str(thumbnail_file))
                                    
                                    # Use Base Color for resolution info
                                    if key == 'baseColor' and not resolution_info:
                                        resolution_info = await extract_image_info(target_file)
                                        
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to process {display_name} texture: {e}")
                            continue
                            
            else:
                # Single Texture: One file
                target_file = asset_subfolder / source_file.name
                shutil.copy2(source_file, target_file)
                copied_files.append(convert_to_network_path(str(target_file)))
                logger.info(f"📋 Copied texture file to Asset folder: {source_file} -> {target_file}")
                
                # For single textures, default to BaseColor (position 0) - user should specify if different
                # TODO: Add texture_slot field to UploadAssetRequest for single textures
                position, texture_type = get_texture_position_and_type_from_slot('baseColor')  # Default to baseColor
                # Clean asset name - replace spaces with underscores
                clean_asset_name_for_thumbnail = clean_asset_name.replace(' ', '_')
                thumbnail_file = thumbnail_folder / f"{clean_asset_name_for_thumbnail}_{position}_{texture_type}_thumbnail.png"
                if await generate_texture_thumbnail(target_file, thumbnail_file):
                    thumbnails_created.append(str(thumbnail_file))
                    resolution_info = await extract_image_info(target_file)

        # Handle Preview image for Textures (if provided)
        if upload_request.asset_type == 'Textures' and upload_request.preview_image_path:
            try:
                preview_source = Path(upload_request.preview_image_path)
                if preview_source.exists():
                    # Generate resized preview image using same logic as thumbnails
                    preview_file = preview_folder / "Preview.png"
                    
                    # Use the same thumbnail generation function for consistent sizing and EXR handling
                    logger.info(f"🔧 Processing preview image: {preview_source}")
                    if await generate_texture_thumbnail(preview_source, preview_file):
                        preview_files_created.append(str(preview_file))
                        logger.info(f"✅ Created resized preview image: {preview_source} -> {preview_file}")
                    else:
                        logger.warning(f"⚠️ Failed to generate preview thumbnail, trying fallback...")
                        # Fallback to simple copy if thumbnail generation fails
                        import shutil
                        shutil.copy2(preview_source, preview_file)
                        preview_files_created.append(str(preview_file))
                        logger.warning(f"⚠️ Used original preview image: {preview_file}")
                else:
                    logger.warning(f"⚠️ Preview image source not found: {preview_source}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to process preview image: {e}")
        
        # Create metadata.json file
        metadata = {
            "id": asset_id,
            "name": clean_asset_name,
            "asset_type": upload_request.asset_type,
            "dimension": upload_request.dimension,
            "created_by": upload_request.created_by,
            "created_at": datetime.now().isoformat(),
            "description": upload_request.description,
            "subcategory": upload_request.subcategory,
            "file_info": {
                "original_path": str(source_file) if upload_request.asset_type == 'HDRI' or upload_request.subcategory != 'Texture Sets' else None,
                "filename": source_file.name if upload_request.asset_type == 'HDRI' or upload_request.subcategory != 'Texture Sets' else None,
                "size_bytes": source_file.stat().st_size if upload_request.asset_type == 'HDRI' or upload_request.subcategory != 'Texture Sets' else None,
                "extension": source_file.suffix if upload_request.asset_type == 'HDRI' or upload_request.subcategory != 'Texture Sets' else None
            },
            "paths": {
                "asset_folder": convert_to_network_path(str(asset_folder)),
                "asset_subfolder": convert_to_network_path(str(asset_subfolder)),
                "copied_files": copied_files,
                "thumbnails": thumbnails_created,
                "preview_files": preview_files_created
            }
        }
        
        # Add texture-specific metadata
        if upload_request.asset_type == 'Textures':
            if upload_request.alpha_subcategory:
                metadata["alpha_subcategory"] = upload_request.alpha_subcategory
            
            # Add texture type metadata fields
            if upload_request.texture_type is not None:
                metadata["texture_type"] = upload_request.texture_type
            
            if upload_request.seamless is not None:
                metadata["seamless"] = upload_request.seamless
            
            if upload_request.uv_tile is not None:
                metadata["uv_tile"] = upload_request.uv_tile
            
            # Generate comprehensive texture tags for metadata
            texture_tags = generate_texture_tags(
                asset_name=clean_asset_name,
                subcategory=upload_request.subcategory,
                alpha_subcategory=upload_request.alpha_subcategory,
                texture_set_paths=upload_request.texture_set_paths,
                texture_type=upload_request.texture_type,
                seamless=upload_request.seamless,
                uv_tile=upload_request.uv_tile,
                resolution_info=resolution_info
            )
            
            # Add tags to metadata
            metadata["tags"] = texture_tags
            
            if upload_request.subcategory == 'Texture Sets' and upload_request.texture_set_paths:
                # Add texture slot mapping for frontend
                texture_slots = {}
                for key, file_path in upload_request.texture_set_paths.items():
                    if file_path and file_path.strip():
                        position, texture_type = get_texture_position_and_type_from_slot(key)
                        texture_slots[key] = {
                            "position": position,
                            "type": texture_type,
                            "original_filename": Path(file_path).name if file_path else None
                        }
                
                metadata["texture_set_info"] = {
                    "type": "texture_set",
                    "provided_paths": upload_request.texture_set_paths,
                    "file_count": len([p for p in upload_request.texture_set_paths.values() if p and p.strip()]),
                    "texture_slots": texture_slots
                }
        
        # Add resolution information if available
        if resolution_info:
            metadata["resolution"] = resolution_info["resolution"]
            metadata["dimensions"] = {
                "width": resolution_info["width"],
                "height": resolution_info["height"],
                "channels": resolution_info["channels"]
            }
            logger.info(f"📏 Added resolution to metadata: {resolution_info['resolution']}")
        
        metadata_file = asset_folder / "metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"📄 Created metadata file: {metadata_file}")
        
        # Calculate total file sizes
        total_size = 0
        if upload_request.asset_type == 'HDRI' or upload_request.subcategory != 'Texture Sets':
            total_size = source_file.stat().st_size
        else:
            # For texture sets, sum all file sizes
            for file_path in copied_files:
                try:
                    total_size += Path(file_path).stat().st_size
                except:
                    pass
        
        # Create asset document for database
        asset_doc = {
            "_key": asset_id,
            "id": asset_id,
            "name": clean_asset_name,
            "category": upload_request.subcategory,  # Use subcategory as main category for textures
            "dimension": upload_request.dimension,
            "asset_type": upload_request.asset_type,
            "hierarchy": {
                "dimension": upload_request.dimension,
                "asset_type": upload_request.asset_type,
                "subcategory": upload_request.subcategory or "General"
            },
            "metadata": metadata,
            "paths": {
                "folder_path": convert_to_network_path(str(asset_folder)),
                "asset_folder": convert_to_network_path(str(asset_folder)),
                "asset_subfolder": convert_to_network_path(str(asset_subfolder)),
                "copied_files": copied_files,
                "thumbnails": thumbnails_created
            },
            "file_sizes": {
                "copied_files": len(copied_files),
                "estimated_total_size": total_size
            },
            "tags": [
                "uploaded", 
                upload_request.asset_type.lower(),
                upload_request.subcategory.lower().replace(' ', '_') if upload_request.subcategory else "general"
            ],
            "created_at": datetime.now().isoformat(),
            "created_by": upload_request.created_by,
            "status": "active",
            "folder_path": str(asset_folder)  # For compatibility with existing frontend
        }
        
        # Add texture-specific fields to database document
        if upload_request.asset_type == 'Textures':
            if upload_request.alpha_subcategory:
                asset_doc["alpha_subcategory"] = upload_request.alpha_subcategory
                asset_doc["tags"].append(upload_request.alpha_subcategory.lower())
            
            if upload_request.subcategory == 'Texture Sets':
                asset_doc["texture_set"] = True
                asset_doc["texture_count"] = len(copied_files)
            
            # Add texture type metadata
            if upload_request.texture_type:
                asset_doc["texture_type"] = upload_request.texture_type
                asset_doc["tags"].append(upload_request.texture_type)
            
            if upload_request.seamless is not None:
                asset_doc["seamless"] = upload_request.seamless
                if upload_request.seamless:
                    asset_doc["tags"].append("seamless")
            
            if upload_request.uv_tile is not None:
                asset_doc["uv_tile"] = upload_request.uv_tile
                if upload_request.uv_tile:
                    asset_doc["tags"].append("uv_tile")
            
            # Generate comprehensive texture tags
            texture_tags = generate_texture_tags(
                asset_name=clean_asset_name,
                subcategory=upload_request.subcategory,
                alpha_subcategory=upload_request.alpha_subcategory,
                texture_set_paths=upload_request.texture_set_paths,
                texture_type=upload_request.texture_type,
                seamless=upload_request.seamless,
                uv_tile=upload_request.uv_tile,
                resolution_info=resolution_info
            )
            
            # Add all texture tags to the asset document
            asset_doc["tags"].extend(texture_tags)
        
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


@router.post("/assets/{asset_id}/update-preview")
async def update_asset_preview_image(
    asset_id: str, 
    file: UploadFile = File(...)
):
    """Update or create preview image for a texture set asset"""
    try:
        # Get asset queries instance
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Get asset data from database
        asset_result = asset_queries.get_asset_with_dependencies(asset_id)
        asset_data = asset_result.get('asset') if asset_result else None
        if not asset_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        # Verify this is a texture set asset
        if asset_data.get('asset_type') != 'Textures' or asset_data.get('category') != 'Texture Sets':
            raise HTTPException(status_code=400, detail="Preview image update is only available for Texture Sets")
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Get asset folder path
        asset_folder_path = asset_data.get('paths', {}).get('asset_folder')
        if not asset_folder_path:
            raise HTTPException(status_code=404, detail="Asset folder path not found")
        
        # Convert to container path (backend runs in container)
        container_path = asset_folder_path.replace('/net/library/atlaslib', '/app/assets')
        asset_folder = Path(container_path)
        
        if not asset_folder.exists():
            raise HTTPException(status_code=404, detail=f"Asset folder not found: {asset_folder}")
        
        # Create Preview folder if it doesn't exist
        preview_folder = asset_folder / "Preview"
        preview_folder.mkdir(exist_ok=True)
        logger.info(f"📁 Preview folder ready: {preview_folder}")
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            # Save uploaded file to temporary location
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)
            logger.info(f"📄 Saved uploaded file to temp: {temp_path}")
        
        try:
            # Define target preview file path
            preview_file = preview_folder / "Preview.png"
            
            # Process the uploaded image using simplified robust approach
            logger.info(f"🔧 Processing preview image: {temp_path} -> {preview_file}")
            
            # Use the same simplified approach we fixed earlier
            success = False
            try:
                # Simple approach: Use PIL for reliable image processing
                from PIL import Image
                import shutil
                
                # For non-image files or if PIL fails, just copy the file
                if temp_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                    try:
                        # Open, convert to RGB if needed, and save as PNG
                        with Image.open(temp_path) as img:
                            # Convert to RGB if necessary (handles RGBA, etc.)
                            if img.mode in ('RGBA', 'LA', 'P'):
                                # Create white background for transparency
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'RGBA':
                                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                                else:
                                    rgb_img.paste(img)
                                img = rgb_img
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Resize if too large (max 2048x2048 for preview) - PRESERVE ASPECT RATIO
                            max_size = 2048
                            if img.width > max_size or img.height > max_size:
                                # Calculate new size preserving aspect ratio (no cropping!)
                                scale_factor = min(max_size / img.width, max_size / img.height)
                                new_width = int(img.width * scale_factor)
                                new_height = int(img.height * scale_factor)
                                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                logger.info(f"📏 Resized preview preserving aspect ratio: {img.width}x{img.height} -> {new_width}x{new_height}")
                            
                            # Save as PNG with good quality
                            img.save(preview_file, 'PNG', optimize=True, quality=95)
                            success = True
                            logger.info(f"✅ PIL processing successful: {preview_file}")
                            
                    except Exception as pil_error:
                        logger.warning(f"⚠️ PIL processing failed: {pil_error}")
                        # Fallback to direct copy
                        shutil.copy2(temp_path, preview_file)
                        success = True
                        logger.info(f"✅ Used direct copy as fallback: {preview_file}")
                else:
                    # For TIFF, TIF, EXR - just copy directly (let browser handle)
                    shutil.copy2(temp_path, preview_file)
                    success = True
                    logger.info(f"✅ Direct copy for {temp_path.suffix}: {preview_file}")
                    
            except Exception as process_error:
                logger.error(f"❌ Preview processing failed: {process_error}")
                success = False
            
            if success:
                logger.info(f"✅ Successfully created preview image: {preview_file}")
                
                # Update database with preview file path
                try:
                    # Convert back to network path for database storage
                    network_preview_path = str(preview_file).replace('/app/assets/', '/net/library/atlaslib/')
                    
                    # Get existing preview files or initialize empty list
                    preview_files = asset_data.get('paths', {}).get('preview_files', [])
                    
                    # Update or add the preview file path
                    if network_preview_path not in preview_files:
                        preview_files = [network_preview_path]  # Replace with single preview file
                    
                    # Update the asset document paths
                    update_data = {
                        'paths.preview_files': preview_files
                    }
                    
                    # Update in database using AQL
                    aql_query = """
                        FOR doc IN Atlas_Library
                        FILTER doc._key == @asset_id
                        UPDATE doc WITH @updates IN Atlas_Library
                        RETURN NEW
                    """
                    bind_vars = {'asset_id': asset_id, 'updates': update_data}
                    
                    cursor = asset_queries.db.aql.execute(aql_query, bind_vars=bind_vars)
                    result_list = list(cursor)
                    
                    if result_list:
                        logger.info(f"✅ Updated database with preview file path: {network_preview_path}")
                    else:
                        logger.warning(f"⚠️ Failed to update database with preview file path")
                    
                except Exception as db_error:
                    logger.error(f"❌ Failed to update database: {db_error}")
                    # Don't fail the entire operation if DB update fails, preview file is still created
                
                return {
                    "success": True,
                    "message": "Preview image updated successfully",
                    "asset_id": asset_id,
                    "preview_path": str(preview_file)
                }
            else:
                # If processing failed, try fallback to simple copy
                logger.warning(f"⚠️ Preview processing failed, trying fallback copy...")
                try:
                    shutil.copy2(temp_path, preview_file)
                    logger.info(f"✅ Used original preview image as fallback: {preview_file}")
                    
                    return {
                        "success": True,
                        "message": "Preview image updated successfully (original copy)",
                        "asset_id": asset_id,
                        "preview_path": str(preview_file)
                    }
                except Exception as copy_error:
                    logger.error(f"❌ Fallback copy failed: {copy_error}")
                    raise HTTPException(status_code=500, detail=f"Failed to save preview image: {str(copy_error)}")
                
        finally:
            # Clean up temporary file
            try:
                temp_path.unlink()
                logger.info(f"🧹 Cleaned up temporary file: {temp_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Failed to cleanup temp file: {cleanup_error}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Preview update failed: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Preview update failed: {str(e)}")


@router.post("/assets/{asset_id}/update-preview-from-path")
async def update_asset_preview_image_from_path(
    asset_id: str, 
    request: dict
):
    """Update or create preview image for a texture set asset from a file path"""
    try:
        # Get asset queries instance
        asset_queries = get_asset_queries()
        if not asset_queries:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Get asset data from database
        asset_result = asset_queries.get_asset_with_dependencies(asset_id)
        asset_data = asset_result.get('asset') if asset_result else None
        if not asset_data:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        # Verify this is a texture set asset
        if asset_data.get('asset_type') != 'Textures' or asset_data.get('category') != 'Texture Sets':
            raise HTTPException(status_code=400, detail="Preview image update is only available for Texture Sets")
        
        # Get file path from request
        file_path = request.get('file_path')
        if not file_path:
            raise HTTPException(status_code=400, detail="file_path is required")
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr'}
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Convert source path to container path if needed (network path to container mount)
        container_source_path = file_path
        if file_path.startswith('/net/library/atlaslib'):
            container_source_path = file_path.replace('/net/library/atlaslib', '/app/assets')
        
        # Check if source file exists (using container path)
        source_path = Path(container_source_path)
        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Source file not found: {file_path} (searched at {container_source_path})")
        
        # Get asset folder path
        asset_folder_path = asset_data.get('paths', {}).get('asset_folder')
        if not asset_folder_path:
            raise HTTPException(status_code=404, detail="Asset folder path not found")
        
        # Convert to container path (backend runs in container)
        container_path = asset_folder_path.replace('/net/library/atlaslib', '/app/assets')
        asset_folder = Path(container_path)
        
        if not asset_folder.exists():
            raise HTTPException(status_code=404, detail=f"Asset folder not found: {asset_folder}")
        
        # Create Preview folder if it doesn't exist
        preview_folder = asset_folder / "Preview"
        preview_folder.mkdir(exist_ok=True)
        logger.info(f"📁 Preview folder ready: {preview_folder}")
        
        # Define target preview file path
        preview_file = preview_folder / "Preview.png"
        
        # Simplified and more robust preview image processing
        logger.info(f"🔧 Processing preview image: {source_path} -> {preview_file}")
        
        success = False
        try:
            # Simple approach: Use PIL for reliable image processing
            from PIL import Image
            import shutil
            
            # Handle different image formats with alpha channel preservation
            if source_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr'}:
                try:
                    # Load image with PIL (supports most formats including basic EXR)
                    with Image.open(source_path) as img:
                        logger.info(f"📷 Original image: {img.mode}, size: {img.size}")
                        
                        # Preserve alpha channels for formats that support them
                        if img.mode in ('RGBA', 'LA'):
                            # Keep alpha channel - PNG supports transparency
                            if img.mode == 'LA':
                                img = img.convert('RGBA')
                            target_mode = 'RGBA'
                            logger.info(f"✅ Preserving alpha channel (mode: {img.mode})")
                            
                        elif img.mode == 'P':
                            # Check if palette has transparency
                            if 'transparency' in img.info:
                                img = img.convert('RGBA')
                                target_mode = 'RGBA'
                                logger.info(f"✅ Converted palette with transparency to RGBA")
                            else:
                                img = img.convert('RGB')
                                target_mode = 'RGB'
                                logger.info(f"✅ Converted palette without transparency to RGB")
                                
                        else:
                            # Convert other modes to RGB
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            target_mode = 'RGB'
                            logger.info(f"✅ Converted to RGB (original mode: {img.mode})")
                        
                        # Resize if too large (max 2048x2048 for preview) - PRESERVE ASPECT RATIO
                        max_size = 2048
                        if img.width > max_size or img.height > max_size:
                            # Calculate new size preserving aspect ratio (no cropping!)
                            scale_factor = min(max_size / img.width, max_size / img.height)
                            new_width = int(img.width * scale_factor)
                            new_height = int(img.height * scale_factor)
                            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            logger.info(f"📏 Resized preview preserving aspect ratio: {img.width}x{img.height} -> {new_width}x{new_height}")
                        
                        # Save as PNG with appropriate settings for alpha preservation
                        save_kwargs = {}
                        if target_mode == 'RGBA':
                            # PNG with alpha channel
                            save_kwargs = {
                                'format': 'PNG',
                                'optimize': True,
                                'compress_level': 6  # Good balance of size/quality for RGBA
                            }
                            logger.info(f"💾 Saving PNG with alpha channel")
                        else:
                            # PNG without alpha channel
                            save_kwargs = {
                                'format': 'PNG', 
                                'optimize': True,
                                'compress_level': 6
                            }
                            logger.info(f"💾 Saving PNG without alpha channel")
                        
                        img.save(preview_file, **save_kwargs)
                        success = True
                        logger.info(f"✅ Image processing successful: {preview_file} (mode: {target_mode})")
                        
                except Exception as pil_error:
                    logger.warning(f"⚠️ PIL processing failed: {pil_error}")
                    # Fallback to direct copy for unsupported formats
                    shutil.copy2(source_path, preview_file)
                    success = True
                    logger.info(f"✅ Used direct copy as fallback: {preview_file}")
            else:
                # For unsupported formats - direct copy
                shutil.copy2(source_path, preview_file)
                success = True
                logger.info(f"✅ Direct copy for {source_path.suffix}: {preview_file}")
                
        except Exception as process_error:
            logger.error(f"❌ Preview processing failed: {process_error}")
            success = False
        
        if success and preview_file.exists():
            logger.info(f"✅ Successfully created preview image: {preview_file}")
            
            # Update database with preview file path
            try:
                # Convert back to network path for database storage
                network_preview_path = str(preview_file).replace('/app/assets/', '/net/library/atlaslib/')
                
                # Update the asset document paths - always replace preview files list
                update_data = {
                    'paths.preview_files': [network_preview_path]
                }
                
                # Update in database using AQL
                aql_query = """
                    FOR doc IN Atlas_Library
                    FILTER doc._key == @asset_id
                    UPDATE doc WITH @updates IN Atlas_Library
                    RETURN NEW
                """
                bind_vars = {'asset_id': asset_id, 'updates': update_data}
                
                cursor = asset_queries.db.aql.execute(aql_query, bind_vars=bind_vars)
                result_list = list(cursor)
                
                if result_list:
                    logger.info(f"✅ Updated database with preview file path: {network_preview_path}")
                else:
                    logger.warning(f"⚠️ Failed to update database with preview file path")
                
            except Exception as db_error:
                logger.error(f"❌ Failed to update database: {db_error}")
                # Don't fail the entire operation if DB update fails, preview file is still created
            
            return {
                "success": True,
                "message": "Preview image updated successfully from file path",
                "asset_id": asset_id,
                "preview_path": str(preview_file),
                "source_path": file_path
            }
        else:
            # If processing failed, try fallback to simple copy
            logger.warning(f"⚠️ Preview processing failed, trying fallback copy...")
            try:
                shutil.copy2(source_path, preview_file)
                logger.info(f"✅ Used original preview image as fallback: {preview_file}")
                
                return {
                    "success": True,
                    "message": "Preview image updated successfully (original copy)",
                    "asset_id": asset_id,
                    "preview_path": str(preview_file),
                    "source_path": file_path
                }
            except Exception as copy_error:
                logger.error(f"❌ Fallback copy failed: {copy_error}")
                raise HTTPException(status_code=500, detail=f"Failed to save preview image: {str(copy_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Preview update from path failed: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Preview update from path failed: {str(e)}")


@router.post("/database/backup")
async def backup_database():
    """Create a complete backup of the Atlas_Library collection"""
    try:
        queries = get_asset_queries()
        if not queries:
            raise HTTPException(status_code=500, detail="Failed to connect to database")
        
        # Get all assets from the collection
        logger.info("🔄 Starting database backup...")
        query = "FOR asset IN Atlas_Library RETURN asset"
        cursor = queries.db.aql.execute(query)
        all_assets = list(cursor)
        
        # Create backup metadata
        backup_timestamp = datetime.now().isoformat()
        backup_data = {
            "backup_metadata": {
                "timestamp": backup_timestamp,
                "database_name": "blacksmith_atlas",
                "collection_name": "Atlas_Library",
                "total_assets": len(all_assets),
                "backup_version": "1.0"
            },
            "assets": all_assets
        }
        
        # Ensure backups directory exists
        backups_dir = Path("/app/backups")
        backups_dir.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        backup_filename = f"atlas_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = backups_dir / backup_filename
        
        # Write backup to file
        import json
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Database backup completed: {backup_path}")
        
        return {
            "success": True,
            "message": "Database backup completed successfully",
            "backup_file": backup_filename,
            "backup_path": str(backup_path),
            "total_assets": len(all_assets),
            "timestamp": backup_timestamp
        }
        
    except Exception as e:
        logger.error(f"❌ Database backup failed: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Database backup failed: {str(e)}")


@router.get("/database/backup/status")
async def get_backup_status():
    """Get information about the latest backup"""
    try:
        backups_dir = Path("/app/backups")
        
        if not backups_dir.exists():
            return {
                "last_backup": None,
                "backup_count": 0,
                "backups_directory_exists": False
            }
        
        # Find the most recent backup file
        backup_files = list(backups_dir.glob("atlas_backup_*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backup_files:
            return {
                "last_backup": None,
                "backup_count": 0,
                "backups_directory_exists": True
            }
        
        latest_backup = backup_files[0]
        
        return {
            "last_backup": {
                "filename": latest_backup.name,
                "timestamp": datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat(),
                "size_bytes": latest_backup.stat().st_size,
                "size_mb": round(latest_backup.stat().st_size / (1024 * 1024), 2)
            },
            "backup_count": len(backup_files),
            "backups_directory_exists": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get backup status: {str(e)}")
        return {
            "last_backup": None,
            "backup_count": 0,
            "error": str(e)
        }