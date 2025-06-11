# backend/main.py - Complete file with working thumbnail endpoint
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.assets import router as assets_router
from pathlib import Path
import os

app = FastAPI(
    title="Blacksmith Atlas API",
    description="Asset Library Management System (JSON Database)",
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


@app.get("/test-thumbnail")
async def test_thumbnail():
    """Direct test - no JSON, no database, just serve the file"""
    from fastapi.responses import FileResponse
    from pathlib import Path

    # Direct path to your PigHead thumbnail
    path = r"C:\Users\alexh\Desktop\BlacksmithAtlas_Files\AssetLibrary\3D\5a337cb9_PigHead\Thumbnail\PigHead_thumbnail.png"

    file = Path(path)
    if file.exists():
        return FileResponse(path)
    else:
        return {"error": "File not found", "path": path, "exists": file.exists()}


# IMPORTANT: Define specific routes BEFORE including routers
# Serve thumbnail images
@app.get("/thumbnails/{asset_id}")
async def get_thumbnail(asset_id: str):
    """Serve thumbnail images for assets"""
    from api.assets import load_json_database

    print(f"📸 Thumbnail requested for asset: {asset_id}")

    try:
        # Load assets from JSON database
        assets = load_json_database()

        # Find the asset by ID
        asset = None
        for a in assets:
            if a.get('id') == asset_id:
                asset = a
                break

        if not asset:
            print(f"❌ Asset not found: {asset_id}")
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

        # Get thumbnail path from asset data
        thumbnail_path = None
        if 'paths' in asset and 'thumbnail' in asset['paths']:
            thumbnail_path = asset['paths']['thumbnail']
            print(f"📸 Found thumbnail path in JSON: {thumbnail_path}")

        if not thumbnail_path:
            print(f"❌ No thumbnail path for asset: {asset_id}")
            raise HTTPException(status_code=404, detail=f"No thumbnail path for asset: {asset_id}")

        # Convert to Path object and check if file exists
        thumb_file = Path(thumbnail_path)

        if not thumb_file.exists():
            print(f"❌ Thumbnail file doesn't exist: {thumbnail_path}")
            raise HTTPException(status_code=404, detail=f"Thumbnail file not found: {thumbnail_path}")

        print(f"✅ Serving thumbnail: {thumb_file}")
        return FileResponse(
            path=str(thumb_file),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error serving thumbnail: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error serving thumbnail: {str(e)}")


# Include routers AFTER defining specific routes
app.include_router(assets_router)


# Debug: List all routes
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
    return {
        "message": "Blacksmith Atlas API (JSON Mode)",
        "version": "1.0.0",
        "database": "JSON",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    # Check if JSON database file exists
    json_db_path = Path(__file__).parent / "assetlibrary" / "database" / "3DAssets.json"

    return {
        "status": "healthy",
        "service": "Blacksmith Atlas Backend",
        "database": "JSON",
        "database_exists": json_db_path.exists(),
        "database_path": str(json_db_path)
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)