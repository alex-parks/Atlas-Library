# backend/api/assets.py - Updated for ArangoDB
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from assetlibrary.database.arango_queries import AssetQueries

router = APIRouter(prefix="/api/v1", tags=["assets"])

# Configuration
ARANGO_CONFIG = {
    'hosts': ['http://localhost:8529'],
    'database': 'blacksmith_atlas',
    'username': 'root',
    'password': ''
}

# Initialize queries
queries = AssetQueries(ARANGO_CONFIG)


# Response models
class AssetResponse(BaseModel):
    id: str
    name: str
    category: str
    asset_type: str = "3D"
    paths: dict
    file_sizes: dict
    tags: List[str] = []
    metadata: dict = {}
    created_at: str
    thumbnail_path: Optional[str] = None

    class Config:
        populate_by_name = True


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
        search: Optional[str] = Query(None, description="Search term"),
        category: Optional[str] = Query(None, description="Filter by category"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        limit: int = Query(100, description="Maximum number of results")
):
    """Get all assets with optional filtering"""
    try:
        # Use ArangoDB query
        results = queries.search_assets(
            search_term=search or "",
            category=category,
            tags=tags
        )

        # Convert to response format
        assets = []
        for doc in results[:limit]:
            asset = AssetResponse(
                id=doc.get('_key', doc.get('id', '')),
                name=doc.get('name', ''),
                category=doc.get('category', 'General'),
                asset_type=doc.get('asset_type', '3D'),
                paths=doc.get('paths', {}),
                file_sizes=doc.get('file_sizes', {}),
                tags=doc.get('tags', []),
                metadata=doc.get('metadata', {}),
                created_at=doc.get('created_at', ''),
                thumbnail_path=doc.get('paths', {}).get('thumbnail')
            )
            assets.append(asset)

        return assets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        result = queries.get_asset_with_dependencies(asset_id)
        if not result or not result.get('asset'):
            raise HTTPException(status_code=404, detail="Asset not found")

        doc = result['asset']
        return AssetResponse(
            id=doc.get('_key', doc.get('id', '')),
            name=doc.get('name', ''),
            category=doc.get('category', 'General'),
            asset_type=doc.get('asset_type', '3D'),
            paths=doc.get('paths', {}),
            file_sizes=doc.get('file_sizes', {}),
            tags=doc.get('tags', []),
            metadata=doc.get('metadata', {}),
            created_at=doc.get('created_at', ''),
            thumbnail_path=doc.get('paths', {}).get('thumbnail')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset library statistics"""
    try:
        stats = queries.get_asset_statistics()
        return {
            "total_assets": stats.get('total_assets', 0),
            "by_category": {item['category']: item['count'] for item in stats.get('by_category', [])},
            "by_type": {item['type']: item['count'] for item in stats.get('by_type', [])},
            "total_size_gb": round(stats.get('total_size_gb', 0), 2),
            "assets_this_week": stats.get('assets_this_week', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/assets/recent/{limit}")
async def get_recent_assets(limit: int = 10):
    """Get most recent assets"""
    try:
        results = queries.get_recent_assets(limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.put("/assets/{asset_id}/tags")
async def update_asset_tags(asset_id: str, tags: List[str]):
    """Update tags for an asset"""
    try:
        success = queries.update_asset_tags(asset_id, tags)
        if success:
            return {"message": "Tags updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update tags")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/test")
async def test_database():
    """Test endpoint to check if ArangoDB is working"""
    try:
        stats = queries.get_asset_statistics()
        return {
            "status": "ArangoDB connected successfully",
            "database": "blacksmith_atlas",
            "total_assets": stats.get('total_assets', 0),
            "connection": "healthy"
        }
    except Exception as e:
        return {
            "status": "ArangoDB connection failed",
            "error": str(e),
            "connection": "unhealthy"
        }