# backend/start_database.py
"""
Database startup script for npm run dev
Initializes SQLite database and syncs with JSON from Asset Library settings
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DatabaseStartup")

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from database.sqlite_manager import SQLiteAssetManager
except ImportError:
    logger.error("❌ Could not import SQLiteAssetManager")
    logger.error("   Make sure database/sqlite_manager.py exists")
    sys.exit(1)


def load_asset_library_settings():
    """Load settings from Asset Library frontend localStorage or config"""
    # Default settings that match your Asset Library
    default_settings = {
        "rootFolder": r"C:\Users\alexh\Desktop\BlacksmithAtlas_Files\AssetLibrary\3D",
        "jsonFilePath": r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json",
        "apiEndpoint": "http://localhost:8000/api/v1/assets"
    }

    # Try to load from config file if it exists
    config_file = Path("config/asset_library_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)
                logger.info(f"✅ Loaded settings from {config_file}")
                return settings
        except Exception as e:
            logger.warning(f"⚠️ Could not load config file: {e}")

    logger.info("📝 Using default Asset Library settings")
    return default_settings


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "database",
        "logs",
        "config"
    ]

    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        logger.info(f"📁 Directory ensured: {dir_path}")


def save_settings_to_config(settings):
    """Save settings to config file for future use"""
    try:
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "asset_library_config.json"
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)

        logger.info(f"💾 Settings saved to {config_file}")

    except Exception as e:
        logger.warning(f"⚠️ Could not save settings: {e}")


def validate_json_file(json_path):
    """Validate the JSON file exists and is readable"""
    json_file = Path(json_path)

    if not json_file.exists():
        logger.error(f"❌ JSON file not found: {json_path}")
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
    except Exception as e:
        return False, f"Error reading JSON: {e}"


def initialize_database(settings):
    """Initialize SQLite database with settings"""
    try:
        json_path = settings["jsonFilePath"]
        db_path = "backend/database/assets.db"

        logger.info(f"🗃️ Initializing SQLite database...")
        logger.info(f"📄 JSON source: {json_path}")
        logger.info(f"💾 Database: {db_path}")

        # Validate JSON file first
        valid, message = validate_json_file(json_path)
        if not valid:
            logger.error(f"❌ JSON validation failed: {message}")
            return None, f"JSON validation failed: {message}"

        # Initialize SQLite manager
        manager = SQLiteAssetManager(db_path=db_path, json_path=json_path)

        # Check if database needs initialization
        existing_assets = manager.get_all_assets()

        if not existing_assets:
            logger.info("📦 Empty database, importing JSON data...")
            success = manager.json_to_sqlite()

            if success:
                new_assets = manager.get_all_assets()
                logger.info(f"✅ Imported {len(new_assets)} assets from JSON")
            else:
                logger.error("❌ Failed to import JSON data")
                return None, "Failed to import JSON data"
        else:
            logger.info(f"✅ Database already contains {len(existing_assets)} assets")

            # Check if JSON is newer and offer to sync
            json_file = Path(json_path)
            if json_file.exists():
                json_modified = datetime.fromtimestamp(json_file.stat().st_mtime)

                # Get latest asset creation time from database
                latest_asset = max(existing_assets, key=lambda x: x.get('created_at', ''))
                if latest_asset.get('created_at'):
                    try:
                        latest_db_time = datetime.fromisoformat(latest_asset['created_at'].replace('Z', '+00:00'))

                        if json_modified > latest_db_time:
                            logger.info("🔄 JSON file is newer, syncing database...")
                            success = manager.json_to_sqlite()
                            if success:
                                synced_assets = manager.get_all_assets()
                                logger.info(f"✅ Synced {len(synced_assets)} assets")
                            else:
                                logger.warning("⚠️ Sync failed, using existing data")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not compare timestamps: {e}")

        # Get final statistics
        stats = manager.get_statistics()
        logger.info(f"📊 Database ready: {stats}")

        return manager, "Database initialized successfully"

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Database initialization failed: {e}"


def create_health_check_endpoint_info(settings):
    """Create info for health check"""
    return {
        "database_startup_time": datetime.now().isoformat(),
        "json_source": settings["jsonFilePath"],
        "root_folder": settings["rootFolder"],
        "api_endpoint": settings["apiEndpoint"]
    }


def main():
    """Main database startup function"""
    print("🚀 Blacksmith Atlas - Database Startup")
    print("=" * 50)

    try:
        # Ensure directories exist
        ensure_directories()

        # Load Asset Library settings
        logger.info("⚙️ Loading Asset Library settings...")
        settings = load_asset_library_settings()

        # Save settings for future reference
        save_settings_to_config(settings)

        # Initialize database
        logger.info("🗄️ Starting database initialization...")
        manager, message = initialize_database(settings)

        if manager is None:
            logger.error(f"❌ Database startup failed: {message}")
            sys.exit(1)

        # Create health info
        health_info = create_health_check_endpoint_info(settings)

        # Save health info for the API to use
        health_file = Path("database/health_info.json")
        with open(health_file, 'w') as f:
            json.dump(health_info, f, indent=2)

        logger.info("✅ Database startup completed successfully!")
        logger.info("🔗 Backend can now connect to SQLite database")
        logger.info(f"📊 Settings: {settings['jsonFilePath']}")

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
        settings = load_asset_library_settings()
        manager = SQLiteAssetManager(json_path=settings["jsonFilePath"])
        assets = manager.get_all_assets()
        stats = manager.get_statistics()

        print(f"Database Status: ✅ Ready")
        print(f"Assets: {len(assets)}")
        print(f"Categories: {list(stats.get('by_category', {}).keys())}")
        print(f"JSON Source: {settings['jsonFilePath']}")

    except Exception as e:
        print(f"Database Status: ❌ Error - {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        quick_status()
    else:
        main()
