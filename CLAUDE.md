# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the Blacksmith Atlas repository.

## Project Overview

Blacksmith Atlas is a comprehensive, object-oriented asset management ecosystem designed to unify VFX production workflows, AI-powered toolsets, and cross-platform asset libraries. Built for professional VFX studios, Atlas serves as the central nervous system for creative operations, spanning from asset libraries to AI-driven production tools.

**Core Philosophy**: Everything is an object. Every tool, asset, workflow, and interaction follows consistent object-oriented patterns to ensure maximum scalability, maintainability, and extensibility.

**Key Features**:
- ✅ **Unified Asset Management**: Cross-DCC integration with Houdini (primary), Maya, Nuke, Flame
- ✅ **ArangoDB Integration**: Document-based storage with graph relationships for asset dependencies
- ✅ **Advanced Frontend**: React/Vite SPA with hierarchical asset browsing and filtering
- ✅ **Houdini Clipboard System**: Web-inspired copy/paste for Atlas assets with encryption support
- ✅ **Real-time Database Sync**: Direct ArangoDB queries for instant asset library updates
- 🚧 **AI-powered Toolset**: ComfyUI integration for workflow automation (planned)
- 🚧 **Producer Analytics**: Bid analysis and project estimation (planned)
- 🚧 **Blacksmith Intelligence**: Chatbot for natural language assistance (planned)

## Current Development Status

### ✅ Completed Features (Production Ready)
1. **Asset Management Core**
   - ArangoDB Atlas_Library collection with full CRUD operations
   - Asset metadata, thumbnails, and file management
   - Hierarchical categorization (3D → Assets/FX/Materials → Subcategories)

2. **Frontend Asset Browser**
   - React-based asset library with grid/list views
   - Navigation through dimensions → categories → subcategories → assets
   - Search, filtering, and real-time database sync
   - Asset preview modals with detailed metadata
   - Copy-to-clipboard functionality for Houdini integration

3. **Houdini Integration** 
   - Core asset export/import system (`houdiniae.py`)
   - Advanced clipboard system with encryption support
   - Shelf tools for seamless Atlas workflow
   - Template-based asset sharing
   - Automatic texture and geometry path remapping

4. **Database Infrastructure**
   - ArangoDB Community Edition with graph relationships
   - Async FastAPI backend with comprehensive error handling
   - Health monitoring and connection management
   - Asset synchronization and orphan cleanup

5. **Deployment & DevOps**
   - Docker Compose multi-service orchestration
   - Cross-platform deployment scripts
   - Professional project structure and organization
   - Comprehensive testing framework setup

### 🚧 In Development
1. **AI Tools Integration** - ComfyUI workflow execution
2. **Producer Analytics** - Project estimation and bid analysis
3. **Additional DCC Support** - Maya, Nuke, Flame panels

### 📋 Planned Features
1. **Blacksmith Intelligence** - Natural language chatbot
2. **Advanced Workflows** - Automated asset processing
3. **Third-party Integrations** - Shotgun, cloud storage
4. **Plugin Ecosystem** - Custom studio tools

## Architecture

### Core Technology Stack
- **Backend**: Python FastAPI application (`/backend`) with async/await patterns using ArangoDB
- **Frontend**: React/Vite SPA (`/frontend`) with Tailwind CSS and Lucide React icons
- **Desktop Application**: Electron wrapper for cross-platform deployment
- **DCC Integration**: PyQt5/6 panels for Houdini, Maya, Nuke, and Flame
- **Database**: ArangoDB Community Edition for document-based storage with graph relationships
- **AI Backend**: ComfyUI integration via REST APIs for workflow execution
- **Message Queue**: Redis for caching, sessions, and background task processing
- **Containerization**: Docker Compose for multi-service orchestration
- **Asset Storage**: Configurable file-based storage with Docker volume mounting

### Object-Oriented Hierarchy
```
BaseAtlasObject
├── AssetObject
│   ├── GeometryAsset (USD, OBJ, FBX)
│   ├── MaterialAsset (Redshift, Arnold, etc.)
│   ├── TextureAsset (EXR, PNG, TIFF)
│   └── LightRigAsset
├── WorkflowObject
│   ├── RenderWorkflow
│   ├── CompositingWorkflow
│   └── AssetCreationWorkflow
├── ProjectObject
│   ├── ProjectMetadata
│   ├── ProjectAssets
│   └── ProjectTimeline
├── AIToolObject
│   ├── ImageProcessingTool
│   ├── AssetGenerationTool
│   └── BidAnalysisTool
└── UserObject
    ├── Artist
    ├── Producer
    └── Administrator
```

## Development Commands

### Starting the Application

**Primary method (Docker):**
```bash
# Start all services with Docker
npm run docker:dev
# or
./scripts/deployment/docker-scripts.sh start

# Stop services
npm run docker:stop
# or 
./scripts/deployment/docker-scripts.sh stop

# View logs
npm run docker:logs

# Check status
npm run docker:status
```

**Legacy development mode:**
```bash
# Start both frontend and backend in development mode
npm run dev:legacy

# Individual services
npm run backend:legacy  # FastAPI on port 8000
npm run frontend:legacy # Vite on port 3011
```

### Database Management
```bash
# Setup ArangoDB
npm run docker:setup-db

# Check database status
npm run db:status
```

### AI Tools Management
```bash
# Start ComfyUI integration
npm run ai:start

# Check AI service status
npm run ai:status

# Process AI job queue
npm run ai:process-queue
```

### DCC Integration
```bash
# Install DCC panels
npm run dcc:install-panels

# Update Houdini integration
npm run dcc:update-houdini

# Test DCC connections
npm run dcc:test-connections
```

### Testing
```bash
# Frontend tests (Playwright)
cd frontend && npm run test
cd frontend && npm run test:ui
cd frontend && npm run test:debug

# Backend API tests
cd backend && python -m pytest

# Integration tests
npm run test:integration

# DCC integration tests
npm run test:dcc
```

### Cleanup
```bash
# Clean up Atlas processes
npm run cleanup

# Full Docker cleanup
npm run docker:cleanup
```

## Project Structure (Recently Cleaned & Organized)

The project has been professionally organized following industry best practices:

### 🗂️ Root Directory
```
Blacksmith-Atlas/
├── README.md                    # Main project documentation
├── CLAUDE.md                   # This file - Claude Code instructions
├── PROJECT_STRUCTURE.md        # Detailed structure documentation
├── docker-compose.yml          # Development containers
├── package.json                # Root package file
└── .gitignore                  # Comprehensive ignore rules
```

### 🖥️ Backend Structure (Python FastAPI)
```
backend/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── api/                        # RESTful API endpoints
│   ├── assets.py              # ✅ Asset management API (WORKING)
│   ├── asset_sync.py          # ✅ Database sync operations (WORKING)
│   └── todos.py               # API utilities
├── assetlibrary/              # Core asset management
│   ├── config.py              # Configuration management
│   ├── models.py              # Data models
│   ├── database/              # Database layer
│   │   ├── arango_queries.py  # ✅ ArangoDB queries (WORKING)
│   │   ├── arango_collection_manager.py
│   │   └── setup_arango_database.py
│   └── houdini/               # 🧹 CLEANED & ORGANIZED
│       ├── houdiniae.py       # ✅ Core Houdini integration (WORKING)
│       ├── atlas_clipboard_system.py  # ✅ Advanced clipboard (WORKING)
│       ├── tools/             # Houdini shelf tools
│       │   ├── shelf_atlas_copy.py
│       │   ├── shelf_atlas_paste.py
│       │   └── shelf_*.py
│       └── templates/         # Template files
├── core/                      # Core business logic
│   ├── asset_manager.py
│   └── base_atlas_object.py   # Object-oriented foundation
└── config/                    # Configuration files
```

### 🎨 Frontend Structure (React/Vite)
```
frontend/
├── src/
│   ├── App.jsx               # ✅ Main application (WORKING)
│   └── components/
│       ├── AssetLibrary.jsx  # ✅ Asset browser - FULLY FUNCTIONAL
│       ├── Settings.jsx     # ✅ Settings panel (WORKING)
│       ├── AITools.jsx      # 🚧 AI tools interface
│       ├── ProducerTools.jsx # 🚧 Producer analytics
│       └── DeliveryTool/    # Delivery management
├── package.json
└── vite.config.js
```

### 📜 Scripts (Organized by Purpose)
```
scripts/
├── deployment/               # 🧹 Deployment utilities
│   ├── docker-scripts.sh   # ✅ Docker management (WORKING)
│   └── docker-scripts.bat
├── database/                # 🧹 Database management  
│   ├── init_arangodb.py    # Database initialization
│   ├── reset_arangodb.py   # Database reset
│   └── init-company-db.py
├── development/             # Development utilities
│   ├── cleanup-atlas.js
│   └── verify_setup.py
└── utilities/               # 🧹 General utilities
    ├── atlas_sync.py
    ├── calculate_folder_sizes.py
    └── update_asset_metadata.py
```

### 📚 Documentation (Organized by Topic)
```
docs/
├── setup/                   # 🧹 Setup and installation guides
│   ├── ARANGODB_EXAMPLE_QUERIES.md
│   ├── COMPANY_ARANGODB_SETUP.md
│   └── SHARED_DATABASE_SETUP.md
├── houdini/                 # 🧹 Houdini-specific documentation
│   ├── ATLAS_CLIPBOARD_SYSTEM.md
│   ├── HOUDINI_SHELF_BUTTONS.md
│   ├── houdini_menus/
│   └── houdini_shelves/
└── development/             # 🧹 Development documentation
    ├── COMPLETE_SYSTEM_OVERVIEW.md
    ├── IMPLEMENTATION_SUMMARY.md
    └── PROJECT_STRUCTURE.md
```

### 🧪 Testing (Organized by Component)
```
tests/
├── backend/                 # 🧹 Backend tests
│   ├── test_arango_connection.py
│   ├── test_database_integration.py
│   └── test_houdini_auto_insert.py
├── frontend/                # 🧹 Frontend tests
│   └── example.spec.js
├── integration/             # Integration tests
└── fixtures/                # Test data
```

### 🛠️ Development Tools
```
.dev/                        # 🧹 Development utilities (gitignored)
├── debug/                   # Debug scripts and tools
│   ├── debug_assets.py
│   ├── debug_database_connection.py
│   └── houdiniae_*.py (backups/variants)
├── temp/                    # Temporary files
└── logs/                    # Development logs
```

### ⚙️ Configuration
```
config/
├── environments/            # Environment configurations
│   ├── development.env
│   └── production.env
└── docker/                  # Docker configurations
```

## Recent Development History & Key Accomplishments

### 🎯 Latest Session Accomplishments
**Date**: Recent cleanup and feature completion session

#### ✅ Fixed Frontend Database Sync
- **Issue**: Sync DB button was performing complex bidirectional filesystem sync
- **Solution**: Simplified to pure ArangoDB refresh - queries existing Atlas_Library collection
- **Result**: Instant database sync without filesystem scanning
- **Files Modified**: `frontend/src/components/AssetLibrary.jsx:258-276`

#### 🧹 Complete Project Cleanup & Organization
- **Issue**: Scattered test files, debug scripts, random utilities throughout project
- **Solution**: Professional reorganization following industry best practices
- **Key Changes**:
  - All test files moved to `/tests/` with component separation
  - Debug utilities organized in `.dev/debug/` (gitignored)
  - Scripts categorized by purpose: `deployment/`, `database/`, `utilities/`
  - Documentation organized by topic: `setup/`, `houdini/`, `development/`
  - Houdini integration cleaned: `backend/assetlibrary/houdini/` with tools/ and templates/
  - Removed temporary files, backups, duplicates
  - Created comprehensive `.gitignore`

#### 📋 Documentation Updates
- **Created**: `PROJECT_CLEANUP_PLAN.md` - Detailed cleanup documentation
- **Created**: `PROJECT_STRUCTURE.md` - Complete structure overview
- **Updated**: This `CLAUDE.md` file with current status and accomplishments

### 🏗️ Core System Status

#### ✅ Production-Ready Components
1. **Asset Management System**
   - ArangoDB `Atlas_Library` collection fully operational
   - Asset CRUD operations with metadata, thumbnails, file management
   - Hierarchical categorization: 3D → Assets/FX/Materials/HDAs → Subcategories

2. **Frontend Asset Browser** 
   - React-based interface with grid/list views
   - Navigation: dimensions → categories → subcategories → assets
   - Real-time search, filtering, and database sync
   - Asset preview modals with comprehensive metadata display
   - Copy-to-clipboard for Houdini integration

3. **Database Infrastructure**
   - ArangoDB Community Edition with graph relationships
   - FastAPI async backend with error handling
   - Health monitoring and connection management
   - Direct database querying for optimal performance

4. **Houdini Integration**
   - Core export/import system: `backend/assetlibrary/houdini/houdiniae.py`
   - Advanced clipboard system: `atlas_clipboard_system.py` (540+ lines)
   - Shelf tools for seamless workflow
   - Automatic texture and geometry path remapping

#### 🔧 Key Technical Implementations
1. **ArangoDB Integration**: Direct queries to `Atlas_Library` collection using `arango_queries.py`
2. **Frontend State Management**: React hooks with real-time database updates
3. **Asset Processing**: Template-based export/import with dependency tracking
4. **File Management**: Automatic thumbnail generation and metadata extraction
5. **Docker Deployment**: Multi-service orchestration with health checks

### 🎯 Next Development Priorities
1. **AI Tools Integration** - ComfyUI workflow execution framework
2. **Producer Analytics** - Project estimation and bid analysis tools  
3. **Additional DCC Support** - Maya, Nuke, Flame panel development
4. **Advanced Workflows** - Automated asset processing pipelines

## Working with This Project

### 🚀 Getting Started Quickly
1. **Start Services**: `./scripts/deployment/docker-scripts.sh start`
2. **Access Frontend**: http://localhost:3011 (Asset Library fully functional)
3. **Access Backend API**: http://localhost:8000 (FastAPI with ArangoDB)
4. **Database Status**: Check ArangoDB at http://localhost:8529

### 🔑 Key Files to Understand
- **`frontend/src/components/AssetLibrary.jsx`** - Main user interface (COMPLETE)
- **`backend/api/assets.py`** - Asset API endpoints (WORKING)
- **`backend/assetlibrary/database/arango_queries.py`** - Database queries (WORKING)
- **`backend/assetlibrary/houdini/houdiniae.py`** - Houdini integration core
- **`backend/assetlibrary/houdini/atlas_clipboard_system.py`** - Advanced clipboard

### 📊 Database Schema (ArangoDB)
**Primary Collection**: `Atlas_Library`
```javascript
// Asset document structure
{
  "_key": "asset_id",
  "name": "Asset Name",
  "asset_type": "Assets|FX|Materials|HDAs",
  "category": "Subcategory Name", 
  "dimension": "3D",
  "hierarchy": {
    "dimension": "3D",
    "asset_type": "Assets",
    "subcategory": "Blacksmith Asset"
  },
  "metadata": {
    "render_engine": "Redshift|Karma",
    "created_by": "artist_name",
    "houdini_version": "20.0"
  },
  "paths": {
    "asset_folder": "/path/to/asset",
    "thumbnail": "/path/to/thumbnail.png"
  },
  "file_sizes": {},
  "tags": [],
  "created_at": "2024-timestamp"
}
```

### 🛠️ Common Development Tasks

#### Adding New Assets to Database
1. Use ArangoDB web interface: http://localhost:8529
2. Insert into `Atlas_Library` collection
3. Frontend will automatically show new assets via sync button

#### Debugging Database Issues  
1. Check connection: `backend/assetlibrary/database/arango_queries.py:16-35`
2. Test queries: Use debug endpoint `/api/v1/debug/test-connection`
3. Monitor logs: `docker logs blacksmith-atlas-backend-1`

#### Frontend Development
1. Main component: `frontend/src/components/AssetLibrary.jsx`
2. Asset loading: Lines 220-240 (`loadAssets()` function)
3. Database sync: Lines 258-276 (`syncDatabase()` function)
4. Hot reload enabled: Changes reflect immediately

#### Backend API Development
1. Asset endpoints: `backend/api/assets.py`
2. Database queries: `backend/assetlibrary/database/arango_queries.py`
3. Houdini integration: `backend/assetlibrary/houdini/`
4. Test endpoints: http://localhost:8000/docs (FastAPI auto-docs)

### 🐛 Troubleshooting

#### Database Connection Issues
- Check ArangoDB container: `docker ps | grep arango`
- Restart services: `./scripts/deployment/docker-scripts.sh restart`
- Check environment: `config/environments/development.env`

#### Frontend Not Loading Assets
- Check sync button functionality (recently fixed)
- Verify API endpoint: http://localhost:8000/api/v1/assets
- Check browser console for errors

#### Houdini Integration Issues
- Verify paths in: `backend/assetlibrary/houdini/houdiniae.py`
- Check clipboard system: `atlas_clipboard_system.py`
- Review Houdini docs: `docs/houdini/`

### 📈 Performance Considerations
- **Database**: Direct ArangoDB queries (no filesystem scanning)
- **Frontend**: React hooks with optimized re-renders
- **Assets**: Lazy loading with thumbnail previews
- **Docker**: Multi-stage builds for production optimization

## Development Workflow

### Phase-Based Development Approach
Development follows a 5-phase roadmap with clear dependencies and progressive feature building:

**Phase 1: Foundation (MVP)**
- Core asset management with CRUD operations
- Basic React frontend with asset browsing
- Docker containerization and ArangoDB integration
- User authentication and role-based access control

**Phase 2: DCC Integration**
- PyQt panel development for Houdini, Maya, Nuke, Flame
- Cross-application asset workflows with format conversion
- Enhanced asset management with collections and dependencies
- Advanced search and metadata filtering

**Phase 3: AI Integration**
- ComfyUI client integration with job queue management
- AI tool framework with custom workflow support
- Automated asset processing and thumbnail generation
- Result caching and batch processing capabilities

**Phase 4: Producer Analytics**
- Bid analysis with AI-powered project estimation
- Analytics dashboard with real-time project monitoring
- Resource planning and timeline generation
- Cost tracking and predictive modeling

**Phase 5: Intelligence & Automation**
- Blacksmith chatbot with natural language processing
- Advanced workflow automation and optimization
- Third-party integrations (Shotgun, cloud storage)
- Plugin ecosystem for custom studio tools

### Core System Architecture

#### Asset Management System
The foundation is built around object-oriented patterns:
- **BaseAtlasObject**: Core abstraction for all system entities
- **AssetObject**: Specialized for 3D models, textures, materials, light rigs
- **ArangoDB Integration**: Document-based storage with graph relationships
- **Format Handlers**: Pluggable architecture for USD, FBX, OBJ, texture formats
- **Version Control**: Git-like versioning system for all assets
- **Dependency Tracking**: Automatic resolution of asset relationships

#### AI Tools Integration
- **AIToolObject**: Base class for all AI workflow implementations
- **ComfyUI Client**: REST API integration with workflow submission
- **Job Queue System**: Redis-based distributed task processing
- **Result Caching**: Intelligent caching of AI-generated content
- **Custom Workflows**: Template system for studio-specific AI tools

#### DCC Integration Framework
- **AtlasPanelBase**: Common PyQt architecture for all DCCs
- **Format Conversion**: Automatic asset format handling between applications
- **Workflow Automation**: Scripted asset setup and dependency resolution
- **Real-time Sync**: Live updates of asset changes across applications

### API Architecture
- RESTful endpoints under `/api/v1/` with full OpenAPI documentation
- WebSocket integration for real-time job status and asset updates
- Authentication with JWT tokens and role-based permissions
- Health check endpoint at `/health` with service status monitoring
- Specialized endpoints:
  - `/api/v1/assets` - Asset CRUD operations
  - `/api/v1/ai-tools` - AI workflow execution and status
  - `/api/v1/projects` - Producer tools and analytics
  - `/api/v1/chat` - Chatbot interaction interface

### Frontend Architecture
- React functional components with hooks and context for state management
- Tailwind CSS for styling with dark mode as default professional theme
- Lucide React for consistent iconography across all interfaces
- Component-based sidebar navigation with role-based feature access
- Real-time updates via WebSocket for job status and asset changes
- Progressive disclosure of features based on user roles and development phases

## Development Guidelines

### Object-Oriented Architecture Principles
- **Everything is an Object**: All system entities inherit from BaseAtlasObject
- **Consistent Interfaces**: Standardized methods across all object types (validate, serialize, etc.)
- **Pluggable Architecture**: Format handlers, DCC integrations, and AI tools use plugin patterns
- **Dependency Injection**: Services injected for testability and modularity
- **Factory Patterns**: Object creation through specialized factory classes

### Backend Development
- **FastAPI with async/await**: Leverage Python's asyncio for high-performance API endpoints
- **ArangoDB Document Store**: Use document-based storage with graph relationships for asset dependencies
- **Pydantic Models**: Strict validation for all API requests and responses
- **Docker-friendly Paths**: Environment variables for all file system operations
- **Comprehensive Error Handling**: Proper HTTP status codes with detailed error messages
- **Background Tasks**: Use Redis and Celery for AI job processing and long-running operations

### Frontend Development
- **React Functional Components**: Use hooks and context for state management
- **Tailwind CSS Utility Classes**: Consistent styling with dark mode as default
- **Progressive Feature Disclosure**: Show features based on current development phase and user role
- **Real-time Updates**: WebSocket integration for live status and notifications
- **Responsive Design**: Desktop-first approach with Electron wrapper
- **Error Boundaries**: Graceful error handling with user-friendly messages

### DCC Integration Development
- **PyQt Panel Architecture**: Common base class for all DCC integrations
- **Format Handler Pattern**: Pluggable converters for asset format translation
- **Async Communication**: Non-blocking communication between DCCs and Atlas backend
- **Error Recovery**: Graceful handling of DCC connection failures and timeouts
- **Version Compatibility**: Support for multiple versions of each DCC application

### AI Tools Development
- **Workflow Templates**: JSON-based ComfyUI workflow definitions
- **Input Validation**: Schema validation for all AI tool parameters
- **Job Queue Management**: Redis-based queue with priority and retry logic
- **Result Caching**: Intelligent caching based on input parameters and workflow version
- **Resource Management**: GPU/CPU allocation and monitoring for AI processing

### Asset Processing Guidelines
- **USD as Primary Format**: Universal Scene Description for maximum compatibility
- **Format Support Matrix**: USD, FBX, OBJ for geometry; EXR, PNG, TIFF for textures
- **Automatic Previews**: Generate thumbnails and previews for all imported assets
- **Dependency Resolution**: Track and maintain asset relationships automatically
- **Version Management**: Git-like versioning with diff capabilities for assets

## Environment Configuration

### Environment Variables
- `ATLAS_ENV` - Environment mode (development/production/staging)
- `ARANGO_HOST` - ArangoDB host (default: localhost)
- `ARANGO_PORT` - ArangoDB port (default: 8529)
- `ARANGO_DATABASE` - Database name (default: blacksmith_atlas)
- `ASSET_LIBRARY_PATH` - Asset storage path (default: /app/assets)
- `REDIS_HOST` - Redis host for caching and job queue (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `COMFYUI_HOST` - ComfyUI server host for AI workflows
- `COMFYUI_PORT` - ComfyUI server port (default: 8188)
- `JWT_SECRET_KEY` - Secret key for JWT token generation
- `ATLAS_LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)

### Service Ports
- **Frontend (React/Vite)**: 3011
- **Backend API (FastAPI)**: 8000
- **ArangoDB**: 8529
- **Redis**: 6379
- **ComfyUI**: 8188
- **WebSocket**: 8001
- **Electron**: Varies by platform

## Database Schema

### Core Collections (ArangoDB)

#### atlas_objects (Base Collection)
- `_key`: UUID identifier for all Atlas objects
- `object_type`: Object type classification (asset, project, user, ai_tool, workflow)
- `name`: Display name
- `metadata`: Flexible JSON metadata storage
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp
- `created_by`: User ID of creator
- `tags`: Array of classification tags

#### assets (Extends atlas_objects)
- `asset_type`: Specific asset classification (geometry, material, texture, light_rig)
- `file_paths`: Object containing all file paths (source, preview, thumbnail)
- `file_formats`: Supported format information
- `file_size`: Total file size in bytes
- `version_number`: Current version number
- `parent_asset_id`: Reference to parent asset for versions
- `preview_data`: Generated preview information
- `processing_status`: Asset processing state

#### projects (Extends atlas_objects)
- `status`: Project status (active, completed, cancelled)
- `start_date`: Project start date
- `end_date`: Project end date
- `budget`: Project budget information
- `client_info`: Client details and requirements
- `team_members`: Array of assigned user IDs
- `asset_list`: Associated asset references

#### ai_jobs (Task Processing)
- `_key`: Unique job identifier
- `tool_name`: AI tool used for processing
- `workflow_id`: ComfyUI workflow identifier
- `status`: Job status (queued, processing, completed, failed)
- `input_parameters`: Job input configuration
- `output_data`: Generated results and file paths
- `priority`: Job queue priority
- `estimated_duration`: Predicted processing time
- `actual_duration`: Actual processing time
- `created_at`: Job creation timestamp
- `completed_at`: Job completion timestamp
- `error_message`: Error details if failed

#### users (Extends atlas_objects)
- `email`: User email address
- `role`: User role (artist, producer, administrator)
- `permissions`: Granular permission array
- `preferences`: User interface and workflow preferences
- `last_login`: Last login timestamp
- `dcc_integrations`: Connected DCC applications

### Graph Relationships (ArangoDB Edges)

#### asset_dependencies
- `_from`: Source asset ID
- `_to`: Dependent asset ID
- `dependency_type`: Type of dependency (texture, material, reference)
- `required`: Whether dependency is mandatory

#### project_assets
- `_from`: Project ID
- `_to`: Asset ID
- `usage_type`: How asset is used in project
- `assigned_to`: User responsible for asset

## Testing Strategy

### Automated Testing Framework
Following comprehensive testing approach with coverage targets and continuous integration:

#### Frontend Testing
- **Playwright E2E Tests**: Complete user workflow testing across all development phases
- **React Testing Library**: Component unit tests with user interaction simulation
- **Visual Regression Testing**: Screenshot comparison for UI consistency
- **Accessibility Testing**: WCAG compliance validation
- **Performance Testing**: Load time and rendering performance metrics
- **Cross-Platform Testing**: Electron app testing on Windows, macOS, Linux

#### Backend Testing
- **FastAPI Unit Tests**: Individual API endpoint testing with pytest
- **Integration Tests**: Database operations and service interactions
- **Load Testing**: Performance testing with concurrent users and large datasets
- **AI Workflow Testing**: ComfyUI integration and job processing validation
- **Security Testing**: Authentication, authorization, and data protection
- **Asset Processing Tests**: Format conversion and thumbnail generation validation

#### DCC Integration Testing
- **Panel Functionality**: PyQt panel testing in isolated environments
- **Asset Import/Export**: Cross-application workflow validation
- **Format Conversion**: Automated testing of USD, FBX, OBJ pipelines
- **Error Recovery**: Connection failure and timeout handling
- **Version Compatibility**: Testing across multiple DCC versions

#### AI Tools Testing
- **Workflow Validation**: ComfyUI workflow execution and result verification
- **Input Validation**: Parameter validation and error handling
- **Queue Management**: Job priority and retry logic testing
- **Result Caching**: Cache hit/miss ratio and performance impact
- **Resource Management**: GPU memory and processing monitoring

### Testing Coverage Targets
- **Unit Tests**: >90% code coverage
- **Integration Tests**: All API endpoints and critical workflows
- **E2E Tests**: Complete user journeys for each development phase
- **Performance Tests**: Load testing with 100+ concurrent users
- **Security Tests**: Automated vulnerability scanning and penetration testing

## Deployment

### Docker Deployment
The application is designed for containerized deployment:
- Multi-stage Docker builds
- Docker Compose for development
- Volume mounting for asset storage
- Health checks for services

### Cross-Platform Support
- Works on Windows, macOS, and Linux
- Platform-specific deployment scripts
- Cross-platform Python dependencies
- Docker ensures environment consistency

## Common Development Tasks

### Adding New Asset Types
1. **Extend Object Hierarchy**: Create new class inheriting from AssetObject in `backend/core/base_atlas_object.py`
2. **Database Schema**: Update ArangoDB collections and add new asset type fields
3. **Format Handler**: Implement format-specific import/export logic in `backend/assetlibrary/formats/`
4. **API Endpoints**: Add REST endpoints in `backend/api/assets.py` for new asset type
5. **Frontend Components**: Create React components for asset display and interaction
6. **DCC Integration**: Add support in relevant PyQt panels for new asset type
7. **Testing**: Write unit and integration tests for new asset type workflows

### Adding AI Tools
1. **Workflow Definition**: Create ComfyUI workflow JSON in `ai_workflows/`
2. **Tool Object**: Implement AIToolObject subclass with input/output schema validation
3. **API Integration**: Add endpoints in `backend/api/ai_tools.py` for tool execution
4. **Frontend Interface**: Create UI components for tool parameter input and result display
5. **Job Processing**: Integrate with Redis job queue for background processing
6. **Testing**: Validate workflow execution and result handling

### DCC Integration Expansion
1. **Panel Base**: Extend AtlasPanelBase for new DCC in `dcc_panels/`
2. **DCC API**: Implement application-specific asset import/export methods
3. **Communication Layer**: Set up client-server communication with Atlas backend
4. **Installation Scripts**: Create DCC-specific installation and setup procedures
5. **Testing**: Validate panel functionality and asset workflows in target DCC

### Producer Tool Development
1. **Analysis Engine**: Implement analysis algorithms in `backend/analytics/`
2. **Data Models**: Create Pydantic models for project data and results
3. **API Endpoints**: Add routes in `backend/api/projects.py` for producer features
4. **Dashboard Components**: Build React components for data visualization
5. **Reporting**: Implement export functionality for external tools
6. **Testing**: Validate analysis accuracy and performance

### Adding Third-Party Integrations
1. **Client Implementation**: Create service client in `backend/integrations/`
2. **Authentication**: Implement secure credential management
3. **Data Mapping**: Define data transformation between systems
4. **Sync Logic**: Implement bidirectional data synchronization
5. **Configuration**: Add integration settings to environment variables
6. **Testing**: Test integration reliability and error handling

## Security Implementation

### Authentication & Authorization
- **JWT Token System**: Secure token-based authentication with refresh mechanism
- **Role-Based Access Control**: Granular permissions based on user roles (Artist, Producer, Admin)
- **Session Management**: Redis-based session storage with configurable timeout
- **API Key Management**: Secure storage and rotation of third-party service keys
- **Multi-Factor Authentication**: Optional 2FA for enhanced security

### Data Protection
- **Encryption at Rest**: ArangoDB encryption for sensitive data storage
- **Encryption in Transit**: TLS/SSL for all client-server communication
- **Secure File Storage**: Encrypted asset storage with access logging
- **Audit Trail**: Comprehensive logging of all user actions and system events
- **Data Anonymization**: Privacy protection for user data in logs and analytics

### Network Security
- **CORS Configuration**: Restrictive cross-origin policies for production
- **Rate Limiting**: API endpoint protection against abuse
- **Input Validation**: Comprehensive sanitization of all user inputs
- **SQL Injection Prevention**: Parameterized queries and ORM usage
- **File Upload Security**: Virus scanning and format validation for asset uploads

### Infrastructure Security
- **Container Security**: Minimal Docker images with security scanning
- **Environment Isolation**: Separate configurations for development/staging/production
- **Secret Management**: Secure credential storage using environment variables
- **Backup Encryption**: Encrypted database and asset backups
- **Monitoring & Alerting**: Real-time security event detection and notification

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
