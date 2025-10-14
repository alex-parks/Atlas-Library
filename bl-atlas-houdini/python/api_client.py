#!/usr/bin/env python3
"""
Blacksmith Atlas - API Client (Standalone)
==========================================

Handles communication with the Atlas API and database ingestion.
Embedded version of the ingestion functionality for standalone use.

Author: Blacksmith VFX
Version: 3.0 (Standalone)
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from config_manager import get_local_config, get_network_config
except ImportError:
    print("⚠️  Could not import config_manager, using fallback config")
    class FallbackConfig:
        @property
        def api_base_url(self):
            return "http://localhost:8000"
        @property
        def database_url(self):
            return "http://localhost:8529"
        @property
        def api_timeout(self):
            return 30
        @property
        def retry_attempts(self):
            return 3
        @property
        def use_ssl(self):
            return False
        @property
        def verify_ssl(self):
            return True

    def get_local_config():
        return FallbackConfig()

    def get_network_config():
        return FallbackConfig()

class AtlasAPIClient:
    """Handles all Atlas API communication"""

    def __init__(self, api_base_url: str = None, use_network: bool = False):
        self.use_network = use_network

        # Load the appropriate config based on use_network flag
        if use_network:
            self.config = get_network_config()
        else:
            self.config = get_local_config()

        self.api_base_url = (api_base_url or self.config.api_base_url).rstrip('/')

        print(f"🌐 Atlas API Client - {'Network' if use_network else 'Local'} Mode")
        print(f"📡 API URL: {self.api_base_url}")

        self._test_connection()

    def _test_connection(self):
        """Test connection to the Atlas API using curl"""
        try:
            curl_cmd = [
                'curl', '-s', '-f',  # silent, fail on HTTP errors
                '--connect-timeout', str(self.config.api_timeout),
                '--max-time', str(self.config.api_timeout * 2)
            ]

            # Add SSL options for network mode
            if self.use_network and self.config.use_ssl:
                if not self.config.verify_ssl:
                    curl_cmd.extend(['-k'])  # --insecure flag
                curl_cmd.extend(['--ssl-reqd'])

            # Test with assets endpoint since /health is not routed through Traefik
            curl_cmd.append(f"{self.api_base_url}/api/v1/assets?limit=1")

            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=self.config.api_timeout)

            if result.returncode == 0:
                assets_data = json.loads(result.stdout)
                total_assets = assets_data.get('total', 0)
                print(f"✅ Connected to Atlas API")
                print(f"📊 Database has {total_assets} assets")
            else:
                raise Exception(f"API connection test failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout connecting to Atlas API at {self.api_base_url}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response from API: {e}")
            raise
        except Exception as e:
            print(f"❌ Failed to connect to Atlas API at {self.api_base_url}: {e}")
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
                "ingested_by": "atlas_api_client_standalone",
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
                '-H', f'User-Agent: Atlas-Standalone-Client/3.0-{"Network" if self.use_network else "Local"}',
                '-d', json_data,
                '--silent',  # Suppress progress output
                '--show-error',  # Show errors
                '--fail',  # Fail silently on HTTP errors
                '--connect-timeout', str(self.config.api_timeout),
                '--max-time', str(self.config.api_timeout * 2)
            ]

            # Add SSL options for network mode
            if self.use_network and self.config.use_ssl:
                if not self.config.verify_ssl:
                    curl_cmd.extend(['-k'])  # --insecure flag
                curl_cmd.extend(['--ssl-reqd'])

            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=self.config.api_timeout)

            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                print(f"✅ Created asset: {response_data.get('name')} (ID: {response_data.get('id')})")
                return response_data

            elif result.returncode == 22:  # HTTP error (409, etc.)
                # Try to parse error response
                try:
                    error_data = json.loads(result.stderr) if result.stderr else "HTTP error"
                    if "already exists" in str(error_data):
                        print(f"⚠️ Asset already exists: {asset_data['name']}")
                        return None
                    else:
                        print(f"❌ HTTP error creating asset {asset_data['name']}: {error_data}")
                        return None
                except json.JSONDecodeError:
                    print(f"❌ HTTP error creating asset {asset_data['name']}: {result.stderr}")
                    return None
            else:
                print(f"❌ Curl failed creating asset {asset_data['name']}: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"❌ Timeout creating asset {asset_data['name']}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response creating asset {asset_data['name']}: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error creating asset {asset_data['name']}: {e}")
            return None

    def ingest_metadata_file(self, metadata_file_path: str) -> Optional[Dict[str, Any]]:
        """Ingest a single metadata.json file"""
        metadata_path = Path(metadata_file_path)

        if not metadata_path.exists():
            print(f"❌ Metadata file not found: {metadata_file_path}")
            return None

        if not metadata_path.name.endswith(('.json', '.metadata')):
            print(f"⚠️ File doesn't appear to be a metadata file: {metadata_file_path}")

        try:
            print(f"📄 Processing metadata file: {metadata_file_path}")

            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Validate required fields
            if not metadata.get('name'):
                print(f"❌ Missing required 'name' field in {metadata_file_path}")
                return None

            # Transform to asset format
            asset_data = self.transform_metadata_to_asset(metadata, str(metadata_path))

            # Create asset
            result = self.create_asset(asset_data)

            if result:
                print(f"🎉 Successfully ingested asset: {result['name']}")
                return result
            else:
                return None

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {metadata_file_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing {metadata_file_path}: {e}")
            return None


def call_atlas_api_ingestion(metadata_file_path: str, use_network: bool = False) -> bool:
    """
    Main function to ingest metadata via Atlas API
    Standalone version embedded directly in this module
    """
    try:
        mode = "Network" if use_network else "Local"
        print(f"📡 Starting {mode} API ingestion for: {metadata_file_path}")

        # Create API client and ingest
        client = AtlasAPIClient(use_network=use_network)
        result = client.ingest_metadata_file(metadata_file_path)

        if result:
            print("✅ API ingestion completed successfully!")
            return True
        else:
            print("❌ API ingestion failed")
            return False

    except Exception as e:
        print(f"❌ API ingestion error: {e}")
        import traceback
        traceback.print_exc()
        return False