# backend/main.py - Simplified for JSON Database
from fastapi import FastAPI
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


# Serve thumbnail images
@app.get("/thumbnails/{asset_id}")
async def get_thumbnail(asset_id: str):
    """Serve thumbnail images for assets"""
    from fastapi import HTTPException

    # First, try to get the exact path from JSON database
    from api.assets import load_json_database
    try:
        assets = load_json_database()
        for asset in assets:
            if asset.get('id') == asset_id and 'paths' in asset and 'thumbnail' in asset['paths']:
                thumbnail_path = Path(asset['paths']['thumbnail'])
                print(f"🔍 Checking JSON path: {thumbnail_path}")
                if thumbnail_path.exists():
                    print(f"✅ Found thumbnail at JSON path: {thumbnail_path}")
                    return FileResponse(thumbnail_path)
                else:
                    print(f"❌ JSON path doesn't exist: {thumbnail_path}")
    except Exception as e:
        print(f"⚠️ Error reading JSON database: {e}")

    # Extract asset name from asset_id (format: id_assetname)
    asset_name = asset_id.split('_', 1)[-1] if '_' in asset_id else asset_id

    # Try multiple common thumbnail path patterns
    thumbnail_patterns = [
        # Your actual structure
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/{asset_name}_thumbnail.png",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/{asset_name}_thumbnail.jpg",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/{asset_id}_thumbnail.png",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/thumbnail.png",
        # Alternative structures
        f"C:/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail/{asset_name}_thumbnail.png",
        f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/USD/{asset_id}/Thumbnail/{asset_name}_thumbnail.png",
    ]

    print(f"🔍 Looking for thumbnails for asset_id: {asset_id}")
    print(f"🔍 Asset name extracted: {asset_name}")

    for i, thumbnail_path in enumerate(thumbnail_patterns):
        path_obj = Path(thumbnail_path)
        print(f"🔍 Pattern {i + 1}: {thumbnail_path}")
        if path_obj.exists():
            print(f"✅ Found thumbnail at pattern {i + 1}: {thumbnail_path}")
            return FileResponse(path_obj)
        else:
            print(f"❌ Pattern {i + 1} doesn't exist: {thumbnail_path}")

    # If still not found, try to find any PNG/JPG in the thumbnail folder
    folder_pattern = f"C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/{asset_id}/Thumbnail"
    thumbnail_folder = Path(folder_pattern)

    if thumbnail_folder.exists():
        print(f"📁 Thumbnail folder exists: {thumbnail_folder}")
        # Find any image file in the folder
        for ext in ['.png', '.jpg', '.jpeg']:
            for thumb_file in thumbnail_folder.glob(f"*{ext}"):
                print(f"✅ Found thumbnail file: {thumb_file}")
                return FileResponse(thumb_file)
        print(f"❌ No image files found in: {thumbnail_folder}")
    else:
        print(f"❌ Thumbnail folder doesn't exist: {thumbnail_folder}")

    # Return 404 if not found
    print(f"❌ No thumbnail found for asset_id: {asset_id}")
    raise HTTPException(status_code=404, detail=f"Thumbnail not found for asset: {asset_id}")


# Include routers
app.include_router(assets_router)


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