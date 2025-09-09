# backend/main.py - Enhanced FastAPI application with all TODO features
#v.0.1.0
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError

# Import only working routers for now
from backend.api.assets import router as assets_router
from backend.api.config import router as config_router
# Disabled problematic routers until Pydantic compatibility is fixed
# from backend.api.asset_sync import router as sync_router
# from backend.api.products import router as products_router
# from backend.api.users import router as users_router

# Temporarily disable custom error handlers and middleware
# from backend.core.error_handlers import (
#     http_exception_handler,
#     validation_exception_handler,
#     business_logic_exception_handler,
#     resource_not_found_exception_handler,
#     duplicate_resource_exception_handler,
#     database_exception_handler,
#     external_service_exception_handler,
#     general_exception_handler,
#     BusinessLogicError,
#     ResourceNotFoundError,
#     DuplicateResourceError,
#     DatabaseError,
#     ExternalServiceError
# )
# from backend.core.middleware import (
#     rate_limiting_middleware,
#     request_logging_middleware,
#     security_headers_middleware
# )
# from backend.core.redis_cache import cache

from pathlib import Path
import os
import logging
from datetime import datetime
from backend.core.config_manager import config as atlas_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blacksmith Atlas API",
    description="Enhanced Asset Library Management System with ArangoDB, Redis, and comprehensive RESTful API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Temporarily disable custom middleware
# app.middleware("http")(security_headers_middleware)
# app.middleware("http")(request_logging_middleware)
# app.middleware("http")(rate_limiting_middleware)

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

# Temporarily disable custom exception handlers
# app.add_exception_handler(HTTPException, http_exception_handler)
# app.add_exception_handler(RequestValidationError, validation_exception_handler)
# app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
# app.add_exception_handler(ResourceNotFoundError, resource_not_found_exception_handler)
# app.add_exception_handler(DuplicateResourceError, duplicate_resource_exception_handler)
# app.add_exception_handler(DatabaseError, database_exception_handler)
# app.add_exception_handler(ExternalServiceError, external_service_exception_handler)
# app.add_exception_handler(Exception, general_exception_handler)

# Initialize ArangoDB handler
try:
    from backend.assetlibrary.database.arango_queries import AssetQueries
    # Get the correct environment configuration from Atlas config
    # Check if we're in Docker by looking for ARANGO_HOST env variable
    is_docker = os.getenv('ARANGO_HOST') is not None
    
    # Use config file settings, but override host if in Docker
    db_config = atlas_config.get('api.database', {})
    
    # In Docker, use container name; otherwise use config
    db_host = os.getenv('ARANGO_HOST') if is_docker else db_config.get('host', 'localhost')
    
    arango_config = {
        'hosts': [f"http://{db_host}:{db_config.get('port', '8529')}"],
        'database': db_config.get('name', 'blacksmith_atlas'),
        'username': db_config.get('username', 'root'),
        'password': db_config.get('password', 'atlas_password'),
        'collections': {
            'assets': 'Atlas_Library'
        }
    }
    logger.info(f"🔧 Database configuration: host={db_host}, is_docker={is_docker}")
    asset_queries = AssetQueries(arango_config)
    database_available = True
    logger.info("✅ ArangoDB connection initialized")
except Exception as e:
    logger.error(f"❌ ArangoDB connection failed: {e}")
    raise Exception(f"Failed to connect to ArangoDB: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Enhanced Blacksmith Atlas API v2.0...")
    
    # Test database connection - temporarily disabled to debug
    logger.warning("⚠️  Database startup check temporarily disabled for debugging")
    
    # Redis temporarily disabled
    logger.info("⚠️ Redis disabled temporarily for testing")
    
    logger.info("🎉 All systems ready!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Blacksmith Atlas API...")
    # Add any cleanup code here if needed

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
        # Try to get the folder path from the asset data
        folder_path = asset.get('folder_path') or asset.get('paths', {}).get('folder_path')
        if folder_path:
            # Convert network path to container path if needed
            if folder_path.startswith('/net/library/atlaslib/'):
                container_folder = folder_path.replace('/net/library/atlaslib/', '/app/assets/')
                logger.info(f"[THUMBNAIL] Converted path: {folder_path} -> {container_folder}")
                folder_path = container_folder
            
            # Look for thumbnail folder in the asset's folder
            thumbnail_folder = Path(folder_path) / "Thumbnail"
            logger.info(f"[THUMBNAIL] Looking for thumbnails in: {thumbnail_folder}")
            if thumbnail_folder.exists() and thumbnail_folder.is_dir():
                logger.info(f"[THUMBNAIL] Found thumbnail folder: {thumbnail_folder}")
                for ext in ['.png', '.jpg', '.jpeg']:
                    for img_file in thumbnail_folder.glob(f"*{ext}"):
                        logger.info(f"[THUMBNAIL] Found thumbnail file: {img_file}")
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

@app.get("/api/v1/assets/{asset_id}/thumbnail-sequence")
async def get_thumbnail_sequence(asset_id: str):
    """Get list of thumbnail sequence frames for an asset"""
    logger.info(f"[THUMBNAIL-SEQUENCE] Requested for asset: {asset_id}")
    try:
        asset = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")
        
        # Build thumbnail folder path
        asset_name = asset.get('name', '')
        asset_path = os.getenv('ASSET_LIBRARY_PATH', '/app/assets')
        
        # Try multiple possible folder structures
        thumbnail_folders = []
        
        # Check folder_path from metadata (most accurate path)
        folder_path = asset.get('folder_path')
        if folder_path:
            # Convert network path to container path if needed
            if folder_path.startswith('/net/library/atlaslib/'):
                container_folder = folder_path.replace('/net/library/atlaslib/', '/app/assets/')
                thumbnail_folders.append(Path(container_folder) / "Thumbnail")
            else:
                thumbnail_folders.append(Path(folder_path) / "Thumbnail")
        
        # Check paths.folder_path as well
        paths_folder_path = asset.get('paths', {}).get('folder_path')
        if paths_folder_path and paths_folder_path != folder_path:
            if paths_folder_path.startswith('/net/library/atlaslib/'):
                container_folder = paths_folder_path.replace('/net/library/atlaslib/', '/app/assets/')
                thumbnail_folders.append(Path(container_folder) / "Thumbnail")
            else:
                thumbnail_folders.append(Path(paths_folder_path) / "Thumbnail")
        
        # Legacy field name
        if asset.get('paths', {}).get('asset_folder'):
            asset_folder = Path(asset['paths']['asset_folder'])
            thumbnail_folders.append(asset_folder / "Thumbnail")
        
        # Fallback search patterns
        thumbnail_folders.extend([
            Path(asset_path) / "3D" / "Assets" / "BlacksmithAssets" / asset_id / "Thumbnail",
            Path(asset_path) / "3D" / "Assets" / "Blacksmith Asset" / asset_id / "Thumbnail",
            Path(asset_path) / "3D" / f"{asset_id}_{asset_name}" / "Thumbnail",
            Path(asset_path) / "3D" / asset_id / "Thumbnail"
        ])
        
        # Find thumbnail sequence files
        sequence_files = []
        for thumbnail_folder in thumbnail_folders:
            if thumbnail_folder.exists():
                logger.info(f"[SEQUENCE] Checking folder: {thumbnail_folder}")
                # Look for PNG sequence files (common naming patterns)
                for pattern in ["*.png", "*.jpg", "*.jpeg", "*.exr"]:
                    files = sorted(list(thumbnail_folder.glob(pattern)))
                    if files:
                        logger.info(f"[SEQUENCE] Found {len(files)} files with pattern {pattern}")
                        sequence_files = files
                        break
                if sequence_files:
                    break
        
        if not sequence_files:
            logger.error(f"[SEQUENCE] No thumbnail sequence found for asset: {asset_id}")
            raise HTTPException(status_code=404, detail=f"No thumbnail sequence found for asset: {asset_id}")
        
        # Extract actual frame numbers from filenames
        def extract_frame_number(filename):
            """Extract frame number from filename like 'asset_1001.png' or 'asset.1001.png'"""
            import re
            # Common patterns: asset_1001.png, asset.1001.png, 1001.png
            patterns = [
                r'_(\d{4})\.',  # asset_1001.png
                r'\.(\d{4})\.',  # asset.1001.png  
                r'^(\d{4})\.',   # 1001.png
                r'(\d{4})$'      # 1001 (without extension)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename)
                if match:
                    return int(match.group(1))
            
            # Fallback to filename sorting order if no frame number found
            return None

        # Build frames with actual frame numbers
        frames_with_numbers = []
        for i, file in enumerate(sequence_files):
            actual_frame = extract_frame_number(file.name)
            frames_with_numbers.append({
                "index": i,  # 0-based index for API access
                "frame_number": actual_frame,  # Actual frame number from filename
                "filename": file.name,
                "url": f"/api/v1/assets/{asset_id}/thumbnail-sequence/frame/{i}"
            })

        # Calculate frame range
        frame_numbers = [f["frame_number"] for f in frames_with_numbers if f["frame_number"] is not None]
        frame_range = {
            "start": min(frame_numbers) if frame_numbers else 1,
            "end": max(frame_numbers) if frame_numbers else len(sequence_files)
        }

        # Return sequence metadata
        sequence_info = {
            "asset_id": asset_id,
            "frame_count": len(sequence_files),
            "frame_range": frame_range,
            "base_url": f"/api/v1/assets/{asset_id}/thumbnail-sequence/frame",
            "frames": frames_with_numbers
        }
        
        logger.info(f"[SEQUENCE] Returning {len(sequence_files)} frames for asset: {asset_id}")
        return sequence_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error getting thumbnail sequence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting thumbnail sequence: {str(e)}")

@app.get("/api/v1/assets/{asset_id}/thumbnail-sequence/frame/{frame_number}")
async def get_thumbnail_sequence_frame(asset_id: str, frame_number: int):
    """Get a specific frame from the thumbnail sequence"""
    logger.info(f"[THUMBNAIL-FRAME] Requested frame {frame_number} for asset: {asset_id}")
    try:
        asset = asset_queries.get_asset_with_dependencies(asset_id).get('asset')
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")
        
        # Build thumbnail folder path (same logic as above)
        asset_name = asset.get('name', '')
        asset_path = os.getenv('ASSET_LIBRARY_PATH', '/app/assets')
        
        # Try multiple possible folder structures
        thumbnail_folders = []
        
        # Check folder_path from metadata (most accurate path)
        folder_path = asset.get('folder_path')
        if folder_path:
            # Convert network path to container path if needed
            if folder_path.startswith('/net/library/atlaslib/'):
                container_folder = folder_path.replace('/net/library/atlaslib/', '/app/assets/')
                thumbnail_folders.append(Path(container_folder) / "Thumbnail")
            else:
                thumbnail_folders.append(Path(folder_path) / "Thumbnail")
        
        # Check paths.folder_path as well
        paths_folder_path = asset.get('paths', {}).get('folder_path')
        if paths_folder_path and paths_folder_path != folder_path:
            if paths_folder_path.startswith('/net/library/atlaslib/'):
                container_folder = paths_folder_path.replace('/net/library/atlaslib/', '/app/assets/')
                thumbnail_folders.append(Path(container_folder) / "Thumbnail")
            else:
                thumbnail_folders.append(Path(paths_folder_path) / "Thumbnail")
        
        # Legacy field name
        if asset.get('paths', {}).get('asset_folder'):
            asset_folder = Path(asset['paths']['asset_folder'])
            thumbnail_folders.append(asset_folder / "Thumbnail")
        
        thumbnail_folders.extend([
            Path(asset_path) / "3D" / "Assets" / "BlacksmithAssets" / asset_id / "Thumbnail",
            Path(asset_path) / "3D" / "Assets" / "Blacksmith Asset" / asset_id / "Thumbnail",
            Path(asset_path) / "3D" / f"{asset_id}_{asset_name}" / "Thumbnail",
            Path(asset_path) / "3D" / asset_id / "Thumbnail"
        ])
        
        # Find thumbnail sequence files
        sequence_files = []
        for thumbnail_folder in thumbnail_folders:
            if thumbnail_folder.exists():
                for pattern in ["*.png", "*.jpg", "*.jpeg", "*.exr"]:
                    files = sorted(list(thumbnail_folder.glob(pattern)))
                    if files:
                        sequence_files = files
                        break
                if sequence_files:
                    break
        
        if not sequence_files:
            raise HTTPException(status_code=404, detail=f"No thumbnail sequence found for asset: {asset_id}")
        
        # Validate frame number
        if frame_number < 0 or frame_number >= len(sequence_files):
            raise HTTPException(status_code=400, detail=f"Frame {frame_number} out of range (0-{len(sequence_files)-1})")
        
        # Serve the specific frame
        frame_path = sequence_files[frame_number]
        logger.info(f"[FRAME] Serving frame {frame_number}: {frame_path.name}")
        
        return FileResponse(
            path=str(frame_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error serving thumbnail frame: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving thumbnail frame: {str(e)}")

# Include only working routers for now
app.include_router(assets_router)
app.include_router(config_router)
# Disabled problematic routers until Pydantic compatibility is fixed
# app.include_router(sync_router)
# app.include_router(products_router, prefix="/api/v1")
# app.include_router(users_router, prefix="/api/v1")

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
    """API root endpoint with system information"""
    try:
        stats = asset_queries.get_asset_statistics()
        redis_connected = False  # Temporarily disabled
        
        return {
            "message": "Enhanced Blacksmith Atlas API",
            "version": "2.0.0",
            "database": "ArangoDB Community Edition",
            "cache": "Redis" if redis_connected else "Not available",
            "features": [
                "Complete CRUD operations",
                "Pagination support", 
                "Graph traversal",
                "Generic collection endpoints",
                "Redis caching",
                "Rate limiting",
                "Request logging",
                "Standardized error handling"
            ],
            "endpoints": {
                "documentation": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "assets": "/api/v1/assets",
                "products": "/api/v1/products", 
                "users": "/api/v1/users"
            },
            "status": "running",
            "statistics": {
                "assets_count": stats.get('total_assets', 0),
                "categories": [c['category'] for c in stats.get('by_category', [])],
                "redis_connected": redis_connected
            }
        }
    except Exception as e:
        return {
            "message": "Enhanced Blacksmith Atlas API",
            "version": "2.0.0", 
            "status": "running",
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "Enhanced Blacksmith Atlas Backend",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check ArangoDB
    try:
        stats = asset_queries.get_asset_statistics()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "ArangoDB Community Edition",
            "assets_count": stats.get('total_assets', 0)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy", 
            "type": "ArangoDB Community Edition",
            "error": str(e)
        }
    
    # Redis temporarily disabled
    health_status["components"]["cache"] = {
        "status": "disabled",
        "type": "Redis", 
        "message": "Cache temporarily disabled for testing"
    }
    
    return health_status

@app.post("/admin/save-config")
async def save_config():
    # Configuration saving logic here
    return {"message": "Configuration saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)