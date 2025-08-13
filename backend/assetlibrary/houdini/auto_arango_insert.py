#!/usr/bin/env python3
"""
Auto ArangoDB Asset Insertion for Blacksmith Atlas
=================================================

This script automatically inserts assets into the Asset_Library collection
when exporting from Houdini, using metadata.json file data.

Usage: Called automatically during Houdini export process
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add backend path for imports
script_dir = Path(__file__).parent
backend_path = script_dir.parent.parent
sys.path.insert(0, str(backend_path))

# Import ArangoDB
try:
    from arango import ArangoClient
    ARANGO_AVAILABLE = True
except ImportError:
    print("⚠️  ArangoDB client not available - install with: pip install python-arango")
    ARANGO_AVAILABLE = False

# Import Atlas configuration
try:
    from assetlibrary.config import BlacksmithAtlasConfig
    CONFIG_AVAILABLE = True
except ImportError:
    print("⚠️  Atlas configuration not available")
    CONFIG_AVAILABLE = False


class AutoArangoAssetInserter:
    """Automatically insert assets into ArangoDB Asset_Library collection"""
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.client = None
        self.db = None
        self.asset_collection = None
        self.connected = False
        
        if ARANGO_AVAILABLE and CONFIG_AVAILABLE:
            self._connect()
    
    def _connect(self) -> bool:
        """Connect to ArangoDB"""
        try:
            # Get database configuration
            db_config = BlacksmithAtlasConfig.get_database_config(self.environment)
            
            print(f"🔌 Connecting to ArangoDB ({self.environment})...")
            
            # Create client and connect
            self.client = ArangoClient(hosts=db_config['hosts'])
            self.db = self.client.db(
                db_config['database'],
                username=db_config['username'],
                password=db_config['password']
            )
            
            # Test connection
            db_info = self.db.properties()
            print(f"✅ Connected to ArangoDB: {db_info.get('name', 'Unknown')}")
            
            # Get Asset_Library collection
            if self.db.has_collection('Asset_Library'):
                self.asset_collection = self.db.collection('Asset_Library')
                print("✅ Asset_Library collection found")
                self.connected = True
                return True
            else:
                print("❌ Asset_Library collection not found")
                return False
            
        except Exception as e:
            print(f"❌ Failed to connect to ArangoDB: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        return self.connected and ARANGO_AVAILABLE and self.asset_collection is not None
    
    def read_metadata(self, metadata_file_path: str) -> Optional[Dict]:
        """Read and parse metadata.json file"""
        try:
            metadata_path = Path(metadata_file_path)
            if not metadata_path.exists():
                print(f"❌ Metadata file not found: {metadata_file_path}")
                return None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            print(f"📄 Read metadata from: {metadata_file_path}")
            return metadata
            
        except Exception as e:
            print(f"❌ Failed to read metadata: {e}")
            return None
    
    def create_arango_document(self, metadata: Dict) -> Dict:
        """
        Create ArangoDB document from metadata.json
        
        Mapping per user requirements:
        - _id = "id" from metadata
        - _key = "id" + "_" + "name" from metadata  
        - name = "name" from metadata
        - asset_type = "asset_type" from metadata
        - subcategory = "subcategory" from metadata
        - render_engine = "render_engine" from metadata
        - dimension = "3D" (hardcoded)
        - created_by = "created_by" from metadata
        - created_at = "created_at" from metadata
        - template_file = "template_file" from metadata
        - source_hip_file = "source_hip_file" from metadata
        - houdini_version = "houdini_version" from metadata
        - export_context = "export_context" from metadata
        - export_time = "export_time" from metadata
        """
        
        # Required fields from metadata
        asset_id = metadata.get("id", "unknown_id")
        asset_name = metadata.get("name", "Unknown Asset")
        
        # Get or derive the folder path - this is the absolute path to the asset folder on disk
        folder_path = metadata.get("folder_path", "")
        if not folder_path and metadata.get("asset_folder"):
            # If folder_path not explicitly set, try to derive from asset_folder
            folder_path = metadata.get("asset_folder")
        
        # Create document key (id_name format)
        document_key = f"{asset_id}_{asset_name}".replace(" ", "_").replace("-", "_")
        
        # Build ArangoDB document
        arango_doc = {
            # ArangoDB system fields
            "_key": document_key,  # Use id_name format as requested
            
            # Core asset fields from metadata
            "id": asset_id,
            "name": asset_name,
            "asset_type": metadata.get("asset_type", "Unknown"),
            "subcategory": metadata.get("subcategory", "General"),
            "render_engine": metadata.get("render_engine", "Redshift"),
            "dimension": "3D",  # Hardcoded as requested
            "created_by": metadata.get("created_by", "unknown"),
            "created_at": metadata.get("created_at", datetime.now().isoformat()),
            "template_file": metadata.get("template_file", ""),
            "source_hip_file": metadata.get("source_hip_file", ""),
            "houdini_version": metadata.get("houdini_version", ""),
            "export_context": metadata.get("export_context", ""),
            "export_time": metadata.get("export_time", datetime.now().isoformat()),
            
            # Folder path for direct file system access
            "folder_path": folder_path,  # Absolute path to asset folder on disk
            
            # Additional fields for compatibility with existing frontend
            "category": metadata.get("subcategory", "General"),
            "description": metadata.get("description", f"{metadata.get('asset_type', 'Asset')}: {asset_name}"),
            "tags": metadata.get("tags", []),
            "status": "active",
            "updated_at": datetime.now().isoformat(),
            
            # Frontend hierarchy structure for filtering
            "hierarchy": {
                "dimension": "3D",
                "asset_type": metadata.get("asset_type", "Unknown"),
                "subcategory": metadata.get("subcategory", "General"),
                "render_engine": metadata.get("render_engine", "Redshift")
            },
            
            # File information
            "paths": {
                "asset_folder": metadata.get("asset_folder", ""),
                "folder_path": folder_path,  # Direct folder path for file manager access
                "metadata": metadata.get("metadata_file", ""),
                "geometry": metadata.get("geometry_folder", ""),
                "textures": metadata.get("textures_folder", ""),
                "template": metadata.get("template_file", "")
            },
            
            # Complete metadata for reference
            "full_metadata": metadata,
            
            # Sync tracking
            "last_arango_sync": datetime.now().isoformat(),
            "sync_source": "houdini_export"
        }
        
        return arango_doc
    
    def insert_asset(self, metadata_file_path: str) -> bool:
        """
        Insert asset into ArangoDB from metadata.json file
        
        Args:
            metadata_file_path: Path to the metadata.json file
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if not self.is_connected():
            print("❌ Database not connected - cannot insert asset")
            return False
        
        # Read metadata
        metadata = self.read_metadata(metadata_file_path)
        if not metadata:
            return False
        
        try:
            # Create ArangoDB document
            arango_doc = self.create_arango_document(metadata)
            
            # Check if asset already exists
            existing_asset = None
            try:
                existing_asset = self.asset_collection.get(arango_doc["_key"])
            except:
                pass  # Asset doesn't exist, which is fine
            
            if existing_asset:
                # Update existing asset
                result = self.asset_collection.update(arango_doc)
                print(f"🔄 Updated existing asset in ArangoDB: {arango_doc['name']}")
            else:
                # Insert new asset
                result = self.asset_collection.insert(arango_doc)
                print(f"➕ Inserted new asset into ArangoDB: {arango_doc['name']}")
            
            # Log success details
            print(f"   📋 Asset ID: {arango_doc['id']}")
            print(f"   🏷️ Asset Type: {arango_doc['asset_type']}")
            print(f"   📁 Subcategory: {arango_doc['subcategory']}")
            print(f"   🎨 Render Engine: {arango_doc['render_engine']}")
            print(f"   🗄️ Document Key: {arango_doc['_key']}")
            print(f"   ⏰ Export Time: {arango_doc['export_time']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to insert asset into ArangoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def batch_insert_from_directory(self, library_path: str) -> Dict[str, int]:
        """
        Batch insert all assets from a library directory
        
        Args:
            library_path: Path to asset library root
            
        Returns:
            Dict with insertion statistics
        """
        
        if not self.is_connected():
            print("❌ Database not connected - cannot batch insert")
            return {"error": "Database not connected"}
        
        library_root = Path(library_path)
        if not library_root.exists():
            print(f"❌ Library path not found: {library_path}")
            return {"error": "Library path not found"}
        
        stats = {
            "assets_processed": 0,
            "assets_inserted": 0,
            "assets_updated": 0,
            "errors": 0
        }
        
        print(f"🔄 Batch inserting assets from: {library_path}")
        
        # Find all metadata.json files
        for metadata_file in library_root.rglob("metadata.json"):
            stats["assets_processed"] += 1
            
            try:
                if self.insert_asset(str(metadata_file)):
                    # We don't distinguish between insert/update in this simple case
                    stats["assets_inserted"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                print(f"❌ Error processing {metadata_file}: {e}")
                stats["errors"] += 1
        
        print(f"📊 Batch insert completed:")
        print(f"   📋 Processed: {stats['assets_processed']}")
        print(f"   ➕ Inserted/Updated: {stats['assets_inserted']}")
        print(f"   ❌ Errors: {stats['errors']}")
        
        return stats


# Global inserter instance
_inserter = None

def get_arango_inserter(environment: str = 'development') -> AutoArangoAssetInserter:
    """Get global inserter instance"""
    global _inserter
    if _inserter is None:
        _inserter = AutoArangoAssetInserter(environment)
    return _inserter


def auto_insert_on_export(metadata_file_path: str) -> bool:
    """
    Automatically insert asset into ArangoDB after Houdini export
    
    This function is called by the Houdini export process
    
    Args:
        metadata_file_path: Path to the metadata.json file created during export
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    print("🚀 AUTO-INSERT TO ARANGODB")
    print("=" * 40)
    
    try:
        inserter = get_arango_inserter()
        success = inserter.insert_asset(metadata_file_path)
        
        if success:
            print("✅ Auto-insert to ArangoDB successful!")
        else:
            print("❌ Auto-insert to ArangoDB failed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Auto-insert error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test script
    import argparse
    
    parser = argparse.ArgumentParser(description='Insert assets into ArangoDB from metadata.json')
    parser.add_argument('--metadata', help='Path to metadata.json file')
    parser.add_argument('--library', help='Path to asset library for batch insert')
    parser.add_argument('--env', default='development', help='Environment (development/production)')
    
    args = parser.parse_args()
    
    inserter = AutoArangoAssetInserter(args.env)
    
    if args.metadata:
        # Single asset insert
        success = inserter.insert_asset(args.metadata)
        sys.exit(0 if success else 1)
    
    elif args.library:
        # Batch insert
        stats = inserter.batch_insert_from_directory(args.library)
        sys.exit(0 if stats.get("errors", 0) == 0 else 1)
    
    else:
        print("❌ Specify either --metadata or --library")
        sys.exit(1)