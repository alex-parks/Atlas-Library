# Migration to Centralized Configuration System

## 🎯 Overview

Your Blacksmith Atlas system has been successfully updated to use a centralized configuration system. This document guides you through the final cleanup and verification steps.

## 📋 What Has Been Done

### ✅ **New Configuration System Implemented:**
- **`config/atlas_config.json`** - Single source of truth for all paths and settings
- **`backend/core/config_manager.py`** - Configuration management class
- **`backend/api/config.py`** - Configuration API endpoints
- **`frontend/src/utils/config.js`** - Frontend configuration utility

### ✅ **Updated Components:**
- **`backend/assetlibrary/houdini/houdiniae.py`** - Uses centralized config for library and HDA paths
- **`backend/api/assets.py`** - Updated to use new config system
- **`backend/api/asset_sync.py`** - Updated database and path references
- **`backend/api/generic_crud.py`** - Updated database configuration
- **`backend/main.py`** - Updated initialization to use new config

## 🗑️ Cleanup Old Configuration Files

### **Safe Removal Process:**

1. **Run the cleanup script:**
   ```bash
   /net/dev/alex.parks/scm/int/Blacksmith-Atlas/scripts/utilities/cleanup_old_config.sh
   ```

   This script will:
   - Create backups of old config files
   - Remove the old configuration files
   - Verify the new config system is in place

2. **Manual removal (alternative):**
   ```bash
   # Create backup first
   mkdir -p /net/dev/alex.parks/scm/int/Blacksmith-Atlas/backup/old_config
   
   # Backup old files
   cp /net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/config.py /backup/old_config/
   cp /net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/config/asset_library_config.json /backup/old_config/
   
   # Remove old files
   rm /net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/assetlibrary/config.py
   rm /net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend/config/asset_library_config.json
   ```

## ⚠️ Files That Still Reference Old Config

These files may need manual updates if you use them:

### **Utility Scripts:**
- `scripts/utilities/calculate_folder_sizes.py`
- `scripts/utilities/update_asset_metadata.py`
- `backend/start_database.py`

**These are not critical to core functionality** but may need updates if you use them regularly.

## 🔧 Post-Migration Configuration

### **1. Update Your HDA Path:**
Edit `/config/atlas_config.json`:
```json
{
  "paths": {
    "houdini": {
      "render_farm_hda": "/your/actual/path/to/render_farm.hda",
      "hda_type_name": "your_company::render_farm::1.0"
    }
  }
}
```

### **2. Update Library Paths (if needed):**
```json
{
  "paths": {
    "asset_library_root": "/your/library/path",
    "asset_library_3d": "/your/library/path/3D",
    "asset_library_2d": "/your/library/path/2D"
  }
}
```

## 🧪 Testing the New System

### **1. Backend API Test:**
```bash
# Test configuration endpoint
curl http://localhost:8000/api/v1/config/paths

# Test configuration validation
curl http://localhost:8000/api/v1/config/validate
```

### **2. Frontend Test:**
```javascript
// In browser console or frontend component
import config from './utils/config';
await config.load();
console.log('Library path:', config.assetLibraryRoot);
console.log('HDA path:', config.get('paths.houdini.render_farm_hda'));
```

### **3. Houdini Export Test:**
- Export an asset from Houdini using your shelf button
- Verify the HDA loads automatically
- Check that HDA parameters are populated with asset information

## 🔄 Service Restart

After cleanup, restart your services:

```bash
# Stop services
npm run docker:stop

# Start services (will use new config)
npm run docker:dev
```

## 📊 Verification Checklist

- [ ] Old config files removed (or backed up safely)
- [ ] New config file updated with your HDA path
- [ ] Backend services restarted
- [ ] Frontend configuration loads correctly
- [ ] Asset export from Houdini works with HDA loading
- [ ] API configuration endpoints respond correctly

## 🚨 Rollback Plan (If Needed)

If you encounter issues:

1. **Restore old files from backup**
2. **Revert the updated files:**
   - `backend/api/assets.py`
   - `backend/main.py`
   - `backend/api/asset_sync.py`
   - `backend/api/generic_crud.py`

3. **Use git to revert changes:**
   ```bash
   git checkout HEAD~1 -- backend/api/assets.py backend/main.py
   ```

## 🎉 Benefits of New System

### **Single Source of Truth:**
- All paths configurable from one file
- Easy environment migration
- Consistent configuration across all components

### **Better Integration:**
- HDA automatically loads after export
- All asset information passed to HDA parameters
- Dynamic path resolution

### **Future-Proof:**
- Easy to add new configuration options
- API endpoints for configuration management
- Frontend/backend configuration synchronization

## 📞 Support

If you encounter issues:
1. Check the backup files in `/backup/old_config/`
2. Verify paths in `config/atlas_config.json`
3. Check service logs for configuration errors
4. Use the validation endpoint to diagnose issues

---

**Your Blacksmith Atlas system now has a robust, centralized configuration system that will make future updates and environment changes much easier!**