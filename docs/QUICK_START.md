# 🚀 Quick Start Guide

**Get Blacksmith Atlas running in under 2 minutes!**

## Prerequisites

1. **Install Docker Desktop**
   - [Download for Windows](https://www.docker.com/products/docker-desktop/)
   - [Download for Mac](https://www.docker.com/products/docker-desktop/)
   - [Download for Linux](https://docs.docker.com/engine/install/)

2. **Start Docker Desktop**
   - Launch the application
   - Wait for it to fully start (green icon in system tray)

## 🎯 One-Command Setup

### Windows
```cmd
scripts/deployment/docker-scripts.bat start
```

### Mac/Linux
```bash
chmod +x scripts/deployment/docker-scripts.sh
./scripts/deployment/docker-scripts.sh start
```

### Alternative (npm)
```bash
npm start
```

## ✅ Verify It's Working

1. **Frontend**: Open http://localhost:3011
2. **Backend API**: Open http://localhost:8000
3. **API Docs**: Open http://localhost:8000/docs

You should see:
- ✅ Frontend loads with the Blacksmith Atlas interface
- ✅ Backend shows "Blacksmith Atlas API" message
- ✅ API documentation is interactive

## 🛠️ Common Commands

| Command | Description |
|---------|-------------|
| `npm start` | Start everything |
| `npm stop` | Stop everything |
| `npm run logs` | View live logs |
| `npm run status` | Check service status |
| `npm run restart` | Restart all services |

## 🐛 Troubleshooting

### "Docker not running"
- Start Docker Desktop
- Wait for it to fully initialize

### "Port already in use"
- Stop other applications using ports 8000/3011
- Or restart Docker: `docker system prune -f`

### "Permission denied" (Linux/Mac)
- Make script executable: `chmod +x scripts/deployment/docker-scripts.sh`

## 🎉 Next Steps

1. **Explore the Interface**: Navigate through the asset library
2. **Add Assets**: Upload some test files
3. **Configure Database**: See [Database Setup](SHARED_DATABASE_SETUP.md)
4. **Deploy to Team**: Share this project with your colleagues

## 📞 Need Help?

- Check the logs: `npm run logs`
- Review [Docker Setup](DOCKER_SETUP.md)
- Check [Development Notes](CLAUDE.md)

---

**🎯 You're all set! Blacksmith Atlas is now running and ready to use.** 