# backend/api/assets.py - REPLACE ENTIRE FILE
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
import json
from pathlib import Path

router = APIRouter(prefix="/api/v1", tags=["assets"])







# Pydantic models
class AssetResponse(BaseModel):
    id: str
    name: str
    asset_type: str
    file_path: str
    file_size: int
    file_format: str
    status: str
    tags: List[str]
    description: str
    artist: str
    thumbnail_path: Optional[str] = None
    textures_path: Optional[str] = None
    created_at: str


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
        search: Optional[str] = None,
        asset_type: Optional[str] = None
):
    """Get all assets with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM assets WHERE 1=1"
        params = []

        # Add search filter
        if search:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        # Add type filter
        if asset_type and asset_type != 'all':
            if asset_type == '2d':
                query += " AND asset_type IN ('texture', 'image', 'reference')"
            elif asset_type == '3d':
                query += " AND asset_type IN ('geometry', 'material', 'light_rig')"
            else:
                query += " AND asset_type = ?"
                params.append(asset_type)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to response format
        assets = []
        for row in rows:
            asset = dict(row)
            # Parse tags JSON
            try:
                asset['tags'] = json.loads(asset['tags']) if asset['tags'] else []
            except:
                asset['tags'] = []

            assets.append(asset)

        conn.close()
        return assets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Asset not found")

        asset = dict(row)
        # Parse tags JSON
        try:
            asset['tags'] = json.loads(asset['tags']) if asset['tags'] else []
        except:
            asset['tags'] = []

        conn.close()
        return asset

    except Exception as e:
        if "Asset not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/assets/types")
async def get_asset_types():
    """Get available asset types"""
    return [
        {"value": "geometry", "name": "Geometry", "category": "3D"},
        {"value": "material", "name": "Material", "category": "3D"},
        {"value": "light_rig", "name": "Light Rig", "category": "3D"},
        {"value": "texture", "name": "Texture", "category": "2D"},
        {"value": "image", "name": "Image", "category": "2D"},
        {"value": "reference", "name": "Reference", "category": "2D"}
    ]


@router.get("/assets/stats/summary")
async def get_asset_stats():
    """Get asset library statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total assets
        cursor.execute("SELECT COUNT(*) FROM assets")
        total_assets = cursor.fetchone()[0]

        # Assets by type
        cursor.execute("SELECT asset_type, COUNT(*) FROM assets GROUP BY asset_type")
        asset_types = {row[0]: row[1] for row in cursor.fetchall()}

        # Total size
        cursor.execute("SELECT SUM(file_size) FROM assets")
        total_size = cursor.fetchone()[0] or 0

        # Artists
        cursor.execute("SELECT DISTINCT artist FROM assets WHERE artist != ''")
        artists = [row[0] for row in cursor.fetchall()]

        # Sample tags
        cursor.execute("SELECT tags FROM assets LIMIT 10")
        all_tags = set()
        for row in cursor.fetchall():
            try:
                tags = json.loads(row[0]) if row[0] else []
                all_tags.update(tags)
            except:
                pass

        conn.close()

        return {
            "total_assets": total_assets,
            "asset_types": asset_types,
            "total_size": total_size,
            "artists": artists,
            "tags": list(all_tags)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/assets/{asset_id}/thumbnail")
async def get_asset_thumbnail(asset_id: str):
    """Get asset thumbnail image"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT thumbnail_path FROM assets WHERE id = ?", (asset_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Asset not found")

        thumbnail_path = row[0]
        conn.close()

        if not thumbnail_path or not Path(thumbnail_path).exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        return FileResponse(thumbnail_path)

    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/test")
async def test_database():
    """Test endpoint to check if database is working"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assets")
        count = cursor.fetchone()[0]
        conn.close()

        return {
            "status": "Database connected successfully",
            "assets_count": count,
            "database_path": str(Path(DB_PATH).absolute())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")