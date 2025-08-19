#!/usr/bin/env python3
"""
Houdini to ArangoDB Integration Script
=====================================

Standalone database integration script for inserting Houdini-exported assets
into ArangoDB 3D_Atlas_Library collection. Designed for Docker environment 
communication and reliable error handling.

Features:
- Docker-native ArangoDB connection (arangodb:8529)
- Environment-based configuration (.env file)
- Comprehensive error handling with graceful fallback
- Schema validation and transformation
- Retry logic with exponential backoff
- Detailed logging for debugging

Usage:
    # Direct usage from Houdini export workflow
    inserter = HoudiniArangoInserter()
    success = inserter.process_exported_asset("/path/to/asset/folder")
    
    # Command line usage for testing
    python houdini_arango_insert.py --metadata /path/to/metadata.json
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
import traceback

# Add backend path for configuration imports
script_dir = Path(__file__).parent
backend_path = script_dir.parent.parent
sys.path.insert(0, str(backend_path))

# Import ArangoDB client with fallback handling
try:
    from arango import ArangoClient
    from arango.exceptions import DocumentInsertError, DocumentUpdateError
    ARANGO_AVAILABLE = True
except ImportError as e:
    logging.error(f"ArangoDB client not available: {e}")
    ARANGO_AVAILABLE = False

# Import Atlas configuration
try:
    from assetlibrary.config import BlacksmithAtlasConfig
    CONFIG_AVAILABLE = True
except ImportError as e:
    logging.error(f"Atlas configuration not available: {e}")
    CONFIG_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HoudiniArangoInserter:
    """
    Standalone database integration for Houdini asset exports
    
    Handles ArangoDB connections, metadata processing, and document insertion
    with comprehensive error handling and Docker environment support.
    """
    
    def __init__(self, environment: str = 'development', max_retries: int = 3):
        """
        Initialize the database inserter
        
        Args:
            environment: Environment configuration ('development' or 'production')
            max_retries: Maximum retry attempts for database operations
        """
        self.environment = environment
        self.max_retries = max_retries
        self.retry_delay = 1.0  # Initial retry delay in seconds
        
        # Database connection objects
        self.client: Optional[ArangoClient] = None
        self.db = None
        self.asset_collection = None
        self.connected = False
        
        # Connection configuration
        self.db_config = None
        
        # Load configuration and attempt initial connection
        if ARANGO_AVAILABLE and CONFIG_AVAILABLE:
            self._load_configuration()
            self._connect()
        else:
            logger.error("Cannot initialize - missing required dependencies")
    
    def _load_configuration(self) -> None:
        """Load database configuration from Atlas config system"""
        try:
            self.db_config = BlacksmithAtlasConfig.get_database_config(self.environment)
            logger.info(f"Loaded database config for environment: {self.environment}")
            logger.debug(f"Database: {self.db_config['database']}")
            logger.debug(f"Hosts: {self.db_config['hosts']}")
            
            # Enhanced Docker environment detection
            if os.path.exists('/.dockerenv'):
                logger.info("🐳 Running inside Docker container")
                # Ensure we're using Docker-friendly settings
                if 'localhost' in str(self.db_config['hosts'][0]):
                    logger.warning("⚠️ Localhost detected in Docker - using arangodb hostname")
                    self.db_config['hosts'] = ['http://arangodb:8529']
            else:
                logger.info("🖥️ Running on host system")
                
        except Exception as e:
            logger.error(f"Failed to load database configuration: {e}")
            self.db_config = None
    
    def _connect(self) -> bool:
        """
        Establish connection to ArangoDB with retry logic and timeout management
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.db_config:
            logger.error("No database configuration available")
            return False
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔌 Connecting to ArangoDB (attempt {attempt + 1}/{self.max_retries})...")
                logger.info(f"   Environment: {self.environment}")
                logger.info(f"   Host: {self.db_config['hosts'][0]}")
                logger.info(f"   Database: {self.db_config['database']}")
                
                # Create ArangoDB client with timeout and connection pooling
                self.client = ArangoClient(
                    hosts=self.db_config['hosts'],
                    request_timeout=30,  # 30 second timeout
                    max_conn_pool_size=10  # Connection pooling
                )
                
                # Connect to database with timeout
                self.db = self.client.db(
                    self.db_config['database'],
                    username=self.db_config['username'],
                    password=self.db_config['password']
                )
                
                # Test connection by getting database properties
                db_info = self.db.properties()
                logger.info(f"✅ Connected to ArangoDB: {db_info.get('name', 'Unknown')}")
                
                # Get or create 3D_Atlas_Library collection
                if self.db.has_collection('3D_Atlas_Library'):
                    self.asset_collection = self.db.collection('3D_Atlas_Library')
                    logger.info("✅ 3D_Atlas_Library collection found")
                else:
                    logger.warning("⚠️ 3D_Atlas_Library collection not found - attempting to create")
                    self.asset_collection = self.db.create_collection('3D_Atlas_Library')
                    logger.info("✅ 3D_Atlas_Library collection created")
                
                self.connected = True
                return True
                
            except Exception as e:
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("❌ All connection attempts failed")
        
        self.connected = False
        return False
    
    def is_connected(self) -> bool:
        """Check if database connection is active and ready"""
        return (self.connected and 
                ARANGO_AVAILABLE and 
                self.asset_collection is not None)
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and transform metadata for database storage
        
        Args:
            metadata: Raw metadata dictionary from JSON file
            
        Returns:
            Dict containing validation results and transformed data
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'transformed_data': None
        }
        
        # Check required fields
        required_fields = ['id', 'name', 'asset_type']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Check for either category or subcategory
        if not metadata.get('category') and not metadata.get('subcategory'):
            validation_result['valid'] = False
            validation_result['errors'].append("Missing required field: category or subcategory")
        
        if not validation_result['valid']:
            return validation_result
        
        try:
            # Transform metadata to database schema
            asset_id = str(metadata.get('id', 'unknown'))
            asset_name = str(metadata.get('name', 'Unknown Asset'))
            
            # Create document key as id_name format (combining id + underscore + name)
            document_key = f"{asset_id}_{asset_name}".replace(' ', '_').replace('-', '_')
            # Remove invalid characters for ArangoDB document keys
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '.', '[', ']']
            for char in invalid_chars:
                document_key = document_key.replace(char, '_')
            
            # Build transformed document
            transformed_data = {
                # ArangoDB system fields
                '_key': document_key,
                
                # Core asset identification
                'id': asset_id,
                'name': asset_name,
                'asset_type': metadata.get('asset_type', 'Assets'),
                'category': metadata.get('category', metadata.get('subcategory', 'General')),
                'dimension': '3D',
                
                # Frontend hierarchy structure for filtering
                'hierarchy': {
                    'dimension': '3D',
                    'asset_type': metadata.get('asset_type', 'Assets'),
                    'subcategory': metadata.get('category', metadata.get('subcategory', 'General'))
                },
                
                # Metadata and tracking
                'metadata': {
                    'render_engine': metadata.get('render_engine', 'Redshift'),
                    'created_by': metadata.get('created_by', 'unknown'),
                    'houdini_version': metadata.get('houdini_version', '20.0'),
                    'description': metadata.get('description', f"{metadata.get('asset_type', 'Asset')}: {asset_name}"),
                    'tags': metadata.get('tags', []),
                    'export_time': metadata.get('export_time', datetime.now().isoformat()),
                    'export_context': metadata.get('export_context', 'houdini_export'),
                    'template_file': metadata.get('template_file', ''),
                    'source_hip_file': metadata.get('source_hip_file', '')
                },
                
                # File paths and organization
                'paths': {
                    'asset_folder': metadata.get('asset_folder', ''),
                    'metadata_file': metadata.get('metadata_file', ''),
                    'template': metadata.get('template_file', ''),
                    'geometry': metadata.get('geometry_folder', ''),
                    'textures': metadata.get('textures_folder', '')
                },
                
                # Additional compatibility fields
                'tags': metadata.get('tags', []),
                'description': metadata.get('description', f"{metadata.get('asset_type', 'Asset')}: {asset_name}"),
                'status': 'active',
                
                # Timestamps
                'created_at': metadata.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat(),
                'last_database_sync': datetime.now().isoformat(),
                
                # Sync tracking
                'sync_source': 'houdini_export',
                'full_metadata': metadata  # Preserve complete original metadata
            }
            
            validation_result['transformed_data'] = transformed_data
            logger.debug(f"✅ Metadata validation successful for asset: {asset_name}")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Transformation error: {str(e)}")
            logger.error(f"❌ Metadata transformation failed: {e}")
        
        return validation_result
    
    def insert_asset_document(self, document: Dict[str, Any]) -> bool:
        """
        Insert or update asset document in 3D_Atlas_Library collection
        
        Args:
            document: Validated and transformed document data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("❌ Database not connected - cannot insert document")
            return False
        
        document_key = document.get('_key', 'unknown')
        asset_name = document.get('name', 'Unknown')
        
        for attempt in range(self.max_retries):
            try:
                # Check if document already exists
                existing_doc = None
                try:
                    existing_doc = self.asset_collection.get(document_key)
                except:
                    pass  # Document doesn't exist, which is fine for new assets
                
                if existing_doc:
                    # Update existing document
                    result = self.asset_collection.update(document)
                    logger.info(f"🔄 Updated existing asset: {asset_name}")
                    logger.info(f"   🆔 Document Key: {document_key}")
                    logger.info(f"   📁 Asset Type: {document.get('asset_type', 'Unknown')}")
                    logger.info(f"   🏷️ Category: {document.get('category', 'Unknown')}")
                else:
                    # Insert new document
                    result = self.asset_collection.insert(document)
                    logger.info(f"➕ Inserted new asset: {asset_name}")
                    logger.info(f"   🆔 Document Key: {document_key}")
                    logger.info(f"   📁 Asset Type: {document.get('asset_type', 'Unknown')}")
                    logger.info(f"   🏷️ Category: {document.get('category', 'Unknown')}")
                
                return True
                
            except (DocumentInsertError, DocumentUpdateError) as e:
                logger.error(f"❌ Document operation failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ All insert attempts failed for: {asset_name}")
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error during document insertion: {e}")
                logger.error(traceback.format_exc())
                break
        
        return False
    
    def _map_paths_for_environment(self, asset_folder_path: str) -> str:
        """
        Map file paths between host and container environments
        
        Args:
            asset_folder_path: Original asset folder path
            
        Returns:
            str: Mapped path appropriate for current environment
        """
        path_str = str(asset_folder_path)
        
        # Docker container path mapping
        if os.path.exists('/.dockerenv'):
            # Running inside Docker container
            if '/net/library/atlaslib' in path_str:
                mapped_path = path_str.replace('/net/library/atlaslib', '/app/assets')
                logger.info(f"🔄 Docker path mapping: {path_str} → {mapped_path}")
                return mapped_path
            elif not path_str.startswith('/app/assets'):
                # Assume host path needs mapping
                mapped_path = f"/app/assets/{Path(path_str).name}"
                logger.info(f"🔄 Docker path mapping: {path_str} → {mapped_path}")
                return mapped_path
        else:
            # Running on host system
            if path_str.startswith('/app/assets'):
                mapped_path = path_str.replace('/app/assets', '/net/library/atlaslib')
                logger.info(f"🔄 Host path mapping: {path_str} → {mapped_path}")
                return mapped_path
        
        # No mapping needed
        return path_str
    
    def process_exported_asset(self, asset_folder_path: str) -> bool:
        """
        Main function to process exported asset and update database
        
        Args:
            asset_folder_path: Path to the exported asset folder containing metadata.json
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("🚀 Processing exported asset for database insertion")
        logger.info("=" * 60)
        
        try:
            # Map paths for current environment (Docker/host)
            mapped_path = self._map_paths_for_environment(asset_folder_path)
            asset_folder = Path(mapped_path)
            
            if not asset_folder.exists():
                logger.error(f"❌ Asset folder not found: {mapped_path}")
                logger.error(f"   Original path: {asset_folder_path}")
                return False
            
            # Look for metadata.json file
            metadata_file = asset_folder / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"❌ metadata.json not found in: {asset_folder_path}")
                return False
            
            # Read metadata file
            logger.info(f"📄 Reading metadata from: {metadata_file}")
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            asset_name = metadata.get('name', 'Unknown Asset')
            logger.info(f"📋 Processing asset: {asset_name}")
            
            # Validate and transform metadata
            validation_result = self.validate_metadata(metadata)
            if not validation_result['valid']:
                logger.error("❌ Metadata validation failed:")
                for error in validation_result['errors']:
                    logger.error(f"   • {error}")
                return False
            
            if validation_result['warnings']:
                logger.warning("⚠️ Metadata validation warnings:")
                for warning in validation_result['warnings']:
                    logger.warning(f"   • {warning}")
            
            # Insert document into database
            document = validation_result['transformed_data']
            if self.insert_asset_document(document):
                logger.info(f"✅ Successfully processed asset: {asset_name}")
                return True
            else:
                logger.error(f"❌ Failed to insert asset: {asset_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Unexpected error processing asset: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def batch_process_assets(self, library_path: str) -> Dict[str, int]:
        """
        Batch process multiple assets from a library directory
        
        Args:
            library_path: Path to asset library root directory
            
        Returns:
            Dict with processing statistics
        """
        logger.info(f"🔄 Batch processing assets from: {library_path}")
        
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            library_root = Path(library_path)
            if not library_root.exists():
                logger.error(f"❌ Library path not found: {library_path}")
                return stats
            
            # Find all metadata.json files
            metadata_files = list(library_root.rglob("metadata.json"))
            logger.info(f"📊 Found {len(metadata_files)} metadata files")
            
            for metadata_file in metadata_files:
                stats['processed'] += 1
                asset_folder = metadata_file.parent
                
                logger.info(f"\n📁 Processing {stats['processed']}/{len(metadata_files)}: {asset_folder.name}")
                
                if self.process_exported_asset(str(asset_folder)):
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info("\n📊 Batch processing complete:")
            logger.info(f"   📋 Total processed: {stats['processed']}")
            logger.info(f"   ✅ Successful: {stats['successful']}")
            logger.info(f"   ❌ Failed: {stats['failed']}")
            logger.info(f"   ⏭️ Skipped: {stats['skipped']}")
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            stats['failed'] = stats['processed'] - stats['successful']
        
        return stats


def main():
    """Command line interface for testing and manual operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Houdini to ArangoDB Asset Integration')
    parser.add_argument('--metadata', help='Path to metadata.json file')
    parser.add_argument('--asset-folder', help='Path to asset folder containing metadata.json')
    parser.add_argument('--library', help='Path to asset library for batch processing')
    parser.add_argument('--env', default='development', 
                       choices=['development', 'production'],
                       help='Environment configuration')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize inserter
    inserter = HoudiniArangoInserter(environment=args.env)
    
    if not inserter.is_connected():
        logger.error("❌ Failed to connect to database - check configuration and connection")
        sys.exit(1)
    
    success = False
    
    if args.metadata:
        # Process single metadata file
        asset_folder = Path(args.metadata).parent
        success = inserter.process_exported_asset(str(asset_folder))
        
    elif args.asset_folder:
        # Process single asset folder
        success = inserter.process_exported_asset(args.asset_folder)
        
    elif args.library:
        # Batch process library
        stats = inserter.batch_process_assets(args.library)
        success = stats['failed'] == 0
        
    else:
        logger.error("❌ Please specify --metadata, --asset-folder, or --library")
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()