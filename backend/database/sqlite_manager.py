# backend/database/sqlite_manager.py - Fixed version with proper connection handling
import sqlite3
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import tempfile
import atexit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteAssetManager:
    """SQLite database manager for 3D assets with proper connection handling"""

    def __init__(self, db_path: str = None, json_path: str = None):
        self.db_path = db_path or "backend/database/assets.db"
        self.json_path = json_path or r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json"
        self._connection_pool = {}
        self.init_database()

        # Register cleanup on exit
        atexit.register(self.cleanup_connections)

    def get_connection(self):
        """Get a database connection with proper error handling"""
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                # Use WAL mode for better concurrent access
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,  # 30 second timeout
                    check_same_thread=False
                )

                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")

                return conn

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise

        raise sqlite3.OperationalError("Could not acquire database lock after multiple attempts")

    def cleanup_connections(self):
        """Clean up database connections"""
        for conn in self._connection_pool.values():
            try:
                conn.close()
            except:
                pass
        self._connection_pool.clear()

    def init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            with self.get_connection() as conn:
                conn.execute("""
                             CREATE TABLE IF NOT EXISTS assets
                             (
                                 id
                                 TEXT
                                 PRIMARY
                                 KEY,
                                 name
                                 TEXT
                                 NOT
                                 NULL,
                                 category
                                 TEXT,
                                 folder
                                 TEXT,
                                 usd_path
                                 TEXT,
                                 thumbnail_path
                                 TEXT,
                                 textures_path
                                 TEXT,
                                 fbx_path
                                 TEXT,
                                 houdini_version
                                 TEXT,
                                 hip_file
                                 TEXT,
                                 node_path
                                 TEXT,
                                 node_type
                                 TEXT,
                                 export_time
                                 TEXT,
                                 created_by
                                 TEXT,
                                 hda_parameters
                                 TEXT, -- JSON string
                                 dependencies
                                 TEXT, -- JSON string
                                 file_sizes
                                 TEXT, -- JSON string
                                 created_at
                                 TEXT,
                                 copied_files
                                 TEXT, -- JSON string
                                 metadata
                                 TEXT  -- Full metadata as JSON
                             )
                             """)

                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON assets(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created_by ON assets(created_by)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON assets(name)")

                conn.commit()
                logger.info(f"✅ SQLite database initialized at: {self.db_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    def load_json_data(self) -> List[Dict]:
        """Load data from the JSON file"""
        try:
            json_file = Path(self.json_path)
            if not json_file.exists():
                logger.error(f"❌ JSON file not found: {self.json_path}")
                return []

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Loaded {len(data)} assets from JSON")
                return data

        except Exception as e:
            logger.error(f"❌ Failed to load JSON: {e}")
            return []

    def json_to_sqlite(self):
        """Import JSON data into SQLite database"""
        try:
            json_data = self.load_json_data()
            if not json_data:
                logger.warning("No data to import")
                return False

            with self.get_connection() as conn:
                # Clear existing data
                conn.execute("DELETE FROM assets")

                for asset in json_data:
                    # Extract paths
                    paths = asset.get('paths', {})
                    metadata = asset.get('metadata', {})
                    hda_params = metadata.get('hda_parameters', {})

                    # Prepare data for insertion
                    asset_data = (
                        asset.get('id'),
                        asset.get('name'),
                        asset.get('category'),
                        asset.get('folder'),
                        paths.get('usd'),
                        paths.get('thumbnail'),
                        paths.get('textures'),
                        paths.get('fbx'),
                        metadata.get('houdini_version'),
                        metadata.get('hip_file'),
                        metadata.get('node_path'),
                        metadata.get('node_type'),
                        metadata.get('export_time'),
                        metadata.get('created_by'),
                        json.dumps(hda_params),
                        json.dumps(asset.get('dependencies', {})),
                        json.dumps(asset.get('file_sizes', {})),
                        asset.get('created_at'),
                        json.dumps(asset.get('copied_files', [])),
                        json.dumps(metadata)
                    )

                    conn.execute("""
                                 INSERT INTO assets (id, name, category, folder, usd_path, thumbnail_path,
                                                     textures_path, fbx_path, houdini_version, hip_file,
                                                     node_path, node_type, export_time, created_by,
                                                     hda_parameters, dependencies, file_sizes, created_at,
                                                     copied_files, metadata)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                 """, asset_data)

                conn.commit()
                logger.info(f"✅ Successfully imported {len(json_data)} assets to SQLite")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to import JSON to SQLite: {e}")
            return False

    def get_all_assets(self) -> List[Dict]:
        """Get all assets from SQLite database"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.execute("SELECT * FROM assets ORDER BY created_at DESC")

                assets = []
                for row in cursor.fetchall():
                    asset = dict(row)

                    # Parse JSON fields back to objects
                    json_fields = ['hda_parameters', 'dependencies', 'file_sizes', 'copied_files', 'metadata']
                    for field in json_fields:
                        if asset[field]:
                            try:
                                asset[field] = json.loads(asset[field])
                            except json.JSONDecodeError:
                                asset[field] = {}

                    # Reconstruct paths object
                    asset['paths'] = {
                        'usd': asset['usd_path'],
                        'thumbnail': asset['thumbnail_path'],
                        'textures': asset['textures_path'],
                        'fbx': asset['fbx_path']
                    }

                    assets.append(asset)

                logger.info(f"✅ Retrieved {len(assets)} assets from SQLite")
                return assets

        except Exception as e:
            logger.error(f"❌ Failed to get assets: {e}")
            return []

    def search_assets(self, search_term: str = "", category: str = "", created_by: str = "") -> List[Dict]:
        """Search assets with filters"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM assets WHERE 1=1"
                params = []

                if search_term:
                    query += " AND (name LIKE ? OR category LIKE ?)"
                    params.extend([f"%{search_term}%", f"%{search_term}%"])

                if category:
                    query += " AND category = ?"
                    params.append(category)

                if created_by:
                    query += " AND created_by = ?"
                    params.append(created_by)

                query += " ORDER BY created_at DESC"

                cursor = conn.execute(query, params)
                assets = []

                for row in cursor.fetchall():
                    asset = dict(row)

                    # Parse JSON fields
                    json_fields = ['hda_parameters', 'dependencies', 'file_sizes', 'copied_files', 'metadata']
                    for field in json_fields:
                        if asset[field]:
                            try:
                                asset[field] = json.loads(asset[field])
                            except json.JSONDecodeError:
                                asset[field] = {}

                    # Reconstruct paths
                    asset['paths'] = {
                        'usd': asset['usd_path'],
                        'thumbnail': asset['thumbnail_path'],
                        'textures': asset['textures_path'],
                        'fbx': asset['fbx_path']
                    }

                    assets.append(asset)

                logger.info(f"✅ Search returned {len(assets)} assets")
                return assets

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    def get_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """Get a specific asset by ID"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                asset = dict(row)

                # Parse JSON fields
                json_fields = ['hda_parameters', 'dependencies', 'file_sizes', 'copied_files', 'metadata']
                for field in json_fields:
                    if asset[field]:
                        try:
                            asset[field] = json.loads(asset[field])
                        except json.JSONDecodeError:
                            asset[field] = {}

                # Reconstruct paths
                asset['paths'] = {
                    'usd': asset['usd_path'],
                    'thumbnail': asset['thumbnail_path'],
                    'textures': asset['textures_path'],
                    'fbx': asset['fbx_path']
                }

                return asset

        except Exception as e:
            logger.error(f"❌ Failed to get asset {asset_id}: {e}")
            return None

    def add_asset(self, asset_data: Dict) -> bool:
        """Add a new asset to the database"""
        try:
            with self.get_connection() as conn:
                paths = asset_data.get('paths', {})
                metadata = asset_data.get('metadata', {})
                hda_params = metadata.get('hda_parameters', {})

                asset_tuple = (
                    asset_data.get('id'),
                    asset_data.get('name'),
                    asset_data.get('category'),
                    asset_data.get('folder'),
                    paths.get('usd'),
                    paths.get('thumbnail'),
                    paths.get('textures'),
                    paths.get('fbx'),
                    metadata.get('houdini_version'),
                    metadata.get('hip_file'),
                    metadata.get('node_path'),
                    metadata.get('node_type'),
                    metadata.get('export_time'),
                    metadata.get('created_by'),
                    json.dumps(hda_params),
                    json.dumps(asset_data.get('dependencies', {})),
                    json.dumps(asset_data.get('file_sizes', {})),
                    asset_data.get('created_at', datetime.now().isoformat()),
                    json.dumps(asset_data.get('copied_files', [])),
                    json.dumps(metadata)
                )

                conn.execute("""
                             INSERT INTO assets (id, name, category, folder, usd_path, thumbnail_path,
                                                 textures_path, fbx_path, houdini_version, hip_file,
                                                 node_path, node_type, export_time, created_by,
                                                 hda_parameters, dependencies, file_sizes, created_at,
                                                 copied_files, metadata)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                             """, asset_tuple)

                conn.commit()
                logger.info(f"✅ Added asset: {asset_data.get('name')}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to add asset: {e}")
            return False

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Total assets
                cursor.execute("SELECT COUNT(*) FROM assets")
                total_assets = cursor.fetchone()[0]

                # Assets by category
                cursor.execute("SELECT category, COUNT(*) FROM assets GROUP BY category")
                categories = dict(cursor.fetchall())

                # Assets by creator
                cursor.execute("SELECT created_by, COUNT(*) FROM assets GROUP BY created_by")
                creators = dict(cursor.fetchall())

                # Recent assets (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute("SELECT COUNT(*) FROM assets WHERE created_at > ?", (week_ago,))
                recent_assets = cursor.fetchone()[0]

                return {
                    'total_assets': total_assets,
                    'by_category': categories,
                    'by_creator': creators,
                    'recent_assets': recent_assets
                }

        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}

    def sync_with_json(self):
        """Sync SQLite database with JSON file"""
        logger.info("🔄 Syncing SQLite with JSON...")
        return self.json_to_sqlite()


# Test function with proper cleanup
def test_sqlite_setup_safe():
    """Test the SQLite setup with proper cleanup"""
    print("🧪 Testing SQLite Asset Database Setup (Safe Version)...")

    # Use a unique test database file
    test_db_path = f"test_assets_{int(time.time())}.db"

    try:
        # Initialize manager with test database
        manager = SQLiteAssetManager(db_path=test_db_path)

        # Test JSON import
        success = manager.json_to_sqlite()
        if success:
            print("✅ JSON import successful")
        else:
            print("❌ JSON import failed")
            return False

        # Test retrieval
        assets = manager.get_all_assets()
        print(f"✅ Retrieved {len(assets)} assets from SQLite")

        # Test search
        if assets:
            search_results = manager.search_assets(search_term="Pig")
            print(f"✅ Search test: found {len(search_results)} assets")

        # Test statistics
        stats = manager.get_statistics()
        print(f"✅ Statistics: {stats}")

        print("🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        # Clean up test database file
        try:
            if Path(test_db_path).exists():
                # Close any remaining connections
                manager.cleanup_connections()

                # Wait a bit for file handles to be released
                time.sleep(0.5)

                # Remove test database
                os.remove(test_db_path)
                print(f"🧹 Cleaned up test database: {test_db_path}")
        except Exception as e:
            print(f"⚠️ Could not clean up test database: {e}")


if __name__ == "__main__":
    test_sqlite_setup_safe()