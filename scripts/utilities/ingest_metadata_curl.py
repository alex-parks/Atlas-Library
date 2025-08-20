#!/usr/bin/env python3
"""
Blacksmith Atlas Metadata Ingestion Script (Curl Version)

This script ingests metadata.json files into the Atlas API using curl via subprocess.
It processes Houdini asset metadata and creates comprehensive asset records.

Usage:
    python ingest_metadata_curl.py path/to/metadata.json
    python ingest_metadata_curl.py --directory path/to/folder/with/metadata/files
    python ingest_metadata_curl.py --batch path/to/folder --recursive
"""

import json
import subprocess
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AtlasMetadataIngester:
    """Class to handle ingestion of metadata files into Atlas API using curl"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        
        # Test API connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to the Atlas API using curl"""
        try:
            curl_cmd = [
                'curl', '-s', '-f',  # silent, fail on HTTP errors
                f"{self.api_base_url}/health"
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                health_data = json.loads(result.stdout)
                logger.info(f"✅ Connected to Atlas API v{health_data.get('version', 'unknown')}")
                
                # Check if database is healthy
                db_status = health_data.get('components', {}).get('database', {}).get('status')
                if db_status != 'healthy':
                    logger.warning(f"⚠️ Database status: {db_status}")
                else:
                    logger.info(f"📊 Database healthy with {health_data.get('components', {}).get('database', {}).get('assets_count', 0)} assets")
            else:
                raise Exception(f"API health check failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout connecting to Atlas API at {self.api_base_url}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response from API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to Atlas API at {self.api_base_url}: {e}")
            raise
    
    def transform_metadata_to_asset(self, metadata: Dict[str, Any], metadata_file_path: str) -> Dict[str, Any]:
        """Transform Houdini metadata into Atlas asset format"""
        
        # Extract basic asset information
        asset_data = {
            "name": metadata.get("name", "Unknown Asset"),
            "category": metadata.get("subcategory", "Unknown"),
            "paths": {
                "metadata_file": metadata_file_path,
                "folder_path": metadata.get("folder_path"),
                "template_file": metadata.get("template_file"),
                "source_hip_file": metadata.get("source_hip_file")
            },
            "created_at": metadata.get("created_at"),
            "created_by": metadata.get("created_by"),
            "metadata": {
                # Core asset information
                "id": metadata.get("id"),  # Include the UID_Name ID for proper key assignment
                "asset_id": metadata.get("id"),
                "asset_type": metadata.get("asset_type", "Assets"),
                "dimension": metadata.get("dimension", "3D"),
                "render_engine": metadata.get("render_engine", "Unknown"),
                "description": metadata.get("description", ""),
                "subcategory": metadata.get("subcategory"),
                
                # Hierarchy information
                "hierarchy": metadata.get("hierarchy", {}),
                
                # Export metadata
                "export_metadata": metadata.get("export_metadata", {}),
                "export_method": metadata.get("export_method"),
                "export_version": metadata.get("export_version"),
                
                # Houdini-specific data
                "houdini_version": metadata.get("houdini_version"),
                "node_summary": metadata.get("node_summary", {}),
                "template_size": metadata.get("template_size"),
                
                # File information
                "textures": metadata.get("textures", {}),
                "geometry_files": metadata.get("geometry_files", {}),
                "search_keywords": metadata.get("search_keywords", []),
                
                # Database sync status
                "database_synced": metadata.get("database_synced", False),
                "database_sync_error": metadata.get("database_sync_error"),
                
                # Creator information (preserve original)
                "created_by": metadata.get("created_by"),
                
                # Ingestion metadata
                "ingested_at": datetime.now().isoformat(),
                "ingested_by": "metadata_ingester_curl",
                "original_metadata_file": metadata_file_path
            },
            "file_sizes": self._calculate_file_sizes(metadata),
            "tags": self._extract_tags(metadata)
        }
        
        # Add paths for specific file types
        if metadata.get("textures", {}).get("files"):
            asset_data["paths"]["textures"] = metadata["textures"]["files"][:5]  # First 5 for preview
        
        if metadata.get("geometry_files", {}).get("files"):
            asset_data["paths"]["geometry"] = metadata["geometry_files"]["files"][:5]  # First 5 for preview
        
        return asset_data
    
    def _calculate_file_sizes(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate file size information from metadata"""
        file_sizes = {
            "template_size": metadata.get("template_size", 0),
            "texture_count": metadata.get("textures", {}).get("count", 0),
            "geometry_count": metadata.get("geometry_files", {}).get("count", 0)
        }
        
        # Calculate total estimated size (rough estimation)
        total_size = file_sizes["template_size"]
        
        # Estimate texture sizes (rough calculation)
        texture_count = file_sizes["texture_count"]
        if texture_count > 0:
            # Estimate average texture size based on common texture sizes
            estimated_texture_size = texture_count * 2048 * 1024  # 2MB per texture average
            total_size += estimated_texture_size
            file_sizes["estimated_texture_size"] = estimated_texture_size
        
        file_sizes["estimated_total_size"] = total_size
        
        return file_sizes
    
    def _extract_tags(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract and normalize tags from metadata"""
        tags = set()
        
        # Add basic tags from metadata
        if metadata.get("tags"):
            tags.update(metadata["tags"])
        
        # Add search keywords
        if metadata.get("search_keywords"):
            tags.update(metadata["search_keywords"])
        
        # Add render engine as tag
        if metadata.get("render_engine"):
            tags.add(metadata["render_engine"].lower())
        
        # Add asset type as tag
        if metadata.get("asset_type"):
            tags.add(metadata["asset_type"].lower())
        
        # Add dimension as tag
        if metadata.get("dimension"):
            tags.add(metadata["dimension"].lower())
        
        # Add file type tags
        if metadata.get("textures", {}).get("count", 0) > 0:
            tags.add("has_textures")
        
        if metadata.get("geometry_files", {}).get("count", 0) > 0:
            tags.add("has_geometry")
        
        # Add Houdini-specific tags
        if metadata.get("houdini_version"):
            tags.add("houdini")
            tags.add(f"houdini_{metadata['houdini_version'].split('.')[0]}")  # Major version
        
        return list(tags)
    
    def create_asset(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create asset using curl via subprocess"""
        try:
            # Convert asset_data to JSON
            json_data = json.dumps(asset_data)
            
            # Use curl via subprocess
            curl_cmd = [
                'curl', '-X', 'POST', 
                f"{self.api_base_url}/api/v1/assets",
                '-H', 'Content-Type: application/json',
                '-H', 'User-Agent: Atlas-Metadata-Ingester-Curl/1.0',
                '-d', json_data,
                '--silent',  # Suppress progress output
                '--show-error',  # Show errors
                '--fail'  # Fail silently on HTTP errors
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                logger.info(f"✅ Created asset: {response_data.get('name')} (ID: {response_data.get('id')})")
                return response_data
            
            elif result.returncode == 22:  # HTTP error (409, etc.)
                # Try to parse error response
                try:
                    error_data = json.loads(result.stderr) if result.stderr else "HTTP error"
                    if "already exists" in str(error_data):
                        logger.warning(f"⚠️ Asset already exists: {asset_data['name']}")
                        return None
                    else:
                        logger.error(f"❌ HTTP error creating asset {asset_data['name']}: {error_data}")
                        return None
                except json.JSONDecodeError:
                    logger.error(f"❌ HTTP error creating asset {asset_data['name']}: {result.stderr}")
                    return None
            else:
                logger.error(f"❌ Curl failed creating asset {asset_data['name']}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout creating asset {asset_data['name']}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response creating asset {asset_data['name']}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating asset {asset_data['name']}: {e}")
            return None
    
    def ingest_metadata_file(self, metadata_file_path: str) -> Optional[Dict[str, Any]]:
        """Ingest a single metadata.json file"""
        metadata_path = Path(metadata_file_path)
        
        if not metadata_path.exists():
            logger.error(f"❌ Metadata file not found: {metadata_file_path}")
            return None
        
        if not metadata_path.name.endswith(('.json', '.metadata')):
            logger.warning(f"⚠️ File doesn't appear to be a metadata file: {metadata_file_path}")
        
        try:
            logger.info(f"📄 Processing metadata file: {metadata_file_path}")
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Validate required fields
            if not metadata.get('name'):
                logger.error(f"❌ Missing required 'name' field in {metadata_file_path}")
                return None
            
            # Transform to asset format
            asset_data = self.transform_metadata_to_asset(metadata, str(metadata_path))
            
            # Create asset
            result = self.create_asset(asset_data)
            
            if result:
                logger.info(f"🎉 Successfully ingested asset: {result['name']}")
                return result
            else:
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {metadata_file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error processing {metadata_file_path}: {e}")
            return None
    
    def ingest_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, Any]:
        """Ingest all metadata files in a directory"""
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            logger.error(f"❌ Directory not found or not a directory: {directory_path}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        # Find metadata files
        if recursive:
            metadata_files = list(directory.rglob("metadata.json")) + list(directory.rglob("*.metadata"))
        else:
            metadata_files = list(directory.glob("metadata.json")) + list(directory.glob("*.metadata"))
        
        if not metadata_files:
            logger.warning(f"⚠️ No metadata files found in {directory_path}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"📁 Found {len(metadata_files)} metadata files in {directory_path}")
        
        # Process each file
        stats = {"success": 0, "failed": 0, "skipped": 0}
        
        for metadata_file in metadata_files:
            result = self.ingest_metadata_file(str(metadata_file))
            if result:
                stats["success"] += 1
            elif result is None:
                stats["skipped"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(f"📊 Ingestion complete: {stats['success']} successful, {stats['failed']} failed, {stats['skipped']} skipped")
        return stats
    
    def get_asset_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Search for an existing asset by name using curl"""
        try:
            # Encode the search parameter
            import urllib.parse
            search_param = urllib.parse.quote(name)
            
            curl_cmd = [
                'curl', '-s', '-f',
                f"{self.api_base_url}/api/v1/assets?search={search_param}&limit=1"
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("items") and len(data["items"]) > 0:
                    return data["items"][0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for asset {name}: {e}")
            return None

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Ingest Houdini metadata.json files into Blacksmith Atlas API using curl"
    )
    
    parser.add_argument(
        "path",
        help="Path to metadata.json file or directory containing metadata files"
    )
    
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Atlas API base URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--directory",
        action="store_true",
        help="Treat path as directory and ingest all metadata files"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search for metadata files in subdirectories"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse files but don't create assets (validation only)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize ingester
    try:
        ingester = AtlasMetadataIngester(args.api_url)
    except Exception as e:
        logger.error(f"❌ Failed to initialize ingester: {e}")
        sys.exit(1)
    
    # Process path
    path = Path(args.path)
    
    if args.directory or path.is_dir():
        # Directory mode
        stats = ingester.ingest_directory(str(path), args.recursive)
        
        if stats["success"] > 0:
            logger.info(f"🎉 Successfully ingested {stats['success']} assets!")
            sys.exit(0)
        else:
            logger.error("❌ No assets were successfully ingested")
            sys.exit(1)
    
    else:
        # Single file mode
        if not path.exists():
            logger.error(f"❌ File not found: {path}")
            sys.exit(1)
        
        result = ingester.ingest_metadata_file(str(path))
        
        if result:
            logger.info(f"🎉 Successfully ingested asset: {result['name']}")
            sys.exit(0)
        else:
            logger.error("❌ Failed to ingest asset")
            sys.exit(1)

if __name__ == "__main__":
    main()