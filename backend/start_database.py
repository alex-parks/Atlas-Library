# backend/start_database.py - ArangoDB version
"""
Database startup script for npm run dev
Initializes ArangoDB database and syncs with JSON from Asset Library settings
"""

import sys
import json
import time
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DatabaseStartup")

# Add current directory to path and ensure we're in the right directory
current_dir = Path(__file__).parent.resolve()
os.chdir(current_dir)  # Ensure we're in the backend directory
sys.path.append(str(current_dir))

try:
    from assetlibrary.database.setup_arango_database import setup_database, migrate_json_to_arango, test_connection
    from arango.client import ArangoClient
except ImportError as e:
    logger.error(f"❌ Could not import ArangoDB modules: {e}")
    logger.error("   Make sure arango package is installed: pip install python-arango")
    sys.exit(1)


def load_asset_library_settings():
    """Load settings from Asset Library frontend localStorage or config"""

    # Default settings with absolute paths
    project_root = current_dir.parent  # Go up one level from backend to project root
    default_settings = {
        "rootFolder": str(project_root / "BlacksmithAtlas_Files" / "AssetLibrary" / "3D"),
        "jsonFilePath": str(current_dir / "assetlibrary" / "database" / "3DAssets.json"),
        "apiEndpoint": "http://localhost:8000/api/v1/assets",
        "autoRebuildOnChange": True
    }

    # Alternative absolute paths if the above don't work
    fallback_settings = {
        "rootFolder": r"C:\Users\alexh\Desktop\BlacksmithAtlas_Files\AssetLibrary\3D",
        "jsonFilePath": r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json",
        "apiEndpoint": "http://localhost:8000/api/v1/assets",
        "autoRebuildOnChange": True
    }

    # Try to load from config file if it exists
    config_file = current_dir / "config" / "asset_library_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)

                # Validate that paths are not empty or just '.'
                json_path = settings.get("jsonFilePath", "")
                if json_path and json_path != "." and Path(json_path).exists():
                    logger.info(f"✅ Loaded settings from {config_file}")
                    return settings
                else:
                    logger.warning(f"⚠️ Config file has invalid JSON path: '{json_path}'")

        except Exception as e:
            logger.warning(f"⚠️ Could not load config file: {e}")

    # Try default settings first
    default_json_path = Path(default_settings["jsonFilePath"])
    if default_json_path.exists():
        logger.info("📝 Using default Asset Library settings (relative paths)")
        return default_settings

    # Fall back to absolute paths
    fallback_json_path = Path(fallback_settings["jsonFilePath"])
    if fallback_json_path.exists():
        logger.info("📝 Using fallback Asset Library settings (absolute paths)")
        return fallback_settings

    # If nothing works, create a minimal config with the fallback
    logger.warning("⚠️ No valid JSON file found, using fallback settings")
    logger.warning(f"   Tried: {default_json_path}")
    logger.warning(f"   Tried: {fallback_json_path}")

    return fallback_settings


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        current_dir / "database",
        current_dir / "logs",
        current_dir / "config"
    ]

    for dir_path in directories:
        dir_path.mkdir(exist_ok=True, parents=True)
        logger.info(f"📁 Directory ensured: {dir_path}")


def save_settings_to_config(settings):
    """Save settings to config file for future use"""
    try:
        config_dir = current_dir / "config"
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "asset_library_config.json"
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)

        logger.info(f"💾 Settings saved to {config_file}")

    except Exception as e:
        logger.warning(f"⚠️ Could not save settings: {e}")


def validate_json_file(json_path):
    """Validate the JSON file exists and is readable"""

    # Handle empty or invalid paths
    if not json_path or json_path == "." or json_path == "":
        logger.error(f"❌ Invalid JSON path: '{json_path}'")
        return False, f"Invalid path: '{json_path}'"

    json_file = Path(json_path)

    # Convert to absolute path if relative
    if not json_file.is_absolute():
        json_file = current_dir / json_file

    logger.info(f"🔍 Checking JSON file: {json_file}")

    if not json_file.exists():
        logger.error(f"❌ JSON file not found: {json_file}")
        return False, "File not found"

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            return False, f"JSON file is not a list: {type(data)}"

        logger.info(f"✅ JSON file validated: {len(data)} assets")
        return True, f"{len(data)} assets found"

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except PermissionError as e:
        return False, f"Permission denied accessing file: {e}"
    except Exception as e:
        return False, f"Error reading JSON: {e}"


def initialize_arangodb_database(settings):
    """Initialize ArangoDB database with settings"""
    try:
        json_path = settings["jsonFilePath"]

        # Ensure we have absolute paths
        if not Path(json_path).is_absolute():
            json_path = str(current_dir / json_path)

        logger.info(f"🗃️ Initializing ArangoDB database...")
        logger.info(f"📄 JSON source: {json_path}")

        # Validate JSON file first
        valid, message = validate_json_file(json_path)
        if not valid:
            logger.error(f"❌ JSON validation failed: {message}")
            return None, f"JSON validation failed: {message}"

        # Set up ArangoDB database and collections
        logger.info("🔧 Setting up ArangoDB database and collections...")
        db = setup_database()

        # Check if database needs initialization
        assets_collection = db.collection('assets')
        
        try:
            existing_assets_count = assets_collection.count()
        except Exception as e:
            logger.warning(f"⚠️ Could not get asset count: {e}")
            existing_assets_count = 0

        if existing_assets_count == 0:
            logger.info("📦 Empty database, importing JSON data...")
            
            # Create a temporary migration function with our JSON path
            def migrate_with_custom_path():
                json_file = Path(json_path)
                if not json_file.exists():
                    logger.error(f"❌ JSON file not found for migration: {json_file}")
                    return False
                
                with open(json_file, 'r') as f:
                    json_assets = json.load(f)
                
                logger.info(f"📦 Migrating {len(json_assets)} assets from JSON to ArangoDB...")
                
                migrated = 0
                skipped = 0
                
                for asset in json_assets:
                    try:
                        # Prepare document for ArangoDB
                        arango_doc = {
                            '_key': asset['id'],  # Use existing ID as key
                            'name': asset['name'],
                            'category': asset['category'],
                            'asset_type': '3D',  # All your current assets are 3D
                            'folder': asset.get('folder', ''),
                            'paths': asset.get('paths', {}),
                            'metadata': asset.get('metadata', {}),
                            'file_sizes': asset.get('file_sizes', {}),
                            'dependencies': asset.get('dependencies', {}),
                            'tags': [],  # Start with empty tags
                            'created_at': asset.get('created_at', ''),
                            'updated_at': asset.get('created_at', ''),  # Use created_at if no updated_at
                            'legacy_json': True  # Mark as migrated from JSON
                        }
                        
                        # Insert into ArangoDB
                        assets_collection.insert(arango_doc)
                        migrated += 1
                        logger.info(f"✅ Migrated: {asset['name']} (ID: {asset['id']})")
                        
                    except Exception as e:
                        if 'unique constraint violated' in str(e).lower():
                            skipped += 1
                            logger.info(f"⏭️ Skipped (already exists): {asset['name']}")
                        else:
                            logger.error(f"❌ Failed to migrate {asset['name']}: {e}")
                
                logger.info(f"📊 Migration complete!")
                logger.info(f"   ✅ Migrated: {migrated}")
                logger.info(f"   ⏭️ Skipped: {skipped}")
                return True
            
            success = migrate_with_custom_path()
            
            if success:
                try:
                    new_assets_count = assets_collection.count()
                    logger.info(f"✅ Imported {new_assets_count} assets from JSON")
                except Exception as e:
                    logger.warning(f"⚠️ Could not get final count: {e}")
                    logger.info("✅ Import completed")
            else:
                logger.error("❌ Failed to import JSON data")
                return None, "Failed to import JSON data"
        else:
            logger.info(f"✅ Database already contains {existing_assets_count} assets")

            # Check if JSON is newer and offer to sync
            json_file = Path(json_path)
            if json_file.exists():
                json_modified = datetime.fromtimestamp(json_file.stat().st_mtime)
                logger.info("🔄 JSON file found, database sync may be needed")

        # Get final statistics
        try:
            final_count = assets_collection.count()
            logger.info(f"📊 Database ready: {final_count} assets")
        except Exception as e:
            logger.warning(f"⚠️ Could not get final count: {e}")
            logger.info("📊 Database ready")

        return db, "Database initialized successfully"

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Database initialization failed: {e}"


def create_health_check_endpoint_info(settings):
    """Create info for health check"""
    return {
        "database_startup_time": datetime.now().isoformat(),
        "database_type": "ArangoDB",
        "json_source": settings["jsonFilePath"],
        "root_folder": settings["rootFolder"],
        "api_endpoint": settings["apiEndpoint"],
        "current_directory": str(current_dir)
    }


def main():
    """Main database startup function"""
    print("🚀 Blacksmith Atlas - ArangoDB Database Startup")
    print("=" * 60)

    try:
        # Ensure we're in the right directory
        logger.info(f"📁 Working directory: {current_dir}")

        # Ensure directories exist
        ensure_directories()

        # Load Asset Library settings
        logger.info("⚙️ Loading Asset Library settings...")
        settings = load_asset_library_settings()

        # Log the settings for debugging
        logger.info(f"📄 JSON Path: {settings['jsonFilePath']}")
        logger.info(f"📁 Root Folder: {settings['rootFolder']}")

        # Save settings for future reference
        save_settings_to_config(settings)

        # Initialize database
        logger.info("🗄️ Starting ArangoDB database initialization...")
        db, message = initialize_arangodb_database(settings)

        if db is None:
            logger.error(f"❌ Database startup failed: {message}")
            sys.exit(1)

        # Create health info
        health_info = create_health_check_endpoint_info(settings)

        # Save health info for the API to use
        health_file = current_dir / "database" / "health_info.json"
        with open(health_file, 'w') as f:
            json.dump(health_info, f, indent=2)

        logger.info("✅ ArangoDB database startup completed successfully!")
        logger.info("🔗 Backend can now connect to ArangoDB database")
        logger.info(f"📊 Final settings: {settings['jsonFilePath']}")

        # Success indicator for npm script
        print("DATABASE_READY=true")

        return True

    except Exception as e:
        logger.error(f"❌ Database startup failed: {e}")
        import traceback
        traceback.print_exc()

        # Failure indicator for npm script
        print("DATABASE_READY=false")
        sys.exit(1)


def quick_status():
    """Quick status check for the database"""
    try:
        test_connection()
        print(f"Working Directory: {current_dir}")

    except Exception as e:
        print(f"Database Status: ❌ Error - {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        quick_status()
    else:
        main()