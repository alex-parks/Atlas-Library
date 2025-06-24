# 🐳 Blacksmith Atlas - Docker Setup Guide

## Overview

Blacksmith Atlas has been fully Dockerized to provide consistent, cross-platform deployment across your entire company. This eliminates the "works on my machine" problem and ensures everyone has the same environment.

## 🚀 Quick Start

### Prerequisites

1. **Install Docker Desktop**
   - [Windows](https://docs.docker.com/desktop/install/windows-install/)
   - [Mac](https://docs.docker.com/desktop/install/mac-install/)
   - [Linux](https://docs.docker.com/desktop/install/linux-install/)

2. **Install Docker Compose**
   - Usually included with Docker Desktop
   - Verify with: `docker-compose --version`

### Start Everything (One Command)

**Windows:**
```cmd
docker-scripts.bat start
```

**Mac/Linux:**
```bash
chmod +x docker-scripts.sh
./docker-scripts.sh start
```

**Manual (if scripts don't work):**
```bash
docker-compose up -d
```

### Access Your Application

- **Frontend**: http://localhost:3011
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ArangoDB**: http://localhost:8529

## 📁 Project Structure

```
BlacksmithAtlas/
├── Dockerfile                 # Backend container
├── docker-compose.yml         # Multi-service orchestration
├── .dockerignore             # Files to exclude from builds
├── docker-scripts.sh         # Linux/Mac scripts
├── docker-scripts.bat        # Windows scripts
├── frontend/
│   └── Dockerfile            # Frontend container
├── electron/
│   └── Dockerfile            # Electron container
└── backend/
    └── requirements.txt      # Python dependencies
```

## 🔧 Available Commands

### Using Scripts (Recommended)

**Windows:**
```cmd
docker-scripts.bat start      # Start everything
docker-scripts.bat backend    # Start backend only
docker-scripts.bat frontend   # Start frontend only
docker-scripts.bat stop       # Stop everything
docker-scripts.bat logs       # View logs
docker-scripts.bat status     # Check status
docker-scripts.bat cleanup    # Clean up everything
```

**Mac/Linux:**
```bash
./docker-scripts.sh start     # Start everything
./docker-scripts.sh backend   # Start backend only
./docker-scripts.sh frontend  # Start frontend only
./docker-scripts.sh stop      # Stop everything
./docker-scripts.sh logs      # View logs
./docker-scripts.sh status    # Check status
./docker-scripts.sh cleanup   # Clean up everything
```

### Using Docker Compose Directly

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d backend arangodb

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Clean up everything
docker-compose down --volumes --remove-orphans
```

## 🏗️ Architecture

### Services

1. **ArangoDB** (`arangodb`)
   - Database server
   - Port: 8529
   - Persistent data storage

2. **Backend** (`backend`)
   - FastAPI application
   - Port: 8000
   - Connects to ArangoDB

3. **Frontend** (`frontend`)
   - React/Vite application
   - Port: 3011
   - Connects to backend API

4. **Electron** (`electron`) - Optional
   - Desktop application wrapper
   - Requires X11 forwarding on Linux

### Network

All services communicate through the `atlas-network` Docker network.

### Volumes

- `arango_data`: Persistent ArangoDB data
- `arango_apps`: ArangoDB applications
- `./assets:/app/assets`: Asset library files
- `./logs:/app/logs`: Application logs

## 🔄 Migration from Virtual Environment

### What Changed

| Before (venv) | After (Docker) |
|---------------|----------------|
| `python -m venv .venv` | `docker-compose up -d` |
| `source .venv/bin/activate` | No activation needed |
| `pip install -r requirements.txt` | Automatic in container |
| `npm run dev` | `docker-scripts.sh start` |
| `npm run backend` | `docker-scripts.sh backend` |

### Benefits

✅ **Consistent Environment**: Same setup across all platforms
✅ **No Dependencies**: No need to install Python, Node.js, or ArangoDB locally
✅ **Easy Deployment**: One command to start everything
✅ **Isolation**: No conflicts with system packages
✅ **Scalability**: Easy to deploy to production

## 🛠️ Development Workflow

### Daily Development

1. **Start the application:**
   ```bash
   ./docker-scripts.sh start
   ```

2. **Make code changes** (files are mounted, changes are reflected immediately)

3. **View logs:**
   ```bash
   ./docker-scripts.sh logs backend
   ```

4. **Stop when done:**
   ```bash
   ./docker-scripts.sh stop
   ```

### Code Changes

- **Backend changes**: Automatically reloaded (uvicorn --reload)
- **Frontend changes**: Hot reloaded by Vite
- **Database changes**: Restart backend service

### Adding Dependencies

**Backend (Python):**
1. Edit `backend/requirements.txt`
2. Rebuild: `docker-compose build backend`

**Frontend (Node.js):**
1. Edit `frontend/package.json`
2. Rebuild: `docker-compose build frontend`

## 🔧 Configuration

### Environment Variables

Set these in `docker-compose.yml` or as environment variables:

```yaml
environment:
  - ATLAS_ENV=production
  - ARANGO_HOST=arangodb
  - ARANGO_PORT=8529
  - ARANGO_USER=root
  - ARANGO_PASSWORD=atlas_password
  - ARANGO_DATABASE=blacksmith_atlas
  - ASSET_LIBRARY_PATH=/app/assets
  - LOG_PATH=/app/logs
```

### Database Configuration

The application automatically connects to the ArangoDB container. No manual setup required.

### Asset Library

Mount your asset library to `/app/assets` in the container:

```yaml
volumes:
  - ./your-asset-library:/app/assets
```

## 🚀 Production Deployment

### Company-Wide Setup

1. **Central Server Setup:**
   ```bash
   # On your company server
   git clone <your-repo>
   cd BlacksmithAtlas
   docker-compose up -d
   ```

2. **Client Configuration:**
   - Update `backend/assetlibrary/config.py` with server details
   - Set `ATLAS_ENV=production`
   - Configure ArangoDB connection

3. **Network Access:**
   - Configure firewall rules
   - Set up SSL certificates
   - Use VPN if needed

### Scaling

```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Use load balancer
docker-compose up -d nginx
```

## 🐛 Troubleshooting

### Common Issues

**Docker not running:**
```bash
# Start Docker Desktop
# Or on Linux:
sudo systemctl start docker
```

**Port conflicts:**
```bash
# Check what's using the ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :3011

# Stop conflicting services or change ports in docker-compose.yml
```

**Permission issues (Linux):**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

**Database connection issues:**
```bash
# Check if ArangoDB is running
docker-compose ps arangodb

# View ArangoDB logs
docker-compose logs arangodb

# Restart database
docker-compose restart arangodb
```

### Debugging

**View all logs:**
```bash
docker-compose logs -f
```

**Access container shell:**
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```

**Check container status:**
```bash
docker-compose ps
```

**Rebuild everything:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📊 Monitoring

### Health Checks

- Backend: `http://localhost:8000/health`
- ArangoDB: `http://localhost:8529/_api/version`

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Resource Usage

```bash
# Container resource usage
docker stats

# Disk usage
docker system df
```

## 🔒 Security

### Best Practices

1. **Change default passwords** in `docker-compose.yml`
2. **Use environment files** for sensitive data
3. **Enable SSL** for production
4. **Restrict network access** with firewalls
5. **Regular updates** of base images

### Environment Files

Create `.env` file:
```env
ARANGO_PASSWORD=your_secure_password
ATLAS_ENV=production
```

Reference in `docker-compose.yml`:
```yaml
env_file:
  - .env
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [ArangoDB Documentation](https://www.arangodb.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 Support

For issues specific to your company setup:

1. Check the troubleshooting section above
2. View logs: `./docker-scripts.sh logs`
3. Check status: `./docker-scripts.sh status`
4. Contact your system administrator

---

**🎉 Congratulations!** Your Blacksmith Atlas is now fully Dockerized and ready for cross-platform deployment across your company! 