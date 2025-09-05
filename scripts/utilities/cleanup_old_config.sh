#!/bin/bash
# Cleanup Old Configuration Files
# This script safely removes the old configuration files after migration to the new centralized config system

echo "🧹 Blacksmith Atlas - Configuration Cleanup"
echo "============================================"

PROJECT_ROOT="/net/dev/alex.parks/scm/int/Blacksmith-Atlas"

# Files to remove
OLD_CONFIG_PY="$PROJECT_ROOT/backend/assetlibrary/config.py"
OLD_CONFIG_JSON="$PROJECT_ROOT/backend/config/asset_library_config.json"

echo "📋 Files to be removed:"
echo "  - $OLD_CONFIG_PY"
echo "  - $OLD_CONFIG_JSON"
echo ""

# Check if new config exists
NEW_CONFIG="$PROJECT_ROOT/config/atlas_config.json"
if [ ! -f "$NEW_CONFIG" ]; then
    echo "❌ ERROR: New configuration file not found at $NEW_CONFIG"
    echo "   Please ensure the new config system is properly set up before running cleanup."
    exit 1
fi

echo "✅ New configuration file found: $NEW_CONFIG"
echo ""

# Create backup directory
BACKUP_DIR="$PROJECT_ROOT/backup/old_config_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in: $BACKUP_DIR"

# Backup old files before deletion
if [ -f "$OLD_CONFIG_PY" ]; then
    cp "$OLD_CONFIG_PY" "$BACKUP_DIR/"
    echo "  ✅ Backed up config.py"
fi

if [ -f "$OLD_CONFIG_JSON" ]; then
    cp "$OLD_CONFIG_JSON" "$BACKUP_DIR/"
    echo "  ✅ Backed up asset_library_config.json"
fi

# Remove old files
echo ""
echo "🗑️ Removing old configuration files..."

if [ -f "$OLD_CONFIG_PY" ]; then
    rm "$OLD_CONFIG_PY"
    echo "  ✅ Removed $OLD_CONFIG_PY"
else
    echo "  ⚠️ File not found: $OLD_CONFIG_PY"
fi

if [ -f "$OLD_CONFIG_JSON" ]; then
    rm "$OLD_CONFIG_JSON"
    echo "  ✅ Removed $OLD_CONFIG_JSON"
else
    echo "  ⚠️ File not found: $OLD_CONFIG_JSON"
fi

echo ""
echo "✅ Configuration cleanup complete!"
echo ""
echo "📝 IMPORTANT NOTES:"
echo "  - Old configuration files have been backed up to: $BACKUP_DIR"
echo "  - The new centralized configuration is at: $NEW_CONFIG"
echo "  - Some utility scripts in /scripts/utilities/ may need manual updates"
echo "  - Restart backend services to ensure they use the new configuration"
echo ""
echo "🔧 To update HDA and library paths, edit: $NEW_CONFIG"