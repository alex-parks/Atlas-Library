#!/usr/bin/env python3
"""
Blacksmith Atlas - Template-Based Asset Exporter (Standalone)
============================================================

Standalone version of the Template-Based Asset Exporter.
Extracted from the main Atlas codebase with complete functionality.

Author: Blacksmith VFX
Version: 3.0 (Standalone)
"""

import os
import sys
import json
import uuid
import re
import urllib.request
import subprocess
import traceback
import copy
import fnmatch
from datetime import datetime
from pathlib import Path
import shutil
import glob

# Try to import Houdini - will work when running inside Houdini
HOU_AVAILABLE = False
try:
    import hou
    HOU_AVAILABLE = True
except ImportError:
    print("⚠️  Houdini not available - running in standalone mode")

# Import Atlas configuration
try:
    from config_manager import get_network_config
    atlas_config = get_network_config()
    if atlas_config and atlas_config.asset_library_3d:
        print(f"✅ Atlas network configuration loaded successfully")
        print(f"📁 Library path: {atlas_config.asset_library_3d}")
    else:
        raise ValueError("Config loaded but missing required fields")
except (ImportError, ValueError) as e:
    print(f"⚠️  Could not load network Atlas config: {e}")
    print("⚠️  Using fallback configuration")
    atlas_config = None
    # Create a minimal fallback config
    class FallbackConfig:
        @property
        def asset_library_3d(self):
            return "/net/library/atlaslib/3D"
        @property
        def houdini_hda_path(self):
            return "/net/dev/alex.parks/scm/int/Blacksmith-Atlas/bl-atlas-houdini/otls/object_AtlasThumbnail.1.0.hda"
        @property
        def houdini_hda_type(self):
            return "AtlasThumbnail::1.0"
        @property
        def api_base_url(self):
            return "http://localhost:8000"
    atlas_config = FallbackConfig()

class TemplateAssetExporter:
    """Export assets using Houdini's template system"""
    
    def _sanitize_name_for_filesystem(self, name):
        """Sanitize asset name for filesystem and node naming (replace spaces and special chars with underscores)"""
        import re
        # Replace spaces, hyphens, and other problematic characters with underscores
        # Keep only alphanumeric characters and underscores
        sanitized = re.sub(r'[^\w]', '_', name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized
    
    def __init__(self, asset_name, subcategory="Props", description="", tags=None, asset_type=None, render_engine=None, metadata=None, action="create_new", parent_asset_id=None, variant_name=None, thumbnail_action="automatic", thumbnail_file_path="", export_no_references=False, bl_atlas_root=None):
        # Store the raw input for variants (will be overridden for variants)
        self.raw_input_name = asset_name
        self.subcategory = subcategory  
        self.description = description
        self.tags = tags or []
        self.asset_type = asset_type or "Assets"
        self.render_engine = render_engine or "Redshift"
        self.metadata = metadata or ""
        self.action = action
        self.parent_asset_id = parent_asset_id
        self.thumbnail_action = thumbnail_action  # automatic, choose, disable
        self.thumbnail_file_path = thumbnail_file_path  # path to custom thumbnail file
        self.export_no_references = export_no_references  # skip copying geometry and texture files
        self.bl_atlas_root = bl_atlas_root  # path to bl-atlas-houdini directory
        
        # Handle variant name - determine based on action
        if action == "create_new":
            self.variant_name = "default"
        elif action == "variant" and variant_name:
            self.variant_name = variant_name
        elif action == "version_up":
            # For version_up, copy variant_name from parent (will be looked up later)
            self.variant_name = None  # Will be set by _get_variant_name_from_parent()
        else:
            self.variant_name = "default"
        
        # Generate unique asset ID (11 character base UID + 3 digit version = 16 characters total)
        
        if action == "create_new":
            # Generate new 11-character base UID + 2-character variant + 3-digit version = 16 characters total
            self.base_uid = str(uuid.uuid4()).replace('-', '')[:11].upper()
            self.variant_id = "AA"  # Always start with AA variant for new assets
            self.version = 1
            # For new assets, use the provided name
            self.asset_name = asset_name
        elif action == "version_up":
            # For version_up: expects 13 characters (11 base + 2 variant)
            if not parent_asset_id or len(parent_asset_id) != 13:
                raise ValueError(f"Parent asset ID required for version_up and must be exactly 13 characters (11 base + 2 variant)")
            self.base_uid = parent_asset_id[:11].upper()  # First 11 characters as base UID
            self.variant_id = parent_asset_id[11:13].upper()  # Characters 11-13 as variant ID
            self.version = self._get_next_version(parent_asset_id, action)  # Pass full 13-char asset ID
            # For version_up, inherit the original asset name (not the version name)
            self.asset_name = self._get_original_asset_name_from_base_uid(self.base_uid)
        elif action == "variant":
            # For variant: expects 11 characters (base UID only)
            if not parent_asset_id or len(parent_asset_id) != 11:
                raise ValueError(f"Parent asset ID required for variant and must be exactly 11 characters (base UID)")
            self.base_uid = parent_asset_id.upper()  # Use the 11-character base UID
            # Generate next variant ID based on existing variants for this base UID
            self.variant_id = self._get_next_variant_id(self.base_uid)
            self.version = 1  # Reset version to 001 for new variant
            # For variants, use the original asset name from the base UID, not the variant name
            self.asset_name = self._get_original_asset_name_from_base_uid(self.base_uid)
        else:
            raise ValueError(f"Invalid action: {action}. Must be 'create_new', 'version_up', or 'variant'")
        
        # Create full 16-character asset ID (11 base + 2 variant + 3 version)
        self.asset_id = f"{self.base_uid}{self.variant_id}{self.version:03d}"
        
        # The 13-character asset ID (without version) for referencing
        self.asset_base_id = f"{self.base_uid}{self.variant_id}"
        
        # Set variant_name for version_up if not already set
        if action == "version_up" and self.variant_name is None:
            self.variant_name = self._get_variant_name_from_parent(parent_asset_id)
        
        # Sanitize asset name for display purposes only
        self.sanitized_asset_name = re.sub(r'[^a-zA-Z0-9_-]', '_', asset_name)
        
        # Set up paths based on hierarchy structure using Atlas config
        self.library_root = Path(atlas_config.asset_library_3d)
        
        # Create proper directory structure based on asset type and subcategory
        # Convert subcategory names to folder names
        subcategory_folder_map = {
            "Blacksmith Asset": "BlacksmithAssets",
            "Megascans": "Megascans", 
            "Kitbash": "Kitbash",
            "Blacksmith FX": "BlacksmithFX",
            "Atmosphere": "Atmosphere",
            "FLIP": "FLIP", 
            "Pyro": "Pyro",
            "Blacksmith Materials": "BlacksmithMaterials",
            "Redshift": "Redshift",
            "Karma": "Karma",
            "Blacksmith HDAs": "BlacksmithHDAs"
        }
        
        subcategory_folder = subcategory_folder_map.get(subcategory, subcategory.replace(" ", ""))
        
        # Asset folder is named with the full 16-character UID
        self.asset_folder = self.library_root / asset_type / subcategory_folder / self.asset_id
        self.data_folder = self.asset_folder / "Data"
        self.textures_folder = self.asset_folder / "Textures"
        self.geometry_folder = self.asset_folder / "Geometry"
        self.thumbnail_folder = self.asset_folder / "Thumbnail"
        
        # Database key is the full 16-character UID
        self.database_key = self.asset_id
    
    def _collect_all_nodes(self, parent_node):
        """Recursively collect all nodes from a parent node"""
        all_nodes = []
        
        def collect_recursive(node):
            """Recursively collect all nodes"""
            for child in node.children():
                all_nodes.append(child)
                collect_recursive(child)  # Recurse into children
        
        collect_recursive(parent_node)
        return all_nodes

    def _get_artist_name(self):
        """Extract artist name from POSE environment variable or fallback to USER"""
        try:
            # Try to get from Houdini POSE variable first
            if HOU_AVAILABLE:
                try:
                    pose_path = hou.expandString("$POSE")
                    if pose_path and "/net/users/linux/" in pose_path:
                        # Extract username from path like "/net/users/linux/alex.parks/houdini20.5/poselib"
                        parts = pose_path.split("/")
                        for i, part in enumerate(parts):
                            if part == "linux" and i + 1 < len(parts):
                                # Next part after "linux" should be the username
                                username = parts[i + 1]
                                if username and username != "":
                                    print(f"   👤 Artist extracted from POSE: {username}")
                                    return username
                except Exception as e:
                    print(f"   ⚠️ Could not extract artist from POSE: {e}")
                    pass
            
            # Fallback to standard environment variables
            fallback_user = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
            print(f"   👤 Artist from environment fallback: {fallback_user}")
            return fallback_user
        except:
            return 'unknown'
    
    def _get_next_version(self, asset_base_id, action):
        """Get the next version number for version up or variant actions"""
        try:
            if action == "version_up":
                # Query the Atlas API to find existing versions for this asset (14-char base + variant)
                print(f"   🔍 Looking up existing versions for asset base ID: {asset_base_id}")
                
                try:
                    
                    # Query the Atlas API to get all assets
                    api_url = f"{atlas_config.api_base_url}/api/v1/assets?limit=1000"
                    print(f"   🌐 Making API request to: {api_url}")
                    
                    response = urllib.request.urlopen(api_url, timeout=30)
                    assets_data = json.loads(response.read().decode())
                    all_assets = assets_data.get('items', [])
                    
                    print(f"   📊 Found {len(all_assets)} total assets in database")
                    
                    # Filter assets that match the asset base ID (first 13 characters: 11 base + 2 variant)
                    matching_assets = []
                    for asset in all_assets:
                        asset_id = asset.get('id', '')
                        if len(asset_id) >= 13 and asset_id[:13].upper() == asset_base_id.upper():
                            matching_assets.append(asset)
                            print(f"   ✅ Found matching asset: {asset_id}")
                    
                    print(f"   📊 Total matching assets: {len(matching_assets)}")
                    
                    if not matching_assets:
                        print(f"   ❌ No existing versions found for asset base ID: {asset_base_id}")
                        print(f"   ⚠️ Asset not found in database - cannot version up")
                        # This will trigger an error in Houdini
                        raise ValueError(f"No Asset Found: {asset_base_id} not found in database")
                    
                    # Parse version numbers from matching assets
                    existing_versions = []
                    for asset in matching_assets:
                        asset_id = asset.get('id', '')
                        if len(asset_id) == 16:  # 16-character UIDs now
                            try:
                                version_str = asset_id[-3:]  # Last 3 characters are version
                                version_num = int(version_str)
                                existing_versions.append(version_num)
                                print(f"   ✅ Parsed version {version_num:03d} from {asset_id}")
                            except ValueError:
                                print(f"   ⚠️ Invalid version format in asset ID: {asset_id} (last 3: '{asset_id[-3:]}')")
                        else:
                            print(f"   ⚠️ Asset ID wrong length: {asset_id} (expected 14, got {len(asset_id)})")
                    
                    # Calculate next version number
                    next_version = max(existing_versions) + 1 if existing_versions else 1
                    print(f"   📊 Existing versions: {existing_versions}")
                    print(f"   🔢 Next version calculated: {next_version}")
                    
                    return next_version
                    
                except ValueError as ve:
                    # Re-raise ValueError to trigger proper error in Houdini
                    raise ve
                except Exception as api_error:
                    print(f"   ❌ API lookup failed: {api_error}")
                    print(f"   ⚠️ Falling back to version 1")
                    return 1
                
            elif action == "variant":
                # For variants, use same logic as version_up for now
                return self._get_next_version(asset_base_id, "version_up")
            else:
                return 1
                
        except ValueError as ve:
            # Re-raise ValueError for proper error handling
            raise ve
        except Exception as e:
            print(f"   ⚠️ Error getting next version, defaulting to 1: {e}")
            return 1
    
    def _get_next_variant_id(self, base_uid):
        """Get the next variant ID using letter-based incrementation (AA->AB->AC...->AZ->BA)"""
        try:
            print(f"   🔍 Getting next variant ID for base: {base_uid}")
            
            # Query the Atlas API to find all existing variants for this base UID
            try:
                
                # Query the Atlas API to get all assets
                api_url = f"{atlas_config.api_base_url}/api/v1/assets?limit=1000"
                print(f"   🌐 Making API request to: {api_url}")
                
                response = urllib.request.urlopen(api_url, timeout=30)
                assets_data = json.loads(response.read().decode())
                all_assets = assets_data.get('items', [])
                
                print(f"   📊 Found {len(all_assets)} total assets in database")
                
                # Filter assets that match the base UID (first 11 characters)
                matching_variants = set()
                print(f"   🔍 Searching for base UID: '{base_uid.upper()}'")
                
                for asset in all_assets:
                    asset_id = asset.get('id', '')
                    if len(asset_id) >= 13:
                        asset_base = asset_id[:11].upper()
                        if asset_base == base_uid.upper():
                            variant_id = asset_id[11:13].upper()
                            matching_variants.add(variant_id)
                            print(f"   ✅ Found variant: {variant_id} in asset {asset_id}")
                        else:
                            # Debug: show first few non-matching assets
                            if len(matching_variants) == 0:
                                print(f"   ❌ Asset {asset_id[:20]}... doesn't match base '{base_uid.upper()}' (got '{asset_base}')")
                
                print(f"   📊 All existing variants for {base_uid}: {sorted(matching_variants)}")
                print(f"   🔢 Total matching variants found: {len(matching_variants)}")
                
                # Generate next variant ID using letter logic
                next_variant = self._increment_variant_id(matching_variants)
                print(f"   🔢 Next variant calculated: {next_variant}")
                
                return next_variant
                
            except Exception as api_error:
                print(f"   ❌ API lookup failed: {api_error}")
                # Fallback: start with AB (assuming AA exists)
                return "AB"
                
        except Exception as e:
            print(f"   ⚠️ Error getting next variant, falling back to AB: {e}")
            return "AB"
    
    def _increment_variant_id(self, existing_variants):
        """Generate the next available variant ID using AA->AB->AC...->AZ->BA logic"""
        print(f"   🔢 _increment_variant_id called with: {existing_variants}")
        
        # Start with AA if no variants exist
        if not existing_variants:
            print(f"   ✅ No existing variants, starting with AA")
            return "AA"
        
        # Convert existing variants to numbers for easier processing
        variant_numbers = []
        for variant in existing_variants:
            if len(variant) == 2:
                first_char = ord(variant[0]) - ord('A')
                second_char = ord(variant[1]) - ord('A')
                variant_num = first_char * 26 + second_char
                variant_numbers.append(variant_num)
                print(f"   🔢 Variant '{variant}' -> number {variant_num}")
        
        print(f"   🔢 All variant numbers: {sorted(variant_numbers)}")
        
        # Find the next available number
        variant_numbers.sort()
        next_num = 0
        while next_num in variant_numbers:
            print(f"   🔍 Checking number {next_num} - already exists, incrementing")
            next_num += 1
        
        print(f"   ✅ Next available number: {next_num}")
        
        # Convert back to letters
        first_char = chr(ord('A') + (next_num // 26))
        second_char = chr(ord('A') + (next_num % 26))
        
        result = f"{first_char}{second_char}"
        print(f"   🔢 Next variant ID: {result} (from number {next_num})")
        
        return result
    
    def _increment_single_variant_id(self, current_variant):
        """Increment a single variant ID (fallback method)"""
        if len(current_variant) != 2:
            return "AB"
        
        first_char = current_variant[0]
        second_char = current_variant[1]
        
        # Increment second character first
        if second_char < 'Z':
            return f"{first_char}{chr(ord(second_char) + 1)}"
        elif first_char < 'Z':
            return f"{chr(ord(first_char) + 1)}A"
        else:
            # Wrap around (shouldn't happen in practice)
            return "AA"
    
    def _get_variant_name_from_parent(self, parent_asset_id):
        """Get the variant_name from the parent asset for version_up actions"""
        try:
            print(f"   🔍 Looking up variant_name for parent asset: {parent_asset_id}")
            
            
            # Query the Atlas API to get all assets and find ones matching the 14-char pattern
            api_url = "http://localhost:8000/api/v1/assets?limit=1000"
            print(f"   🌐 Making API request to: {api_url}")
            
            response = urllib.request.urlopen(api_url, timeout=30)
            assets_data = json.loads(response.read().decode())
            all_assets = assets_data.get('items', [])
            
            # Find assets that match the 13-character pattern (ignore version)
            matching_assets = []
            for asset in all_assets:
                asset_id = asset.get('id', '')
                if len(asset_id) >= 13 and asset_id[:13].upper() == parent_asset_id.upper():
                    matching_assets.append(asset)
            
            if matching_assets:
                # Use the first matching asset (they should all have the same variant_name)
                variant_name = matching_assets[0].get('variant_name', 'default')
                print(f"   ✅ Found variant_name: {variant_name} from asset {matching_assets[0].get('id')}")
                return variant_name
            else:
                print(f"   ⚠️ No matching assets found for pattern: {parent_asset_id}")
                return "default"
            
        except Exception as e:
            print(f"   ⚠️ Error getting parent variant_name, defaulting to 'default': {e}")
            return "default"
    
    def _get_original_asset_name_from_base_uid(self, base_uid):
        """Get the original asset name from the base UID for variant creation"""
        try:
            print(f"   🔍 Looking up original asset name for base UID: {base_uid}")
            
            # Query the Atlas API to get all assets and find the original (AA variant)
            api_url = "http://localhost:8000/api/v1/assets?limit=1000"
            print(f"   🌐 Making API request to: {api_url}")
            
            response = urllib.request.urlopen(api_url, timeout=30)
            assets_data = json.loads(response.read().decode())
            all_assets = assets_data.get('items', [])
            
            # Find assets that match the base UID (first 11 characters) and are original (variant AA)
            original_asset = None
            for asset in all_assets:
                asset_id = asset.get('id', '')
                if len(asset_id) >= 13:
                    asset_base_uid = asset_id[:11].upper()
                    asset_variant_id = asset_id[11:13].upper()
                    if asset_base_uid == base_uid.upper() and asset_variant_id == "AA":
                        original_asset = asset
                        print(f"   ✅ Found original asset (AA variant): {asset_id}")
                        break
            
            if original_asset:
                original_name = original_asset.get('name', f'Asset_{base_uid}')
                print(f"   ✅ Original asset name: {original_name}")
                return original_name
            else:
                print(f"   ⚠️ No original asset (AA variant) found for base UID: {base_uid}")
                return f"Asset_{base_uid}"
            
        except Exception as e:
            print(f"   ⚠️ Error getting original asset name, using fallback: {e}")
            return f"Asset_{base_uid}"

    def _get_parent_branded_status(self):
        """Get the branded status from the parent asset for inheritance"""
        try:
            if not self.parent_asset_id:
                return None
                
            print(f"   🔍 Looking up branded status for parent asset: {self.parent_asset_id}")
            
            # For variants, we need to find the original asset (AA variant) with the base UID
            # For versions, we need to find the previous version
            if self.action == "variant":
                # For variants, find the original asset (AA variant) from the base UID
                base_uid = self.parent_asset_id  # This is the 11-character base UID
                target_asset_id = f"{base_uid}AA001"  # Original asset format
                print(f"   🔍 Variant inheritance: Looking for original asset {target_asset_id}")
            elif self.action == "create_version" or self.action == "version_up":
                # For versions, parent_asset_id is base_uid + variant_id (14 chars)
                # We need to find the previous version by appending version number
                if len(self.parent_asset_id) == 13:
                    # Calculate previous version number
                    current_version = self.version
                    prev_version = current_version - 1 if current_version > 1 else 1
                    target_asset_id = f"{self.parent_asset_id}{prev_version:03d}"
                    print(f"   🔍 Version inheritance: Looking for previous version {target_asset_id}")
                else:
                    # If parent_asset_id is already full 14-char ID, use it directly
                    target_asset_id = self.parent_asset_id
                    print(f"   🔍 Version inheritance: Looking for parent asset {target_asset_id}")
            else:
                # Default case
                target_asset_id = self.parent_asset_id
                print(f"   🔍 Default inheritance: Looking for parent asset {target_asset_id}")
            
            # Query the Atlas API to get all assets and find the target
            api_url = f"{atlas_config.api_base_url}/api/v1/assets?limit=1000"
            print(f"   🌐 Making API request to: {api_url}")
            
            response = urllib.request.urlopen(api_url, timeout=30)
            assets_data = json.loads(response.read().decode())
            all_assets = assets_data.get('items', [])
            
            # Find the target asset
            target_asset = None
            for asset in all_assets:
                asset_id = asset.get('id', '')
                if asset_id == target_asset_id:
                    target_asset = asset
                    print(f"   ✅ Found target asset: {asset_id}")
                    break
            
            if target_asset:
                # Check for branded status in multiple locations
                branded_status = (
                    target_asset.get('branded') or
                    target_asset.get('metadata', {}).get('branded') or
                    target_asset.get('metadata', {}).get('export_metadata', {}).get('branded') or
                    False
                )
                print(f"   ✅ Target asset branded status: {branded_status}")
                return branded_status
            else:
                print(f"   ⚠️ Target asset not found: {target_asset_id}")
                return None
                
        except Exception as e:
            print(f"   ⚠️ Error getting parent branded status: {e}")
            return None

    def _get_branded_status(self):
        """Get branded status, inheriting from parent for versions/variants"""
        try:
            # First check if branded status is explicitly set in metadata
            if isinstance(self.metadata, dict) and "branded" in self.metadata:
                branded_status = self.metadata.get("branded", False)
                print(f"   🏷️ Using explicit branded status: {branded_status}")
                return branded_status
            
            # For versions and variants, inherit from parent
            if self.action in ["create_version", "version_up", "variant"] and self.parent_asset_id:
                parent_branded_status = self._get_parent_branded_status()
                if parent_branded_status is not None:
                    print(f"   🏷️ Inherited branded status from parent: {parent_branded_status}")
                    return parent_branded_status
            
            # Default to False for new assets
            print(f"   🏷️ Using default branded status: False")
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error determining branded status: {e}")
            return False

    def _build_export_metadata(self):
        """Build export metadata including essential variant information"""
        try:
            # Start with structured metadata if it exists as dict
            export_metadata = {}
            if isinstance(self.metadata, dict):
                export_metadata.update(self.metadata)
            
            # Always include essential information for API consumption
            essential_metadata = {
                "dimension": "3D",
                "asset_type": self.asset_type,
                "subcategory": self.subcategory,
                "render_engine": self.render_engine,
                "houdini_version": "Unknown",
                "export_time": datetime.now().isoformat(),
                "tags": self.tags,
                "action": self.action,
                "parent_asset_id": self.parent_asset_id,
                "branded": False,
                "thumbnail_action": self.thumbnail_action,
                "thumbnail_file_path": self.thumbnail_file_path if self.thumbnail_action == "choose" else None,
                "export_no_references": self.export_no_references
            }
            
            # Get Houdini version if available
            if HOU_AVAILABLE:
                try:
                    version_tuple = hou.applicationVersion()
                    essential_metadata["houdini_version"] = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
                except:
                    try:
                        essential_metadata["houdini_version"] = hou.applicationVersionString()
                    except:
                        pass
            
            # Add variant information (crucial for API response)
            if self.variant_name and self.variant_name != "default":
                essential_metadata["variant_name"] = self.variant_name
            
            # Inherit branded status from parent asset for versions/variants
            if self.action in ["create_version", "version_up", "variant"] and self.parent_asset_id:
                parent_branded_status = self._get_parent_branded_status()
                if parent_branded_status is not None:
                    essential_metadata["branded"] = parent_branded_status
                    print(f"   🏷️ Inherited branded status from parent: {parent_branded_status}")
            
            # Update export_metadata with essential info (existing values take precedence)
            for key, value in essential_metadata.items():
                if key not in export_metadata:
                    export_metadata[key] = value
                    
            print(f"   📋 Built export_metadata with variant_name: {export_metadata.get('variant_name', 'None')}")
            return export_metadata
            
        except Exception as e:
            print(f"   ⚠️ Error building export metadata: {e}")
            return {}
    
    def load_and_configure_render_hda(self, parent_node, nodes_to_export, metadata):
        """Load the render farm HDA and configure it with Atlas asset information"""
        try:
            if not HOU_AVAILABLE:
                print("❌ Houdini not available - cannot load HDA")
                return False
            
            # Get HDA path from Atlas configuration
            hda_path = atlas_config.houdini_hda_path
            print(f"   🔍 Looking for HDA at: {hda_path}")
            
            # Check if HDA file exists
            if not os.path.exists(hda_path):
                print(f"   ❌ HDA not found at: {hda_path}")
                print(f"   🔍 Please verify the file exists and path is correct")
                return False
            
            print(f"   ✅ HDA file found: {hda_path}")
            
            # Install the HDA definition if not already loaded
            hda_installed = False
            try:
                # Try to install the HDA
                hou.hda.installFile(hda_path)
                hda_installed = True
                print(f"   📦 HDA installed from: {hda_path}")
            except Exception as e:
                print(f"   ⚠️ Could not install HDA: {e}")
                # Continue anyway - maybe it's already installed
            
            # Get HDA type name from Atlas configuration
            hda_type_name = atlas_config.houdini_hda_type
            print(f"   🔍 Looking for HDA type: {hda_type_name}")
            
            # Try to find the HDA type
            try:
                # First, let's see what HDA types are available
                print(f"   🔍 Checking available HDA types in Object category...")
                obj_category = hou.objNodeTypeCategory()
                hda_definition = obj_category.nodeType(hda_type_name)
                
                if not hda_definition:
                    print(f"   ⚠️ HDA type '{hda_type_name}' not found in Object category")
                    # Try in other categories
                    print(f"   🔍 Searching in other categories...")
                    category_functions = [
                        ("Driver", hou.ropNodeTypeCategory),
                        ("Rop", hou.ropNodeTypeCategory), 
                        ("Sop", hou.sopNodeTypeCategory),
                        ("Shop", hou.shopNodeTypeCategory),
                        ("Vop", hou.vopNodeTypeCategory)
                    ]
                    
                    for category_name, category_func in category_functions:
                        try:
                            category = category_func()
                            hda_definition = category.nodeType(hda_type_name)
                            if hda_definition:
                                print(f"   ✅ Found HDA type in {category_name} category")
                                break
                            else:
                                print(f"   🔍 Not found in {category_name} category")
                        except Exception as e:
                            print(f"   ⚠️ Error checking {category_name} category: {e}")
                
                if not hda_definition:
                    print(f"   ❌ Could not find HDA type: {hda_type_name}")
                    print(f"   💡 Try checking the HDA type name in the Type Properties")
                    print(f"   💡 Common formats: 'namespace::name::version' or just 'name::version'")
                    
                    # List available HDAs to help debug
                    print(f"   🔍 Available HDAs in Object category:")
                    try:
                        obj_types = obj_category.nodeTypes()
                        hda_types = [nt.name() for nt in obj_types.values() if nt.definition() and nt.definition().libraryFilePath()]
                        if hda_types:
                            for hda in hda_types[:10]:  # Show first 10
                                print(f"      - {hda}")
                            if len(hda_types) > 10:
                                print(f"      ... and {len(hda_types) - 10} more")
                        else:
                            print(f"      (No HDAs found in Object category)")
                    except Exception as e:
                        print(f"      Error listing HDAs: {e}")
                    
                    return False
                else:
                    print(f"   ✅ Found HDA definition: {hda_definition.name()}")
                    
            except Exception as e:
                print(f"   ⚠️ Error finding HDA type: {e}")
                return False
            
            # Create an instance of the HDA
            try:
                # Create HDA right next to (as sibling of) the exported node
                hda_parent = parent_node.parent()
                if hda_parent is None:
                    # If parent is None, we're at root level, use /obj
                    hda_parent = hou.node("/obj")
                
                print(f"   📍 Creating HDA as sibling to {parent_node.name()} in {hda_parent.path()}")
                
                # Sanitize asset name for node naming (replace spaces and special chars with underscores)
                sanitized_asset_name = self._sanitize_name_for_filesystem(self.asset_name)
                hda_node_name = f"render_{sanitized_asset_name}_{self.asset_id}"
                hda_node = hda_parent.createNode(hda_type_name, node_name=hda_node_name)
                
                # Position the HDA node right below the exported asset node
                try:
                    export_pos = parent_node.position()
                    hda_node.setPosition([export_pos[0], export_pos[1] - 1.0])  # Place 1 unit below
                    print(f"   📍 Positioned HDA below exported asset at {hda_node.position()}")
                except Exception as e:
                    print(f"   ⚠️ Could not position HDA node: {e}")
                
                print(f"   🎬 Created HDA node: {hda_node.path()}")
                
            except Exception as e:
                print(f"   ❌ Failed to create HDA node: {e}")
                return False
            
            # Configure HDA parameters with Atlas asset information
            try:
                # REQUIRED PARAMETER 1: assetname (string) - Name of the asset
                if hda_node.parm("assetname"):
                    hda_node.parm("assetname").set(self.asset_name)
                    print(f"      ✅ Set assetname: {self.asset_name}")
                
                # REQUIRED PARAMETER 2: atlasassetpath (string) - Relative Houdini path to exported subnet
                if hda_node.parm("atlasassetpath"):
                    # Create relative path to the exported asset node (e.g., "../Helicopter")
                    atlas_asset_path = f"../{parent_node.name()}"
                    hda_node.parm("atlasassetpath").set(atlas_asset_path)
                    print(f"      ✅ Set atlasassetpath: {atlas_asset_path}")
                
                # REQUIRED PARAMETER 3: thumbnailpath (string) - Full path to Thumbnail folder
                thumbnail_path_valid = False
                if hda_node.parm("thumbnailpath"):
                    hda_node.parm("thumbnailpath").set(str(self.thumbnail_folder))
                    print(f"      ✅ Set thumbnailpath: {self.thumbnail_folder}")
                    
                    # Check if thumbnail path is valid (folder exists and is an actual asset thumbnail folder)
                    if self.thumbnail_folder.exists() and self.thumbnail_folder.is_dir():
                        thumbnail_path_valid = True
                        print(f"      ✅ Thumbnail path is valid: {self.thumbnail_folder}")
                    else:
                        print(f"      ⚠️  Thumbnail path does not exist: {self.thumbnail_folder}")
                
                # Store HDA node and thumbnail path validity for later execution
                self._hda_node = hda_node
                self._thumbnail_path_valid = thumbnail_path_valid
                
                # Legacy parameters (keep for backward compatibility)
                if hda_node.parm("asset_name"):
                    hda_node.parm("asset_name").set(self.asset_name)
                    print(f"      ✅ Set asset_name: {self.asset_name}")
                
                if hda_node.parm("asset_id"):
                    hda_node.parm("asset_id").set(self.asset_id)
                    print(f"      ✅ Set asset_id: {self.asset_id}")
                
                if hda_node.parm("asset_folder"):
                    hda_node.parm("asset_folder").set(str(self.asset_folder))
                    print(f"      ✅ Set asset_folder: {self.asset_folder}")
                
                if hda_node.parm("template_file"):
                    render_engine_lower = self.render_engine.lower()
                    template_file_path = str(self.asset_folder / f"template_{render_engine_lower}.hip")
                    hda_node.parm("template_file").set(template_file_path)
                    print(f"      ✅ Set template_file: template_{render_engine_lower}.hip")
                
                if hda_node.parm("render_engine"):
                    hda_node.parm("render_engine").set(self.render_engine)
                    print(f"      ✅ Set render_engine: {self.render_engine}")
                
                if hda_node.parm("subcategory"):
                    hda_node.parm("subcategory").set(self.subcategory)
                    print(f"      ✅ Set subcategory: {self.subcategory}")
                
                if hda_node.parm("asset_type"):
                    hda_node.parm("asset_type").set(self.asset_type)
                    print(f"      ✅ Set asset_type: {self.asset_type}")
                
                # Set metadata as JSON string if HDA has a metadata parameter
                if hda_node.parm("metadata"):
                    metadata_json = json.dumps(metadata, indent=2)
                    hda_node.parm("metadata").set(metadata_json)
                    print(f"      ✅ Set metadata JSON ({len(metadata_json)} chars)")
                
                # Set additional parameters you might have in your HDA
                if hda_node.parm("description"):
                    hda_node.parm("description").set(self.description)
                    print(f"      ✅ Set description: {self.description}")
                
                if hda_node.parm("tags") and self.tags:
                    tags_str = ", ".join(self.tags)
                    hda_node.parm("tags").set(tags_str)
                    print(f"      ✅ Set tags: {tags_str}")
                
                # Set thumbnail folder path (for saving thumbnails)
                if hda_node.parm("thumbnail_folder"):
                    hda_node.parm("thumbnail_folder").set(str(self.thumbnail_folder))
                    print(f"      ✅ Set thumbnail_folder: {self.thumbnail_folder}")
                
                # Set expected thumbnail file path
                # Sanitize asset name for file naming (replace spaces and special chars with underscores)
                sanitized_asset_name = self._sanitize_name_for_filesystem(self.asset_name)
                expected_thumbnail = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.png"
                if hda_node.parm("thumbnail_path"):
                    hda_node.parm("thumbnail_path").set(str(expected_thumbnail))
                    print(f"      ✅ Set thumbnail_path: {expected_thumbnail.name}")
                
                # 🎯 SET FRAME RANGE PARAMETERS (NEW!)
                if hda_node.parm("framein"):
                    hda_node.parm("framein").set(self.framein)
                    print(f"      🎯 Set framein: {self.framein}")
                else:
                    print(f"      ⚠️ No framein parameter found on HDA")
                
                if hda_node.parm("frameout"):
                    hda_node.parm("frameout").set(self.frameout)
                    print(f"      🎯 Set frameout: {self.frameout}")
                else:
                    print(f"      ⚠️ No frameout parameter found on HDA")
                
                print(f"   ✅ HDA parameters configured successfully (including frame range {self.framein}-{self.frameout})")
                return True
                
            except Exception as e:
                print(f"   ❌ Failed to configure HDA parameters: {e}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error loading render HDA: {e}")
            traceback.print_exc()
            return False

    def copy_custom_thumbnail(self):
        """Copy user-selected thumbnail file(s) to the thumbnail folder"""
        try:
            if not self.thumbnail_file_path or not self.thumbnail_file_path.strip():
                print(f"   ❌ No thumbnail file path provided")
                return False
            
            from pathlib import Path
            import shutil
            import re
            import glob
            
            thumbnail_path_str = self.thumbnail_file_path.strip()
            print(f"   📁 Processing thumbnail path: {thumbnail_path_str}")
            
            # Check for Houdini-style frame variables
            houdini_frame_patterns = [
                r'\$F\d*',    # $F, $F4, $F04, etc.
                r'\$SF',      # $SF (sub-frame)
                r'#{2,}',     # ##, ####, etc.
                r'%\d*d',     # %04d, %d, etc.
            ]
            
            is_sequence = any(re.search(pattern, thumbnail_path_str) for pattern in houdini_frame_patterns)
            
            if is_sequence:
                print(f"   🎬 Detected sequence pattern in: {thumbnail_path_str}")
                
                # Handle Houdini frame variables by expanding them
                parent_dir = Path(thumbnail_path_str).parent
                filename = Path(thumbnail_path_str).name
                
                # Convert Houdini patterns to glob patterns more precisely
                glob_pattern = filename
                
                # Replace Houdini frame variables with specific wildcard patterns
                # $F -> * but more specifically looking for numbers
                if '$F' in glob_pattern:
                    # For patterns like "name.$F.exr", we want to match "name.1001.exr", "name.1142.exr", etc.
                    glob_pattern = re.sub(r'\$F\d*', '*', glob_pattern)
                
                glob_pattern = re.sub(r'\$SF', '*', glob_pattern)        # $SF -> *
                glob_pattern = re.sub(r'#{2,}', '*', glob_pattern)       # #### -> *
                glob_pattern = re.sub(r'%\d*d', '*', glob_pattern)       # %04d -> *
                
                print(f"   🔍 Searching for files matching: {parent_dir / glob_pattern}")
                
                # Find matching files
                sequence_files = []
                if parent_dir.exists():
                    try:
                        # Use glob to find all matching files
                        all_matches = list(parent_dir.glob(glob_pattern))
                        
                        # Filter to only include files that have numeric frame numbers
                        for match in all_matches:
                            # Check if the file has a frame number pattern (3+ digits)
                            if re.search(r'\.\d{3,6}\.', match.name) or re.search(r'_\d{3,6}\.', match.name):
                                sequence_files.append(match)
                        
                        print(f"   📁 Found {len(sequence_files)} potential sequence files")
                        
                        # Sort files by frame number
                        def extract_frame_number(filepath):
                            """Extract frame number from filename - look for 3+ digit sequences"""
                            # Look for patterns like .1001. or _1001. or just 1001 at the end
                            matches = re.findall(r'[\._](\d{3,6})[\._]', filepath.name)
                            if matches:
                                return int(matches[-1])  # Use the last match (typically the frame number)
                            
                            # Fallback: look for any 3+ digit number
                            matches = re.findall(r'(\d{3,6})', filepath.name)
                            if matches:
                                return int(matches[-1])
                            
                            return 0
                        
                        try:
                            sequence_files.sort(key=extract_frame_number)
                            print(f"   📊 Sorted sequence files by frame number")
                        except:
                            sequence_files.sort()  # Fallback to alphabetical sort
                            print(f"   📊 Sorted sequence files alphabetically (frame number sort failed)")
                        
                    except Exception as e:
                        print(f"   ⚠️ Error during file search: {e}")
                        sequence_files = []
                
                if sequence_files:
                    print(f"   📁 Found sequence with {len(sequence_files)} files")
                    files_to_copy = sequence_files
                else:
                    print(f"   ❌ No files found matching pattern: {thumbnail_path_str}")
                    return False
            else:
                # Single file or existing path
                thumbnail_path = Path(thumbnail_path_str)
                if thumbnail_path.exists():
                    files_to_copy = [thumbnail_path]
                    print(f"   📄 Single file detected: {thumbnail_path}")
                else:
                    print(f"   ❌ Thumbnail file not found: {thumbnail_path}")
                    return False
            
            # Ensure thumbnail folder exists
            self.thumbnail_folder.mkdir(parents=True, exist_ok=True)
            sanitized_asset_name = self._sanitize_name_for_filesystem(self.asset_name)
            
            # Copy files
            copied_count = 0
            for i, file_to_copy in enumerate(files_to_copy):
                if len(files_to_copy) == 1:
                    # Single file - determine target name
                    if file_to_copy.suffix.lower() == '.exr':
                        target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.png"
                    else:
                        target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail{file_to_copy.suffix}"
                else:
                    # Sequence - preserve original frame numbers exactly as they appear
                    # Extract frame number from original filename (look for 3-6 digit sequences)
                    frame_match = re.search(r'\.(\d{3,6})\.', file_to_copy.name)
                    if frame_match:
                        frame_num = frame_match.group(1)  # Keep original padding (1001, 1142, etc.)
                        if file_to_copy.suffix.lower() == '.exr':
                            target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.{frame_num}.png"
                        else:
                            target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.{frame_num}{file_to_copy.suffix}"
                    else:
                        # Fallback: look for any number in the filename
                        number_match = re.search(r'(\d{3,6})', file_to_copy.stem)
                        if number_match:
                            frame_num = number_match.group(1)
                            if file_to_copy.suffix.lower() == '.exr':
                                target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.{frame_num}.png"
                            else:
                                target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.{frame_num}{file_to_copy.suffix}"
                        else:
                            # Last resort: sequential numbering
                            if file_to_copy.suffix.lower() == '.exr':
                                target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.{i+1:04d}.png"
                            else:
                                target_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.{i+1:04d}{file_to_copy.suffix}"
                
                # Handle EXR conversion
                if file_to_copy.suffix.lower() == '.exr':
                    print(f"   🎨 Converting EXR: {file_to_copy.name} -> {target_file.name}")
                    success = self._convert_exr_to_png(file_to_copy, target_file)
                    if success:
                        copied_count += 1
                    else:
                        print(f"   ⚠️ EXR conversion failed, copying as-is: {file_to_copy.name}")
                        # Fallback: copy original EXR
                        fallback_target = target_file.with_suffix('.exr')
                        shutil.copy2(file_to_copy, fallback_target)
                        copied_count += 1
                else:
                    print(f"   📋 Copying: {file_to_copy.name} -> {target_file.name}")
                    shutil.copy2(file_to_copy, target_file)
                    copied_count += 1
            
            print(f"   ✅ Successfully copied {copied_count} thumbnail files to {self.thumbnail_folder}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error copying custom thumbnail: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _convert_exr_to_png(self, exr_path, png_path, max_size=None):
        """Convert EXR file to PNG for web display"""
        try:
            # Try multiple libraries for EXR support
            converted = False
            
            # Method 1: Try OpenImageIO (most professional)
            try:
                import OpenImageIO as oiio
                
                print(f"   🔧 Using OpenImageIO for EXR conversion")
                
                # Read EXR
                input_image = oiio.ImageInput.open(str(exr_path))
                if not input_image:
                    raise Exception(f"Could not open {exr_path}")
                
                spec = input_image.spec()
                width, height = spec.width, spec.height
                channels = spec.nchannels
                
                # Read pixels
                pixels = input_image.read_image(oiio.FLOAT)
                input_image.close()
                
                if pixels is None:
                    raise Exception("Could not read pixel data")
                
                # Convert to numpy array and handle tone mapping
                import numpy as np
                image_array = np.array(pixels).reshape(height, width, channels)
                
                # Simple tone mapping for HDR -> LDR conversion
                # Gamma correction and exposure adjustment
                exposure = 0.0  # Can adjust this based on image content
                image_array = image_array * (2.0 ** exposure)  # Exposure
                image_array = np.power(image_array, 1.0/2.2)   # Gamma correction
                image_array = np.clip(image_array, 0.0, 1.0)   # Clamp to [0,1]
                
                # Convert to 8-bit
                image_array = (image_array * 255).astype(np.uint8)
                
                # Handle different channel counts and preserve alpha
                if channels >= 4:
                    # RGBA - use all channels including alpha
                    image_array = image_array[:, :, :4]
                    mode = 'RGBA'
                elif channels == 3:
                    # RGB - add full alpha channel
                    alpha_channel = np.ones((height, width, 1), dtype=np.uint8) * 255
                    image_array = np.concatenate([image_array[:, :, :3], alpha_channel], axis=2)
                    mode = 'RGBA'
                elif channels == 2:
                    # Grayscale + Alpha
                    gray_rgb = np.repeat(image_array[:, :, :1], 3, axis=2)
                    alpha_channel = image_array[:, :, 1:2]
                    image_array = np.concatenate([gray_rgb, alpha_channel], axis=2)
                    mode = 'RGBA'
                else:
                    # Grayscale - replicate to RGB and add alpha
                    gray_rgb = np.repeat(image_array[:, :, :1], 3, axis=2)
                    alpha_channel = np.ones((height, width, 1), dtype=np.uint8) * 255
                    image_array = np.concatenate([gray_rgb, alpha_channel], axis=2)
                    mode = 'RGBA'
                
                # Create PNG with alpha support
                from PIL import Image
                pil_image = Image.fromarray(image_array, mode)
                
                # Resize only if image is over 2000 pixels on any dimension
                if pil_image.width > 2000 or pil_image.height > 2000:
                    # Calculate new size - cut in half while maintaining aspect ratio
                    new_width = pil_image.width // 2
                    new_height = pil_image.height // 2
                    
                    print(f"   📏 Resizing from {pil_image.width}x{pil_image.height} to {new_width}x{new_height}")
                    
                    try:
                        # Try new PIL version (Pillow >= 10.0.0)
                        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    except AttributeError:
                        # Fallback for older PIL versions
                        pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                
                pil_image.save(png_path, 'PNG')
                converted = True
                
            except ImportError:
                print(f"   ℹ️ OpenImageIO not available")
            except Exception as e:
                print(f"   ⚠️ OpenImageIO conversion failed: {e}")
            
            # Method 2: Try OpenCV (good fallback)
            if not converted:
                try:
                    import cv2
                    import numpy as np
                    
                    print(f"   🔧 Using OpenCV for EXR conversion")
                    
                    # Read EXR with all channels including alpha
                    img = cv2.imread(str(exr_path), cv2.IMREAD_UNCHANGED)
                    if img is None:
                        raise Exception(f"Could not read {exr_path}")
                    
                    # Handle different channel configurations
                    if len(img.shape) == 3 and img.shape[2] == 4:
                        # BGRA -> RGBA
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
                    elif len(img.shape) == 3 and img.shape[2] == 3:
                        # BGR -> RGB and add alpha channel
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        alpha = np.ones((img.shape[0], img.shape[1], 1), dtype=img.dtype)
                        img = np.concatenate([img, alpha], axis=2)
                    elif len(img.shape) == 2:
                        # Grayscale -> RGBA
                        gray = img[:, :, np.newaxis]
                        rgb = np.repeat(gray, 3, axis=2)
                        alpha = np.ones((img.shape[0], img.shape[1], 1), dtype=img.dtype)
                        img = np.concatenate([rgb, alpha], axis=2)
                    
                    # Simple tone mapping
                    img = np.power(img, 1.0/2.2)  # Gamma correction
                    img = np.clip(img, 0.0, 1.0)  # Clamp
                    img = (img * 255).astype(np.uint8)
                    
                    # Resize only if image is over 2000 pixels on any dimension
                    h, w = img.shape[:2]
                    if w > 2000 or h > 2000:
                        # Cut in half while maintaining aspect ratio
                        new_w = w // 2
                        new_h = h // 2
                        print(f"   📏 Resizing from {w}x{h} to {new_w}x{new_h}")
                        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Save as PNG with alpha support
                    from PIL import Image
                    pil_image = Image.fromarray(img, 'RGBA')
                    pil_image.save(png_path, 'PNG')
                    converted = True
                    
                except ImportError:
                    print(f"   ℹ️ OpenCV not available")
                except Exception as e:
                    print(f"   ⚠️ OpenCV conversion failed: {e}")
            
            # Method 3: Try PIL with custom EXR handling (basic fallback)
            if not converted:
                try:
                    from PIL import Image
                    print(f"   🔧 Attempting PIL EXR conversion (limited support)")
                    
                    # PIL has limited EXR support, but worth trying
                    pil_image = Image.open(exr_path)
                    
                    # Convert to RGBA to preserve transparency
                    if pil_image.mode != 'RGBA':
                        if pil_image.mode == 'RGB':
                            # Add full alpha channel
                            pil_image = pil_image.convert('RGBA')
                        elif pil_image.mode in ['L', 'LA', 'P']:
                            # Convert other modes to RGBA
                            pil_image = pil_image.convert('RGBA')
                        else:
                            # Fallback conversion
                            pil_image = pil_image.convert('RGBA')
                    
                    # Resize only if image is over 2000 pixels on any dimension
                    if pil_image.width > 2000 or pil_image.height > 2000:
                        # Calculate new size - cut in half while maintaining aspect ratio
                        new_width = pil_image.width // 2
                        new_height = pil_image.height // 2
                        
                        print(f"   📏 Resizing from {pil_image.width}x{pil_image.height} to {new_width}x{new_height}")
                        
                        try:
                            # Try new PIL version (Pillow >= 10.0.0)
                            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        except AttributeError:
                            # Fallback for older PIL versions
                            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                    
                    pil_image.save(png_path, 'PNG')
                    converted = True
                    
                except Exception as e:
                    print(f"   ⚠️ PIL EXR conversion failed: {e}")
            
            if converted:
                print(f"   ✅ Successfully converted EXR to PNG: {png_path.name}")
                return True
            else:
                print(f"   ❌ All EXR conversion methods failed")
                return False
                
        except Exception as e:
            print(f"   ❌ EXR conversion error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_text_thumbnail(self):
        """Create a text-based thumbnail using the asset name"""
        try:
            # Try to import PIL for text rendering
            try:
                from PIL import Image, ImageDraw, ImageFont
                pil_available = True
            except ImportError:
                print(f"   ℹ️ PIL not available, will try alternative methods")
                pil_available = False
            
            sanitized_asset_name = self._sanitize_name_for_filesystem(self.asset_name)
            thumbnail_file = self.thumbnail_folder / f"{sanitized_asset_name}_thumbnail.png"
            
            if pil_available:
                # Create a nice text-based thumbnail using PIL
                width, height = 512, 512
                background_color = (45, 45, 45)  # Dark gray
                text_color = (255, 255, 255)  # White
                accent_color = (100, 150, 255)  # Light blue
                
                # Create image
                img = Image.new('RGB', (width, height), background_color)
                draw = ImageDraw.Draw(img)
                
                # Try to use a decent font
                try:
                    # Try common system fonts
                    font_large = ImageFont.truetype("arial.ttf", 48)
                    font_small = ImageFont.truetype("arial.ttf", 24)
                except:
                    try:
                        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)  # macOS
                        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                    except:
                        try:
                            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)  # Linux
                            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                        except:
                            # Fallback to default font
                            font_large = ImageFont.load_default()
                            font_small = ImageFont.load_default()
                
                # Draw background pattern
                for i in range(0, width, 64):
                    draw.line([(i, 0), (i, height)], fill=(55, 55, 55), width=1)
                for i in range(0, height, 64):
                    draw.line([(0, i), (width, i)], fill=(55, 55, 55), width=1)
                
                # Draw accent border
                draw.rectangle([(10, 10), (width-10, height-10)], outline=accent_color, width=3)
                
                # Prepare text
                lines = []
                current_line = ""
                words = self.asset_name.split()
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    # Rough estimate of text width
                    if len(test_line) > 15 and current_line:  # Wrap long lines
                        lines.append(current_line)
                        current_line = word
                    else:
                        current_line = test_line
                
                if current_line:
                    lines.append(current_line)
                
                # Calculate text position
                total_height = len(lines) * 50
                start_y = (height - total_height) // 2
                
                # Draw main asset name
                for i, line in enumerate(lines):
                    # Get text size for centering
                    try:
                        bbox = draw.textbbox((0, 0), line, font=font_large)
                        text_width = bbox[2] - bbox[0]
                    except:
                        text_width = len(line) * 25  # Rough estimate
                    
                    x = (width - text_width) // 2
                    y = start_y + i * 60
                    
                    draw.text((x, y), line, fill=text_color, font=font_large)
                
                # Draw subtitle (description)
                subtitle = str(self.description) if self.description else f"{self.asset_type} • {self.subcategory}"
                subtitle_color = (180, 180, 180)  # Light grey instead of accent blue
                
                try:
                    bbox = draw.textbbox((0, 0), subtitle, font=font_small)
                    subtitle_width = bbox[2] - bbox[0]
                except:
                    subtitle_width = len(subtitle) * 12
                
                subtitle_x = (width - subtitle_width) // 2
                subtitle_y = start_y + len(lines) * 60 + 20
                
                draw.text((subtitle_x, subtitle_y), subtitle, fill=subtitle_color, font=font_small)
                
                # Save the image
                img.save(thumbnail_file, 'PNG')
                print(f"   ✅ Created text-based thumbnail: {thumbnail_file}")
                
            else:
                # Fallback: Create a simple file with asset info (could be read by other tools)
                from datetime import datetime
                info_file = self.thumbnail_folder / f"{sanitized_asset_name}_info.txt"
                with open(info_file, 'w') as f:
                    f.write(f"Asset Name: {self.asset_name}\n")
                    if self.description:
                        f.write(f"Description: {self.description}\n")
                    f.write(f"Asset Type: {self.asset_type}\n") 
                    f.write(f"Subcategory: {self.subcategory}\n")
                    f.write(f"Render Engine: {self.render_engine}\n")
                    f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Note: Text-based thumbnail - PIL not available for image generation\n")
                
                print(f"   ℹ️ Created text info file: {info_file} (PIL not available for image)")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating text thumbnail: {e}")
            import traceback
            traceback.print_exc()
            return False

    def auto_execute_dl_submit(self):
        """Simple auto-execute dl_Submit button after HDA is loaded"""
        try:
            if not hasattr(self, '_hda_node') or not self._hda_node:
                print(f"   ℹ️ No HDA node available for auto-execution")
                return False
                
            hda_node = self._hda_node
            
            print(f"   ⏱️ Waiting 1 second for HDA to fully initialize...")
            
            if HOU_AVAILABLE:
                import time
                time.sleep(1.0)  # Wait for HDA to be ready
                
                # Check if dl_Submit parameter exists
                if not hda_node.parm("dl_Submit"):
                    print(f"   ℹ️ No dl_Submit parameter found on HDA")
                    return False
                    
                # Check if thumbnail path is valid (optional safety check)
                thumbnail_parm = hda_node.parm("thumbnailpath")
                if thumbnail_parm:
                    thumbnail_path = thumbnail_parm.evalAsString()
                    if thumbnail_path and not os.path.exists(thumbnail_path):
                        print(f"   ⚠️ Thumbnail path doesn't exist, skipping auto-execution: {thumbnail_path}")
                        return False
                
                # Execute the button
                print(f"   🎯 Auto-executing dl_Submit button...")
                hda_node.parm("dl_Submit").pressButton()
                print(f"   ✅ Successfully executed dl_Submit button!")
                return True
            else:
                print(f"   ❌ Houdini not available for auto-execution")
                return False
                
        except Exception as e:
            print(f"   ❌ Error during auto-execution: {e}")
            return False

    def export_as_template(self, parent_node, nodes_to_export):
        """Export nodes as template using saveChildrenToFile"""
        try:
            if not HOU_AVAILABLE:
                print("❌ Houdini not available")
                return False
            
            print(f"🚀 TEMPLATE EXPORT: {self.asset_name}")
            print(f"   📂 Target: {self.asset_folder}")
            
            # Check if folder already exists - safety check for variants
            if self.asset_folder.exists():
                print(f"   ⚠️  WARNING: Asset folder already exists: {self.asset_folder}")
                print(f"   🔍 Asset ID: {self.asset_id}")
                print(f"   🔍 Base UID: {self.base_uid}")
                print(f"   🔍 Variant ID: {self.variant_id}")
                print(f"   🔍 Version: {self.version}")
                
                # For safety, don't overwrite existing folders
                if self.action == "variant":
                    print(f"   ❌ SAFETY CHECK: Preventing variant overwrite!")
                    print(f"   ℹ️  Existing variant {self.variant_id} found. The next variant should be calculated differently.")
                    hou.ui.displayMessage(f"Asset folder already exists!\n\n{self.asset_folder}\n\nVariant {self.variant_id} already exists. Please check variant calculation.", 
                                         severity=hou.severityType.Error)
                    return False
            
            # Create directories
            self.asset_folder.mkdir(parents=True, exist_ok=True)
            self.data_folder.mkdir(exist_ok=True)
            self.thumbnail_folder.mkdir(exist_ok=True)
            print(f"   📁 Created thumbnail folder: {self.thumbnail_folder}")
            
            # Check if we should skip file processing
            if self.export_no_references:
                print(f"   📁 EXPORT WITH NO REFERENCES MODE - Skipping file processing...")
                bgeo_sequences = []
                vdb_sequences = []
                texture_info = []
                geometry_info = []
                path_mappings = {}
                self.framein = 1
                self.frameout = 240
                print(f"   ✅ Using default frame range: 1-240")
            else:
                # PRE-SCAN: Detect BGEO and VDB sequences with original paths (before any remapping)
                print(f"   🎬 PRE-SCANNING FOR BGEO SEQUENCES WITH ORIGINAL PATHS...")
                bgeo_sequences = self.detect_bgeo_sequences_early(parent_node)
                
                print(f"   💨 PRE-SCANNING FOR VDB SEQUENCES WITH ORIGINAL PATHS...")
                vdb_sequences = self.detect_vdb_sequences_early(parent_node)
                
                # Process materials and copy textures FIRST
                texture_info = self.process_materials_and_textures(parent_node, nodes_to_export)
                
                # Process geometry files and copy them (now with BGEO and VDB sequence info)
                geometry_info = self.process_geometry_files(parent_node, nodes_to_export, bgeo_sequences, vdb_sequences)
                
                # 🎯 DETECT SMART FRAME RANGE based on sequences
                framein, frameout = self.detect_frame_range(bgeo_sequences, vdb_sequences)
                print(f"   🎯 Smart frame range detected: {framein}-{frameout}")
                
                # Store frame range for HDA configuration and metadata
                self.framein = framein
                self.frameout = frameout
                
                # 🆕 REMAP ALL FILE PATHS FROM JOB LOCATIONS TO LIBRARY LOCATIONS
                print(f"   🔄 Remapping file paths before export...")
                path_mappings = self.remap_paths_before_export(parent_node, nodes_to_export, texture_info, geometry_info)
                print(f"   ✅ Path remapping complete: {len(path_mappings)} paths updated")
            
            # Export template with render engine suffix in root folder
            render_engine_lower = self.render_engine.lower()
            template_file = self.asset_folder / f"template_{render_engine_lower}.hip"
            print(f"   💾 Saving {self.render_engine} template to: {template_file}")
            
            # Use saveChildrenToFile with correct syntax (children, network_boxes, filename)
            try:
                parent_node.saveChildrenToFile(nodes_to_export, parent_node.networkBoxes(), str(template_file))
                print(f"   ✅ Template saved successfully: template_{render_engine_lower}.hip")
            except Exception as e:
                print(f"   ❌ Template save failed: {e}")
                # As a fallback, just create an empty file so the export doesn't fail
                template_file.touch()
                print(f"   ⚠️ Created empty template file as fallback")
            
            print(f"   ✅ Template saved: {template_file.name} ({template_file.stat().st_size / 1024:.1f} KB)")
            
            # Create metadata
            print(f"   📋 Creating metadata...")
            metadata = self.create_asset_metadata(template_file, nodes_to_export, texture_info, geometry_info, path_mappings)
            print(f"   ✅ Metadata created successfully")
            
            # 🎨 HANDLE THUMBNAIL BASED ON MODE
            print(f"   🎨 Thumbnail Mode: {self.thumbnail_action}")
            
            if self.thumbnail_action == "automatic":
                # Original behavior: Load HDA and auto-execute dl_Submit
                print(f"   🎬 Loading and configuring render farm HDA...")
                render_hda_success = self.load_and_configure_render_hda(parent_node, nodes_to_export, metadata)
                if render_hda_success:
                    print(f"   ✅ Render farm HDA loaded and configured successfully")
                    
                    # Auto-execute dl_Submit button after HDA is loaded
                    print(f"   🚀 Auto-executing dl_Submit button...")
                    auto_exec_success = self.auto_execute_dl_submit()
                    if auto_exec_success:
                        print(f"   ✅ dl_Submit button executed successfully - render should start!")
                    else:
                        print(f"   ℹ️ dl_Submit button not executed - check console for details")
                else:
                    print(f"   ⚠️ Render farm HDA configuration had issues (check console)")
                    
            elif self.thumbnail_action == "choose":
                # Copy custom thumbnail file
                print(f"   📁 Using custom thumbnail: {self.thumbnail_file_path}")
                self.copy_custom_thumbnail()
                
            elif self.thumbnail_action == "disable":
                # Create text-based thumbnail
                print(f"   📝 Creating text-based thumbnail")
                self.create_text_thumbnail()
                
            else:
                print(f"   ⚠️ Unknown thumbnail action: {self.thumbnail_action}, defaulting to automatic")
                # Fallback to automatic mode
                render_hda_success = self.load_and_configure_render_hda(parent_node, nodes_to_export, metadata)
                if render_hda_success:
                    auto_exec_success = self.auto_execute_dl_submit()
                    if auto_exec_success:
                        print(f"   ✅ dl_Submit button executed successfully - render should start!")
                    else:
                        print(f"   ℹ️ dl_Submit button not executed - check console for details")
            
            print(f"✅ Export complete: {self.asset_folder}")
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            traceback.print_exc()
            return False

    def process_materials_and_textures(self, parent_node, nodes_to_export):
        """Process materials and copy textures using comprehensive scanning like test script"""
        texture_info = []
        
        try:
            print("   🔍 NEW COMPREHENSIVE SCANNING METHOD ACTIVE! 🎯")
            print("   🔍 Scanning for materials and textures using comprehensive method...")
            
            # Get ALL nodes recursively inside the subnet (like our test script)
            all_nodes = self._collect_all_nodes(parent_node)
            
            print(f"   📋 Found {len(all_nodes)} total nodes (including nested)")
            
            # Find ALL material-related nodes (VOP, Shop, MatNet)
            material_nodes = []
            matnet_nodes = []
            vop_nodes = []
            
            for node in all_nodes:
                node_type = node.type().name()
                category = node.type().category().name()
                
                
                # Collect different types of nodes
                if node_type == 'matnet':
                    matnet_nodes.append(node)
                
                elif category == 'Vop':
                    vop_nodes.append(node)
                
                elif category == 'Shop':
                    material_nodes.append(node)
            
            print(f"   📊 SUMMARY:")
            print(f"      🎨 MatNet nodes: {len(matnet_nodes)}")
            print(f"      🔧 VOP nodes: {len(vop_nodes)}")
            print(f"      🏪 Shop materials: {len(material_nodes)}")
            
            # Scan ALL VOP nodes for texture parameters (like our test script)
            # Scan all VOP nodes for texture references
            for vop_node in vop_nodes:
                
                # Get material name for folder organization
                material_name = "Unknown"
                # Try to get parent material name
                parent = vop_node.parent()
                while parent and material_name == "Unknown":
                    if parent.type().category().name() in ['Vop', 'Shop']:
                        material_name = parent.name()
                        break
                    parent = parent.parent()
                
                # Get ALL parameters on this VOP node
                all_parms = vop_node.parms()
                
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        # Check if this looks like a file path with texture extensions
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            any(ext in parm_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx'])):
                            
                            # Expand Houdini variables
                            expanded_path = hou.expandString(parm_value)
                            print(f"         🖼️ TEXTURE PARAMETER: {parm.name()} = '{parm_value}'")
                            print(f"            EXPANDED TO: '{expanded_path}'")
                            
                            if os.path.exists(expanded_path):
                                texture_info.append({
                                    'material': vop_node.path(),
                                    'material_name': material_name,
                                    'node': vop_node.path(),
                                    'parameter': parm.name(),
                                    'file': expanded_path,
                                    'filename': os.path.basename(expanded_path),
                                    'original_path': parm_value
                                })
                                print(f"            ✅ FILE EXISTS: {os.path.basename(expanded_path)}")
                            else:
                                # Check if it's a UDIM pattern
                                if '<UDIM>' in parm_value or '<udim>' in parm_value or '<UDIM>' in expanded_path or '<udim>' in expanded_path:
                                    print(f"            📋 UDIM PATTERN DETECTED - checking for actual files...")
                                    # Try to find actual UDIM files
                                    udim_pattern = expanded_path.replace('<UDIM>', '*').replace('<udim>', '*')
                                    print(f"            � Searching with pattern: {udim_pattern}")
                                    udim_files = glob.glob(udim_pattern)
                                    if udim_files:
                                        print(f"            🎯 Found {len(udim_files)} UDIM files:")
                                        # Add the PATTERN as a single entry, not individual files
                                        texture_info.append({
                                            'material': vop_node.path(),
                                            'material_name': material_name,
                                            'node': vop_node.path(),
                                            'parameter': parm.name(),
                                            'file': expanded_path,  # Keep the original pattern with <UDIM>
                                            'filename': os.path.basename(expanded_path),  # Pattern filename
                                            'original_path': parm_value,  # Original parameter value
                                            'is_udim_pattern': True,  # Mark as UDIM pattern
                                            'udim_files_found': udim_files,  # Store actual files for copying
                                            'udim_count': len(udim_files)
                                        })
                                        # Show sample files for verification
                                        for udim_file in udim_files[:5]:  # Show first 5
                                            print(f"              • {os.path.basename(udim_file)}")
                                        if len(udim_files) > 5:
                                            print(f"              ... and {len(udim_files)-5} more")
                                    else:
                                        print(f"            ❌ No UDIM files found with pattern: {udim_pattern}")
                                        # Try checking if the base file exists (like .1001)
                                        test_udim = expanded_path.replace('<UDIM>', '1001').replace('<udim>', '1001')
                                        if os.path.exists(test_udim):
                                            print(f"            🎯 Found single UDIM file - adding as pattern anyway: {os.path.basename(test_udim)}")
                                            texture_info.append({
                                                'material': vop_node.path(),
                                                'material_name': material_name,
                                                'node': vop_node.path(),
                                                'parameter': parm.name(),
                                                'file': expanded_path,  # Keep the original pattern with <UDIM>
                                                'filename': os.path.basename(expanded_path),
                                                'original_path': parm_value,
                                                'is_udim_pattern': True,
                                                'udim_files_found': [test_udim],  # Store the one file we found
                                                'udim_count': 1
                                            })
                                else:
                                    print(f"            ❌ FILE NOT FOUND: {expanded_path}")
                    
                    except Exception as e:
                        pass  # Skip parameters that can't be evaluated
            
            # Also scan SHOP materials
            print(f"   🔍 SCANNING SHOP MATERIALS:")
            
            for shop_node in material_nodes:
                print(f"      � Scanning SHOP: {shop_node.path()} ({shop_node.type().name()})")
                
                material_name = shop_node.name()
                all_parms = shop_node.parms()
                
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            any(ext in parm_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx'])):
                            
                            expanded_path = hou.expandString(parm_value)
                            print(f"         🖼️ TEXTURE PARAMETER: {parm.name()} = '{parm_value}'")
                            
                            if os.path.exists(expanded_path):
                                texture_info.append({
                                    'material': shop_node.path(),
                                    'material_name': material_name,
                                    'node': shop_node.path(),
                                    'parameter': parm.name(),
                                    'file': expanded_path,
                                    'filename': os.path.basename(expanded_path),
                                    'original_path': parm_value
                                })
                                print(f"            ✅ FILE EXISTS: {os.path.basename(expanded_path)}")
                            else:
                                # Handle UDIM patterns for SHOP materials too - preserve pattern
                                if '<UDIM>' in parm_value or '<udim>' in parm_value or '<UDIM>' in expanded_path or '<udim>' in expanded_path:
                                    udim_pattern = expanded_path.replace('<UDIM>', '*').replace('<udim>', '*')
                                    udim_files = glob.glob(udim_pattern)
                                    if udim_files:
                                        print(f"            🎯 SHOP UDIM pattern found with {len(udim_files)} files - preserving pattern")
                                        texture_info.append({
                                            'material': shop_node.path(),
                                            'material_name': material_name,
                                            'node': shop_node.path(),
                                            'parameter': parm.name(),
                                            'file': expanded_path,  # Keep the original pattern with <UDIM>
                                            'filename': os.path.basename(expanded_path),
                                            'original_path': parm_value,
                                            'is_udim_pattern': True,  # Mark as UDIM pattern
                                            'udim_files_found': udim_files,
                                            'udim_count': len(udim_files)
                                        })
                    
                    except Exception as e:
                        pass
            
            if texture_info:
                print(f"   🖼️ Found {len(texture_info)} textures to copy:")
                
                # Create main textures folder
                textures_folder = self.asset_folder / "Textures"
                textures_folder.mkdir(exist_ok=True)
                print(f"   📁 Created main textures folder: {textures_folder}")
                
                # Group textures by material name
                textures_by_material = {}
                for tex_info in texture_info:
                    mat_name = tex_info.get('material_name', 'Unknown')
                    if mat_name not in textures_by_material:
                        textures_by_material[mat_name] = []
                    textures_by_material[mat_name].append(tex_info)
                
                print(f"   📋 Organizing textures by {len(textures_by_material)} materials:")
                for mat_name, textures in textures_by_material.items():
                    print(f"      • {mat_name}: {len(textures)} textures")
                
                # Copy textures organized by material folders
                copied_textures = []
                for mat_name, textures in textures_by_material.items():
                    # Create material subfolder
                    material_folder = textures_folder / mat_name
                    material_folder.mkdir(exist_ok=True)
                    print(f"   📁 Created material folder: {material_folder}")
                    
                    # Copy textures for this material
                    for tex_info in textures:
                        try:
                            # Handle UDIM patterns specially
                            if tex_info.get('is_udim_pattern', False):
                                print(f"      🎯 Processing UDIM pattern: {tex_info['filename']}")
                                
                                # Copy all the individual UDIM files
                                udim_files = tex_info.get('udim_files_found', [])
                                if udim_files:
                                    print(f"         Copying {len(udim_files)} UDIM files...")
                                    
                                    # Copy each UDIM file
                                    for udim_file_path in udim_files:
                                        udim_source = Path(udim_file_path)
                                        udim_dest = material_folder / udim_source.name
                                        
                                        # Handle duplicate filenames
                                        counter = 1
                                        original_dest = udim_dest
                                        while udim_dest.exists():
                                            stem = original_dest.stem
                                            suffix = original_dest.suffix
                                            udim_dest = material_folder / f"{stem}_{counter}{suffix}"
                                            counter += 1
                                        
                                        # Copy the UDIM file
                                        shutil.copy2(udim_source, udim_dest)
                                        print(f"         ✅ Copied UDIM: {udim_source.name} -> {mat_name}/{udim_dest.name}")
                                    
                                    # Create relative path with preserved <UDIM> pattern
                                    pattern_filename = tex_info['filename']  # This has <UDIM> in it
                                    relative_pattern_path = f"Textures/{mat_name}/{pattern_filename}"
                                    
                                    # Update texture info with the PATTERN path (preserving <UDIM>)
                                    tex_info['relative_path'] = relative_pattern_path
                                    tex_info['library_path'] = relative_pattern_path  # Add library_path too
                                    tex_info['copied_file'] = str(material_folder / pattern_filename)
                                    copied_textures.append(tex_info)
                                    
                                    print(f"         🎯 UDIM pattern remapping will use: {relative_pattern_path}")
                                else:
                                    print(f"         ❌ No UDIM files found to copy")
                            
                            else:
                                # Handle regular texture files
                                source_file = Path(tex_info['file'])
                                if source_file.exists():
                                    # Create destination filename in material folder
                                    dest_file = material_folder / source_file.name
                                    
                                    # Handle duplicate filenames
                                    counter = 1
                                    original_dest = dest_file
                                    while dest_file.exists():
                                        stem = original_dest.stem
                                        suffix = original_dest.suffix
                                        dest_file = material_folder / f"{stem}_{counter}{suffix}"
                                        counter += 1
                                    
                                    # Copy the texture file
                                    shutil.copy2(source_file, dest_file)
                                    
                                    print(f"      ✅ Copied: {source_file.name} -> {mat_name}/{dest_file.name}")
                                    
                                    # Update texture info with new relative path
                                    tex_info['copied_file'] = str(dest_file)
                                    tex_info['relative_path'] = f"Textures/{mat_name}/{dest_file.name}"
                                    tex_info['library_path'] = f"Textures/{mat_name}/{dest_file.name}"  # Add library_path too
                                    copied_textures.append(tex_info)
                                    
                                else:
                                    print(f"      ⚠️ Texture file not found: {source_file}")
                        
                        except Exception as e:
                            print(f"      ❌ Error copying texture {tex_info.get('filename', 'unknown')}: {e}")
                
                print(f"   ✅ Copied {len(copied_textures)} texture files organized by material")
                texture_info = copied_textures
            
            else:
                print("   📋 No textures found to copy")
            
        except Exception as e:
            print(f"   ⚠️ Error processing materials and textures: {e}")
            traceback.print_exc()
        
        return texture_info

    def detect_bgeo_sequences_early(self, parent_node):
        """Detect BGEO sequences before any path remapping occurs"""
        bgeo_sequences = {}
        
        try:
            print("      🔍 EARLY BGEO SCAN: Scanning for BGEO sequences with original frame variables...")
            
            # Get ALL nodes recursively
            all_nodes = self._collect_all_nodes(parent_node)
            print(f"      📋 EARLY BGEO SCAN: Checking {len(all_nodes)} nodes for BGEO sequence patterns...")
            
            # Debug: Show what nodes we found
            cache_nodes_found = 0
            for node in all_nodes[:10]:  # Show first 10 nodes
                node_type = node.type().name()
                print(f"         • {node.path()} ({node_type})")
                if (node_type.lower() in ['filecache', 'rop_geometry', 'geometry'] or 
                    'cache' in node_type.lower() or 
                    node_type.startswith('filecache::')):
                    cache_nodes_found += 1
            
            if len(all_nodes) > 10:
                print(f"         ... and {len(all_nodes) - 10} more nodes")
                
            print(f"      🎯 EARLY BGEO SCAN: Found {cache_nodes_found} potential cache nodes")
            
            # Look for file cache nodes and geometry ROPs with frame variables
            for node in all_nodes:
                node_type = node.type().name()
                
                # Check file cache, rop_geometry, and regular file nodes
                # Include versioned file cache nodes like 'filecache::2.0'
                is_cache_node = (
                    node_type.lower() in ['filecache', 'rop_geometry', 'geometry', 'file'] or 
                    'cache' in node_type.lower() or 
                    node_type.startswith('filecache::')
                )
                
                if is_cache_node:
                    print(f"         🎯 Found cache node: {node.path()} ({node_type})")
                    
                    # Check the 'file' parameter specifically (this is where BGEO sequences are typically stored)
                    file_parm = node.parm('file')
                    if file_parm:
                        try:
                            raw_value = file_parm.unexpandedString()
                            eval_value = file_parm.evalAsString()
                            
                            print(f"            🔍 Checking 'file' parameter:")
                            print(f"               Raw: '{raw_value}'")
                            print(f"               Evaluated: '{eval_value}'")
                            
                            # Look for BGEO files with frame variables in the RAW value
                            if (isinstance(raw_value, str) and 
                                raw_value.strip() and
                                ('.bgeo' in raw_value.lower()) and
                                any(var in raw_value for var in ['${F4}', '${F}', '${FF}', '$F4', '$F', '${OS}', '$OS'])):
                                
                                print(f"            ✅ BGEO SEQUENCE FOUND: {raw_value}")
                                
                                # Process this sequence using the raw value with variables
                                sequence_info = self._process_bgeo_sequence(node, file_parm, raw_value, raw_value)
                                if sequence_info:
                                    sequence_key = f"{node.path()}:file"
                                    bgeo_sequences[sequence_key] = {
                                        'node': node,
                                        'parameter': file_parm,
                                        'original_pattern': raw_value,
                                        'sequence_info': sequence_info,
                                        'node_name': node.name()
                                    }
                                    print(f"            📊 Stored {len(sequence_info)} sequence files for {sequence_key}")
                            else:
                                print(f"            ❌ No BGEO sequence pattern found in 'file' parameter")
                                    
                        except Exception as e:
                            print(f"            ❌ Error checking 'file' parameter: {e}")
                    else:
                        print(f"            ❌ No 'file' parameter found on {node.path()}")
                        
                        # Show available parameters for debugging
                        print(f"            📋 Available parameters:")
                        for parm in node.parms()[:10]:  # Show first 10 params
                            try:
                                parm_name = parm.name()
                                parm_value = parm.unexpandedString()
                                if isinstance(parm_value, str) and parm_value.strip():
                                    print(f"               {parm_name}: '{parm_value[:50]}{'...' if len(str(parm_value)) > 50 else ''}'")
                            except:
                                pass
            
            print(f"      ✅ Found {len(bgeo_sequences)} BGEO sequences total")
            for seq_key, seq_data in bgeo_sequences.items():
                print(f"         • {seq_key}: {len(seq_data['sequence_info'])} files")
            
            return bgeo_sequences
            
        except Exception as e:
            print(f"      ❌ Error in BGEO sequence detection: {e}")
            traceback.print_exc()
            return {}

    def detect_vdb_sequences_early(self, parent_node):
        """Detect VDB sequences before any path remapping occurs - based on BGEO logic"""
        vdb_sequences = {}
        
        try:
            print("      🔍 EARLY VDB SCAN: Scanning for VDB sequences with original frame variables...")
            
            # Get ALL nodes recursively
            all_nodes = self._collect_all_nodes(parent_node)
            print(f"      📋 EARLY VDB SCAN: Checking {len(all_nodes)} nodes for VDB sequence patterns...")
            
            # Debug: Show what nodes we found
            cache_nodes_found = 0
            for node in all_nodes[:10]:  # Show first 10 nodes
                node_type = node.type().name()
                print(f"         • {node.path()} ({node_type})")
                if (node_type.lower() in ['filecache', 'rop_geometry', 'geometry', 'file'] or 
                    'cache' in node_type.lower() or 
                    node_type.startswith('filecache::')):
                    cache_nodes_found += 1
            
            if len(all_nodes) > 10:
                print(f"         ... and {len(all_nodes) - 10} more nodes")
                
            print(f"      🎯 EARLY VDB SCAN: Found {cache_nodes_found} potential cache nodes")
            
            # Look for file cache nodes and geometry ROPs with frame variables
            for node in all_nodes:
                node_type = node.type().name()
                
                # Check file cache, rop_geometry, and regular file nodes
                # Include versioned file cache nodes like 'filecache::2.0'
                is_cache_node = (
                    node_type.lower() in ['filecache', 'rop_geometry', 'geometry', 'file'] or 
                    'cache' in node_type.lower() or 
                    node_type.startswith('filecache::')
                )
                
                if is_cache_node:
                    print(f"         🎯 Found cache node: {node.path()} ({node_type})")
                    
                    # Check the 'file' parameter specifically (this is where VDB sequences are typically stored)
                    file_parm = node.parm('file')
                    if file_parm:
                        try:
                            raw_value = file_parm.unexpandedString()
                            eval_value = file_parm.evalAsString()
                            
                            print(f"            🔍 Checking 'file' parameter:")
                            print(f"               Raw: '{raw_value}'")
                            print(f"               Evaluated: '{eval_value}'")
                            
                            # Look for VDB files with frame variables in the RAW value
                            if (isinstance(raw_value, str) and 
                                raw_value.strip() and
                                ('.vdb' in raw_value.lower()) and
                                any(var in raw_value for var in ['${F4}', '${F}', '${FF}', '$F4', '$F', '${OS}', '$OS'])):
                                
                                print(f"            ✅ VDB SEQUENCE FOUND: {raw_value}")
                                
                                # Process this sequence using the raw value with variables
                                sequence_info = self._process_vdb_sequence(node, file_parm, raw_value, raw_value)
                                if sequence_info:
                                    sequence_key = f"{node.path()}:file"
                                    vdb_sequences[sequence_key] = {
                                        'node': node,
                                        'parameter': file_parm,
                                        'original_pattern': raw_value,
                                        'sequence_info': sequence_info,
                                        'node_name': node.name()
                                    }
                                    print(f"            📊 Stored {len(sequence_info)} VDB sequence files for {sequence_key}")
                            else:
                                print(f"            ❌ No VDB sequence pattern found in 'file' parameter")
                                    
                        except Exception as e:
                            print(f"            ❌ Error checking 'file' parameter: {e}")
                    else:
                        print(f"            ❌ No 'file' parameter found on {node.path()}")
            
            print(f"      ✅ Found {len(vdb_sequences)} VDB sequences total")
            for seq_key, seq_data in vdb_sequences.items():
                print(f"         • {seq_key}: {len(seq_data['sequence_info'])} files")
            
            return vdb_sequences
            
        except Exception as e:
            print(f"      ❌ Error in VDB sequence detection: {e}")
            traceback.print_exc()
            return {}

    def _process_vdb_sequence(self, node, parm, parm_value, expanded_path):
        """Process VDB sequence and discover all files in the sequence - based on BGEO logic"""
        try:
            print(f"            🎬 Processing VDB sequence from node: {node.name()}")
            print(f"            📄 Raw pattern: {parm_value}")
            
            # Step 1: Replace ${OS} with node name to get the actual folder path
            actual_path = parm_value
            if '${OS}' in actual_path:
                actual_path = actual_path.replace('${OS}', node.name())
            if '$OS' in actual_path and '${OS}' not in actual_path:
                actual_path = actual_path.replace('$OS', node.name())
            
            # Step 2: Extract directory path and filename pattern
            sequence_file_pattern = Path(actual_path).name
            sequence_dir = str(Path(actual_path).parent)
            
            print(f"            📂 Target directory: {sequence_dir}")
            print(f"            🔍 Looking for pattern: {sequence_file_pattern}")
            
            # Step 3: Extract base filename by removing frame variables
            # From: JOB_0180_simExplosion_v026.${F4}.vdb
            # Get: JOB_0180_simExplosion_v026
            base_filename = sequence_file_pattern
            frame_vars = ['${F4}', '${F}', '${FF}', '$F4', '$F']
            
            # Remove frame variable to get prefix
            prefix = ""
            for var in frame_vars:
                if var in base_filename:
                    prefix = base_filename.split(var)[0]
                    break
            
            # If no frame variable found, use the whole name minus extension as prefix
            if not prefix:
                if '.vdb' in base_filename:
                    prefix = base_filename.split('.vdb')[0]
                else:
                    prefix = base_filename
                    
            # Extract sequence base name (remove trailing dots and frame separators)
            sequence_base_name = prefix.rstrip('._')
            
            print(f"            🏷️  Base prefix: '{prefix}'")
            print(f"            🏷️  Sequence name: '{sequence_base_name}'")
            
            # Step 4: Find all VDB files in the directory that match the pattern
            sequence_files = []
            sequence_dir_path = Path(sequence_dir)
            
            if sequence_dir_path.exists():
                print(f"            🔍 Scanning directory for VDB files...")
                
                for file_path in sequence_dir_path.iterdir():
                    if file_path.is_file():
                        filename = file_path.name
                        # Check if it's a VDB file and starts with our prefix
                        if (filename.lower().endswith('.vdb') and 
                            filename.startswith(prefix)):
                            sequence_files.append(str(file_path))
                            
                print(f"            ✅ Found {len(sequence_files)} VDB files matching pattern")
                
                if sequence_files:
                    # Sort files to ensure proper sequence order
                    sequence_files.sort()
                    print(f"            📋 Range: {os.path.basename(sequence_files[0])} → {os.path.basename(sequence_files[-1])}")
                else:
                    print(f"            ❌ No files found starting with '{prefix}' and ending with .vdb")
                    # Show what files are actually in the directory
                    all_files = [f.name for f in sequence_dir_path.iterdir() if f.is_file()]
                    if all_files:
                        print(f"            📋 Files in directory: {all_files[:5]}{'...' if len(all_files) > 5 else ''}")
                    return None
            else:
                print(f"            ❌ Directory doesn't exist: {sequence_dir_path}")
                return None
            
            # Create geometry info entries for the sequence
            sequence_info = []
            
            # Add a pattern mapping entry for path remapping (preserves frame variables)
            pattern_info = {
                'node_path': node.path(),
                'parameter': 'file', 
                'original_path': parm_value,  # Keep the frame variables
                'library_path': f"Geometry/vdb/{sequence_base_name}/{sequence_file_pattern}",  # Use truncated filename, lowercase vdb
                'file_type': f'vdb/{sequence_base_name}',  # 🔧 FIX: Use lowercase vdb + truncated filename!
                'is_pattern_mapping': True,
                'sequence_pattern': parm_value,
                'sequence_base_name': sequence_base_name,
                'filename': sequence_file_pattern
            }
            sequence_info.append(pattern_info)
            print(f"            🔗 Pattern mapping: {parm_value} → Geometry/vdb/{sequence_base_name}/{sequence_file_pattern}")
            
            # Add individual file entries for copying
            for seq_file in sequence_files:
                file_path = Path(seq_file)
                file_info = {
                    'node_path': node.path(),
                    'parameter': 'file',
                    'file': str(file_path),
                    'original_path': str(file_path), 
                    'library_path': f"Geometry/vdb/{sequence_base_name}/{file_path.name}",
                    'file_type': f'vdb/{sequence_base_name}',  # 🔧 FIX: Use lowercase vdb + truncated filename!
                    'filename': file_path.name,
                    'is_pattern_mapping': False,
                    'sequence_pattern': parm_value,
                    'sequence_base_name': sequence_base_name
                }
                sequence_info.append(file_info)
            
            print(f"            ✅ Created {len(sequence_info)} VDB sequence entries ({1} pattern + {len(sequence_files)} files)")
            return sequence_info
            
        except Exception as e:
            print(f"            ❌ Error processing VDB sequence: {e}")
            traceback.print_exc()
            return None

    def _copy_vdb_sequence(self, geometry_folder, file_type, files, copied_files):
        """Copy VDB sequence files to filename-based subfolders - updated for lowercase vdb"""
        try:
            print(f"   💨 VDB SEQUENCE COPYING STARTED")
            print(f"      file_type: '{file_type}'")
            print(f"      geometry_folder: '{geometry_folder}'")
            print(f"      files to copy: {len(files)}")
            
            # Create the vdb/filename_truncated folder structure (file_type is already 'vdb/filename_truncated')
            type_folder = geometry_folder / file_type
            type_folder.mkdir(parents=True, exist_ok=True)
            print(f"   📁 Created VDB sequence folder: {type_folder}")
            print(f"      Full path: {type_folder.absolute()}")
            
            # Group files by sequence pattern
            sequences = {}
            for geo_info in files:
                sequence_pattern = geo_info.get('sequence_pattern', geo_info['original_path'])
                sequence_base_name = geo_info.get('sequence_base_name', 'unknown')
                sequence_key = f"{sequence_pattern}_{sequence_base_name}"
                if sequence_key not in sequences:
                    sequences[sequence_key] = []
                sequences[sequence_key].append(geo_info)
            
            # Process each sequence
            for sequence_key, sequence_files in sequences.items():
                # Get sequence base name from the first file for logging
                sequence_base_name = sequence_files[0].get('sequence_base_name', 'unknown')
                print(f"      💨 Processing VDB sequence: {sequence_base_name}")
                print(f"         📁 Files will be copied directly to: {type_folder}")
                print(f"         📁 Full structure: Geometry/vdb/{sequence_base_name}/")
                
                copied_in_sequence = 0
                
                for geo_info in sequence_files:
                    # Skip pattern mapping entries during file copying - they don't have real files
                    if geo_info.get('is_pattern_mapping', False):
                        print(f"         🔒 VDB PATTERN MAPPING PRESERVATION:")
                        print(f"            original_path: {geo_info.get('original_path')}")
                        print(f"            library_path: {geo_info.get('library_path')}")
                        print(f"            is_pattern_mapping: {geo_info.get('is_pattern_mapping')}")
                        
                        # Make a deep copy to ensure pattern mapping isn't modified
                        pattern_copy = copy.deepcopy(geo_info)
                        
                        # Verify the copy preserved the original_path
                        print(f"            AFTER COPY - original_path: {pattern_copy.get('original_path')}")
                        print(f"            AFTER COPY - is_pattern_mapping: {pattern_copy.get('is_pattern_mapping')}")
                        
                        copied_files.append(pattern_copy)
                        continue
                    
                    source_file = Path(geo_info['file'])
                    if source_file.exists():
                        # Copy the VDB file directly to the type_folder (which is already Geometry/vdb/truncated_filename/)
                        dest_file = type_folder / source_file.name
                        
                        # Copy the VDB file
                        shutil.copy2(source_file, dest_file)
                        
                        print(f"         ✅ Copied: {source_file.name} → vdb/{sequence_base_name}/{dest_file.name}")
                        
                        # Update geometry info with new relative path
                        geo_info['copied_file'] = str(dest_file)
                        
                        # Don't overwrite library_path for pattern mappings - they need to preserve frame variables
                        if not geo_info.get('is_pattern_mapping', False):
                            geo_info['library_path'] = f"Geometry/vdb/{sequence_base_name}/{dest_file.name}"
                        else:
                            print(f"         🔒 Preserving pattern mapping library_path: {geo_info.get('library_path')}")
                        
                        copied_files.append(geo_info)
                        copied_in_sequence += 1
                        
                    else:
                        print(f"         ⚠️ VDB file not found: {source_file}")
                
                print(f"      ✅ Sequence complete: {copied_in_sequence}/{len(sequence_files)} files copied")
                print(f"      📂 Files saved to: Geometry/vdb/{sequence_base_name}/")
                    
        except Exception as e:
            print(f"      ❌ Error copying VDB sequence: {e}")
            traceback.print_exc()

    def detect_frame_range(self, bgeo_sequences=None, vdb_sequences=None):
        """Detect smart frame range based on sequences or use defaults"""
        try:
            print("   🎯 DETECTING FRAME RANGE...")
            
            # Default frame range for static assets
            default_framein = 1001
            default_frameout = 1018  # 18 frame render
            
            # Check if we have any sequences that would extend the frame range
            all_sequences = {}
            
            # Combine BGEO and VDB sequences
            if bgeo_sequences:
                all_sequences.update(bgeo_sequences)
                print(f"      📊 Found {len(bgeo_sequences)} BGEO sequences to analyze")
            
            if vdb_sequences:
                all_sequences.update(vdb_sequences)
                print(f"      📊 Found {len(vdb_sequences)} VDB sequences to analyze")
            
            if not all_sequences:
                print(f"      📊 No sequences detected - using defaults: {default_framein}-{default_frameout}")
                return default_framein, default_frameout
            
            # Extract frame numbers from all sequence files
            all_frame_numbers = []
            
            for seq_key, seq_data in all_sequences.items():
                sequence_info = seq_data.get('sequence_info', [])
                sequence_name = seq_data.get('node_name', 'unknown')
                
                print(f"      🔍 Analyzing sequence '{sequence_name}' with {len(sequence_info)} files")
                
                for file_info in sequence_info:
                    # Skip pattern mappings - look at actual files only
                    if file_info.get('is_pattern_mapping', False):
                        continue
                        
                    filename = file_info.get('filename', '')
                    if filename:
                        # Extract frame number from filename
                        frame_number = self._extract_frame_number_from_filename(filename)
                        if frame_number is not None:
                            all_frame_numbers.append(frame_number)
                            print(f"         📄 {filename} → frame {frame_number}")
            
            if all_frame_numbers:
                # Find the range of frame numbers
                min_frame = min(all_frame_numbers)
                max_frame = max(all_frame_numbers)
                
                # Always start at 1001, but extend to the longest sequence
                framein = default_framein  # Always 1001
                frameout = max(max_frame, default_frameout)  # At least to 1018 or end of sequence
                
                print(f"      📊 Sequence analysis:")
                print(f"         Actual frame range: {min_frame}-{max_frame} ({len(all_frame_numbers)} frames)")
                print(f"         Smart frame range: {framein}-{frameout} (start at 1001, end at sequence end)")
                
                return framein, frameout
            else:
                print(f"      📊 No frame numbers extracted from sequences - using defaults: {default_framein}-{default_frameout}")
                return default_framein, default_frameout
                
        except Exception as e:
            print(f"      ❌ Error detecting frame range: {e}")
            traceback.print_exc()
            # Return defaults on error
            return 1001, 1018

    def _extract_frame_number_from_filename(self, filename):
        """Extract frame number from filename (e.g., 'sim_1005.bgeo' -> 1005)"""
        try:
            import re
            
            # Look for 4-digit frame numbers (most common)
            match = re.search(r'\.(\d{4})\.', filename)
            if match:
                return int(match.group(1))
            
            # Look for other digit patterns
            match = re.search(r'_(\d{4})[._]', filename)
            if match:
                return int(match.group(1))
                
            # Look for 3-digit patterns  
            match = re.search(r'\.(\d{3})\.', filename)
            if match:
                return int(match.group(1))
                
            # Look for any digits at end before extension
            match = re.search(r'(\d+)\.[^.]+$', filename)
            if match:
                frame_num = int(match.group(1))
                # Only consider reasonable frame numbers (avoid version numbers, etc.)
                if 1 <= frame_num <= 9999:
                    return frame_num
            
            return None
            
        except Exception as e:
            print(f"         ⚠️ Error extracting frame number from '{filename}': {e}")
            return None

    def process_geometry_files(self, parent_node, nodes_to_export, bgeo_sequences=None, vdb_sequences=None):
        """Process geometry files (Alembic, FBX, etc.) and copy them to library"""
        geometry_info = []
        
        try:
            print("   🔍 SCANNING FOR GEOMETRY FILES (Alembic, FBX, OBJ, etc.)...")
            
            # First, add pre-detected BGEO sequences to geometry_info
            if bgeo_sequences:
                print(f"   🎬 Adding {len(bgeo_sequences)} pre-detected BGEO sequences...")
                
                # Consolidate sequences by sequence base name to avoid duplicates
                consolidated_sequences = {}
                for seq_key, seq_data in bgeo_sequences.items():
                    sequence_info = seq_data['sequence_info']
                    if sequence_info:  # Make sure we have sequence files
                        sequence_base_name = sequence_info[0].get('sequence_base_name', 'unknown')
                        if sequence_base_name not in consolidated_sequences:
                            consolidated_sequences[sequence_base_name] = sequence_info
                            print(f"      📁 Adding sequence '{sequence_base_name}': {len(sequence_info)} files")
                        else:
                            print(f"      🔄 Skipping duplicate sequence '{sequence_base_name}' (already have {len(consolidated_sequences[sequence_base_name])} files)")
                
                # Add consolidated sequences to geometry_info
                for seq_name, seq_info in consolidated_sequences.items():
                    geometry_info.extend(seq_info)
                    
                    # Count pattern mappings for debugging
                    pattern_count = sum(1 for item in seq_info if item.get('is_pattern_mapping', False))
                    regular_count = len(seq_info) - pattern_count
                    
                    print(f"      ✅ Added {len(seq_info)} files for sequence '{seq_name}' ({pattern_count} patterns, {regular_count} regular files)")
                    
                    # Debug: Show pattern mappings
                    for item in seq_info:
                        if item.get('is_pattern_mapping', False):
                            print(f"         🔗 Pattern: {item.get('filename', 'NO_FILENAME')}")
                            print(f"            original_path: {item.get('original_path', 'NO_ORIGINAL')}")
                            print(f"            library_path: {item.get('library_path', 'NO_LIBRARY')}")
            
            # Add pre-detected VDB sequences to geometry_info
            if vdb_sequences:
                print(f"   💨 Adding {len(vdb_sequences)} pre-detected VDB sequences...")
                
                # Consolidate VDB sequences by sequence base name to avoid duplicates
                consolidated_vdb_sequences = {}
                for seq_key, seq_data in vdb_sequences.items():
                    sequence_info = seq_data['sequence_info']
                    if sequence_info:  # Make sure we have sequence files
                        sequence_base_name = sequence_info[0].get('sequence_base_name', 'unknown')
                        if sequence_base_name not in consolidated_vdb_sequences:
                            consolidated_vdb_sequences[sequence_base_name] = sequence_info
                            print(f"      💨 Adding VDB sequence '{sequence_base_name}': {len(sequence_info)} files")
                        else:
                            print(f"      🔄 Skipping duplicate VDB sequence '{sequence_base_name}' (already have {len(consolidated_vdb_sequences[sequence_base_name])} files)")
                
                # Add consolidated VDB sequences to geometry_info
                for seq_name, seq_info in consolidated_vdb_sequences.items():
                    geometry_info.extend(seq_info)
                    
                    # Count pattern mappings for debugging
                    pattern_count = sum(1 for item in seq_info if item.get('is_pattern_mapping', False))
                    regular_count = len(seq_info) - pattern_count
                    
                    print(f"      ✅ Added {len(seq_info)} files for VDB sequence '{seq_name}' ({pattern_count} patterns, {regular_count} regular files)")
                    
                    # Debug: Show pattern mappings
                    for item in seq_info:
                        if item.get('is_pattern_mapping', False):
                            print(f"         💨 VDB Pattern: {item.get('filename', 'NO_FILENAME')}")
                            print(f"            original_path: {item.get('original_path', 'NO_ORIGINAL')}")
                            print(f"            library_path: {item.get('library_path', 'NO_LIBRARY')}")
            
            # Get ALL nodes recursively inside the subnet
            all_nodes = self._collect_all_nodes(parent_node)
            
            print(f"   📋 Scanning {len(all_nodes)} nodes for NON-SEQUENCE geometry file references...")
            
            # Common geometry file extensions
            geometry_extensions = ['.abc', '.fbx', '.obj', '.bgeo', '.bgeo.sc', '.ply', '.vdb', '.sim', '.geo']
            
            # Scan all nodes for geometry file parameters
            for node in all_nodes:
                node_type = node.type().name()
                category = node.type().category().name()
                
                # Only show output for nodes that have geometry files
                # Get ALL parameters on this node
                all_parms = node.parms()
                found_geometry = False
                
                # Check for geometry file parameters
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        # Check if this looks like a NON-BGEO geometry file path
                        # BGEO files are ONLY handled by early pre-scan
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            not any(bgeo_ext in parm_value.lower() for bgeo_ext in ['.bgeo', '.bgeo.sc']) and
                            any(ext in parm_value.lower() for ext in ['.abc', '.fbx', '.obj', '.vdb'])):
                            
                            # Expand Houdini variables
                            expanded_path = hou.expandString(parm_value)
                            
                            # No fallback BGEO sequence detection - rely only on early pre-scan
                            
                            if os.path.exists(expanded_path):
                                # Determine file type and subfolder
                                # Handle compound extensions properly
                                expanded_path_lower = expanded_path.lower()
                                
                                if expanded_path_lower.endswith('.abc'):
                                    subfolder = 'Alembic'
                                elif expanded_path_lower.endswith('.fbx'):
                                    subfolder = 'FBX'
                                elif expanded_path_lower.endswith('.obj'):
                                    subfolder = 'OBJ'
                                elif expanded_path_lower.endswith('.vdb'):
                                    # Skip individual VDB files - they should be handled by VDB sequence detection
                                    print(f"            🔄 SKIPPING individual VDB file (handled by sequence detection): {os.path.basename(expanded_path)}")
                                    continue
                                else:
                                    subfolder = 'Other'
                                
                                geometry_info.append({
                                    'node': node.path(),
                                    'node_name': node.name(),
                                    'parameter': parm.name(),
                                    'file': expanded_path,
                                    'filename': os.path.basename(expanded_path),
                                    'original_path': parm_value,
                                    'file_type': subfolder,
                                    'extension': Path(expanded_path).suffix.lower(),
                                    'is_sequence': False
                                })
                                print(f"            ✅ GEOMETRY FILE FOUND: {os.path.basename(expanded_path)} ({subfolder})")
                            else:
                                print(f"            ❌ GEOMETRY FILE NOT FOUND: {expanded_path}")
                    
                    except Exception as e:
                        # Log the error but continue processing
                        print(f"            ⚠️ Error processing parameter {parm.name()}: {e}")
                        pass
            
            if geometry_info:
                print(f"   📁 Found {len(geometry_info)} geometry files to copy:")
                
                # Create main geometry folder
                geometry_folder = self.asset_folder / "Geometry"
                geometry_folder.mkdir(exist_ok=True)
                print(f"   📁 Created main geometry folder: {geometry_folder}")
                
                # Group geometry files by type
                files_by_type = {}
                for geo_info in geometry_info:
                    file_type = geo_info['file_type']
                    if file_type not in files_by_type:
                        files_by_type[file_type] = []
                    files_by_type[file_type].append(geo_info)
                
                print(f"   📋 Organizing geometry files by {len(files_by_type)} types:")
                for file_type, files in files_by_type.items():
                    print(f"      • {file_type}: {len(files)} files")
                
                # Copy geometry files organized by type
                copied_files = []
                for file_type, files in files_by_type.items():
                    print(f"      🔍 Processing file_type: '{file_type}' with {len(files)} files")
                    # Handle BGEO sequences specially (both uppercase and lowercase)
                    if file_type.startswith('BGEO/') or file_type.startswith('bgeo/'):
                        print(f"      🎬 Using BGEO sequence method for: {file_type}")
                        # This is a BGEO sequence with sequence-specific subfolder
                        self._copy_bgeo_sequence(geometry_folder, file_type, files, copied_files)
                    # Handle VDB sequences specially (lowercase only now)
                    elif file_type.startswith('vdb/'):
                        print(f"      💨 Using VDB sequence method for: {file_type}")
                        # This is a VDB sequence with filename-based subfolder
                        self._copy_vdb_sequence(geometry_folder, file_type, files, copied_files)
                    else:
                        print(f"      📁 Using standard method for: {file_type}")
                        # Standard file copying for other types
                        self._copy_standard_geometry_files(geometry_folder, file_type, files, copied_files)
                
                print(f"   ✅ Copied {len(copied_files)} geometry files organized by type")
                geometry_info = copied_files
            
            else:
                print("   📋 No geometry files found to copy")
            
        except Exception as e:
            print(f"   ⚠️ Error processing geometry files: {e}")
            traceback.print_exc()
        
        return geometry_info

    def _process_bgeo_sequence(self, node, parm, parm_value, expanded_path):
        """Process BGEO sequence and discover all files in the sequence"""
        try:
            print(f"            🎬 Processing BGEO sequence from node: {node.name()}")
            print(f"            📄 Raw pattern: {parm_value}")
            
            # Step 1: Replace ${OS} with node name to get the actual folder path
            actual_path = parm_value
            if '${OS}' in actual_path:
                actual_path = actual_path.replace('${OS}', node.name())
            if '$OS' in actual_path and '${OS}' not in actual_path:
                actual_path = actual_path.replace('$OS', node.name())
            
            # Step 2: Extract directory path and filename pattern
            sequence_file_pattern = Path(actual_path).name
            sequence_dir = str(Path(actual_path).parent)
            
            print(f"            📂 Target directory: {sequence_dir}")
            print(f"            🔍 Looking for pattern: {sequence_file_pattern}")
            
            # Step 3: Extract base filename by removing frame variables
            # From: Library_LibraryExport_v001.${F4}.bgeo.sc
            # Get: Library_LibraryExport_v001
            base_filename = sequence_file_pattern
            frame_vars = ['${F4}', '${F}', '${FF}', '$F4', '$F']
            
            # Remove frame variable to get prefix
            prefix = ""
            for var in frame_vars:
                if var in base_filename:
                    prefix = base_filename.split(var)[0]
                    break
            
            # If no frame variable found, use the whole name minus extension as prefix
            if not prefix:
                if '.bgeo' in base_filename:
                    prefix = base_filename.split('.bgeo')[0]
                else:
                    prefix = base_filename
                    
            # Extract sequence base name (remove trailing dots and frame separators)
            sequence_base_name = prefix.rstrip('._')
            
            print(f"            🏷️  Base prefix: '{prefix}'")
            print(f"            🏷️  Sequence name: '{sequence_base_name}'")
            
            # Step 4: Find all BGEO files in the directory that match the pattern
            sequence_files = []
            sequence_dir_path = Path(sequence_dir)
            
            if sequence_dir_path.exists():
                print(f"            🔍 Scanning directory for BGEO files...")
                
                for file_path in sequence_dir_path.iterdir():
                    if file_path.is_file():
                        filename = file_path.name
                        # Check if it's a BGEO file and starts with our prefix
                        if (filename.lower().endswith(('.bgeo', '.bgeo.sc')) and 
                            filename.startswith(prefix)):
                            sequence_files.append(str(file_path))
                            
                print(f"            ✅ Found {len(sequence_files)} BGEO files matching pattern")
                
                if sequence_files:
                    # Sort files to ensure proper sequence order
                    sequence_files.sort()
                    print(f"            📋 Range: {os.path.basename(sequence_files[0])} → {os.path.basename(sequence_files[-1])}")
                else:
                    print(f"            ❌ No files found starting with '{prefix}' and ending with .bgeo/.bgeo.sc")
                    # Show what files are actually in the directory
                    all_files = [f.name for f in sequence_dir_path.iterdir() if f.is_file()]
                    if all_files:
                        print(f"            📋 Files in directory: {all_files[:5]}{'...' if len(all_files) > 5 else ''}")
                    return None
            else:
                print(f"            ❌ Directory doesn't exist: {sequence_dir_path}")
                return None
            
            # Create geometry info entries for the sequence
            sequence_info = []
            
            for seq_file in sequence_files:
                sequence_info.append({
                    'node': node.path(),
                    'node_name': node.name(),
                    'parameter': parm.name(),
                    'file': seq_file,
                    'filename': os.path.basename(seq_file),
                    'original_path': seq_file,  # Use the ACTUAL file path, not the pattern
                    'file_type': f'bgeo/{sequence_base_name}',  # Use the FILENAME PREFIX as folder name (like VDB)
                    'extension': Path(seq_file).suffix.lower(),
                    'is_sequence': True,
                    'sequence_pattern': parm_value,
                    'sequence_base_name': sequence_base_name,  # Use filename prefix as base name (like VDB)
                    'sequence_total': len(sequence_files)
                })
            
            # Add a special entry for the sequence pattern mapping (for path remapping)
            library_pattern_path = f"Geometry/bgeo/{sequence_base_name}/{os.path.basename(parm_value)}"
            sequence_info.append({
                'node': node.path(),
                'node_name': node.name(),
                'parameter': parm.name(),
                'file': parm_value,  # Keep original pattern with variables
                'filename': os.path.basename(parm_value),
                'original_path': parm_value,  # Original pattern for remapping
                'library_path': library_pattern_path,  # Library pattern for remapping
                'file_type': f'bgeo/{sequence_base_name}',
                'extension': Path(parm_value).suffix.lower(),
                'is_sequence': True,
                'is_pattern_mapping': True,  # Special flag for pattern remapping
                'sequence_pattern': parm_value,
                'sequence_base_name': sequence_base_name,
                'sequence_total': len(sequence_files)
            })
            
            print(f"            ✅ Created sequence info for {len(sequence_info)} files (including pattern mapping)")
            print(f"            📁 Will be organized under: bgeo/{sequence_base_name}/")
            print(f"            🔗 Pattern mapping: {os.path.basename(parm_value)} → {library_pattern_path}")
            return sequence_info
            
        except Exception as e:
            print(f"            ❌ Error processing BGEO sequence: {e}")
            traceback.print_exc()
            return None

    def _copy_bgeo_sequence(self, geometry_folder, file_type, files, copied_files):
        """Copy BGEO sequence files to sequence-specific subfolders"""
        try:
            # Create the bgeo/sequence_name folder structure
            type_folder = geometry_folder / file_type
            type_folder.mkdir(parents=True, exist_ok=True)
            print(f"   📁 Created BGEO sequence folder: {type_folder}")
            
            # Group files by sequence pattern
            sequences = {}
            for geo_info in files:
                sequence_pattern = geo_info.get('sequence_pattern', geo_info['original_path'])
                if sequence_pattern not in sequences:
                    sequences[sequence_pattern] = []
                sequences[sequence_pattern].append(geo_info)
            
            # Process each sequence
            for sequence_pattern, sequence_files in sequences.items():
                # Get sequence base name from the first file for logging
                sequence_base_name = sequence_files[0].get('sequence_base_name', 'unknown')
                print(f"      🎬 Processing BGEO sequence: {sequence_base_name}")
                print(f"         📁 Copying {len(sequence_files)} files to {file_type}/")
                
                copied_in_sequence = 0
                
                for geo_info in sequence_files:
                    # Skip pattern mapping entries during file copying - they don't have real files
                    if geo_info.get('is_pattern_mapping', False):
                        print(f"         🔒 BGEO PATTERN MAPPING PRESERVATION:")
                        print(f"            original_path: {geo_info.get('original_path')}")
                        print(f"            library_path: {geo_info.get('library_path')}")
                        print(f"            is_pattern_mapping: {geo_info.get('is_pattern_mapping')}")
                        
                        # COPY THE LOGIC FROM WORKING REGULAR GEOMETRY FILES
                        # Make a deep copy to ensure pattern mapping isn't modified during individual file processing
                        pattern_copy = copy.deepcopy(geo_info)
                        
                        # Verify the copy preserved the original_path
                        print(f"            AFTER COPY - original_path: {pattern_copy.get('original_path')}")
                        print(f"            AFTER COPY - is_pattern_mapping: {pattern_copy.get('is_pattern_mapping')}")
                        
                        copied_files.append(pattern_copy)
                        continue
                    
                    source_file = Path(geo_info['file'])
                    if source_file.exists():
                        # Create destination filename in sequence-specific folder
                        dest_file = type_folder / source_file.name
                        
                        # Copy the geometry file
                        shutil.copy2(source_file, dest_file)
                        
                        # Update geometry info with new relative path
                        geo_info['copied_file'] = str(dest_file)
                        
                        # Don't overwrite library_path for pattern mappings - they need to preserve frame variables
                        if not geo_info.get('is_pattern_mapping', False):
                            geo_info['library_path'] = f"Geometry/{file_type}/{dest_file.name}"
                        else:
                            print(f"         🔒 Preserving pattern mapping library_path: {geo_info.get('library_path')}")
                        # Pattern mappings keep their original library_path with frame variables
                        
                        copied_files.append(geo_info)
                        copied_in_sequence += 1
                        
                        
                    else:
                        print(f"         ⚠️ BGEO file not found: {source_file}")
                
                print(f"      ✅ Sequence complete: {copied_in_sequence}/{len(sequence_files)} files copied")
                print(f"      📂 Files saved to: Geometry/{file_type}/")
                    
        except Exception as e:
            print(f"      ❌ Error copying BGEO sequence: {e}")
            traceback.print_exc()

    def _copy_standard_geometry_files(self, geometry_folder, file_type, files, copied_files):
        """Copy standard geometry files (ABC, FBX, OBJ, etc.)"""
        try:
            # Create type subfolder
            type_folder = geometry_folder / file_type
            type_folder.mkdir(exist_ok=True)
            print(f"   📁 Created geometry type folder: {type_folder}")
            
            # Copy files for this type
            for geo_info in files:
                try:
                    # Skip pattern mapping entries during file copying - they don't have real files
                    if geo_info.get('is_pattern_mapping', False):
                        print(f"      🔒 Preserving pattern mapping library_path: {geo_info.get('library_path')}")
                        copied_files.append(geo_info)  # Keep pattern mapping in copied_files
                        continue
                    
                    source_file = Path(geo_info['file'])
                    if source_file.exists():
                        # Create destination filename in type folder
                        dest_file = type_folder / source_file.name
                        
                        # Handle duplicate filenames
                        counter = 1
                        original_dest = dest_file
                        while dest_file.exists():
                            stem = original_dest.stem
                            suffix = original_dest.suffix
                            dest_file = type_folder / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        # Copy the geometry file
                        shutil.copy2(source_file, dest_file)
                        
                        print(f"      ✅ Copied: {source_file.name} -> {file_type}/{dest_file.name}")
                        
                        # Update geometry info with new relative path
                        geo_info['copied_file'] = str(dest_file)
                        
                        # Don't overwrite library_path for pattern mappings - they need to preserve frame variables  
                        if not geo_info.get('is_pattern_mapping', False):
                            geo_info['library_path'] = f"Geometry/{file_type}/{dest_file.name}"
                        else:
                            print(f"      🔒 Preserving pattern mapping library_path: {geo_info.get('library_path')}")
                        # Pattern mappings keep their original library_path with frame variables
                        
                        copied_files.append(geo_info)
                        
                    else:
                        print(f"      ⚠️ Geometry file not found: {source_file}")
                
                except Exception as e:
                    print(f"      ❌ Error copying geometry file {geo_info['file']}: {e}")
                    
        except Exception as e:
            print(f"      ❌ Error in standard geometry file copying: {e}")

    def extract_textures_from_material(self, material_node):
        """Extract texture file paths from a material node using comprehensive scanning"""
        texture_info = []
        
        try:
            print(f"         🔍 Extracting textures from material: {material_node.path()}")
            
            # Get material name for folder organization
            material_name = material_node.name()
            
            # Process the material node and all its children recursively
            nodes_to_check = [material_node]
            nodes_to_check.extend(material_node.allSubChildren())
            
            print(f"            📋 Checking {len(nodes_to_check)} nodes in material network...")
            
            for node in nodes_to_check:
                print(f"            🔍 Checking node: {node.name()} ({node.type().name()})")
                
                # Check VOP nodes (most common for textures)
                if node.type().category().name() == 'Vop':
                    # Get ALL parameters on this VOP node
                    all_parms = node.parms()
                    
                    for parm in all_parms:
                        try:
                            parm_value = parm.eval()
                            
                            # Check if this looks like a file path with texture extensions
                            if (isinstance(parm_value, str) and 
                                parm_value.strip() and 
                                any(ext in parm_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx'])):
                                
                                # Expand Houdini variables
                                expanded_path = hou.expandString(parm_value)
                                
                                if os.path.exists(expanded_path):
                                    texture_info.append({
                                        'material': material_node.path(),
                                        'material_name': material_name,
                                        'node': node.path(),
                                        'parameter': parm.name(),
                                        'file': expanded_path,
                                        'filename': os.path.basename(expanded_path),
                                        'original_path': parm_value
                                    })
                                    print(f"               ✅ Found texture: {parm.name()} -> {os.path.basename(expanded_path)}")
                                else:
                                    # Check if it's a UDIM pattern
                                    if '<UDIM>' in parm_value or '<udim>' in parm_value or '<UDIM>' in expanded_path or '<udim>' in expanded_path:
                                        print(f"               📋 UDIM pattern detected: {parm.name()}")
                                        # Try to find actual UDIM files
                                        udim_pattern = expanded_path.replace('<UDIM>', '*').replace('<udim>', '*')
                                        udim_files = glob.glob(udim_pattern)
                                        if udim_files:
                                            print(f"               🎯 Found {len(udim_files)} UDIM files")
                                            for udim_file in udim_files:
                                                texture_info.append({
                                                    'material': material_node.path(),
                                                    'material_name': material_name,
                                                    'node': node.path(),
                                                    'parameter': parm.name(),
                                                    'file': udim_file,
                                                    'filename': os.path.basename(udim_file),
                                                    'original_path': parm_value,
                                                    'is_udim': True
                                                })
                                                print(f"                 • {os.path.basename(udim_file)}")
                                        else:
                                            # Try checking if the base file exists (like .1001)
                                            test_udim = expanded_path.replace('<UDIM>', '1001').replace('<udim>', '1001')
                                            if os.path.exists(test_udim):
                                                texture_info.append({
                                                    'material': material_node.path(),
                                                    'material_name': material_name,
                                                    'node': node.path(),
                                                    'parameter': parm.name(),
                                                    'file': test_udim,
                                                    'filename': os.path.basename(test_udim),
                                                    'original_path': parm_value,
                                                    'is_udim': True
                                                })
                                                print(f"               ✅ Found single UDIM: {os.path.basename(test_udim)}")
                                            else:
                                                print(f"               ❌ UDIM file not found: {expanded_path}")
                                    else:
                                        print(f"               ❌ Texture file not found: {expanded_path}")
                        
                        except Exception as e:
                            pass  # Skip parameters that can't be evaluated
                
                # Also check SHOP materials
                elif node.type().category().name() == 'Shop':
                    all_parms = node.parms()
                    
                    for parm in all_parms:
                        try:
                            parm_value = parm.eval()
                            
                            if (isinstance(parm_value, str) and 
                                parm_value.strip() and 
                                any(ext in parm_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx'])):
                                
                                expanded_path = hou.expandString(parm_value)
                                
                                if os.path.exists(expanded_path):
                                    texture_info.append({
                                        'material': material_node.path(),
                                        'material_name': material_name,
                                        'node': node.path(),
                                        'parameter': parm.name(),
                                        'file': expanded_path,
                                        'filename': os.path.basename(expanded_path),
                                        'original_path': parm_value
                                    })
                                    print(f"               ✅ Found SHOP texture: {parm.name()} -> {os.path.basename(expanded_path)}")
                                else:
                                    # Handle UDIM patterns for SHOP materials too - preserve pattern
                                    if '<UDIM>' in parm_value or '<udim>' in parm_value or '<UDIM>' in expanded_path or '<udim>' in expanded_path:
                                        udim_pattern = expanded_path.replace('<UDIM>', '*').replace('<udim>', '*')
                                        udim_files = glob.glob(udim_pattern)
                                        if udim_files:
                                            print(f"               🎯 UDIM pattern found in material extract with {len(udim_files)} files - preserving pattern")
                                            texture_info.append({
                                                'material': material_node.path(),
                                                'material_name': material_name,
                                                'node': node.path(),
                                                'parameter': parm.name(),
                                                'file': expanded_path,  # Keep the original pattern with <UDIM>
                                                'filename': os.path.basename(expanded_path),
                                                'original_path': parm_value,
                                                'is_udim_pattern': True,  # Mark as UDIM pattern
                                                'udim_files_found': udim_files,
                                                'udim_count': len(udim_files)
                                            })
                        
                        except Exception as e:
                            pass
        
        except Exception as e:
            print(f"      ⚠️ Error extracting textures from {material_node.path()}: {e}")
        
        print(f"         📋 Found {len(texture_info)} textures in material '{material_name}'")
        return texture_info
    
    def _build_accumulative_tags(self):
        """Build comprehensive tag list from multiple sources"""
        tags = set()  # Use set to avoid duplicates
        
        # 1. Add original user-provided tags (split by spaces and commas)
        if self.tags:
            for tag in self.tags:
                if isinstance(tag, str):
                    # Split by both commas and spaces, clean up
                    for word in tag.replace(',', ' ').split():
                        word = word.strip().lower()
                        if word:
                            tags.add(word)
                else:
                    # Handle case where tag is already cleaned
                    tags.add(str(tag).strip().lower())
        
        # 2. Add hierarchy-based tags (folder structure)
        tags.add("3d")  # Always 3D from Houdini
        tags.add(self.asset_type.lower().replace(' ', '_'))  # e.g., "assets", "fx", "materials"
        tags.add(self.subcategory.lower().replace(' ', '_'))  # e.g., "blacksmith_asset", "megascans", "pyro"
        
        # 3. Add render engine as tag
        tags.add(self.render_engine.lower())  # e.g., "redshift", "karma"
        
        # 4. Add asset name words as tags (common search terms)
        for word in self.asset_name.lower().replace('_', ' ').split():
            word = word.strip()
            if word and len(word) > 2:  # Skip very short words
                tags.add(word)
        
        # 5. Add description words as potential tags (if they look like keywords)
        if self.description:
            desc_words = self.description.lower().replace(',', ' ').replace('_', ' ').split()
            for word in desc_words:
                word = word.strip()
                # Only add meaningful words (avoid articles, prepositions, etc.)
                if (word and len(word) > 3 and 
                    word not in ['with', 'from', 'this', 'that', 'have', 'been', 'will', 'they', 'were', 'said', 'each', 'which']):
                    tags.add(word)
        
        # Convert back to sorted list
        return sorted(list(tags))

    def create_asset_metadata(self, template_file, nodes_exported, texture_info=None, geometry_info=None, path_mappings=None):
        """Create metadata JSON for the asset"""
        try:
            if texture_info is None:
                texture_info = []
            if geometry_info is None:
                geometry_info = []
            
            # Get Houdini info if available
            houdini_version = "Unknown"
            hip_file = "Unknown"
            
            if HOU_AVAILABLE:
                try:
                    # Get proper Houdini version
                    version_tuple = hou.applicationVersion()
                    houdini_version = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
                    hip_file = hou.hipFile.path()
                except:
                    try:
                        # Fallback to application version string
                        houdini_version = hou.applicationVersionString()
                    except:
                        pass
            
            # Analyze exported nodes
            node_summary = self.analyze_exported_nodes(nodes_exported)
            
            # Create metadata structure with hierarchy data for frontend filtering
            metadata = {
                "id": self.asset_id,  # Full 16-character UID
                "base_uid": self.base_uid,  # 11-character base UID
                "variant_id": self.variant_id,  # 2-character variant ID
                "asset_base_id": self.asset_base_id,  # 13-character asset base ID (base + variant)
                "version": self.version,  # Version number (integer)
                "version_string": f"{self.version:03d}",  # Padded version string
                "action": self.action,  # Action used to create this asset
                "parent_asset_id": self.parent_asset_id,  # Parent asset ID for versions/variants
                "variant_name": self.variant_name,  # Variant name metadata field
                "name": self.asset_name,
                "asset_type": self.asset_type,
                "subcategory": self.subcategory,
                "description": self.description,
                "render_engine": self.render_engine,
                "tags": self._build_accumulative_tags(),
                "created_at": datetime.now().isoformat(),
                "created_by": self._get_artist_name(),
                
                # Branding information (inherit from parent for versions/variants)
                "branded": self._get_branded_status(),
                
                # Frontend hierarchy filtering structure
                "dimension": "3D",  # Always 3D from Houdini
                "hierarchy": {
                    "dimension": "3D",
                    "asset_type": self.asset_type,  # Assets, FX, Materials, HDAs
                    "subcategory": self.subcategory,  # Blacksmith Asset, Megascans, etc.
                    "render_engine": self.render_engine
                },
                
                # Include any structured metadata passed from Houdini + essential variant info
                "export_metadata": self._build_export_metadata(),
                
                # 🎯 FRAME RANGE INFORMATION (NEW!)
                "frame_range": {
                    "framein": getattr(self, 'framein', 1001),
                    "frameout": getattr(self, 'frameout', 1018),
                    "total_frames": getattr(self, 'frameout', 1018) - getattr(self, 'framein', 1001) + 1,
                    "detection_method": "smart_sequence_detection" if hasattr(self, 'framein') else "default_static"
                },
                
                # Template file info
                "template_file": template_file.name,
                "template_size": template_file.stat().st_size,
                
                # Source info
                "source_hip_file": hip_file,
                "houdini_version": houdini_version,
                
                # Node analysis
                "node_summary": node_summary,
                
                # Export method
                "export_method": "template_based",
                "export_version": "1.0",
                
                # For search functionality
                "search_keywords": self._generate_search_keywords(),
                
                # Texture info (simplified - no verbose mapping)
                "textures": {
                    "count": len(texture_info),
                    "files": [tex['relative_path'] for tex in texture_info if 'relative_path' in tex]
                },
                
                # Geometry file info (simplified - no verbose mapping)
                "geometry_files": {
                    "count": len(geometry_info),
                    "files": [geo['relative_path'] for geo in geometry_info if 'relative_path' in geo]
                },
                
                # Path remapping info (NEW)
                "path_remapping": {
                    "total_remapped": len(path_mappings) if path_mappings else 0,
                    "paths_json_file": "Data/paths.json",
                    "remapped_during_export": True if path_mappings else False
                },
                
                # Direct folder path for file manager access
                "folder_path": str(self.asset_folder)
            }
            
            # Write metadata to file
            metadata_file = self.asset_folder / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"   📋 Created metadata: {metadata_file}")
            
            # Automatically ingest into database via API
            self._ingest_to_database(metadata_file, metadata)
            
            return metadata
            
        except Exception as e:
            print(f"   ⚠️ Error creating metadata: {e}")
            return {}
    
    def analyze_exported_nodes(self, nodes):
        """Analyze the exported nodes for metadata"""
        summary = {
            "total_nodes": len(nodes),
            "node_types": {},
            "categories": {}
        }
        
        for node in nodes:
            node_type = node.type().name()
            category = node.type().category().name()
            
            # Count node types
            if node_type not in summary["node_types"]:
                summary["node_types"][node_type] = 0
            summary["node_types"][node_type] += 1
            
            # Count categories  
            if category not in summary["categories"]:
                summary["categories"][category] = 0
            summary["categories"][category] += 1
        
        return summary
    
    def _create_texture_mapping(self, texture_info):
        """Create comprehensive texture mapping for import reconstruction"""
        import re
        
        # Group textures by their original parameter paths and organize UDIM sequences
        parameter_mappings = {}
        udim_sequences = {}
        
        for tex_info in texture_info:
            if 'relative_path' not in tex_info:
                continue
                
            original_path = tex_info.get('original_path', '')
            library_relative_path = tex_info['relative_path']
            material_name = tex_info.get('material_name', 'Unknown')
            node_path = tex_info.get('node', '')
            parameter_name = tex_info.get('parameter', '')
            filename = tex_info.get('filename', '')
            
            # Create a unique key for this parameter location
            param_key = f"{node_path}:{parameter_name}"
            
            # Check if this is part of a UDIM sequence
            udim_match = re.search(r'\.(\d{4})\.', filename)
            if udim_match:
                # This is a UDIM tile
                udim_tile = udim_match.group(1)
                base_pattern = filename.replace(f'.{udim_tile}.', '.<UDIM>.')
                udim_key = f"{param_key}:{base_pattern}"
                
                if udim_key not in udim_sequences:
                    udim_sequences[udim_key] = {
                        'node_path': node_path,
                        'parameter': parameter_name,
                        'material_name': material_name,
                        'original_pattern': original_path,
                        'library_pattern': library_relative_path.replace(filename, base_pattern),
                        'tiles': [],
                        'is_udim_sequence': True
                    }
                
                udim_sequences[udim_key]['tiles'].append({
                    'tile': udim_tile,
                    'filename': filename,
                    'library_path': library_relative_path
                })
                
                # Check if original path contained <UDIM> pattern
                if '<UDIM>' in original_path or '<udim>' in original_path:
                    udim_sequences[udim_key]['original_had_udim_pattern'] = True
                    # Update the library pattern to use <UDIM>
                    udim_sequences[udim_key]['library_pattern'] = library_relative_path.replace(filename, base_pattern)
                else:
                    udim_sequences[udim_key]['original_had_udim_pattern'] = False
            else:
                # Single texture file
                if param_key not in parameter_mappings:
                    parameter_mappings[param_key] = {
                        'node_path': node_path,
                        'parameter': parameter_name,
                        'material_name': material_name,
                        'original_path': original_path,
                        'library_path': library_relative_path,
                        'filename': filename,
                        'is_udim_sequence': False
                    }
        
        # Merge single textures and UDIM sequences
        final_mapping = {}
        
        # Add single textures
        for param_key, mapping in parameter_mappings.items():
            final_mapping[param_key] = mapping
        
        # Add UDIM sequences (only if they have multiple tiles OR original had UDIM pattern)
        for udim_key, sequence in udim_sequences.items():
            param_key = udim_key.split(':', 2)[0] + ':' + udim_key.split(':', 2)[1]  # Extract node:parameter
            
            if len(sequence['tiles']) > 1 or sequence.get('original_had_udim_pattern', False):
                # This should be treated as a UDIM sequence
                final_mapping[param_key] = {
                    'node_path': sequence['node_path'],
                    'parameter': sequence['parameter'],
                    'material_name': sequence['material_name'],
                    'original_path': sequence['original_pattern'],
                    'library_path': sequence['library_pattern'],
                    'is_udim_sequence': True,
                    'udim_tiles': sequence['tiles'],
                    'tile_count': len(sequence['tiles'])
                }
                print(f"   📋 UDIM sequence mapped: {param_key} -> {sequence['library_pattern']} ({len(sequence['tiles'])} tiles)")
            else:
                # Single UDIM tile, treat as regular texture
                tile_info = sequence['tiles'][0]
                final_mapping[param_key] = {
                    'node_path': sequence['node_path'],
                    'parameter': sequence['parameter'],
                    'material_name': sequence['material_name'],
                    'original_path': sequence['original_pattern'].replace('.<UDIM>.', f'.{tile_info["tile"]}.'),
                    'library_path': tile_info['library_path'],
                    'filename': tile_info['filename'],
                    'is_udim_sequence': False
                }
                print(f"   📋 Single texture mapped: {param_key} -> {tile_info['library_path']}")
        
        print(f"   📋 Created texture mapping for {len(final_mapping)} parameters")
        return final_mapping
    
    def _create_geometry_mapping(self, geometry_info):
        """Create comprehensive geometry file mapping for import reconstruction"""
        
        parameter_mappings = {}
        
        for geo_info in geometry_info:
            if 'relative_path' not in geo_info:
                continue
                
            original_path = geo_info.get('original_path', '')
            library_relative_path = geo_info['relative_path']
            node_path = geo_info.get('node', '')
            parameter_name = geo_info.get('parameter', '')
            filename = geo_info.get('filename', '')
            file_type = geo_info.get('file_type', 'Other')
            
            # Create a unique key for this parameter location
            param_key = f"{node_path}:{parameter_name}"
            
            parameter_mappings[param_key] = {
                'node_path': node_path,
                'parameter': parameter_name,
                'original_path': original_path,
                'library_path': library_relative_path,
                'filename': filename,
                'file_type': file_type,
                'is_geometry_file': True
            }
            
            print(f"   📋 Geometry file mapped: {param_key} -> {library_relative_path} ({file_type})")
        
        print(f"   📋 Created geometry mapping for {len(parameter_mappings)} parameters")
        return parameter_mappings
    
    def _generate_search_keywords(self):
        """Generate search keywords for the asset"""
        keywords = [self.asset_name, self.subcategory]
        keywords.extend(self.tags)
        
        # Add words from asset name
        keywords.extend(self.asset_name.lower().split('_'))
        keywords.extend(self.asset_name.lower().split(' '))
        
        # Remove duplicates and empty strings
        keywords = list(set([k.strip().lower() for k in keywords if k.strip()]))
        
        return keywords

    def remap_paths_before_export(self, parent_node, nodes_to_export, texture_info, geometry_info):
        """
        Remap all file paths from job locations to library locations BEFORE exporting template.
        This ensures the template contains only library paths when saved.
        """
        try:
            
            print(f"   🔍 COMPREHENSIVE PATH REMAPPING BEFORE EXPORT")
            print(f"   📊 Scanning {len(nodes_to_export)} nodes for file path parameters...")
            
            # Check what we received for remapping
            print(f"      Texture info entries: {len(texture_info)}")
            print(f"      Geometry info entries: {len(geometry_info)}")
            if geometry_info:
                pattern_count = sum(1 for geo in geometry_info if geo.get('is_pattern_mapping', False))
                print(f"      Pattern mappings in geometry_info: {pattern_count}")
                # Show first few geometry entries for debugging
                for i, geo_info in enumerate(geometry_info[:3]):
                    is_pattern = geo_info.get('is_pattern_mapping', False)
                    filename = geo_info.get('filename', 'NO_FILENAME')
                    original_path = geo_info.get('original_path', 'NO_ORIGINAL_PATH')
                    library_path = geo_info.get('library_path', 'NO_LIBRARY_PATH')
                    print(f"         Entry {i}: {'🔗PATTERN' if is_pattern else '📄REGULAR'}")
                    print(f"            filename: {filename}")
                    print(f"            original_path: {original_path[:80] if len(str(original_path)) > 80 else original_path}")
                    print(f"            library_path: {library_path}")
            else:
                print(f"      ❌ geometry_info is EMPTY!")
            
            # 1. Collect all nodes recursively (including nested nodes)
            all_nodes = self._collect_all_nodes(parent_node)
            print(f"   📋 Found {len(all_nodes)} total nodes (including nested)")
            
            # 2. Build path mappings from copied file information
            path_mappings = self.build_path_mappings_from_copied_files(texture_info, geometry_info)
            print(f"   📝 Built {len(path_mappings)} initial path mappings from copied files")
            
            # 3. Scan all nodes for file path parameters and discover additional paths
            discovered_paths = self.discover_all_file_paths(all_nodes)
            print(f"   🔍 Discovered {len(discovered_paths)} file path parameters in nodes")
            
            # 4. Try to match discovered paths with copied files or create fallback mappings
            additional_mappings = self.create_additional_path_mappings(discovered_paths, texture_info, geometry_info)
            path_mappings.update(additional_mappings)
            print(f"   ➕ Added {len(additional_mappings)} additional path mappings")
            
            # 5. Update all node parameters to use library paths
            remapped_count = self.update_node_parameters_with_library_paths(all_nodes, path_mappings)
            print(f"   ✅ Updated {remapped_count} node parameters with library paths")
            
            # 6. Save paths.json file in Data folder
            paths_json_file = self.data_folder / "paths.json"
            self.save_paths_json(paths_json_file, path_mappings)
            print(f"   💾 Saved path mappings to: {paths_json_file}")
            
            return path_mappings
            
        except Exception as e:
            print(f"   ❌ Error during path remapping: {e}")
            traceback.print_exc()
            return {}




    def build_path_mappings_from_copied_files(self, texture_info, geometry_info):
        mappings = {}
        try:
            # Add texture path mappings
            for tex_info in texture_info:
                original_path = tex_info.get('original_path')  # The original job path
                # Try both relative_path and library_path for backward compatibility
                library_path = tex_info.get('relative_path') or tex_info.get('library_path')
                is_udim_pattern = tex_info.get('is_udim_pattern', False)
                
                if original_path and library_path:
                    full_library_path = str(self.asset_folder / library_path)
                    mappings[original_path] = full_library_path
                    
                    if is_udim_pattern:
                        print(f"      🎯 UDIM texture mapping: {os.path.basename(original_path)} → {library_path}")
                        # Verify UDIM pattern is preserved
                        if "<UDIM>" in library_path or "<udim>" in library_path:
                            print(f"            ✅ UDIM pattern preserved in library path!")
                        else:
                            print(f"            ⚠️ UDIM pattern NOT found in library path: {library_path}")
                    else:
                        print(f"      🖼️ Texture mapping: {os.path.basename(original_path)} → {library_path}")
                else:
                    print(f"      ❌ Missing texture mapping data - original_path: {bool(original_path)}, library_path: {bool(library_path)}")
            
            # Add geometry path mappings  
            for geo_info in geometry_info:
                original_path = geo_info.get('original_path')  # The original job path
                # Try both relative_path and library_path for backward compatibility
                library_path = geo_info.get('relative_path') or geo_info.get('library_path')
                is_pattern = geo_info.get('is_pattern_mapping', False)
                
                if original_path and library_path:
                    full_library_path = str(self.asset_folder / library_path)
                    mappings[original_path] = full_library_path
                    
                    if is_pattern:
                        print(f"      🎯 BGEO Pattern mapping: {os.path.basename(original_path)} → {library_path}")
                        # Verify frame variables are preserved
                        if "${F4}" in full_library_path or "${F}" in full_library_path:
                            print(f"            ✅ Frame variables preserved in mapping!")
                        else:
                            print(f"            ⚠️ Frame variables NOT found in: {full_library_path}")
                    else:
                        print(f"      🧊 Geometry mapping: {os.path.basename(original_path)} → {library_path}")
                else:
                    print(f"      ❌ Missing mapping data - original_path: {bool(original_path)}, library_path: {bool(library_path)}")
            
            print(f"   📝 Built {len(mappings)} path mappings from copied files")
            return mappings
        except Exception as e:
            print(f"   ❌ Error building path mappings: {e}")
            traceback.print_exc()
            return {}

    def discover_all_file_paths(self, all_nodes):
        discovered_paths = {}
        try:
            file_extensions = ['.abc', '.fbx', '.obj', '.bgeo', '.geo', '.jpg', '.jpeg', '.png', '.exr']
            for node in all_nodes:
                for parm in node.parms():
                    try:
                        parm_value = parm.eval()
                        if (isinstance(parm_value, str) and parm_value.strip() and 
                            any(ext in parm_value.lower() for ext in file_extensions)):
                            param_key = f"{node.path()}::{parm.name()}"
                            discovered_paths[param_key] = parm_value.strip()
                    except:
                        continue
            return discovered_paths
        except:
            return {}

    def create_additional_path_mappings(self, discovered_paths, texture_info, geometry_info):
        additional_mappings = {}
        try:
            copied_files = [t.get('original_path') for t in texture_info + geometry_info if 'original_path' in t]
            for param_key, discovered_path in discovered_paths.items():
                if discovered_path not in copied_files:
                    library_path = self._find_matching_library_file(discovered_path, texture_info, geometry_info)
                    if library_path:
                        full_library_path = str(self.asset_folder / library_path)
                        additional_mappings[discovered_path] = full_library_path
            return additional_mappings
        except:
            return {}

    def _find_matching_library_file(self, original_path, texture_info, geometry_info):
        try:
            original_filename = os.path.basename(original_path)
            for info_list in [texture_info, geometry_info]:
                for info in info_list:
                    if (info.get('original_path') and info.get('relative_path') and 
                        os.path.basename(info['original_path']) == original_filename):
                        return info['relative_path']
            return None
        except:
            return None

    def update_node_parameters_with_library_paths(self, all_nodes, path_mappings):
        """Update all node parameters to use library paths"""
        remapped_count = 0
        
        print(f"   🔄 Starting parameter remapping with {len(path_mappings)} available path mappings:")
        for i, (old_path, new_path) in enumerate(list(path_mappings.items())[:3]):  # Show first 3
            print(f"      {i+1}. {os.path.basename(old_path)} → {os.path.basename(new_path)}")
        if len(path_mappings) > 3:
            print(f"      ... and {len(path_mappings) - 3} more mappings")
        
        try:
            for node in all_nodes:
                node_path = node.path()
                
                # Get all parameters
                all_parms = node.parms()
                
                for parm in all_parms:
                    try:
                        # For BGEO sequence patterns, we need the unexpanded value to preserve frame variables
                        try:
                            unexpanded_value = parm.unexpandedString()
                        except:
                            unexpanded_value = None
                        
                        current_value = parm.eval()
                        
                        if isinstance(current_value, str) and current_value.strip():
                            # First check unexpanded value (preserves frame variables like ${F4})
                            if unexpanded_value and unexpanded_value in path_mappings:
                                new_path = path_mappings[unexpanded_value]
                                
                                print(f"      🔄 Remapping {node_path}::{parm.name()} (pattern)")
                                print(f"         FROM: {unexpanded_value}")
                                print(f"         TO: {new_path}")
                                
                                # Verify frame variables in BGEO sequences
                                if "${F4}" in unexpanded_value or "${F}" in unexpanded_value:
                                    if "${F4}" in new_path or "${F}" in new_path:
                                        print(f"         🎯 BGEO sequence: Frame variables preserved!")
                                    else:
                                        print(f"         ⚠️ BGEO sequence: Frame variables LOST!")
                                
                                # Update the parameter with the new pattern path
                                parm.set(new_path)
                                remapped_count += 1
                                
                            # Otherwise check expanded value (regular file paths)  
                            elif current_value.strip() in path_mappings:
                                old_path = current_value.strip()
                                new_path = path_mappings[old_path]
                                
                                print(f"      🔄 Remapping {node_path}::{parm.name()}")
                                print(f"         FROM: {old_path}")
                                print(f"         TO: {new_path}")
                                
                                # Update the parameter
                                parm.set(new_path)
                                remapped_count += 1
                                
                    except Exception as e:
                        # Silently continue if parameter can't be processed
                        continue
                        
            print(f'   ✅ Successfully remapped {remapped_count} parameters')
            return remapped_count
            
        except Exception as e:
            print(f"   ❌ Error updating parameters: {e}")
            return 0

    def save_paths_json(self, paths_json_file, path_mappings):
        try:
            paths_data = {
                'export_timestamp': str(datetime.now()),
                'asset_id': getattr(self, 'asset_id', 'unknown'),
                'asset_name': self.asset_name,
                'total_mappings': len(path_mappings),
                'path_mappings': {}
            }
            for i, (old_path, new_path) in enumerate(path_mappings.items(), 1):
                key = f'mapping_{i:03d}'
                paths_data['path_mappings'][key] = {
                    'old_path': old_path,
                    'new_path': new_path,
                    'filename': os.path.basename(old_path)
                }
            paths_json_file.parent.mkdir(parents=True, exist_ok=True)
            with open(paths_json_file, 'w') as f:
                json.dump(paths_data, f, indent=2)
            print(f'   💾 Saved {len(path_mappings)} path mappings to paths.json')
        except Exception as e:
            print(f'   ❌ Error saving paths.json: {e}')


class TemplateAssetImporter:
    """Import assets using Houdini's template system"""
    
    def __init__(self, asset_folder):
        self.asset_folder = Path(asset_folder)
        self.data_folder = self.asset_folder / "Data"
    
    def _collect_all_nodes(self, parent_node):
        """Recursively collect all nodes from a parent node"""
        all_nodes = []
        
        def collect_recursive(node):
            """Recursively collect all nodes"""
            for child in node.children():
                all_nodes.append(child)
                collect_recursive(child)  # Recurse into children
        
        collect_recursive(parent_node)
        return all_nodes
    
    def import_into_scene(self, target_parent, as_collapsed_subnet=True):
        """Import the template as a collapsed subnet or expand nodes"""
        try:
            if not HOU_AVAILABLE:
                print("❌ Houdini not available")
                return False
            
            if not self.template_file.exists():
                print(f"❌ Template file not found: {self.template_file}")
                return False
            
            print(f"📦 TEMPLATE IMPORT: {self.asset_folder.name}")
            print(f"   📂 Source: {self.template_file}")
            
            if as_collapsed_subnet:
                # Load metadata to get asset name
                metadata_file = self.asset_folder / "metadata.json"
                asset_name = self.asset_folder.name  # fallback
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        asset_name = metadata.get('name', asset_name)
                        print(f"   📋 Using asset name from metadata: {asset_name}")
                    except Exception as e:
                        print(f"   ⚠️ Could not read metadata: {e}")
                        pass
                
                # Create a subnet to contain the imported content
                print(f"   📦 Creating collapsed subnet: {asset_name}")
                try:
                    # Sanitize asset name for node naming
                    sanitized_node_name = self._sanitize_name_for_filesystem(asset_name)
                    subnet = target_parent.createNode("subnet", sanitized_node_name)
                    subnet.setComment(f"Atlas Asset: {self.asset_folder.name}")
                    subnet.setColor(hou.Color(0.2, 0.8, 0.2))  # Green for imported assets
                    print(f"   ✅ Subnet created: {subnet.path()}")
                except Exception as e:
                    print(f"   ❌ Failed to create subnet: {e}")
                    raise
                
                # Load the template content INTO the subnet
                print(f"   📂 Loading template file: {self.template_file}")
                print(f"   📊 Template file size: {self.template_file.stat().st_size} bytes")
                try:
                    subnet.loadChildrenFromFile(str(self.template_file))
                    print(f"   ✅ Template loaded into subnet")
                    
                    # Check how many children were loaded
                    children = subnet.children()
                    print(f"   📋 Loaded {len(children)} child nodes:")
                    for child in children[:5]:  # Show first 5
                        print(f"      • {child.name()} ({child.type().name()})")
                    if len(children) > 5:
                        print(f"      ... and {len(children)-5} more")
                    
                    # REMAP TEXTURE PATHS TO LIBRARY LOCATIONS
                    print(f"   🔄 Remapping texture paths to library locations...")
                    self.remap_texture_paths(subnet)
                    
                    # REMAP GEOMETRY FILE PATHS TO LIBRARY LOCATIONS
                    print(f"   🔄 Remapping geometry file paths to library locations...")
                    self.remap_geometry_paths(subnet)
                        
                except Exception as e:
                    print(f"   ❌ Failed to load template file: {e}")
                    # Clean up the subnet if template loading failed
                    subnet.destroy()
                    raise
                
                # Keep the subnet collapsed (don't dive inside)
                subnet.setDisplayFlag(True)
                # Only set render flag if the node type supports it (SOP nodes)
                try:
                    if hasattr(subnet, 'setRenderFlag'):
                        subnet.setRenderFlag(True)
                except:
                    pass  # Some node types don't have render flags
                
                print(f"   ✅ Template imported as collapsed subnet: {subnet.path()}")
                return subnet
            else:
                # Original behavior - expand all nodes directly
                target_parent.loadChildrenFromFile(str(self.template_file))
                print(f"   ✅ Template imported with expanded nodes")
                return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            traceback.print_exc()
            return False

    def remap_texture_paths(self, imported_subnet):
        """Remap texture paths from original locations to library locations using metadata mapping"""
        try:
            print(f"   🎯 Starting texture path remapping using metadata mapping...")
            
            # Load the texture mapping from metadata
            metadata_file = self.asset_folder / "metadata.json"
            if not metadata_file.exists():
                print(f"   ⚠️ No metadata file found, skipping texture remapping")
                return
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Get the comprehensive texture mapping
            texture_mapping = metadata.get('textures', {}).get('mapping', {})
            if not texture_mapping:
                print(f"   📋 No texture mapping found in metadata, falling back to comprehensive scan")
                # Fall back to comprehensive scanning
                self._fallback_texture_remapping(imported_subnet, metadata)
                return
            
            print(f"   📋 Found {len(texture_mapping)} texture parameter mappings in metadata")
            
            remapped_count = 0
            
            # Use the precise mapping to update texture parameters
            for param_key, mapping_info in texture_mapping.items():
                try:
                    node_path = mapping_info['node_path']
                    parameter_name = mapping_info['parameter']
                    library_path = mapping_info['library_path']
                    is_udim_sequence = mapping_info.get('is_udim_sequence', False)
                    
                    print(f"      🔍 Remapping parameter: {param_key}")
                    print(f"         Node: {node_path}")
                    print(f"         Parameter: {parameter_name}")
                    print(f"         UDIM Sequence: {is_udim_sequence}")
                    
                    # Find the node in the imported subnet
                    # Remove the original parent path and add the subnet path
                    relative_node_path = node_path.split('/')[-1]  # Get just the node name
                    
                    # Search for the node recursively in the subnet
                    target_node = self._find_node_in_subnet(imported_subnet, relative_node_path)
                    
                    if not target_node:
                        print(f"         ❌ Node not found: {relative_node_path}")
                        continue
                    
                    # Get the parameter
                    if not target_node.parm(parameter_name):
                        print(f"         ❌ Parameter not found: {parameter_name}")
                        continue
                    
                    # Create the full library path
                    full_library_path = str(self.asset_folder / library_path)
                    
                    print(f"         ✅ REMAPPING:")
                    print(f"            TO: {full_library_path}")
                    
                    # Update the parameter
                    target_node.parm(parameter_name).set(full_library_path)
                    remapped_count += 1
                    
                except Exception as e:
                    print(f"         ❌ Error remapping {param_key}: {e}")
                    continue
            
            print(f"   ✅ Metadata-based remapping complete: {remapped_count} parameters remapped")
            
            # Always run fallback scan to catch any missed textures
            print(f"   🔍 Running comprehensive fallback scan to catch any missed textures...")
            self._fallback_texture_remapping(imported_subnet, metadata)
            
        except Exception as e:
            print(f"   ⚠️ Error during texture remapping: {e}")
            traceback.print_exc()

    def _fallback_texture_remapping(self, imported_subnet, metadata):
        """Fallback comprehensive texture scanning and remapping"""
        try:
            print(f"   🔍 FALLBACK: Comprehensive texture parameter scanning...")
            
            # Get texture files list
            texture_files = metadata.get('textures', {}).get('files', [])
            if not texture_files:
                print(f"   📋 No texture files in metadata for fallback")
                return
            
            # Get all nodes recursively in the imported subnet
            all_nodes = self._collect_all_nodes(imported_subnet)
            print(f"   📋 Fallback scanning {len(all_nodes)} nodes...")
            
            # Find all VOP and SHOP nodes that might have texture parameters
            texture_nodes = []
            for node in all_nodes:
                category = node.type().category().name()
                if category in ['Vop', 'Shop']:
                    texture_nodes.append(node)
            
            print(f"   🎯 Fallback found {len(texture_nodes)} VOP/SHOP nodes to check")
            
            fallback_remapped = 0
            
            # For each texture node, check all parameters for texture paths
            for node in texture_nodes:
                print(f"      🔍 Fallback checking {node.path()}")
                
                all_parms = node.parms()
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        # Check if this looks like a texture file path
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            any(ext in parm_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx'])):
                            
                            # Check if this is still pointing to original location (not library)
                            if not str(self.asset_folder) in parm_value:
                                print(f"         🖼️ Found non-library texture: {parm.name()} = '{parm_value}'")
                                
                                # Try to find a matching library texture
                                library_path = self._find_matching_library_texture(parm_value, texture_files)
                                
                                if library_path:
                                    full_library_path = str(self.asset_folder / library_path)
                                    print(f"         ✅ FALLBACK REMAPPING:")
                                    print(f"            FROM: {parm_value}")
                                    print(f"            TO:   {full_library_path}")
                                    
                                    # Update the parameter
                                    parm.set(full_library_path)
                                    fallback_remapped += 1
                                else:
                                    print(f"         ⚠️ No library match found for: {os.path.basename(parm_value)}")
                                
                    except Exception as e:
                        pass  # Skip parameters that can't be evaluated
            
            print(f"   ✅ Fallback remapping complete: {fallback_remapped} additional textures remapped")
            
        except Exception as e:
            print(f"   ⚠️ Error during fallback texture remapping: {e}")

    def _find_matching_library_texture(self, original_path, texture_files):
        """Find matching library texture for fallback remapping"""
        import re
        
        original_filename = os.path.basename(original_path)
        
        # Direct filename match
        for texture_file in texture_files:
            if os.path.basename(texture_file) == original_filename:
                return texture_file
        
        # UDIM pattern matching
        udim_match = re.search(r'\.(\d{4})\.', original_filename)
        if udim_match:
            # Convert to UDIM pattern
            udim_tile = udim_match.group(1)
            udim_pattern = original_filename.replace(f'.{udim_tile}.', '.<UDIM>.')
            
            for texture_file in texture_files:
                if os.path.basename(texture_file) == udim_pattern:
                    return texture_file
        
        # Check if original has <UDIM> pattern
        if '<UDIM>' in original_filename or '<udim>' in original_filename:
            normalized_original = original_filename.replace('<udim>', '<UDIM>')
            for texture_file in texture_files:
                if os.path.basename(texture_file) == normalized_original:
                    return texture_file
        
        return None

    def _find_node_in_subnet(self, subnet, node_name):
        """Find a node by name recursively in the subnet"""
        # Check direct children first
        for child in subnet.children():
            if child.name() == node_name:
                return child
        
        # Search recursively in all children
        for child in subnet.children():
            found_node = self._find_node_recursively(child, node_name)
            if found_node:
                return found_node
        
        return None
    
    def _find_node_recursively(self, parent_node, node_name):
        """Recursively search for a node by name"""
        # Check direct children
        for child in parent_node.children():
            if child.name() == node_name:
                return child
        
        # Search in grandchildren
        for child in parent_node.children():
            found_node = self._find_node_recursively(child, node_name)
            if found_node:
                return found_node
        
        return None

    def remap_geometry_paths(self, imported_subnet):
        """Remap geometry file paths from original locations to library locations"""
        try:
            print(f"   🎯 Starting geometry file path remapping...")
            
            # Load the geometry mapping from metadata
            metadata_file = self.asset_folder / "metadata.json"
            if not metadata_file.exists():
                print(f"   ⚠️ No metadata file found, skipping geometry remapping")
                return
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Get the comprehensive geometry mapping
            geometry_mapping = metadata.get('geometry_files', {}).get('mapping', {})
            if not geometry_mapping:
                print(f"   📋 No geometry mapping found in metadata, running fallback scan")
                self._fallback_geometry_remapping(imported_subnet, metadata)
                return
            
            print(f"   📋 Found {len(geometry_mapping)} geometry file parameter mappings in metadata")
            
            remapped_count = 0
            
            # Use the precise mapping to update geometry file parameters
            for param_key, mapping_info in geometry_mapping.items():
                try:
                    node_path = mapping_info['node_path']
                    parameter_name = mapping_info['parameter']
                    library_path = mapping_info['library_path']
                    file_type = mapping_info.get('file_type', 'Other')
                    
                    print(f"      🔍 Remapping geometry parameter: {param_key}")
                    print(f"         Node: {node_path}")
                    print(f"         Parameter: {parameter_name}")
                    print(f"         File Type: {file_type}")
                    
                    # Find the node in the imported subnet
                    relative_node_path = node_path.split('/')[-1]  # Get just the node name
                    target_node = self._find_node_in_subnet(imported_subnet, relative_node_path)
                    
                    if not target_node:
                        print(f"         ❌ Node not found: {relative_node_path}")
                        continue
                    
                    # Get the parameter
                    if not target_node.parm(parameter_name):
                        print(f"         ❌ Parameter not found: {parameter_name}")
                        continue
                    
                    # Create the full library path
                    full_library_path = str(self.asset_folder / library_path)
                    
                    print(f"         ✅ REMAPPING GEOMETRY FILE:")
                    print(f"            TO: {full_library_path}")
                    
                    # Update the parameter
                    target_node.parm(parameter_name).set(full_library_path)
                    remapped_count += 1
                    
                except Exception as e:
                    print(f"         ❌ Error remapping geometry {param_key}: {e}")
                    continue
            
            print(f"   ✅ Metadata-based geometry remapping complete: {remapped_count} parameters remapped")
            
            # Always run fallback scan to catch any missed geometry files
            print(f"   🔍 Running comprehensive fallback scan for missed geometry files...")
            self._fallback_geometry_remapping(imported_subnet, metadata)
            
        except Exception as e:
            print(f"   ⚠️ Error during geometry file remapping: {e}")
            traceback.print_exc()

    def _fallback_geometry_remapping(self, imported_subnet, metadata):
        """Fallback comprehensive geometry file scanning and remapping"""
        try:
            print(f"   🔍 FALLBACK: Comprehensive geometry file parameter scanning...")
            
            # Get geometry files list
            geometry_files = metadata.get('geometry_files', {}).get('files', [])
            if not geometry_files:
                print(f"   📋 No geometry files in metadata for fallback")
                return
            
            # Get all nodes recursively in the imported subnet
            all_nodes = self._collect_all_nodes(imported_subnet)
            print(f"   📋 Fallback scanning {len(all_nodes)} nodes for geometry files...")
            
            # Common geometry file extensions
            geometry_extensions = ['.abc', '.fbx', '.obj', '.bgeo', '.bgeo.sc', '.ply', '.vdb', '.sim', '.geo']
            
            fallback_remapped = 0
            
            # Scan all nodes for geometry file parameters
            for node in all_nodes:
                all_parms = node.parms()
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        # Check if this looks like a geometry file path
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            any(ext in parm_value.lower() for ext in geometry_extensions)):
                            
                            # Check if this is still pointing to original location (not library)
                            if not str(self.asset_folder) in parm_value:
                                print(f"         📁 Found non-library geometry file: {parm.name()} = '{parm_value}'")
                                
                                # Try to find a matching library geometry file
                                library_path = self._find_matching_library_geometry(parm_value, geometry_files)
                                
                                if library_path:
                                    full_library_path = str(self.asset_folder / library_path)
                                    print(f"         ✅ FALLBACK GEOMETRY REMAPPING:")
                                    print(f"            FROM: {parm_value}")
                                    print(f"            TO:   {full_library_path}")
                                    
                                    # Update the parameter
                                    parm.set(full_library_path)
                                    fallback_remapped += 1
                                else:
                                    print(f"         ⚠️ No library match found for: {os.path.basename(parm_value)}")
                                
                    except Exception as e:
                        pass  # Skip parameters that can't be evaluated
            
            print(f"   ✅ Fallback geometry remapping complete: {fallback_remapped} additional files remapped")
            
        except Exception as e:
            print(f"   ⚠️ Error during fallback geometry remapping: {e}")

    def _find_matching_library_geometry(self, original_path, geometry_files):
        """Find matching library geometry file for fallback remapping"""
        original_filename = os.path.basename(original_path)
        
        # Direct filename match
        for geometry_file in geometry_files:
            if os.path.basename(geometry_file) == original_filename:
                return geometry_file
        
        # BGEO sequence matching
        original_lower = original_filename.lower()
        if original_lower.endswith('.bgeo') or original_lower.endswith('.bgeo.sc'):
            # Check if original path has frame variables
            if any(var in original_path for var in ['${F4}', '${F}', '${FF}', '$F4', '$F']):
                # For sequence patterns, return the pattern itself to be used in remapping
                for geometry_file in geometry_files:
                    # Look for BGEO files in node-specific or sequence-specific subfolders  
                    geometry_file_lower = geometry_file.lower()
                    if (('BGEO/' in geometry_file or 'bgeo/' in geometry_file) and 
                        (geometry_file_lower.endswith('.bgeo') or geometry_file_lower.endswith('.bgeo.sc'))):
                        # Check if this could be from the same sequence
                        geo_basename = os.path.basename(geometry_file)
                        original_basename = os.path.basename(original_path)
                        
                        # Remove frame variables for comparison
                        original_pattern = original_basename
                        for var in ['${F4}', '${F}', '${FF}', '$F4', '$F']:
                            original_pattern = original_pattern.replace(var, '*')
                        
                        # Use glob-like matching
                        if fnmatch.fnmatch(geo_basename, original_pattern):
                            # Return the pattern with the correct library path structure
                            library_pattern = geometry_file.replace(geo_basename, os.path.basename(original_path))
                            return library_pattern
        
        return None

    def _ingest_to_database(self, metadata_file, metadata):
        """Automatically ingest the exported asset into the database via API"""
        try:
            print(f"   🔄 Starting auto-ingestion process...")
            
            # Use subprocess for curl commands (no external dependencies needed)
            
            # Define API endpoint
            api_url = f"{atlas_config.api_base_url}/api/v1/assets"
            
            # Prepare asset data for API (match AssetCreateRequest schema)
            # Use ONLY the 16-character UID as database key (no suffix)
            database_key = self.asset_id  # Always use the pure 16-character UID
            
            asset_data = {
                "name": metadata.get("name", self.asset_name),
                "category": metadata.get("subcategory", self.subcategory),
                "paths": {
                    "asset_folder": str(self.asset_folder),
                    "template_file": metadata.get("template_file", ""),
                    "metadata": str(metadata_file)
                },
                "metadata": {
                    # Include hierarchy for frontend filtering
                    "hierarchy": metadata.get("hierarchy", {
                        "dimension": "3D",
                        "asset_type": metadata.get("asset_type", self.asset_type),
                        "subcategory": metadata.get("subcategory", self.subcategory),
                        "render_engine": metadata.get("render_engine", self.render_engine)
                    }),
                    # Include all original metadata
                    **metadata,
                    # Additional API-specific metadata
                    "tags": metadata.get("tags", []),
                    "created_at": metadata.get("created_at", ""),
                    "created_by": metadata.get("created_by", "unknown"),
                    "status": "active",
                    "dimension": "3D"
                },
                "file_sizes": metadata.get("file_sizes", {})
            }
            
            
            # Make API request using curl
            try:
                
                # Convert asset_data to JSON for curl
                json_data = json.dumps(asset_data)
                
                # Use curl via subprocess
                curl_cmd = [
                    'curl', '-X', 'POST',
                    api_url,
                    '-H', 'Content-Type: application/json',
                    '-H', 'User-Agent: Houdini-Atlas-Export/1.0',
                    '-d', json_data,
                    '--silent',  # Suppress progress output
                    '--show-error'  # Show errors
                ]
                
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
                
                
                if result.returncode == 0:
                    try:
                        response_data = json.loads(result.stdout)
                        asset_id = response_data.get("id", "unknown")
                        print(f"   ✅ Asset successfully ingested into database!")
                        print(f"      🆔 Database ID: {asset_id}")
                        print(f"      📊 Asset available in Atlas frontend")
                        return True
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Invalid JSON response: {e}")
                        print(f"      Raw response: {result.stdout}")
                        return False
                else:
                    print(f"   ❌ Curl request failed with exit code: {result.returncode}")
                    print(f"      Error output: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print(f"   ❌ API request timed out after 30 seconds")
                print(f"   💡 Manual ingestion: Use API client to ingest {metadata_file}")
                return False
            
            except Exception as e:
                print(f"   ❌ Request failed with error: {e}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error during auto-ingestion: {e}")
            print(f"   💡 Manual ingestion: Use API client to ingest {metadata_file}")
            traceback.print_exc()
            return False
