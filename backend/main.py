# backend/main.py - Refactored to use ArangoDB
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backend.api.assets import router as assets_router
from backend.api.todos import router as todos_router
from backend.api.simple_assets import router as simple_assets_router
from backend.api.asset_sync import router as sync_router
from pathlib import Path
import os
import logging
from backend.assetlibrary.config import BlacksmithAtlasConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blacksmith Atlas API",
    description="Asset Library Management System (ArangoDB)",
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

# Initialize ArangoDB handler
try:
    from backend.assetlibrary.database.arango_queries import AssetQueries
    # Get the correct environment configuration
    environment = os.getenv('ATLAS_ENV', 'development')
    arango_config = BlacksmithAtlasConfig.get_database_config(environment)
    asset_queries = AssetQueries(arango_config)
    database_available = True
    logger.info("✅ ArangoDB connection initialized")
except Exception as e:
    logger.error(f"❌ ArangoDB connection failed: {e}")
    raise Exception(f"Failed to connect to ArangoDB: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Blacksmith Atlas API...")
    try:
        stats = asset_queries.get_asset_statistics()
        logger.info(f"📊 ArangoDB connected successfully: {stats}")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise Exception(f"Database connection failed: {e}")

@app.get("/test-thumbnail")
async def test_thumbnail():
    # Docker-friendly path
    asset_path = os.getenv('ASSET_LIBRARY_PATH', '/app/assets')
    path = os.path.join(asset_path, "3D", "5a337cb9_PigHead", "Thumbnail", "PigHead_thumbnail.png")
    file = Path(path)
    if file.exists():
        return FileResponse(path)
    else:
        return {"error": "File not found", "path": path, "exists": file.exists()}

@app.get("/thumbnails/{asset_id}")
async def get_thumbnail(asset_id: str):
    logger.info(f"[THUMBNAIL] Requested for asset: {asset_id}")
    try:
        asset = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset:
            logger.error(f"[ERROR] Asset not found: {asset_id}")
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")
        thumbnail_paths = []
        if 'paths' in asset and asset['paths'].get('thumbnail'):
            thumbnail_paths.append(asset['paths']['thumbnail'])
        if asset.get('thumbnail_path'):
            thumbnail_paths.append(asset['thumbnail_path'])
        asset_name = asset.get('name', '')
        if asset_name:
            # Docker-friendly base path
            base_path = Path(os.getenv('ASSET_LIBRARY_PATH', '/app/assets')) / "3D"
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
        for thumbnail_path in thumbnail_paths:
            if thumbnail_path and Path(thumbnail_path).exists():
                logger.info(f"[OK] Serving thumbnail: {thumbnail_path}")
                return FileResponse(
                    path=str(thumbnail_path),
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"}
                )
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

# Include the routers
app.include_router(assets_router)
app.include_router(todos_router)
app.include_router(simple_assets_router)
app.include_router(sync_router)

@app.get("/test-assets")
async def test_assets():
    """Simple test endpoint to verify database connection and assets"""
    try:
        logger.info("🔍 Testing asset query from main.py")
        assets = asset_queries.search_assets()
        logger.info(f"📊 Found {len(assets)} assets directly")
        
        # Convert to simple format  
        result = []
        for asset in assets:
            result.append({
                "id": asset.get("_key", "unknown"),
                "name": asset.get("name", "Unknown"), 
                "category": asset.get("category", "Unknown"),
                "created_at": asset.get("created_at", "Unknown")
            })
        
        return {
            "total": len(assets),
            "assets": result,
            "source": "main.py direct query"
        }
    except Exception as e:
        logger.error(f"❌ Test assets failed: {e}")
        return {
            "error": str(e),
            "total": 0,
            "assets": []
        }

@app.get("/debug/routes")
async def list_routes():
    routes = []
    for route in app.routes:
        route_info = {}
        if hasattr(route, 'path'):
            route_info['path'] = getattr(route, 'path', None)
        if hasattr(route, 'methods'):
            route_info['methods'] = getattr(route, 'methods', None)
        if hasattr(route, 'name'):
            route_info['name'] = getattr(route, 'name', None)
        if route_info:
            routes.append(route_info)
    return {"routes": routes}

@app.get("/")
async def root():
    try:
        stats = asset_queries.get_asset_statistics()
        return {
            "message": "Blacksmith Atlas API (ArangoDB Mode)",
            "version": "1.0.0",
            "database": "ArangoDB Community Edition",
            "docs": "/docs",
            "status": "running",
            "assets_count": stats.get('total_assets', 0),
            "categories": [c['category'] for c in stats.get('by_category', [])]
        }
    except Exception as e:
        return {
            "message": "Blacksmith Atlas API",
            "version": "1.0.0",
            "database": "ArangoDB",
            "status": "running",
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    try:
        stats = asset_queries.get_asset_statistics()
        return {
            "status": "healthy",
            "service": "Blacksmith Atlas Backend",
            "database": "ArangoDB Community Edition",
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Blacksmith Atlas Backend",
            "database": "ArangoDB",
            "error": str(e)
        }

@app.post("/admin/save-config")
async def save_config():
    # Configuration saving logic here
    return {"message": "Configuration saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)