# Blacksmith Atlas - Cleaned Project Structure

## Overview
The project has been reorganized into a clean, maintainable structure following industry best practices.

## Directory Structure

```
Blacksmith-Atlas/
├── README.md                           # Main project documentation
├── CLAUDE.md                          # Claude Code instructions
├── PROJECT_CLEANUP_PLAN.md            # Cleanup documentation
├── PROJECT_STRUCTURE.md               # This file
├── docker-compose.yml                 # Development containers
├── docker-compose.prod.yml            # Production containers
├── Dockerfile                         # Container definition
├── package.json                       # Root package file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── backend/                           # Python FastAPI backend
│   ├── main.py                        # Application entry point
│   ├── requirements.txt               # Backend dependencies
│   ├── api/                           # REST API endpoints
│   │   ├── assets.py                  # Asset management API
│   │   ├── asset_sync.py              # Database sync operations
│   │   └── todos.py                   # TODO management API
│   ├── assetlibrary/                  # Core asset management
│   │   ├── config.py                  # Configuration management
│   │   ├── models.py                  # Data models
│   │   ├── database/                  # Database layer
│   │   │   ├── arango_queries.py      # ArangoDB queries
│   │   │   ├── arango_collection_manager.py
│   │   │   ├── graph_parser.py        # Graph data parsing
│   │   │   └── setup_arango_database.py
│   │   └── houdini/                   # Houdini integration (CLEANED)
│   │       ├── __init__.py            # Module initialization
│   │       ├── houdiniae.py           # Main Houdini integration
│   │       ├── atlas_clipboard_system.py  # Clipboard functionality
│   │       ├── atlas_clipboard_handler.py # Clipboard handlers
│   │       ├── atlas_clipboard_demo.py    # Demo scripts
│   │       ├── atlas_database.py      # Database integration
│   │       ├── auto_arango_insert.py  # Auto database insertion
│   │       ├── docker_auto_insert.py  # Docker-based insertion
│   │       ├── tools/                 # Shelf tools (ORGANIZED)
│   │       │   ├── shelf_atlas_copy.py
│   │       │   ├── shelf_atlas_paste.py
│   │       │   ├── shelf_button_script.py
│   │       │   ├── shelf_create_atlas_asset.py
│   │       │   ├── shelf_load_atlas_asset.py
│   │       │   └── shelf_paste_atlas_asset.py
│   │       └── templates/             # Template files (ORGANIZED)
│   │           └── hda_pymodule_template.py
│   ├── core/                          # Core business logic
│   │   ├── asset_manager.py
│   │   └── base_atlas_object.py
│   ├── config/                        # Configuration files
│   │   └── asset_library_config.json
│   ├── database/                      # Database utilities
│   │   └── health_info.json
│   └── setup/                         # Setup scripts
│       └── setup_arango_server.py
│
├── frontend/                          # React/Vite frontend
│   ├── (unchanged - already well organized)
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── AssetLibrary.jsx       # Main asset browser
│   │       ├── AITools.jsx
│   │       ├── ProducerTools.jsx
│   │       ├── Settings.jsx
│   │       └── DeliveryTool/          # Delivery management
│   └── tests/ → moved to /tests/frontend/
│
├── scripts/                           # Utility scripts (ORGANIZED)
│   ├── deployment/                    # Deployment utilities
│   │   ├── docker-scripts.sh
│   │   └── docker-scripts.bat
│   ├── database/                      # Database management (ORGANIZED)
│   │   ├── init_arangodb.py
│   │   ├── reset_arangodb.py
│   │   └── init-company-db.py
│   ├── development/                   # Development utilities
│   │   ├── cleanup-atlas.js
│   │   ├── py-launcher.js
│   │   ├── python3.js
│   │   ├── test_shared_database.py
│   │   └── verify_setup.py
│   └── utilities/                     # General utilities (ORGANIZED)
│       ├── atlas_sync.py
│       ├── calculate_folder_sizes.py
│       ├── sync_filesystem_to_database.py
│       └── update_asset_metadata.py
│
├── docs/                              # Documentation (ORGANIZED)
│   ├── api/                          # API documentation
│   ├── setup/                        # Setup and installation guides
│   │   ├── ARANGODB_EXAMPLE_QUERIES.md
│   │   ├── ARANGODB_GRAPH_SCHEMA.md
│   │   ├── COMPANY_ARANGODB_SETUP.md
│   │   └── SHARED_DATABASE_SETUP.md
│   ├── houdini/                      # Houdini-specific docs (ORGANIZED)
│   │   ├── ATLAS_CLIPBOARD_SYSTEM.md
│   │   ├── ATLAS_SHELF_INSTALLATION.md
│   │   ├── HCOPY_HPASTE_DEEP_ANALYSIS.md
│   │   ├── HDA_IMPORT_BY_NAME_SETUP.md
│   │   ├── HDA_PARAMETER_SETUP.md
│   │   ├── HOUDINI_DEVELOPMENT_RELOAD.md
│   │   ├── HOUDINI_RIGHT_CLICK_SETUP.md
│   │   ├── HOUDINI_SHELF_BUTTONS.md
│   │   ├── Atlas.keymap.overrides
│   │   ├── atlas_clipboard_shelf.xml
│   │   ├── houdini_menus/
│   │   │   ├── BLAtlas.xml
│   │   │   ├── OPmenu.xml
│   │   │   └── nodegraphcontextmenus.py
│   │   └── houdini_shelves/
│   │       └── atlas.shelf
│   └── development/                  # Development documentation (ORGANIZED)
│       ├── COMPLETE_ASSET_EXPORT_GUIDE.md
│       ├── COMPLETE_SYSTEM_OVERVIEW.md
│       ├── DOCKER_SETUP.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       ├── PROJECT_STRUCTURE.md
│       ├── QUICK_START.md
│       ├── TEMPLATE_BASED_APPROACH.md
│       └── TODOS_API_IMPLEMENTATION.md
│
├── tests/                             # All tests (ORGANIZED)
│   ├── backend/                       # Backend tests
│   │   ├── test_arango_connection.py
│   │   ├── test_auto_insert.py
│   │   ├── test_database_integration.py
│   │   ├── test_houdini_auto_insert.py
│   │   └── test_todos_api.py
│   ├── frontend/                      # Frontend tests
│   │   └── example.spec.js
│   ├── integration/                   # Integration tests
│   └── fixtures/                      # Test data
│
├── config/                            # Configuration management
│   ├── environments/                  # Environment configs
│   │   ├── development.env
│   │   └── production.env
│   └── docker/                        # Docker configurations
│
└── .dev/                              # Development utilities (ORGANIZED)
    ├── debug/                         # Debug scripts and tools
    │   ├── debug_assets.py
    │   ├── debug_frontend.html
    │   ├── debug_add_params.py
    │   ├── debug_auto_insert.py
    │   ├── debug_database_connection.py
    │   ├── demo_template_workflow.py
    │   ├── atlas_clipboard_demo.py
    │   ├── check_next_export.py
    │   ├── houdiniae_corrupted.py
    │   ├── houdiniae_new.py
    │   ├── houdiniae_template.py
    │   └── test_texture_copying.py
    ├── temp/                          # Temporary files
    └── logs/                          # Development logs
```

## Key Improvements

### 1. Organized Test Structure
- All test files moved to `/tests/` directory
- Separated by component: `backend/`, `frontend/`, `integration/`
- Debug scripts moved to `.dev/debug/`

### 2. Clean Backend Structure
- Houdini integration properly organized in `/backend/assetlibrary/houdini/`
- Shelf tools grouped in `tools/` subdirectory
- Template files organized in `templates/` subdirectory
- Database operations consolidated

### 3. Script Organization
- Deployment scripts in `scripts/deployment/`
- Database utilities in `scripts/database/`
- General utilities in `scripts/utilities/`
- Development tools in `scripts/development/`

### 4. Documentation Consolidation
- API docs in `docs/api/`
- Setup guides in `docs/setup/`
- Houdini-specific docs in `docs/houdini/`
- Development docs in `docs/development/`

### 5. Development Tools
- All development/debug files in `.dev/` directory
- Proper `.gitignore` to prevent future clutter
- Backup files and corrupted versions moved to debug area

### 6. Removed Clutter
- Temporary overlay directories
- Backup files (`.backup`, `_corrupted`)
- Random test files from root directory
- Duplicate batch scripts
- Obsolete API test files

## Benefits

1. **Better Maintainability**: Clear separation of concerns
2. **Easier Navigation**: Logical grouping of related files
3. **Cleaner Git History**: Proper .gitignore prevents future clutter
4. **Professional Structure**: Follows industry best practices
5. **Scalable Architecture**: Easy to add new components

## Development Workflow

The cleaned structure supports these workflows:

1. **Backend Development**: Work in `backend/` with clear module separation
2. **Frontend Development**: Work in `frontend/` (unchanged, already clean)
3. **Testing**: All tests organized by component in `tests/`
4. **Documentation**: Logical documentation structure in `docs/`
5. **Deployment**: Scripts organized in `scripts/deployment/`
6. **Debugging**: Development tools in `.dev/` directory