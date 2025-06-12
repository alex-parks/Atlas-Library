# backend/api/assets.py - Updated to use SQLite
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import os
from datetime import datetime, timedelta
import sys

# Add the database module to path
sys.path.append(str(Path(__file__).parent.parent))
from database.sqlite_manager import SQLiteAssetManager

router = APIRouter(prefix="/api/v1", tags=["assets"])

# Initialize SQLite manager
sqlite_manager = SQLiteAssetManager()

# Base path for assets
ASSET_LIBRARY_BASE = Path("C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D")


# Response models
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
    """Find the actual thumbnail file on disk and return API URL"""
    asset_id = asset_data.get('id', '')
    asset_name = asset_data.get('name', '')

    if not asset_id:
        print(f"[ERROR] No asset ID found")
        return None

    # Try the exact path from database first
    if 'paths' in asset_data and 'thumbnail' in asset_data['paths']:
        db_thumbnail_path = asset_data['paths']['thumbnail']
        if db_thumbnail_path and Path(db_thumbnail_path).exists():
            print(f"[OK] Found thumbnail from DB path: {db_thumbnail_path}")
            return f"http://localhost:8000/thumbnails/{asset_id}"

    # Try direct path fields from SQLite
    thumbnail_path = asset_data.get('thumbnail_path')
    if thumbnail_path and Path(thumbnail_path).exists():
        print(f"[OK] Found thumbnail from direct path: {thumbnail_path}")
        return f"http://localhost:8000/thumbnails/{asset_id}"

    # Try common folder structures
    folder_patterns = [
        ASSET_LIBRARY_BASE / f"{asset_id}_{asset_name}" / "Thumbnail",
        ASSET_LIBRARY_BASE / asset_id / "Thumbnail",
        ASSET_LIBRARY_BASE / asset_name / "Thumbnail",
    ]

    for folder in folder_patterns:
        if folder.exists() and folder.is_dir():
            for ext in ['.png', '.jpg', '.jpeg']:
                for img_file in folder.glob(f"*{ext}"):
                    print(f"[OK] Found thumbnail at: {img_file}")
                    return f"http://localhost:8000/thumbnails/{asset_id}"

    print(f"[ERROR] No thumbnail found for asset: {asset_name} (ID: {asset_id})")
    return None


def convert_asset_to_response(asset_data: dict) -> AssetResponse:
    """Convert raw asset data to API response format"""

    # Find the actual thumbnail file
    thumbnail_url = find_actual_thumbnail(asset_data)

    # Extract artist from metadata
    artist = "Unknown"
    if 'metadata' in asset_data:
        metadata = asset_data['metadata']
        if 'created_by' in metadata:
            artist = metadata['created_by']

    # Also check direct field from SQLite
    if asset_data.get('created_by'):
        artist = asset_data['created_by']

    # Generate description from metadata
    description = ""
    if 'metadata' in asset_data and isinstance(asset_data['metadata'], dict):
        metadata = asset_data['metadata']
        if 'hda_parameters' in metadata and isinstance(metadata['hda_parameters'], dict):
            hda_params = metadata['hda_parameters']
            if 'notes' in hda_params:
                description = hda_params.get('notes', '')

    if not description:
        if 'metadata' in asset_data:
            description = asset_data['metadata'].get('description', '')

    if not description:
        description = f"{asset_data.get('category', 'General')} asset created in Houdini"

    # Handle paths - prioritize the reconstructed paths object
    paths = asset_data.get('paths', {})
    if not paths or all(v is None for v in paths.values()):
        # Fallback to individual path fields
        paths = {
            'usd': asset_data.get('usd_path'),
            'thumbnail': asset_data.get('thumbnail_path'),
            'textures': asset_data.get('textures_path'),
            'fbx': asset_data.get('fbx_path')
        }

    return AssetResponse(
        id=asset_data.get('id', ''),
        name=asset_data.get('name', ''),
        category=asset_data.get('category', 'General'),
        asset_type="3D",
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
        created_by: Optional[str] = Query(None, description="Filter by creator"),
        limit: int = Query(100, description="Maximum number of results")
):
    """Get all assets from SQLite database"""
    try:
        # Use SQLite search functionality
        raw_assets = sqlite_manager.search_assets(
            search_term=search or "",
            category=category or "",
            created_by=created_by or ""
        )

        print(f"[INFO] Loaded {len(raw_assets)} assets from SQLite")

        # Convert to response format with thumbnail detection
        assets = []
        for asset_data in raw_assets:
            try:
                asset_response = convert_asset_to_response(asset_data)
                assets.append(asset_response)
            except Exception as e:
                print(f"[ERROR] Error converting asset {asset_data.get('id', 'unknown')}: {e}")
                continue

        # Apply limit
        assets = assets[:limit]

        print(f"[INFO] Returning {len(assets)} assets")

        # Debug info
        for asset in assets:
            if asset.thumbnail_path:
                print(f"[OK] {asset.name}: {asset.thumbnail_path}")
            else:
                print(f"[ERROR] {asset.name}: No thumbnail found")

        return assets

    except Exception as e:
        print(f"[ERROR] Error in list_assets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        asset_data = sqlite_manager.get_asset_by_id(asset_id)

        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")

        return convert_asset_to_response(asset_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/assets", response_model=AssetResponse)
async def create_asset(asset_request: AssetCreateRequest):
    """Create a new asset"""
    try:
        # Generate ID
        import uuid
        asset_id = uuid.uuid4().hex[:8]

        # Prepare asset data
        asset_data = {
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

        # Add to database
        success = sqlite_manager.add_asset(asset_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create asset")

        return convert_asset_to_response(asset_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating asset: {str(e)}")


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Delete an asset (not implemented in basic SQLite manager)"""
    raise HTTPException(status_code=501, detail="Delete functionality not implemented")


@router.post("/sync")
async def sync_database(background_tasks: BackgroundTasks):
    """Sync SQLite database with JSON file"""
    try:
        # Run sync in background
        background_tasks.add_task(sqlite_manager.sync_with_json)

        return {
            "message": "Database sync started",
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/test")
async def test_database():
    """Test endpoint to check SQLite database"""
    try:
        # Test database connection
        assets = sqlite_manager.get_all_assets()
        stats = sqlite_manager.get_statistics()

        # Test thumbnail detection for each asset
        thumbnail_status = []
        for asset in assets[:5]:  # Test first 5 assets
            thumbnail_url = find_actual_thumbnail(asset)
            thumbnail_status.append({
                "id": asset.get('id'),
                "name": asset.get('name'),
                "has_thumbnail": thumbnail_url is not None,
                "thumbnail_url": thumbnail_url,
                "db_thumbnail_path": asset.get('thumbnail_path', 'No path in DB')
            })

        return {
            "status": "SQLite database connected successfully",
            "database_type": "SQLite",
            "asset_library_base": str(ASSET_LIBRARY_BASE),
            "total_assets": len(assets),
            "statistics": stats,
            "thumbnail_detection": thumbnail_status,
            "connection": "healthy"
        }

    except Exception as e:
        return {
            "status": "Failed",
            "error": str(e),
            "connection": "unhealthy"
        }


@router.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset library statistics from SQLite"""
    try:
        stats = sqlite_manager.get_statistics()

        # Calculate total size from all assets
        assets = sqlite_manager.get_all_assets()
        total_size = 0

        for asset in assets:
            file_sizes = asset.get('file_sizes', {})
            if isinstance(file_sizes, dict):
                for size in file_sizes.values():
                    if isinstance(size, (int, float)):
                        total_size += size

        return {
            "total_assets": stats.get('total_assets', 0),
            "by_category": stats.get('by_category', {}),
            "by_type": {"3D": stats.get('total_assets', 0)},
            "total_size_gb": round(total_size / (1024 ** 3), 2),
            "assets_this_week": stats.get('recent_assets', 0),
            "by_creator": stats.get('by_creator', {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/assets/recent/{limit}")
async def get_recent_assets(limit: int = 10):
    """Get most recent assets"""
    try:
        # SQLite returns assets ordered by created_at DESC by default
        raw_assets = sqlite_manager.get_all_assets()

        recent_assets = []
        for asset_data in raw_assets[:limit]:
            try:
                asset_response = convert_asset_to_response(asset_data)
                recent_assets.append(asset_response)
            except Exception as e:
                print(f"Error converting recent asset: {e}")
                continue

        return recent_assets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/categories")
async def get_categories():
    """Get all available categories"""
    try:
        stats = sqlite_manager.get_statistics()
        categories = list(stats.get('by_category', {}).keys())

        return {
            "categories": categories,
            "count": len(categories)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/creators")
async def get_creators():
    """Get all asset creators"""
    try:
        stats = sqlite_manager.get_statistics()
        creators = list(stats.get('by_creator', {}).keys())

        return {
            "creators": creators,
            "count": len(creators)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")