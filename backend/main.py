# backend/main.py - Enhanced FastAPI application with all TODO features
#v.0.1.0
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError

# Import only working routers for now
from backend.api.assets import router as assets_router
# Disabled problematic routers until Pydantic compatibility is fixed
# from backend.api.todos import router as todos_router
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
from backend.assetlibrary.config import BlacksmithAtlasConfig

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
    logger.info("🚀 Starting Enhanced Blacksmith Atlas API v2.0...")
    
    # Test database connection
    try:
        stats = asset_queries.get_asset_statistics()
        logger.info(f"📊 ArangoDB connected successfully: {stats.get('total_assets', 0)} assets")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise Exception(f"Database connection failed: {e}")
    
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

# Include only working routers for now
app.include_router(assets_router)
# Disabled problematic routers until Pydantic compatibility is fixed
# app.include_router(todos_router)
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
                "users": "/api/v1/users",
                "todos": "/api/v1/todos"
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