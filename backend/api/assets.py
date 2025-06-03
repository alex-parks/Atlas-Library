# backend/api/assets.py - REPLACE ENTIRE FILE
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
import yaml
from pathlib import Path

router = APIRouter(prefix="/api/v1", tags=["assets"])

# Path to your YAML database
YAML_PATH = Path(__file__).parent.parent / "assetlibrary/database/3DAssets.yaml"


# Pydantic models
class AssetResponse(BaseModel):
    id: str
    name: str
    folder: str
    usd_path: str
    thumbnail_path: str
    textures_path: str
    # Adding fields to match frontend expectations
    asset_type: str = "geometry"
    file_size: int = 0
    file_format: str = "USD"
    status: str = "active"
    tags: List[str] = []
    description: str = ""
    artist: str = "Unknown"
    created_at: str = "2025-01-01T00:00:00Z"


def load_yaml_assets() -> List[dict]:
    """Load assets from YAML file"""
    try:
        if YAML_PATH.exists():
            with open(YAML_PATH, 'r') as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, list) else []
        return []
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return []


def convert_yaml_to_asset_response(yaml_asset: dict) -> AssetResponse:
    """Convert YAML asset to AssetResponse format"""
    return AssetResponse(
        id=yaml_asset.get('id', ''),
        name=yaml_asset.get('name', ''),
        folder=yaml_asset.get('folder', ''),
        usd_path=yaml_asset.get('usd_path', ''),
        thumbnail_path=yaml_asset.get('thumbnail_path', ''),
        textures_path=yaml_asset.get('textures_path', ''),
        asset_type="geometry",  # Since these are 3D assets
        file_size=1024000,  # Placeholder size
        file_format="USD",
        status="active",
        tags=["3D", "Houdini"],
        description=f"3D asset: {yaml_asset.get('name', '')}",
        artist="Houdini Artist",
        created_at="2025-01-01T00:00:00Z"
    )


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
        search: Optional[str] = None,
        asset_type: Optional[str] = None
):
    """Get all assets with optional filtering"""
    try:
        yaml_assets = load_yaml_assets()

        # Convert YAML assets to response format
        assets = []
        for yaml_asset in yaml_assets:
            asset = convert_yaml_to_asset_response(yaml_asset)
            assets.append(asset)

        # Apply search filter
        if search:
            assets = [
                asset for asset in assets
                if search.lower() in asset.name.lower() or
                   search.lower() in asset.description.lower()
            ]

        # Apply type filter
        if asset_type and asset_type != 'all':
            if asset_type == '2d':
                assets = [asset for asset in assets if asset.asset_type in ['texture', 'image', 'reference']]
            elif asset_type == '3d':
                assets = [asset for asset in assets if asset.asset_type in ['geometry', 'material', 'light_rig']]
            else:
                assets = [asset for asset in assets if asset.asset_type == asset_type]

        return assets

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading assets: {str(e)}")


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    try:
        yaml_assets = load_yaml_assets()

        for yaml_asset in yaml_assets:
            if yaml_asset.get('id') == asset_id:
                return convert_yaml_to_asset_response(yaml_asset)

        raise HTTPException(status_code=404, detail="Asset not found")

    except Exception as e:
        if "Asset not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
        yaml_assets = load_yaml_assets()
        assets = [convert_yaml_to_asset_response(asset) for asset in yaml_assets]

        # Calculate stats
        total_assets = len(assets)
        asset_types = {}
        total_size = 0
        artists = set()
        all_tags = set()

        for asset in assets:
            # Count by type
            asset_types[asset.asset_type] = asset_types.get(asset.asset_type, 0) + 1
            # Sum sizes
            total_size += asset.file_size
            # Collect artists
            if asset.artist:
                artists.add(asset.artist)
            # Collect tags
            all_tags.update(asset.tags)

        return {
            "total_assets": total_assets,
            "asset_types": asset_types,
            "total_size": total_size,
            "artists": list(artists),
            "tags": list(all_tags)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/assets/{asset_id}/thumbnail")
async def get_asset_thumbnail(asset_id: str):
    """Get asset thumbnail image"""
    try:
        yaml_assets = load_yaml_assets()

        for yaml_asset in yaml_assets:
            if yaml_asset.get('id') == asset_id:
                thumbnail_path = yaml_asset.get('thumbnail_path')
                if thumbnail_path and Path(thumbnail_path).exists():
                    return FileResponse(thumbnail_path)
                else:
                    raise HTTPException(status_code=404, detail="Thumbnail not found")

        raise HTTPException(status_code=404, detail="Asset not found")

    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/test")
async def test_database():
    """Test endpoint to check if YAML database is working"""
    try:
        yaml_assets = load_yaml_assets()

        return {
            "status": "YAML database connected successfully",
            "assets_count": len(yaml_assets),
            "database_path": str(YAML_PATH.absolute()),
            "database_exists": YAML_PATH.exists()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YAML database connection failed: {str(e)}")