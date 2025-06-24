# 📁 Project Structure

**Blacksmith Atlas - Clean & Professional Organization**

## 🎯 Overview

This project has been reorganized for maximum clarity, maintainability, and professional standards. The structure follows industry best practices and makes it easy for teams to understand and contribute.

## 📂 Root Directory Structure

```
BlacksmithAtlas/
├── 📦 Root Configuration
│   ├── docker-compose.yml          # Multi-service orchestration
│   ├── Dockerfile                  # Backend container definition
│   ├── .dockerignore              # Build optimization exclusions
│   ├── package.json               # Project metadata & npm scripts
│   ├── requirements.txt           # Python dependencies
│   ├── .gitignore                 # Clean git exclusions
│   ├── .editorconfig              # Editor consistency
│   └── .gitattributes             # Git line ending handling
│
├── 🖥️ Applications
│   ├── backend/                   # FastAPI backend service
│   │   ├── main.py               # Application entry point
│   │   ├── api/                  # API routes & endpoints
│   │   │   └── assets.py         # Asset management endpoints
│   │   ├── assetlibrary/         # Core asset management
│   │   │   ├── _2D/             # 2D asset processing
│   │   │   ├── _3D/             # 3D asset processing
│   │   │   ├── config.py        # Asset library configuration
│   │   │   ├── models.py        # Data models
│   │   │   └── database/        # Database operations
│   │   ├── core/                 # Base classes & utilities
│   │   │   ├── asset_manager.py # Asset management core
│   │   │   └── base_atlas_object.py
│   │   ├── config/              # Backend configuration
│   │   └── requirements.txt     # Backend dependencies
│   │
│   ├── frontend/                 # React/Vite frontend
│   │   ├── src/                  # React source code
│   │   │   ├── components/      # React components
│   │   │   ├── App.jsx          # Main application
│   │   │   └── main.jsx         # Entry point
│   │   ├── package.json         # Frontend dependencies
│   │   ├── Dockerfile           # Frontend container
│   │   ├── vite.config.js       # Vite configuration
│   │   └── tailwind.config.js   # Tailwind CSS config
│   │
│   └── electron/                 # Desktop application
│       ├── main.js              # Electron main process
│       ├── package.json         # Electron dependencies
│       ├── Dockerfile          # Electron container
│       └── splash.html         # Loading screen
│
├── 📚 Documentation
│   ├── QUICK_START.md           # Get started in 2 minutes
│   ├── DOCKER_SETUP.md          # Complete Docker guide
│   ├── SHARED_DATABASE_SETUP.md # Database configuration
│   ├── CLAUDE.md               # Development notes
│   └── PROJECT_STRUCTURE.md    # This file
│
├── 🔧 Scripts
│   ├── deployment/              # Production deployment
│   │   ├── docker-scripts.bat   # Windows deployment
│   │   └── docker-scripts.sh    # Linux/Mac deployment
│   │
│   └── development/             # Development utilities
│       ├── cleanup-atlas.js     # Process cleanup
│       ├── py-launcher.js       # Python launcher
│       ├── python3.js          # Python3 compatibility
│       ├── test_shared_database.py
│       └── verify_setup.py
│
├── ⚙️ Configuration
│   └── environments/            # Environment-specific configs
│       ├── development.env      # Development settings
│       └── production.env       # Production settings
│
├── 📁 Data
│   ├── assets/                  # Asset library files
│   │   └── .gitkeep            # Maintain folder structure
│   └── logs/                   # Application logs
│       └── .gitkeep            # Maintain folder structure
│
└── 🗂️ Legacy (Deprecated)
    ├── scripts/                 # Original scripts (moved)
    ├── .venv/                  # Virtual environment (no longer needed)
    └── node_modules/           # Dependencies (managed by Docker)
```

## 🎨 Design Principles

### 1. **Separation of Concerns**
- **Applications**: Each service in its own directory
- **Documentation**: All docs in one place
- **Scripts**: Organized by purpose (deployment vs development)
- **Configuration**: Environment-specific settings

### 2. **Professional Standards**
- **Clear naming**: Descriptive folder and file names
- **Consistent structure**: Similar patterns across services
- **Documentation**: Comprehensive guides for each aspect
- **Clean git**: Only necessary files tracked

### 3. **Developer Experience**
- **One-command setup**: `npm start` or `scripts/deployment/docker-scripts.bat start`
- **Clear documentation**: Quick start guides and troubleshooting
- **Logical organization**: Easy to find what you need
- **Cross-platform**: Works on Windows, Mac, Linux

## 🚀 Key Benefits

### For New Developers
- ✅ **Easy onboarding**: Just run one command
- ✅ **Clear structure**: Everything is logically organized
- ✅ **Comprehensive docs**: Multiple guides for different needs
- ✅ **No setup complexity**: Docker handles everything

### For Teams
- ✅ **Consistent environment**: Same setup everywhere
- ✅ **Professional appearance**: Clean, organized codebase
- ✅ **Easy maintenance**: Clear separation of concerns
- ✅ **Scalable**: Easy to add new features or services

### For Companies
- ✅ **Cross-platform**: Works identically on all operating systems
- ✅ **Deployable**: Easy to share across teams
- ✅ **Maintainable**: Clean architecture and documentation
- ✅ **Professional**: Enterprise-ready structure

## 📋 File Purposes

### Root Configuration
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates all services |
| `Dockerfile` | Backend container definition |
| `package.json` | Project metadata and scripts |
| `.gitignore` | Clean git exclusions |

### Documentation
| File | Purpose |
|------|---------|
| `QUICK_START.md` | Get running in 2 minutes |
| `DOCKER_SETUP.md` | Complete Docker guide |
| `PROJECT_STRUCTURE.md` | This overview |

### Scripts
| Directory | Purpose |
|-----------|---------|
| `deployment/` | Production deployment scripts |
| `development/` | Development utilities |

## 🎯 Migration Summary

### What Was Moved
- ✅ **Documentation**: All `.md` files → `docs/`
- ✅ **Deployment scripts**: `docker-scripts.*` → `scripts/deployment/`
- ✅ **Development scripts**: Legacy scripts → `scripts/development/`
- ✅ **Configuration**: Environment files → `config/environments/`

### What Was Cleaned
- ✅ **Git ignore**: Organized and comprehensive
- ✅ **Package.json**: Better organized scripts
- ✅ **README**: Professional and comprehensive
- ✅ **Structure**: Logical and intuitive

### What Was Added
- ✅ **Quick start guide**: Get running in 2 minutes
- ✅ **Environment configs**: Development and production
- ✅ **Structure documentation**: This overview
- ✅ **Professional README**: Comprehensive and helpful

## 🎉 Result

**Your Blacksmith Atlas project is now:**
- 🏗️ **Professionally organized** with clear separation of concerns
- 📚 **Well documented** with multiple guides for different needs
- 🚀 **Easy to use** with one-command setup
- 🌍 **Cross-platform** and company-wide deployable
- 🧹 **Clean and maintainable** with logical structure

---

**🎯 Ready for production deployment across your entire company!** 