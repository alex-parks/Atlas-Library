# backend/api/assets.py - Refactored to use ArangoDB only
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import os
from backend.assetlibrary.config import BlacksmithAtlasConfig

router = APIRouter(prefix="/api/v1", tags=["assets"])

# Initialize ArangoDB handler (with error handling)
try:
    from backend.assetlibrary.database.arango_queries import AssetQueries
    arango_config = BlacksmithAtlasConfig.DATABASE['arango']
    asset_queries = AssetQueries(arango_config)
    database_available = True
except Exception as e:
    asset_queries = None
    database_available = False

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
    return AssetResponse(
        id=asset_data.get('_key', asset_data.get('id', '')),
        name=asset_data.get('name', ''),
        category=asset_data.get('category', 'General'),
        asset_type=asset_data.get('asset_type', '3D'),
        paths=paths,
        file_sizes=asset_data.get('file_sizes', {}),
        tags=asset_data.get('tags', []),
        metadata=asset_data.get('metadata', {}),
        created_at=asset_data.get('created_at', datetime.now().isoformat()),
        thumbnail_path=thumbnail_url,
        artist=artist,
        file_format="USD",
        description=description
    )

@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
        search: Optional[str] = Query(None, description="Search term"),
        category: Optional[str] = Query(None, description="Filter by category"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        limit: int = Query(100, description="Maximum number of results")
):
    if not database_available or not asset_queries:
        # Return empty list when database is not available
        return []
    
    try:
        raw_assets = asset_queries.search_assets(
            search_term=search or "",
            category=category or "",
            tags=tags if tags is not None else []
        )
        assets = []
        for asset_data in raw_assets[:limit]:
            try:
                asset_response = convert_asset_to_response(asset_data)
                assets.append(asset_response)
            except Exception as e:
                continue
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")

@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    if not database_available or not asset_queries:
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
    if not database_available or not asset_queries:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        import uuid
        asset_id = uuid.uuid4().hex[:8]
        asset_data = {
            '_key': asset_id,
            'id': asset_id,
            'name': asset_request.name,
            'category': asset_request.category,
            'paths': asset_request.paths,
            'metadata': asset_request.metadata,
            'file_sizes': asset_request.file_sizes,
            'created_at': datetime.now().isoformat(),
            'dependencies': {},
            'copied_files': []
        }
        from backend.assetlibrary._3D.houdiniae import ArangoDBHandler
        db_handler = ArangoDBHandler(arango_config)
        success = db_handler.save_asset(asset_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create asset")
        return convert_asset_to_response(asset_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating asset: {str(e)}")

@router.get("/assets/stats/summary")
async def get_asset_stats():
    if not database_available or not asset_queries:
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

@router.get("/assets/recent/{limit}")
async def get_recent_assets(limit: int = 10):
    if not database_available or not asset_queries:
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
    if not database_available or not asset_queries:
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
    if not database_available or not asset_queries:
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