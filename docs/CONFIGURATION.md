# Blacksmith Atlas - Configuration Management

## 📋 Overview

The Blacksmith Atlas system now uses a centralized configuration file (`atlas_config.json`) that allows you to manage all important paths and settings from a single location. This makes it easy to move the system between different environments, companies, or locations.

## 🗂️ Configuration File Location

The main configuration file is located at:
```
/net/dev/alex.parks/scm/int/Blacksmith-Atlas/config/atlas_config.json
```

## 📝 Key Configuration Sections

### 1. **Paths Configuration**
The most important section for relocating the system:

```json
{
  "paths": {
    "asset_library_root": "/net/library/atlaslib",
    "asset_library_3d": "/net/library/atlaslib/3D", 
    "asset_library_2d": "/net/library/atlaslib/2D",
    "houdini": {
      "render_farm_hda": "/path/to/your/render_farm.hda",
      "hda_type_name": "blacksmith::render_farm::1.0"
    },
    "thumbnails": "/net/library/atlaslib/thumbnails"
  }
}
```

### 2. **API Configuration**
Backend and frontend URLs:

```json
{
  "api": {
    "backend_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3011"
  }
}
```

### 3. **Database Configuration**
ArangoDB and Redis settings:

```json
{
  "api": {
    "database": {
      "host": "localhost",
      "port": 8529,
      "name": "blacksmith_atlas",
      "username": "root", 
      "password": "atlas_password"
    },
    "redis": {
      "host": "localhost",
      "port": 6379
    }
  }
}
```

## 🔧 How to Change Paths

### **Scenario: Moving to a New Company/Location**

1. **Edit the configuration file:**
   ```bash
   nano /net/dev/alex.parks/scm/int/Blacksmith-Atlas/config/atlas_config.json
   ```

2. **Update the main library path:**
   ```json
   {
     "paths": {
       "asset_library_root": "/new/company/asset/library",
       "asset_library_3d": "/new/company/asset/library/3D",
       "asset_library_2d": "/new/company/asset/library/2D"
     }
   }
   ```

3. **Update your HDA path:**
   ```json
   {
     "paths": {
       "houdini": {
         "render_farm_hda": "/new/path/to/your/render_farm.hda",
         "hda_type_name": "your_company::render_farm::1.0"
       }
     }
   }
   ```

4. **Restart the backend service** to reload configuration

## 🚀 Components That Use Configuration

### **Backend Components:**
- ✅ **houdiniae.py** - Asset export system
- ✅ **assets.py** - Main API endpoints
- ✅ **config.py** - Configuration API endpoints

### **Frontend Components:**
- ✅ **config.js** - Configuration utility
- ✅ All asset-related components (via config utility)

### **Docker/Container Components:**
- Volume mounts in docker-compose.yml (update manually)
- Environment variables (update .env files)

## 🔍 Configuration Validation

### **API Endpoints:**
- `GET /api/v1/config` - Get current configuration
- `GET /api/v1/config/paths` - Get just path configuration
- `GET /api/v1/config/validate` - Validate configuration
- `POST /api/v1/config/reload` - Reload configuration from file

### **Frontend Validation:**
```javascript
import { validateConfig } from './utils/config';

const validation = await validateConfig();
console.log('Config validation:', validation);
```

### **Backend Validation:**
```python
from backend.core.config_manager import config

# Check if paths exist
print("Asset library:", config.asset_library_root)
print("HDA path:", config.houdini_hda_path)
```

## ⚙️ Configuration Management

### **Programmatic Access:**

**Backend (Python):**
```python
from backend.core.config_manager import config

# Get paths
library_path = config.asset_library_root
hda_path = config.houdini_hda_path
backend_url = config.backend_url

# Update configuration
config.set('paths.asset_library_root', '/new/path')
config.save()
```

**Frontend (JavaScript):**
```javascript
import config from './utils/config';

// Load configuration
await config.load();

// Get values
const libraryPath = config.assetLibraryRoot;
const hdaPath = config.get('paths.houdini.render_farm_hda');

// Reload from server
await config.reload();
```

## 🔄 Migration Checklist

When moving to a new environment:

### **1. Configuration File**
- [ ] Update `asset_library_root` path
- [ ] Update `asset_library_3d` path  
- [ ] Update `asset_library_2d` path
- [ ] Update `houdini.render_farm_hda` path
- [ ] Update `houdini.hda_type_name` if needed
- [ ] Update API URLs if needed
- [ ] Update database connection settings

### **2. File System**
- [ ] Create new asset library directory structure
- [ ] Copy existing assets (if needed)
- [ ] Ensure HDA file is accessible
- [ ] Set proper file permissions

### **3. Services**
- [ ] Restart backend service
- [ ] Restart frontend service
- [ ] Test configuration validation
- [ ] Test asset export from Houdini
- [ ] Test frontend asset browsing

### **4. Docker/Container Updates (if using containers)**
- [ ] Update volume mounts in docker-compose.yml
- [ ] Update ASSET_LIBRARY_PATH environment variable
- [ ] Rebuild containers if needed

## 🛠️ Troubleshooting

### **Common Issues:**

1. **"Configuration not found"**
   - Ensure `atlas_config.json` exists in `/config/` folder
   - Check file permissions

2. **"Asset library not found"**
   - Verify paths in configuration file exist
   - Check file system permissions
   - Use validation endpoint to check paths

3. **"HDA not found"**
   - Update HDA path in configuration
   - Ensure HDA file exists and is accessible
   - Check HDA type name matches your HDA

4. **"Backend connection failed"**
   - Check backend_url in configuration
   - Ensure backend service is running
   - Check network connectivity

### **Validation Commands:**

```bash
# Check if configuration is valid
curl http://localhost:8000/api/v1/config/validate

# Get current paths
curl http://localhost:8000/api/v1/config/paths

# Test asset library access
ls -la /path/from/config/asset_library_3d
```

## 📚 Configuration Schema

The complete configuration schema is available in the `atlas_config.json` file. Key sections:

- **paths**: File system paths for assets, HDAs, and utilities
- **api**: Service URLs and database connection settings  
- **asset_structure**: Asset categories and subcategories
- **render_settings**: Rendering engine settings and formats
- **version**: Configuration version tracking

## 🔒 Security Notes

- Configuration file may contain sensitive paths
- Database passwords should be managed securely
- Consider using environment variables for sensitive data
- Validate configuration before deploying to production

---

**This configuration system ensures that your Blacksmith Atlas installation is easily portable between different environments while maintaining all functionality.**