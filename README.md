# 🗡️ Blacksmith Atlas

**Professional Asset Management System for VFX Studios**

A comprehensive, Dockerized asset management platform designed for cross-platform deployment across your entire company.

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Start Everything (One Command)
```bash
# Windows
scripts/deployment/docker-scripts.bat start

# Mac/Linux
chmod +x scripts/deployment/docker-scripts.sh
./scripts/deployment/docker-scripts.sh start
```

### Access Your Application
- **Frontend**: http://localhost:3011
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
BlacksmithAtlas/
├── 📦 Root Configuration
│   ├── docker-compose.yml          # Multi-service orchestration
│   ├── Dockerfile                  # Backend container
│   ├── .dockerignore              # Build optimization
│   ├── package.json               # Project metadata & scripts
│   └── requirements.txt           # Python dependencies
│
├── 🖥️ Applications
│   ├── backend/                   # FastAPI backend service
│   │   ├── main.py               # Application entry point
│   │   ├── api/                  # API routes & endpoints
│   │   ├── assetlibrary/         # Core asset management
│   │   ├── core/                 # Base classes & utilities
│   │   └── requirements.txt      # Backend dependencies
│   │
│   ├── frontend/                 # React/Vite frontend
│   │   ├── src/                  # React components
│   │   ├── package.json          # Frontend dependencies
│   │   └── Dockerfile           # Frontend container
│   │
│   └── electron/                 # Desktop application
│       ├── main.js              # Electron main process
│       ├── package.json         # Electron dependencies
│       └── Dockerfile          # Electron container
│
├── 📚 Documentation
│   ├── DOCKER_SETUP.md          # Docker deployment guide
│   ├── SHARED_DATABASE_SETUP.md # Database configuration
│   └── CLAUDE.md               # Development notes
│
├── 🔧 Scripts
│   ├── deployment/              # Production deployment scripts
│   │   ├── docker-scripts.bat   # Windows deployment
│   │   └── docker-scripts.sh    # Linux/Mac deployment
│   │
│   └── development/             # Development utilities
│       ├── test_shared_database.py
│       └── verify_setup.py
│
├── ⚙️ Configuration
│   └── environments/            # Environment-specific configs
│
├── 📁 Data
│   ├── assets/                  # Asset library files
│   └── logs/                   # Application logs
│
└── 🗂️ Legacy
    ├── scripts/                 # Original scripts (deprecated)
    └── .venv/                  # Virtual environment (no longer needed)
```

## 🛠️ Development

### Available Commands

**Windows:**
```cmd
scripts/deployment/docker-scripts.bat start      # Start everything
scripts/deployment/docker-scripts.bat stop       # Stop everything
scripts/deployment/docker-scripts.bat logs       # View logs
scripts/deployment/docker-scripts.bat status     # Check status
```

**Mac/Linux:**
```bash
./scripts/deployment/docker-scripts.sh start     # Start everything
./scripts/deployment/docker-scripts.sh stop      # Stop everything
./scripts/deployment/docker-scripts.sh logs      # View logs
./scripts/deployment/docker-scripts.sh status    # Check status
```

### Using npm (Alternative)
```bash
npm run docker:dev    # Start with Docker
npm run docker:stop   # Stop services
npm run docker:logs   # View logs
```

## 🏗️ Architecture

### Services
- **Backend**: FastAPI application (Python 3.11)
- **Frontend**: React/Vite application (Node.js 18)
- **Database**: ArangoDB (optional, runs in offline mode without it)

### Features
- ✅ **Cross-Platform**: Works on Windows, Mac, Linux
- ✅ **Dockerized**: Consistent environment everywhere
- ✅ **No Setup**: Just install Docker and run
- ✅ **Scalable**: Easy to deploy across your company
- ✅ **Modern Stack**: FastAPI, React, TypeScript

## 🚀 Deployment

### Company-Wide Setup
1. **Share the project** with your team
2. **Install Docker Desktop** on each machine
3. **Run one command**: `scripts/deployment/docker-scripts.bat start`
4. **Access the application** at http://localhost:3011

### Production Deployment
See [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) for detailed production deployment instructions.

## 📖 Documentation

- **[Docker Setup Guide](docs/DOCKER_SETUP.md)** - Complete Docker deployment
- **[Database Setup](docs/SHARED_DATABASE_SETUP.md)** - ArangoDB configuration
- **[Development Notes](docs/CLAUDE.md)** - Technical implementation details

## 🔧 Configuration

### Environment Variables
```bash
ATLAS_ENV=development          # Environment mode
ARANGO_HOST=localhost          # Database host
ARANGO_PORT=8529              # Database port
ASSET_LIBRARY_PATH=/app/assets # Asset library location
```

### Adding Dependencies
- **Backend**: Edit `backend/requirements.txt`
- **Frontend**: Edit `frontend/package.json`
- **Rebuild**: `docker-compose build`

## 🐛 Troubleshooting

### Common Issues
1. **Docker not running**: Start Docker Desktop
2. **Port conflicts**: Check if ports 8000/3011 are in use
3. **Permission errors**: Run as administrator (Windows)

### Getting Help
1. Check the logs: `scripts/deployment/docker-scripts.bat logs`
2. Verify status: `scripts/deployment/docker-scripts.bat status`
3. Review documentation in `docs/` folder

## 🎯 Benefits

### For Developers
- ✅ **Consistent Environment**: Same setup everywhere
- ✅ **Easy Onboarding**: New developers just run one command
- ✅ **No Dependencies**: No need to install Python, Node.js, or databases locally

### For Companies
- ✅ **Cross-Platform**: Works identically on all operating systems
- ✅ **Scalable**: Easy to deploy across multiple teams
- ✅ **Maintainable**: Clean, organized codebase
- ✅ **Professional**: Enterprise-ready architecture

## 📄 License

This project is proprietary software for Blacksmith VFX.

---

**🎉 Your asset management system is now production-ready and company-wide deployable!** 