#!/usr/bin/env python3
"""
ArangoDB Collection Manager for Blacksmith Atlas
=============================================

Advanced collection management for automatic sync between filesystem and database.
Based on ArangoDB Community Edition best practices for collection operations.

Features:
- Automatic asset collection creation/management
- Bidirectional sync (filesystem ↔ database)
- Asset lifecycle management (add/update/remove)
- Collection optimization and maintenance
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Import ArangoDB
try:
    from arango import ArangoClient
    from arango.database import StandardDatabase
    from arango.collection import StandardCollection
    ARANGO_AVAILABLE = True
except ImportError:
    print("⚠️  ArangoDB client not available - install with: pip install python-arango")
    ARANGO_AVAILABLE = False

# Import Atlas configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from assetlibrary.config import BlacksmithAtlasConfig
    CONFIG_AVAILABLE = True
except ImportError:
    print("⚠️  Atlas configuration not available")
    CONFIG_AVAILABLE = False


class ArangoAssetCollectionManager:
    """
    Advanced ArangoDB collection manager for asset lifecycle management
    
    Based on ArangoDB Community Edition patterns:
    - Document collections for assets
    - Edge collections for relationships
    - Index optimization for search performance
    - Automatic collection creation and management
    """
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.client: Optional[ArangoClient] = None
        self.db: Optional[StandardDatabase] = None
        self.collections: Dict[str, StandardCollection] = {}
        self.connected = False
        self.library_root = Path("/net/library/atlaslib/3D")
        
        # Single collection schema - Atlas_Library only
        self.collection_schemas = {
            'Atlas_Library': {
                'type': 'document',
                'description': 'Single unified collection for all Blacksmith Atlas assets',
                'indexes': [
                    {'type': 'hash', 'fields': ['name']},
                    {'type': 'hash', 'fields': ['asset_type']},
                    {'type': 'hash', 'fields': ['category']},
                    {'type': 'hash', 'fields': ['render_engine']},
                    {'type': 'hash', 'fields': ['status']},
                    {'type': 'hash', 'fields': ['metadata.asset_type']},
                    {'type': 'hash', 'fields': ['metadata.subcategory']},
                    {'type': 'hash', 'fields': ['metadata.render_engine']},
                    {'type': 'hash', 'fields': ['hierarchy.asset_type']},
                    {'type': 'hash', 'fields': ['hierarchy.subcategory']},
                    {'type': 'fulltext', 'fields': ['name', 'description']},
                    {'type': 'skiplist', 'fields': ['created_at']},
                    {'type': 'skiplist', 'fields': ['updated_at']},
                    {'type': 'skiplist', 'fields': ['last_filesystem_sync']}
                ]
            }
        }
        
        if ARANGO_AVAILABLE and CONFIG_AVAILABLE:
            self._connect()
    
    def _connect(self) -> bool:
        """Connect to ArangoDB using Atlas configuration"""
        try:
            # Get database configuration
            db_config = BlacksmithAtlasConfig.get_database_config(self.environment)
            
            logger.info(f"🔌 Connecting to ArangoDB ({self.environment})")
            logger.info(f"   Host: {db_config['hosts'][0]}")
            logger.info(f"   Database: {db_config['database']}")
            
            # Create client and connect
            self.client = ArangoClient(hosts=db_config['hosts'])
            self.db = self.client.db(
                db_config['database'],
                username=db_config['username'],
                password=db_config['password']
            )
            
            # Test connection
            db_info = self.db.properties()
            logger.info(f"✅ Connected to ArangoDB: {db_info.get('name', 'Unknown')}")
            
            # Initialize collections
            self._initialize_collections()
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to ArangoDB: {e}")
            self.connected = False
            return False
    
    def _initialize_collections(self) -> None:
        """Initialize all required collections with proper indexes"""
        logger.info("🗄️ Initializing ArangoDB collections...")
        
        for collection_name, schema in self.collection_schemas.items():
            try:
                # Create collection if it doesn't exist
                if not self.db.has_collection(collection_name):
                    if schema['type'] == 'edge':
                        collection = self.db.create_collection(collection_name, edge=True)
                    else:
                        collection = self.db.create_collection(collection_name)
                    logger.info(f"   ✅ Created collection: {collection_name}")
                else:
                    collection = self.db.collection(collection_name)
                    logger.info(f"   ✅ Using existing collection: {collection_name}")
                
                # Store collection reference
                self.collections[collection_name] = collection
                
                # Create indexes for performance
                self._create_collection_indexes(collection, schema.get('indexes', []))
                
            except Exception as e:
                logger.error(f"   ❌ Failed to initialize collection {collection_name}: {e}")
    
    def _create_collection_indexes(self, collection: StandardCollection, indexes: List[Dict]) -> None:
        """Create optimized indexes for collection"""
        try:
            existing_indexes = {idx['fields']: idx for idx in collection.indexes()}
            
            for index_def in indexes:
                index_fields = tuple(index_def['fields'])
                
                # Skip if index already exists
                if index_fields in existing_indexes:
                    continue
                
                # Create index based on type
                if index_def['type'] == 'hash':
                    collection.add_hash_index(fields=index_def['fields'])
                elif index_def['type'] == 'skiplist':
                    collection.add_skiplist_index(fields=index_def['fields'])
                elif index_def['type'] == 'fulltext':
                    for field in index_def['fields']:
                        collection.add_fulltext_index(fields=[field])
                
                logger.info(f"      📊 Created {index_def['type']} index on {index_def['fields']}")
                
        except Exception as e:
            logger.error(f"   ⚠️ Failed to create indexes: {e}")
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        return self.connected and ARANGO_AVAILABLE and self.db is not None
    
    def scan_filesystem_assets(self, library_path: str = "/app/assets/3D") -> List[dict]:
        """Scan filesystem for asset folders and return metadata"""
        logger.info(f"🔍 Scanning filesystem for assets: {library_path}")
        
        try:
            library_path_obj = Path(library_path)
            if not library_path_obj.exists():
                logger.error(f"❌ Asset library not found: {library_path}")
                return None
            
            assets = []
            
            # Walk through all subdirectories looking for assets
            for root, dirs, files in os.walk(library_path):
                root_path = Path(root)
                
                # Check if this directory contains a metadata.json file (indicating an asset)
                metadata_file = root_path / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Convert container path back to host path for storage
                        host_folder_path = str(root_path).replace('/app/assets', '/net/library/atlaslib')
                        
                        # Add folder path to metadata
                        metadata['folder_path'] = host_folder_path
                        
                        # Ensure required fields exist
                        if 'id' not in metadata:
                            metadata['id'] = root_path.name.split('_')[0] if '_' in root_path.name else root_path.name
                        
                        if 'name' not in metadata:
                            metadata['name'] = root_path.name.split('_', 1)[1] if '_' in root_path.name else root_path.name
                        
                        assets.append(metadata)
                        logger.debug(f"   ✅ Found asset: {metadata.get('name', 'Unknown')} at {host_folder_path}")
                        
                    except Exception as e:
                        logger.warning(f"   ⚠️ Failed to read metadata from {metadata_file}: {e}")
                        continue
            
            logger.info(f"   📊 Found {len(assets)} assets in filesystem")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to scan filesystem: {e}")
            return None
    
    def get_all_assets(self) -> List[Dict]:
        """Get all assets from database - simple and clean"""
        try:
            if not self.is_connected():
                logger.error("❌ Database not connected")
                return []
            
            assets_collection = self.collections.get('Atlas_Library')
            if not assets_collection:
                logger.error("❌ Atlas_Library collection not available")
                return []
            
            # Simple query to get all assets
            query = "FOR asset IN Atlas_Library RETURN asset"
            cursor = self.db.aql.execute(query)
            assets = list(cursor)
            
            logger.info(f"📊 Retrieved {len(assets)} assets from database")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets from database: {e}")
            return []
    
    def get_database_assets(self) -> Dict[str, Dict]:
        """
        Get all assets from database
        Returns: {asset_id: asset_data}
        """
        if not self.is_connected():
            logger.error("❌ Database not connected")
            return {}
        
        try:
            logger.info("🗄️ Fetching assets from database...")
            
            assets_collection = self.collections.get('Atlas_Library')
            if not assets_collection:
                logger.error("❌ Atlas_Library collection not available")
                return {}
            
            # Query all assets
            cursor = assets_collection.all()
            database_assets = {}
            
            for asset in cursor:
                asset_id = asset.get('_key', asset.get('asset_id', asset.get('id')))
                if asset_id:
                    database_assets[asset_id] = asset
            
            logger.info(f"   📊 Found {len(database_assets)} assets in database")
            return database_assets
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch database assets: {e}")
            return {}
    
    def add_asset_to_database(self, asset_data: Dict) -> bool:
        """Add a new asset to the database"""
        if not self.is_connected():
            return False
        
        try:
            assets_collection = self.collections.get('Atlas_Library')
            if not assets_collection:
                return False
            
            # Prepare asset document for ArangoDB
            asset_doc = {
                "_key": asset_data["asset_id"],
                "id": asset_data["asset_id"],
                "name": asset_data["name"],
                "asset_type": asset_data["asset_type"],
                "category": asset_data["category"],
                "render_engine": asset_data["metadata"].get("render_engine", "Redshift"),
                "metadata": asset_data["metadata"],
                "tags": asset_data["metadata"].get("tags", []),
                "description": asset_data["metadata"].get("description", f"{asset_data['asset_type']} asset: {asset_data['name']}"),
                "created_by": asset_data["metadata"].get("created_by", "unknown"),
                "created_at": asset_data["metadata"].get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                
                # Frontend filtering hierarchy
                "dimension": "3D",
                "hierarchy": {
                    "dimension": "3D",
                    "asset_type": asset_data["asset_type"],
                    "subcategory": asset_data["category"],
                    "render_engine": asset_data["metadata"].get("render_engine", "Redshift")
                },
                
                # File paths
                "paths": {
                    "asset_folder": asset_data["path"],
                    "metadata": asset_data["metadata_file"],
                    "textures": str(Path(asset_data["path"]) / "Textures") if (Path(asset_data["path"]) / "Textures").exists() else None,
                    "geometry": str(Path(asset_data["path"]) / "Geometry") if (Path(asset_data["path"]) / "Geometry").exists() else None,
                    "template": None
                },
                
                # File information
                "file_sizes": asset_data["metadata"].get("file_sizes", {}),
                "last_filesystem_sync": datetime.now().isoformat()
            }
            
            # Look for template file
            asset_path = Path(asset_data["path"])
            clipboard_folder = asset_path / "Clipboard"
            if clipboard_folder.exists():
                for template_file in clipboard_folder.glob("*_template.hip"):
                    asset_doc["paths"]["template"] = str(template_file)
                    break
            
            # Insert into database
            result = assets_collection.insert(asset_doc)
            
            # Asset successfully added - no need for separate logging collection
            
            logger.info(f"   ✅ Added asset to database: {asset_data['name']}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to add asset {asset_data.get('name', 'Unknown')}: {e}")
            return False
    
    def update_asset_in_database(self, asset_id: str, asset_data: Dict) -> bool:
        """Update an existing asset in the database"""
        if not self.is_connected():
            return False
        
        try:
            assets_collection = self.collections.get('Atlas_Library')
            if not assets_collection:
                return False
            
            # Update document
            update_data = {
                "updated_at": datetime.now().isoformat(),
                "last_filesystem_sync": datetime.now().isoformat(),
                "metadata": asset_data["metadata"],
                "tags": asset_data["metadata"].get("tags", []),
                "description": asset_data["metadata"].get("description", ""),
                "file_sizes": asset_data["metadata"].get("file_sizes", {})
            }
            
            result = assets_collection.update({"_key": asset_id}, update_data)
            
            # Asset successfully updated
            
            logger.info(f"   ✅ Updated asset in database: {asset_data['name']}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to update asset {asset_id}: {e}")
            return False
    
    def remove_asset_from_database(self, asset_id: str, asset_name: str = "Unknown") -> bool:
        """Remove an asset from the database"""
        if not self.is_connected():
            return False
        
        try:
            assets_collection = self.collections.get('Atlas_Library')
            if not assets_collection:
                return False
            
            # Remove from database
            result = assets_collection.delete({"_key": asset_id})
            
            # Asset successfully removed
            
            logger.info(f"   ✅ Removed asset from database: {asset_name}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to remove asset {asset_id}: {e}")
            return False
    
    def full_bidirectional_sync(self, library_path: str = "/app/assets/3D") -> dict:
        """Simple database-only sync - just refresh frontend display"""
        logger.info("🔄 Starting simple database refresh...")
        
        stats = {
            'assets_added': 0,
            'assets_updated': 0,
            'assets_removed': 0,
            'assets_unchanged': 0,
            'errors': 0
        }
        
        try:
            # Just get all assets from database and count them
            database_assets = self.get_all_assets()
            stats['assets_unchanged'] = len(database_assets)
            
            logger.info(f"📋 Database refresh complete - found {len(database_assets)} assets")
            
        except Exception as e:
            logger.error(f"❌ Database refresh error: {e}")
            stats['errors'] += 1
        
        logger.info("🏁 Simple database refresh complete!")
        logger.info(f"   ➡️ Assets in database: {stats['assets_unchanged']}")
        logger.info(f"   ❌ Errors: {stats['errors']}")
        
        return stats


def get_collection_manager(environment: str = 'development') -> ArangoAssetCollectionManager:
    """
    Get ArangoDB collection manager instance
    """
    return ArangoAssetCollectionManager(environment)


# Global instance
_collection_manager = None

def get_collection_manager(environment: str = 'development') -> ArangoAssetCollectionManager:
    """Get global collection manager instance"""
    global _collection_manager
    if _collection_manager is None:
        _collection_manager = ArangoAssetCollectionManager(environment)
    return _collection_manager


def auto_sync_on_export(asset_data: Dict) -> bool:
    """
    Automatically sync asset to database after Houdini export
    Called by Houdini export process
    """
    try:
        manager = get_collection_manager()
        if not manager.is_connected():
            logger.error("❌ Database not connected - skipping auto-sync")
            return False
        
        # Add/update asset in database
        success = manager.add_asset_to_database(asset_data)
        
        if success:
            logger.info(f"✅ Auto-sync successful: {asset_data.get('name', 'Unknown')}")
        else:
            logger.error(f"❌ Auto-sync failed: {asset_data.get('name', 'Unknown')}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Auto-sync error: {e}")
        return False


if __name__ == "__main__":
    # Test the collection manager
    manager = ArangoAssetCollectionManager()
    
    if manager.is_connected():
        print("✅ Collection manager connected successfully")
        
        # Perform full sync
        stats = manager.full_bidirectional_sync()
        print(f"📊 Sync results: {stats}")
    else:
        print("❌ Collection manager failed to connect")