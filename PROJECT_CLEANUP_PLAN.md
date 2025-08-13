# Blacksmith Atlas - Project Cleanup Plan

## Current Issues
- Test files scattered throughout project
- Debug scripts in multiple locations
- Backup files and duplicates
- Random utility files in project root
- Unorganized backend/_3D directory
- Temporary/build directories in version control
- Mixed documentation locations

## Proposed New Structure

```
Blacksmith-Atlas/
├── README.md
├── CLAUDE.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── package.json
├── requirements.txt
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── api/
│   │   ├── assets.py
│   │   ├── asset_sync.py
│   │   └── todos.py
│   ├── assetlibrary/
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── database/
│   │   ├── houdini/
│   │   │   ├── __init__.py
│   │   │   ├── houdiniae.py
│   │   │   ├── clipboard_system.py
│   │   │   ├── shelf_tools.py
│   │   │   └── templates/
│   │   └── _3D/ (cleaned and organized)
│   ├── core/
│   └── config/
│
├── frontend/
│   ├── (unchanged - already well organized)
│
├── docs/
│   ├── api/
│   ├── setup/
│   ├── houdini/
│   └── development/
│
├── scripts/
│   ├── deployment/
│   ├── database/
│   ├── development/
│   └── utilities/
│
├── tests/
│   ├── backend/
│   ├── frontend/
│   ├── integration/
│   └── fixtures/
│
├── config/
│   ├── environments/
│   └── docker/
│
└── .dev/
    ├── debug/
    ├── temp/
    └── logs/
```

## Cleanup Actions

### 1. Move Test Files
**From scattered locations to organized test structure:**
- `test_*.py` files → `tests/backend/`
- `debug_*.py` files → `.dev/debug/`
- `backend/test_todos_api.py` → `tests/backend/`
- `frontend/tests/` → `tests/frontend/`

### 2. Organize backend/_3D Directory
**Current chaos into organized modules:**
- Group clipboard functionality → `assetlibrary/houdini/clipboard_system.py`
- Group shelf tools → `assetlibrary/houdini/shelf_tools.py`
- Group database integration → `assetlibrary/houdini/database_integration.py`
- Move templates to dedicated folder
- Remove debug/test files

### 3. Clean Documentation
**Consolidate scattered docs:**
- Move all `.md` files from root to appropriate `docs/` subdirectories
- Organize by topic (api, setup, houdini, development)
- Remove duplicate documentation

### 4. Organize Scripts
**Group by purpose:**
- Deployment scripts → `scripts/deployment/`
- Database scripts → `scripts/database/`
- Development utilities → `scripts/development/`

### 5. Remove Temporary/Build Artifacts
- `overlay*/` directories
- `logs/` directory  
- `claude-code-sub-agent-collective/`
- Backup files (`.backup`, `_corrupted`, etc.)

### 6. Update .gitignore
Add proper exclusions for:
- Temporary directories
- Debug files
- Build artifacts
- Development utilities

## Files to Remove/Clean
- `houdiniae.py.backup`
- `houdiniae_corrupted.py`
- Multiple debug test files
- Temporary overlay directories
- Old backup files