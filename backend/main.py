# backend/main.py - Updated with SQLite integration
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.assets import router as assets_router
from database.sqlite_manager import SQLiteAssetManager
from pathlib import Path
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blacksmith Atlas API",
    description="Asset Library Management System (SQLite Database)",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3011",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3011",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize SQLite database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        logger.info("🚀 Starting Blacksmith Atlas API...")

        # Initialize SQLite manager and import JSON data
        sqlite_manager = SQLiteAssetManager()

        # Check if we need to import JSON data
        assets = sqlite_manager.get_all_assets()
        if not assets:
            logger.info("📦 No assets found in SQLite, importing from JSON...")
            success = sqlite_manager.json_to_sqlite()
            if success:
                logger.info("✅ JSON data imported successfully")
            else:
                logger.warning("⚠️ Failed to import JSON data")
        else:
            logger.info(f"✅ Found {len(assets)} assets in SQLite database")

        # Get statistics
        stats = sqlite_manager.get_statistics()
        logger.info(f"📊 Database stats: {stats}")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")


@app.get("/test-thumbnail")
async def test_thumbnail():
    """Direct test - serve the PigHead thumbnail"""
    path = r"C:\Users\alexh\Desktop\BlacksmithAtlas_Files\AssetLibrary\3D\5a337cb9_PigHead\Thumbnail\PigHead_thumbnail.png"

    file = Path(path)
    if file.exists():
        return FileResponse(path)
    else:
        return {"error": "File not found", "path": path, "exists": file.exists()}


@app.get("/thumbnails/{asset_id}")
async def get_thumbnail(asset_id: str):
    """Serve thumbnail images for assets using SQLite database"""
    logger.info(f"[THUMBNAIL] Requested for asset: {asset_id}")

    try:
        # Initialize SQLite manager
        sqlite_manager = SQLiteAssetManager()

        # Get asset from SQLite
        asset = sqlite_manager.get_asset_by_id(asset_id)

        if not asset:
            logger.error(f"[ERROR] Asset not found: {asset_id}")
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

        # Try multiple thumbnail path sources
        thumbnail_paths = []

        # 1. From paths object
        if 'paths' in asset and asset['paths'].get('thumbnail'):
            thumbnail_paths.append(asset['paths']['thumbnail'])

        # 2. From direct thumbnail_path field
        if asset.get('thumbnail_path'):
            thumbnail_paths.append(asset['thumbnail_path'])

        # 3. From reconstructed folder structure
        asset_name = asset.get('name', '')
        if asset_name:
            base_path = Path("C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D")
            folder_patterns = [
                base_path / f"{asset_id}_{asset_name}" / "Thumbnail",
                base_path / asset_id / "Thumbnail",
                base_path / asset_name / "Thumbnail",
            ]

            for folder in folder_patterns:
                if folder.exists() and folder.is_dir():
                    for ext in ['.png', '.jpg', '.jpeg']:
                        for img_file in folder.glob(f"*{ext}"):
                            thumbnail_paths.append(str(img_file))

        # Try each path until we find one that exists
        for thumbnail_path in thumbnail_paths:
            if thumbnail_path and Path(thumbnail_path).exists():
                logger.info(f"[OK] Serving thumbnail: {thumbnail_path}")
                return FileResponse(
                    path=str(thumbnail_path),
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"}
                )

        # If no thumbnail found
        logger.error(f"[ERROR] No thumbnail found for asset: {asset_id}")
        logger.debug(f"[DEBUG] Tried paths: {thumbnail_paths}")
        raise HTTPException(status_code=404, detail=f"No thumbnail found for asset: {asset_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error serving thumbnail: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error serving thumbnail: {str(e)}")


# Include the assets router
app.include_router(assets_router)


@app.get("/debug/routes")
async def list_routes():
    """List all registered routes for debugging"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": route.methods if hasattr(route, 'methods') else None,
                "name": route.name if hasattr(route, 'name') else None
            })
    return {"routes": routes}


@app.get("/")
async def root():
    """Root endpoint with system information"""
    try:
        sqlite_manager = SQLiteAssetManager()
        stats = sqlite_manager.get_statistics()

        return {
            "message": "Blacksmith Atlas API (SQLite Mode)",
            "version": "1.0.0",
            "database": "SQLite",
            "docs": "/docs",
            "status": "running",
            "assets_count": stats.get('total_assets', 0),
            "categories": list(stats.get('by_category', {}).keys())
        }
    except Exception as e:
        return {
            "message": "Blacksmith Atlas API (SQLite Mode)",
            "version": "1.0.0",
            "database": "SQLite",
            "status": "running",
            "error": str(e)
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test SQLite connection
        sqlite_manager = SQLiteAssetManager()
        assets = sqlite_manager.get_all_assets()
        stats = sqlite_manager.get_statistics()

        # Check JSON source file
        json_path = Path(r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json")

        return {
            "status": "healthy",
            "service": "Blacksmith Atlas Backend",
            "database": "SQLite",
            "database_assets": len(assets),
            "json_source_exists": json_path.exists(),
            "json_source_path": str(json_path),
            "statistics": stats
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Blacksmith Atlas Backend",
            "database": "SQLite",
            "error": str(e)
        }


@app.post("/admin/sync")
async def sync_database():
    """Admin endpoint to sync SQLite with JSON"""
    try:
        sqlite_manager = SQLiteAssetManager()
        success = sqlite_manager.sync_with_json()

        if success:
            stats = sqlite_manager.get_statistics()
            return {
                "status": "success",
                "message": "Database synced successfully",
                "statistics": stats
            }
        else:
            return {
                "status": "failed",
                "message": "Database sync failed"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@app.post("/admin/save-config")
async def save_config(config_data: dict):
    """Save Asset Library configuration for database startup"""
    try:
        # Ensure config directory exists
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)

        # Save config to file that the database startup script can read
        config_file = config_dir / "asset_library_config.json"

        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"💾 Configuration saved to {config_file}")

        return {
            "status": "success",
            "message": "Configuration saved successfully",
            "config_file": str(config_file)
        }

    except Exception as e:
        logger.error(f"❌ Failed to save config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)