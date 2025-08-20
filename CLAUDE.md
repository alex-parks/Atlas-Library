# CLAUDE.md - Blacksmith Atlas Library

## Project Overview

**Blacksmith Atlas** is a comprehensive 2D and 3D Asset Library Management System designed for **Blacksmith VFX Company**. This is a professional-grade asset management platform that centralizes all digital assets across the studio's network infrastructure, providing seamless integration between various DCC applications and asset workflows.

### Current Release Status
- **3D Library**: ✅ **Production Ready** - Fully implemented and operational
- **2D Library**: 🚧 **In Construction** - Planned for future release

### Core Architecture Philosophy
The system follows a **containerized microservices architecture** using Docker/Podman, with each component running as an independent service:

- **Backend API**: FastAPI with ArangoDB integration
- **Frontend Interface**: React/Vite SPA with Tailwind CSS
- **Database**: ArangoDB Community Edition (document-based with graph relationships)
- **Cache Layer**: Redis for performance optimization
- **Network Storage**: Company network-mounted asset library

## Container Architecture (Docker Compose)

The system runs as a multi-container application orchestrated via `docker-compose.yml`. All services communicate through a dedicated bridge network (`atlas-network`):

### Service Configuration

#### 🗄️ ArangoDB Database Service
```yaml
arangodb:
  image: arangodb:latest
  container_name: blacksmith-atlas-db
  ports: "8529:8529"
  environment:
    - ARANGO_ROOT_PASSWORD=atlas_password
    - ARANGO_DB_NAME=blacksmith_atlas
  volumes:
    - arango_data:/var/lib/arangodb3
    - arango_apps:/var/lib/arangodb3-apps
```
- **Purpose**: Document-based database with graph relationships
- **Collection**: Single `Atlas_Library` collection for all assets
- **Authentication**: Root user with company-standard password
- **Persistence**: Named volumes for data retention

#### ⚡ Redis Cache Service
```yaml
redis:
  image: redis:7-alpine
  container_name: blacksmith-atlas-redis
  ports: "6379:6379"
  command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```
- **Purpose**: Performance optimization and session management
- **Configuration**: 1GB memory limit with LRU eviction policy
- **Persistence**: Append-only file (AOF) for data durability

#### 🔧 Backend API Service
```yaml
backend:
  build: { context: ., dockerfile: Dockerfile }
  container_name: blacksmith-atlas-backend
  ports: "8000:8000"
  environment:
    - ATLAS_ENV=development
    - ARANGO_HOST=arangodb
    - ARANGO_DATABASE=blacksmith_atlas
    - ASSET_LIBRARY_PATH=/net/library/atlaslib
  volumes:
    - /net/library/atlaslib:/app/assets  # Network asset library mount
    - ./logs:/app/logs
  depends_on: [arangodb, redis]
```
- **Framework**: FastAPI with async/await patterns
- **API Version**: v2.0.0 with comprehensive RESTful endpoints
- **Network Mount**: Company asset library at `/net/library/atlaslib`
- **Dependencies**: Requires ArangoDB and Redis services

#### 🎨 Frontend Interface Service
```yaml
frontend:
  build: { context: ./frontend, dockerfile: Dockerfile }
  container_name: blacksmith-atlas-frontend
  ports: "3011:3011"
  environment:
    - VITE_API_URL=http://localhost:8000
  volumes:
    - ./frontend:/app
    - /app/node_modules
  depends_on: [backend]
```
- **Framework**: React 18 with Vite build system
- **Styling**: Tailwind CSS with dark mode as default
- **Hot Reload**: Development mode with live updates
- **API Integration**: Direct connection to backend service

### Container Management (Podman Compatible)

The system uses Docker Compose syntax but is fully compatible with **Podman** for rootless container management:

```bash
# Start all services
npm run docker:dev
# or direct podman compose
podman compose up -d

# Stop services
npm run docker:stop

# View logs
npm run docker:logs

# Check service status
npm run docker:status

# Database setup
npm run docker:setup-db
```

## Database Architecture (ArangoDB)

### Collection Structure
The database uses a **single collection approach** for optimal performance and simplified queries:

#### `Atlas_Library` Collection (Primary)
```json
{
  "_key": "asset_id_12345678",
  "name": "Asset Name",
  "category": "Subcategory Name",
  "asset_type": "Assets|FX|Materials|HDAs",
  "dimension": "3D",
  "hierarchy": {
    "dimension": "3D",
    "asset_type": "Assets", 
    "subcategory": "Blacksmith Asset",
    "render_engine": "Redshift"
  },
  "metadata": {
    "houdini_version": "20.5.445",
    "export_metadata": { /* Houdini export details */ },
    "textures": { /* Texture file mappings */ },
    "geometry_files": { /* Geometry file mappings */ }
  },
  "paths": {
    "asset_folder": "/net/library/atlaslib/3D/Assets/...",
    "template_file": "template.hipnc",
    "textures": ["path1", "path2"],
    "geometry": ["path1", "path2"]
  },
  "file_sizes": { /* File size information */ },
  "tags": ["tag1", "tag2"],
  "created_at": "2025-08-19T23:17:30.230177",
  "created_by": "username",
  "status": "active"
}
```

### Database Configuration
- **Database Name**: `blacksmith_atlas`
- **Authentication**: Root user with atlas_password
- **Connection**: Internal service discovery via `arangodb:8529`
- **Query Language**: AQL (ArangoDB Query Language)
- **Indexes**: Optimized for name, category, tags, and creation date queries

## API Architecture (FastAPI Backend)

### Core Endpoints Structure

The backend provides a comprehensive RESTful API with the following endpoint categories:

#### Asset Management (`/api/v1/assets`)
```python
GET    /api/v1/assets              # List assets with pagination
POST   /api/v1/assets              # Create new asset
GET    /api/v1/assets/{id}         # Get specific asset
PUT    /api/v1/assets/{id}         # Update entire asset
PATCH  /api/v1/assets/{id}         # Partial asset update
DELETE /api/v1/assets/{id}         # Delete asset
GET    /api/v1/assets/{id}/expand  # Get asset with relationships
```

#### System & Health Monitoring
```python
GET    /health                     # System health check
GET    /                          # API information and statistics
GET    /api/v1/assets/stats/summary # Asset library statistics
GET    /database/status            # Database connection status
GET    /debug/test-connection      # Database connectivity test
```

#### File Serving
```python
GET    /thumbnails/{asset_id}      # Serve asset thumbnails
GET    /test-thumbnail             # Test thumbnail serving
```

#### Administrative Functions
```python
POST   /api/v1/assets/{id}/open-folder  # Open asset folder in file manager
POST   /admin/sync                      # Filesystem to database sync
POST   /admin/sync-bidirectional        # Bidirectional sync
POST   /admin/save-config              # Save system configuration
```

### API Response Format
All endpoints follow consistent response patterns with proper HTTP status codes:

```json
{
  "items": [/* Array of assets */],
  "total": 150,
  "limit": 100, 
  "offset": 0,
  "has_more": true
}
```

### Error Handling
Comprehensive error handling with detailed error messages and proper HTTP status codes (400, 404, 500, etc.).

## Asset Ingestion Workflow

### External Application Integration

The system provides a **standalone REST API** that can be called from any DCC application or external system:

#### Supported Applications
- **Houdini** (Primary integration)
- **Nuke** (REST API client)
- **Unreal Engine** (HTTP requests)
- **Any application supporting REST API calls**

#### Ingestion Process

1. **Metadata Generation**: DCC applications generate `metadata.json` files containing asset information
2. **API Submission**: Applications POST metadata to `/api/v1/assets` endpoint
3. **Database Storage**: API validates and stores data in ArangoDB `Atlas_Library` collection
4. **File Management**: System manages file paths and references on network storage

#### Metadata JSON Structure
```json
{
  "id": "9547BE2E",
  "name": "asset_name",
  "asset_type": "Assets",
  "subcategory": "Blacksmith Asset", 
  "dimension": "3D",
  "render_engine": "Redshift",
  "houdini_version": "20.5.445",
  "template_file": "template.hipnc",
  "textures": {
    "count": 13,
    "files": ["texture1.png", "texture2.exr"],
    "mapping": { /* Detailed texture mappings */ }
  },
  "geometry_files": {
    "count": 10,
    "files": ["model.obj", "model.fbx"],
    "mapping": { /* Geometry file mappings */ }
  }
}
```

#### Ingestion Script Usage
```bash
# Single metadata file
python scripts/utilities/ingest_metadata.py /path/to/metadata.json

# Directory of metadata files  
python scripts/utilities/ingest_metadata.py --directory /path/to/assets/

# Batch processing with recursion
python scripts/utilities/ingest_metadata.py --batch /path/to/library --recursive
```

## Frontend Interface (React Application)

### User Interface Features

#### Asset Library Browser
- **Hierarchical Navigation**: Dimension → Category → Subcategory → Assets
- **View Modes**: Grid view and List view with thumbnail previews
- **Search & Filtering**: Real-time search with category and tag filters
- **Asset Preview**: Modal preview with detailed metadata display

#### Navigation Structure
```
3D Assets
├── Assets
│   ├── Blacksmith Asset (Custom studio assets)
│   ├── Megascans (Quixel library assets)  
│   └── Kitbash (Modular construction assets)
├── FX
│   ├── Blacksmith FX (Custom VFX elements)
│   ├── Atmosphere (Environmental effects)
│   ├── FLIP (Fluid simulations)
│   └── Pyro (Fire, smoke, explosions)
├── Materials
│   ├── Blacksmith Materials (Custom shaders)
│   ├── Redshift (Redshift renderer materials)
│   └── Karma (Karma renderer materials)
└── HDAs
    └── Blacksmith HDAs (Custom Houdini Digital Assets)
```

#### Additional Interface Components
- **Settings Panel**: Configuration management for API endpoints and paths
- **Database Health Monitoring**: Real-time connection status and asset counts
- **Copy-to-Clipboard**: Asset information for DCC integration
- **File System Integration**: Direct folder opening in OS file managers

### Frontend Technology Stack
- **React 18**: Modern functional components with hooks
- **Vite**: Fast build tool with hot reload
- **Tailwind CSS**: Utility-first styling framework
- **Lucide React**: Consistent icon library
- **Dark Mode**: Professional dark theme as default

## Network Asset Library Structure

The system integrates with the company's network-mounted asset library:

### File System Organization
```
/net/library/atlaslib/
├── 3D/                          # 3D Asset Library (Current Release)
│   ├── Assets/
│   │   ├── Blacksmith Asset/    # Studio originals
│   │   ├── Megascans/          # Quixel library
│   │   └── Kitbash/            # Modular assets
│   ├── FX/
│   │   ├── Blacksmith FX/
│   │   ├── Atmosphere/
│   │   ├── FLIP/
│   │   └── Pyro/
│   ├── Materials/
│   │   ├── Blacksmith Materials/
│   │   ├── Redshift/
│   │   └── Karma/
│   └── HDAs/
│       └── Blacksmith HDAs/
└── 2D/                          # 2D Asset Library (Future Release)
    ├── Textures/
    ├── References/
    └── UI/
```

### Asset Folder Structure
Each asset folder contains:
```
AssetID_AssetName/
├── metadata.json               # Asset metadata and export information
├── template.hipnc             # Houdini template file  
├── Textures/                  # Texture maps organized by material
│   ├── MaterialName/
│   │   ├── BaseColor.png
│   │   ├── Normal.exr
│   │   └── Roughness.png
│   └── ...
├── Geometry/                  # Geometry files by format
│   ├── OBJ/
│   ├── FBX/ 
│   ├── Alembic/
│   └── Other/
└── Thumbnail/                 # Asset preview images
    └── AssetName_thumbnail.png
```

## Development Workflow

### Starting the System
```bash
# Primary method (Recommended)
npm run start                    # Start all containers
# or
npm run docker:dev              # Development mode with logs

# Legacy development mode (without containers)
npm run dev:legacy              # Start backend and frontend separately
```

### Service Management
```bash
# Container operations
npm run docker:stop             # Stop all services
npm run docker:restart          # Restart services
npm run docker:logs             # View service logs
npm run docker:status           # Check service health
npm run docker:cleanup          # Clean up containers and volumes

# Database operations  
npm run docker:setup-db         # Initialize ArangoDB collections
npm run db:status              # Check database connectivity
```

### Development Commands
```bash
# Frontend development
cd frontend && npm run dev      # Start frontend dev server

# Backend development  
cd backend && python main.py   # Start FastAPI server

# Database testing
cd backend && python -m backend.assetlibrary.database.setup_arango_database test
```

### Asset Ingestion Testing
```bash
# Test single metadata file ingestion
/scripts/utilities/run_ingester.sh file /path/to/metadata.json

# Test directory ingestion
/scripts/utilities/run_ingester.sh directory /path/to/assets/

# API endpoint testing
curl -X GET http://localhost:8000/api/v1/assets
curl -X GET http://localhost:8000/health
```

## Service URLs and Access Points

### Development URLs
- **Frontend Interface**: http://localhost:3011
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc
- **ArangoDB Web Interface**: http://localhost:8529 (root/atlas_password)
- **Redis**: localhost:6379 (internal service)

### API Integration Examples

#### Creating Assets from External Applications
```python
import requests
import json

# Asset data from DCC application
asset_data = {
    "name": "MyAsset",
    "category": "Blacksmith Asset", 
    "metadata": {
        "asset_type": "Assets",
        "dimension": "3D",
        "render_engine": "Redshift"
    },
    "paths": {
        "template_file": "/path/to/template.hip"
    }
}

# POST to Atlas API
response = requests.post(
    "http://localhost:8000/api/v1/assets",
    json=asset_data
)

if response.status_code == 200:
    print(f"Asset created: {response.json()['id']}")
```

#### Querying Assets
```python
# Search assets
response = requests.get(
    "http://localhost:8000/api/v1/assets", 
    params={"search": "character", "limit": 50}
)

assets = response.json()['items']
```

## File Organization and Project Structure

### Backend Structure (`/backend`)
```
backend/
├── main.py                     # FastAPI application entry point
├── api/                        # REST API endpoints
│   ├── assets.py              # Asset CRUD operations  
│   ├── asset_sync.py          # Database synchronization
│   └── todos.py               # Task management (future)
├── assetlibrary/              # Core asset management
│   ├── config.py              # Configuration management
│   ├── models.py              # Pydantic data models
│   ├── database/              # Database layer
│   │   ├── arango_queries.py  # ArangoDB query methods
│   │   └── setup_arango_database.py # Database initialization
│   └── houdini/               # Houdini integration modules
│       ├── houdiniae.py       # Core Houdini integration
│       └── tools/             # Houdini shelf tools
├── core/                      # Core business logic
│   ├── asset_manager.py       # Asset management classes
│   └── base_atlas_object.py   # Base object definitions
└── requirements.txt           # Python dependencies
```

### Frontend Structure (`/frontend`)
```
frontend/
├── src/
│   ├── App.jsx                # Main application component
│   └── components/
│       ├── AssetLibrary.jsx   # Primary asset browser interface
│       ├── Settings.jsx       # Configuration panel
│       └── AITools.jsx        # Future AI integration
├── public/
│   └── Blacksmith_TopLeft.png # Company branding assets
├── package.json               # Node.js dependencies
└── vite.config.js             # Build configuration
```

### Scripts and Utilities (`/scripts`)
```
scripts/
├── deployment/                # Container deployment scripts
│   ├── docker-scripts.sh     # Unix container management
│   └── docker-scripts.bat    # Windows container management
├── database/                  # Database management scripts
│   ├── init_arangodb.py      # Database initialization
│   └── reset_arangodb.py     # Database reset utilities
└── utilities/                 # Asset management utilities
    ├── ingest_metadata.py     # Metadata ingestion script
    ├── run_ingester.sh        # Ingestion wrapper script
    └── atlas_sync.py          # Filesystem synchronization
```

## Integration with DCC Applications

### Houdini Integration (Primary)
- **Template-based Export**: Assets exported as Houdini template files
- **Shelf Tools**: Custom Houdini shelf buttons for Atlas integration
- **Metadata Generation**: Automatic metadata.json creation during export
- **Texture Remapping**: Intelligent texture path resolution and copying
- **Geometry Handling**: Support for USD, FBX, OBJ, and Alembic formats

### Universal REST API Integration
Any application can integrate with Atlas using standard HTTP requests:

```python
# Example integration for any DCC application
class AtlasAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def create_asset(self, metadata):
        """Submit asset metadata to Atlas"""
        response = requests.post(f"{self.base_url}/api/v1/assets", json=metadata)
        return response.json()
    
    def search_assets(self, query):
        """Search Atlas asset library"""
        response = requests.get(
            f"{self.base_url}/api/v1/assets",
            params={"search": query}
        )
        return response.json()['items']
```

## Security and Access Control

### Network Security
- **Internal Network Access**: Services only accessible on company network
- **Container Isolation**: Each service runs in isolated Docker containers
- **Database Authentication**: ArangoDB requires username/password authentication
- **API CORS**: Cross-Origin Resource Sharing configured for approved origins

### File System Security
- **Network Mount Security**: Asset library mounted with appropriate permissions
- **Path Validation**: All file paths validated to prevent directory traversal
- **Read-Only API Access**: API provides read access to network-mounted assets

## Monitoring and Maintenance

### Health Monitoring
- **Service Health Checks**: All containers include health check configurations
- **Database Connectivity**: Automatic database connection monitoring
- **API Status**: Real-time API health reporting at `/health` endpoint
- **Asset Count Tracking**: Live asset count monitoring and reporting

### Logging and Debugging
- **Structured Logging**: Comprehensive logging throughout all services
- **Debug Endpoints**: Special debug endpoints for troubleshooting
- **Container Logs**: Centralized logging via Docker/Podman
- **Error Tracking**: Detailed error reporting and stack traces

### Backup and Recovery
- **Database Persistence**: ArangoDB data persisted in Docker volumes
- **Asset Library**: Network asset library managed by IT infrastructure
- **Configuration Backup**: System configuration stored in version control

## Performance Optimization

### Caching Strategy
- **Redis Integration**: Redis caching for frequently accessed data
- **Thumbnail Caching**: Efficient thumbnail serving with HTTP cache headers
- **Query Optimization**: ArangoDB indexes for optimal query performance

### Scalability Considerations
- **Horizontal Scaling**: Container-based architecture supports scaling
- **Database Sharding**: ArangoDB supports horizontal scaling as needed
- **Load Balancing**: Future load balancer integration capability
- **Asset CDN**: Future content delivery network integration

## Future Development Roadmap

### Phase 1: 2D Library Integration
- **2D Asset Categories**: Textures, References, UI Elements
- **Image Processing**: Automatic thumbnail generation for 2D assets
- **Metadata Schema**: Extended metadata for 2D asset types

### Phase 2: Enhanced DCC Integration
- **Maya Integration**: Maya-specific asset import/export workflows
- **Nuke Integration**: Nuke project and asset management
- **Unreal Integration**: Unreal Engine asset pipeline integration

### Phase 3: Advanced Features
- **Version Control**: Asset versioning and change tracking  
- **Collaboration Tools**: Multi-user asset management features
- **Analytics Dashboard**: Asset usage analytics and reporting
- **AI Integration**: Automated tagging and asset analysis

## Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check ArangoDB service status
podman logs blacksmith-atlas-db

# Test database connectivity
curl -u root:atlas_password http://localhost:8529/_api/version

# Restart database service
podman restart blacksmith-atlas-db
```

#### API Connection Issues  
```bash
# Check backend service status
podman logs blacksmith-atlas-backend

# Test API health
curl http://localhost:8000/health

# Restart backend service
podman restart blacksmith-atlas-backend
```

#### Asset Ingestion Problems
```bash
# Test metadata ingestion
python scripts/utilities/ingest_metadata.py /path/to/metadata.json --verbose

# Check API connectivity from ingestion script
curl -X POST http://localhost:8000/api/v1/assets -H "Content-Type: application/json" -d '{}'
```

#### Container Management Issues
```bash
# Check all container status
podman compose ps

# Restart all services
podman compose restart  

# Clean restart
podman compose down && podman compose up -d

# Clean up everything
npm run docker:cleanup
```

### Debug Endpoints
- `GET /debug/test-connection` - Test database connection
- `GET /debug/routes` - List all API routes
- `GET /test-assets` - Test asset queries
- `GET /database/status` - Database status details

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

IMPORTANT: Never delete documents unless specifically by user!!!!