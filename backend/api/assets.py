# backend/api/assets.py - SIMPLE DIRECT SOLUTION
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import json
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1", tags=["assets"])

# Path to your JSON database file
JSON_DATABASE_PATH = Path(__file__).parent.parent / "assetlibrary" / "database" / "3DAssets.json"


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


def load_json_database() -> List[dict]:
    """Load assets from JSON database file"""
    if not JSON_DATABASE_PATH.exists():
        return []

    try:
        with open(JSON_DATABASE_PATH, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'assets' in data:
                return data['assets']
            else:
                return []
    except Exception as e:
        print(f"Error loading JSON database: {e}")
        return []


def find_actual_thumbnail(asset_data: dict) -> Optional[str]:
    """Find the actual thumbnail file on disk and return API URL"""
    asset_id = asset_data.get('id', '')
    asset_name = asset_data.get('name', '')

    if not asset_id:
        return None

    # Try the exact path from JSON first
    if 'paths' in asset_data and 'thumbnail' in asset_data['paths']:
        json_thumbnail_path = asset_data['paths']['thumbnail']
        if json_thumbnail_path and Path(json_thumbnail_path).exists():
            print(f"✅ Found thumbnail from JSON path: {json_thumbnail_path}")
            return f"http://localhost:8000/thumbnails/{asset_id}"

    # Search for thumbnail files in expected locations
    search_patterns = [
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/{asset_name}_thumbnail.png",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/{asset_name}_thumbnail.jpg",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}_{asset_name}/Thumbnail/{asset_name}_thumbnail.png",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}_{asset_name}/Thumbnail/{asset_name}_thumbnail.jpg",
    ]

    for pattern in search_patterns:
        if Path(pattern).exists():
            print(f"✅ Found thumbnail at: {pattern}")
            return f"http://localhost:8000/thumbnails/{asset_id}"

    # Try to find any image file in thumbnail folders
    folder_patterns = [
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}_{asset_name}/Thumbnail",
    ]

    for folder_pattern in folder_patterns:
        folder = Path(folder_pattern)
        if folder.exists() and folder.is_dir():
            for ext in ['.png', '.jpg', '.jpeg']:
                for img_file in folder.glob(f"*{ext}"):
                    print(f"✅ Found thumbnail in folder: {img_file}")
                    return f"http://localhost:8000/thumbnails/{asset_id}"

    print(f"❌ No thumbnail found for asset: {asset_name} (ID: {asset_id})")
    return None


def convert_asset_to_response(asset_data: dict) -> AssetResponse:
    """Convert raw asset data to API response format"""

    # Find the actual thumbnail file
    thumbnail_path = find_actual_thumbnail(asset_data)

    # Extract artist from metadata
    artist = "Unknown"
    if 'metadata' in asset_data:
        metadata = asset_data['metadata']
        if 'created_by' in metadata:
            artist = metadata['created_by']
        elif 'hda_parameters' in metadata and 'created_by' in metadata['hda_parameters']:
            artist = metadata['hda_parameters']['created_by']

    # Generate description from metadata
    description = ""
    if 'metadata' in asset_data and 'hda_parameters' in asset_data['metadata']:
        hda_params = asset_data['metadata']['hda_parameters']
        if 'notes' in hda_params:
            description = hda_params.get('notes', '')

    if not description:
        if 'metadata' in asset_data:
            description = asset_data['metadata'].get('description', '')

    if not description:
        description = f"{asset_data.get('category', 'General')} asset created in Houdini"

    return AssetResponse(
        id=asset_data.get('id', ''),
        name=asset_data.get('name', ''),
        category=asset_data.get('category', 'General'),
        asset_type="3D",
        paths=asset_data.get('paths', {}),
        file_sizes=asset_data.get('file_sizes', {}),
        tags=asset_data.get('tags', []),
        metadata=asset_data.get('metadata', {}),
        created_at=asset_data.get('created_at', datetime.now().isoformat()),
        thumbnail_path=thumbnail_path,  # Will be API URL if found, None if not
        artist=artist,
        file_format="USD",
        description=description
    )


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
        search: Optional[str] = Query(None, description="Search term"),
        category: Optional[str] = Query(None, description="Filter by category"),
        limit: int = Query(100, description="Maximum number of results")
):
    """Get all assets with thumbnail detection"""
    try:
        raw_assets = load_json_database()
        print(f"📚 Loaded {len(raw_assets)} assets from JSON")

        # Convert to response format with thumbnail detection
        assets = []
        for asset_data in raw_assets:
            try:
                asset_response = convert_asset_to_response(asset_data)
                assets.append(asset_response)
            except Exception as e:
                print(f"❌ Error converting asset {asset_data.get('id', 'unknown')}: {e}")
                continue

        # Apply filters
        if search:
            search_lower = search.lower()
            assets = [asset for asset in assets if
                      search_lower in asset.name.lower() or
                      search_lower in asset.description.lower()]

        if category:
            assets = [asset for asset in assets if asset.category.lower() == category.lower()]

        # Apply limit
        assets = assets[:limit]

        print(f"📤 Returning {len(assets)} assets")

        # Debug info
        for asset in assets:
            if asset.thumbnail_path:
                print(f"✅ {asset.name}: {asset.thumbnail_path}")
            else:
                print(f"❌ {asset.name}: No thumbnail found")

        return assets

    except Exception as e:
        print(f"❌ Error in list_assets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        raw_assets = load_json_database()

        asset_data = None
        for asset in raw_assets:
            if asset.get('id') == asset_id:
                asset_data = asset
                break

        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")

        return convert_asset_to_response(asset_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/test")
async def test_database():
    """Test endpoint to check everything"""
    try:
        raw_assets = load_json_database()

        # Test thumbnail detection for each asset
        thumbnail_status = []
        for asset in raw_assets:
            thumbnail_url = find_actual_thumbnail(asset)
            thumbnail_status.append({
                "id": asset.get('id'),
                "name": asset.get('name'),
                "has_thumbnail": thumbnail_url is not None,
                "thumbnail_url": thumbnail_url
            })

        return {
            "status": "JSON database connected successfully",
            "database_path": str(JSON_DATABASE_PATH),
            "total_assets": len(raw_assets),
            "thumbnail_detection": thumbnail_status,
            "connection": "healthy"
        }

    except Exception as e:
        return {
            "status": "Failed",
            "error": str(e),
            "connection": "unhealthy"
        }


# Keep the other endpoints for compatibility
@router.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset library statistics"""
    try:
        raw_assets = load_json_database()
        total_assets = len(raw_assets)

        categories = {}
        for asset in raw_assets:
            category = asset.get('category', 'General')
            categories[category] = categories.get(category, 0) + 1

        total_size = 0
        for asset in raw_assets:
            file_sizes = asset.get('file_sizes', {})
            for size in file_sizes.values():
                if isinstance(size, (int, float)):
                    total_size += size

        recent_count = 0
        one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        for asset in raw_assets:
            created_at = asset.get('created_at', '')
            if created_at and created_at > one_week_ago:
                recent_count += 1

        return {
            "total_assets": total_assets,
            "by_category": categories,
            "by_type": {"3D": total_assets},
            "total_size_gb": round(total_size / (1024 ** 3), 2),
            "assets_this_week": recent_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/assets/recent/{limit}")
async def get_recent_assets(limit: int = 10):
    """Get most recent assets"""
    try:
        raw_assets = load_json_database()

        sorted_assets = sorted(raw_assets,
                               key=lambda x: x.get('created_at', ''),
                               reverse=True)

        recent_assets = []
        for asset_data in sorted_assets[:limit]:
            try:
                asset_response = convert_asset_to_response(asset_data)
                recent_assets.append(asset_response)
            except Exception as e:
                print(f"Error converting recent asset: {e}")
                continue

        return recent_assets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")