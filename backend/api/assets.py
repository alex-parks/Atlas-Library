# backend/api/assets.py - Updated for JSON Database
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import json
import os
from datetime import datetime

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
            # Handle both list format and dict format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'assets' in data:
                return data['assets']
            else:
                return []
    except Exception as e:
        print(f"Error loading JSON database: {e}")
        return []


def convert_asset_to_response(asset_data: dict) -> AssetResponse:
    """Convert raw asset data to API response format"""
    # Handle both old and new formats
    thumbnail_path = None
    if 'paths' in asset_data and 'thumbnail' in asset_data['paths']:
        # Convert absolute path to API endpoint
        asset_id = asset_data.get('id', '')
        if asset_id:
            thumbnail_path = f"http://localhost:8000/thumbnails/{asset_id}"
    elif 'thumbnail_path' in asset_data:
        asset_id = asset_data.get('id', '')
        if asset_id:
            thumbnail_path = f"http://localhost:8000/thumbnails/{asset_id}"

    # Extract artist from metadata if available
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
        thumbnail_path=thumbnail_path,
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
    """Get all assets with optional filtering"""
    try:
        raw_assets = load_json_database()

        # Convert to response format
        assets = []
        for asset_data in raw_assets:
            try:
                asset_response = convert_asset_to_response(asset_data)
                assets.append(asset_response)
            except Exception as e:
                print(f"Error converting asset {asset_data.get('id', 'unknown')}: {e}")
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

        return assets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        raw_assets = load_json_database()

        # Find asset by ID
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


@router.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset library statistics"""
    try:
        raw_assets = load_json_database()

        # Calculate statistics
        total_assets = len(raw_assets)

        # Group by category
        categories = {}
        for asset in raw_assets:
            category = asset.get('category', 'General')
            categories[category] = categories.get(category, 0) + 1

        # Calculate total size
        total_size = 0
        for asset in raw_assets:
            file_sizes = asset.get('file_sizes', {})
            for size in file_sizes.values():
                if isinstance(size, (int, float)):
                    total_size += size

        # Count recent assets (this week)
        recent_count = 0
        one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        for asset in raw_assets:
            created_at = asset.get('created_at', '')
            if created_at and created_at > one_week_ago:
                recent_count += 1

        return {
            "total_assets": total_assets,
            "by_category": categories,
            "by_type": {"3D": total_assets},  # All assets are 3D for now
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

        # Sort by created_at (most recent first)
        sorted_assets = sorted(raw_assets,
                               key=lambda x: x.get('created_at', ''),
                               reverse=True)

        # Convert to response format and limit
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


@router.get("/test")
async def test_database():
    """Test endpoint to check if JSON database is working"""
    try:
        raw_assets = load_json_database()

        return {
            "status": "JSON database connected successfully",
            "database_path": str(JSON_DATABASE_PATH),
            "total_assets": len(raw_assets),
            "database_exists": JSON_DATABASE_PATH.exists(),
            "connection": "healthy"
        }

    except Exception as e:
        return {
            "status": "JSON database connection failed",
            "error": str(e),
            "database_path": str(JSON_DATABASE_PATH),
            "connection": "unhealthy"
        }


# Add missing datetime import
from datetime import timedelta