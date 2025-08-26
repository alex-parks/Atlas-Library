#!/usr/bin/env python3
"""
Blacksmith Atlas - Template-Based Asset Exporter
===============================================

This module provides template-based asset export using Houdini's native 
saveChildrenToFile/loadChildrenFromFile methods for perfect reconstruction.
"""

import os
import sys
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

class TemplateAssetExporter:
    """Export assets using Houdini's template system"""
    
    def __init__(self, asset_name, subcategory="Props", description="", tags=None, asset_type=None, render_engine=None, metadata=None, action="create_new", parent_asset_id=None, variant_name=None):
        self.asset_name = asset_name
        self.subcategory = subcategory  
        self.description = description
        self.tags = tags or []
        self.asset_type = asset_type or "Assets"
        self.render_engine = render_engine or "Redshift"
        self.metadata = metadata or ""
        self.action = action
        self.parent_asset_id = parent_asset_id
        
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
        
        # Generate unique asset ID (9 character base UID + 3 digit version = 12 characters total)
        import uuid
        import re
        
        if action == "create_new":
            # Generate new 9-character base UID + 2-character variant + 3-digit version = 14 characters total
            self.base_uid = str(uuid.uuid4()).replace('-', '')[:9].upper()
            self.variant_id = "AA"  # Always start with AA variant for new assets
            self.version = 1
        elif action == "version_up":
            # For version_up: expects 11 characters (9 base + 2 variant)
            if not parent_asset_id or len(parent_asset_id) != 11:
                raise ValueError(f"Parent asset ID required for version_up and must be exactly 11 characters (9 base + 2 variant)")
            self.base_uid = parent_asset_id[:9].upper()  # First 9 characters as base UID
            self.variant_id = parent_asset_id[9:11].upper()  # Characters 9-11 as variant ID
            self.version = self._get_next_version(parent_asset_id, action)  # Pass full 11-char asset ID
        elif action == "variant":
            # For variant: expects 9 characters (base UID only)
            if not parent_asset_id or len(parent_asset_id) != 9:
                raise ValueError(f"Parent asset ID required for variant and must be exactly 9 characters (base UID)")
            self.base_uid = parent_asset_id.upper()  # Use the 9-character base UID
            # Generate next variant ID based on existing variants for this base UID
            self.variant_id = self._get_next_variant_id(self.base_uid)
            self.version = 1  # Reset version to 001 for new variant
        else:
            raise ValueError(f"Invalid action: {action}. Must be 'create_new', 'version_up', or 'variant'")
        
        # Create full 14-character asset ID (9 base + 2 variant + 3 version)
        self.asset_id = f"{self.base_uid}{self.variant_id}{self.version:03d}"
        
        # The 11-character asset ID (without version) for referencing
        self.asset_base_id = f"{self.base_uid}{self.variant_id}"
        
        # Set variant_name for version_up if not already set
        if action == "version_up" and self.variant_name is None:
            self.variant_name = self._get_variant_name_from_parent(parent_asset_id)
        
        # Sanitize asset name for display purposes only
        self.sanitized_asset_name = re.sub(r'[^a-zA-Z0-9_-]', '_', asset_name)
        
        # Set up paths based on hierarchy structure
        self.library_root = Path("/net/library/atlaslib/3D")
        
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
        
        # Asset folder is named with the full 14-character UID
        self.asset_folder = self.library_root / asset_type / subcategory_folder / self.asset_id
        self.data_folder = self.asset_folder / "Data"
        self.textures_folder = self.asset_folder / "Textures"
        self.geometry_folder = self.asset_folder / "Geometry"
        
        # Database key is the full 14-character UID
        self.database_key = self.asset_id
    
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
                # Query the Atlas API to find existing versions for this asset (11-char base + variant)
                print(f"   🔍 Looking up existing versions for asset base ID: {asset_base_id}")
                
                try:
                    import urllib.request
                    import json
                    
                    # Query the Atlas API to get all assets
                    api_url = "http://localhost:8000/api/v1/assets?limit=1000"
                    print(f"   🌐 Making API request to: {api_url}")
                    
                    response = urllib.request.urlopen(api_url, timeout=30)
                    assets_data = json.loads(response.read().decode())
                    all_assets = assets_data.get('items', [])
                    
                    print(f"   📊 Found {len(all_assets)} total assets in database")
                    
                    # Filter assets that match the asset base ID (first 11 characters: 9 base + 2 variant)
                    matching_assets = []
                    for asset in all_assets:
                        asset_id = asset.get('id', '')
                        if len(asset_id) >= 11 and asset_id[:11].upper() == asset_base_id.upper():
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
                        if len(asset_id) == 14:  # 14-character UIDs now
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
                import urllib.request
                import json
                
                # Query the Atlas API to get all assets
                api_url = "http://localhost:8000/api/v1/assets?limit=1000"
                print(f"   🌐 Making API request to: {api_url}")
                
                response = urllib.request.urlopen(api_url, timeout=30)
                assets_data = json.loads(response.read().decode())
                all_assets = assets_data.get('items', [])
                
                print(f"   📊 Found {len(all_assets)} total assets in database")
                
                # Filter assets that match the base UID (first 9 characters)
                matching_variants = set()
                print(f"   🔍 Searching for base UID: '{base_uid.upper()}'")
                
                for asset in all_assets:
                    asset_id = asset.get('id', '')
                    if len(asset_id) >= 11:
                        asset_base = asset_id[:9].upper()
                        if asset_base == base_uid.upper():
                            variant_id = asset_id[9:11].upper()
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
            
            import urllib.request
            import json
            
            # Query the Atlas API to get all assets and find ones matching the 11-char pattern
            api_url = "http://localhost:8000/api/v1/assets?limit=1000"
            print(f"   🌐 Making API request to: {api_url}")
            
            response = urllib.request.urlopen(api_url, timeout=30)
            assets_data = json.loads(response.read().decode())
            all_assets = assets_data.get('items', [])
            
            # Find assets that match the 11-character pattern (ignore version)
            matching_assets = []
            for asset in all_assets:
                asset_id = asset.get('id', '')
                if len(asset_id) >= 11 and asset_id[:11].upper() == parent_asset_id.upper():
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
    
    def export_as_template(self, parent_node, nodes_to_export):
        """Export nodes as template using saveChildrenToFile"""
        try:
            if not HOU_AVAILABLE:
                print("❌ Houdini not available")
                return False
            
            print(f"🚀 TEMPLATE EXPORT: {self.asset_name}")
            print(f"   📂 Target: {self.asset_folder}")
            
            # Create directories
            self.asset_folder.mkdir(parents=True, exist_ok=True)
            self.data_folder.mkdir(exist_ok=True)
            
            # PRE-SCAN: Detect BGEO sequences with original paths (before any remapping)
            print(f"   🎬 PRE-SCANNING FOR BGEO SEQUENCES WITH ORIGINAL PATHS...")
            bgeo_sequences = self.detect_bgeo_sequences_early(parent_node)
            
            # Process materials and copy textures FIRST
            texture_info = self.process_materials_and_textures(parent_node, nodes_to_export)
            
            # Process geometry files and copy them (now with BGEO sequence info)
            geometry_info = self.process_geometry_files(parent_node, nodes_to_export, bgeo_sequences)
            
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
            
            print(f"✅ Export complete: {self.asset_folder}")
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_materials_and_textures(self, parent_node, nodes_to_export):
        """Process materials and copy textures using comprehensive scanning like test script"""
        texture_info = []
        
        try:
            print("   🔍 NEW COMPREHENSIVE SCANNING METHOD ACTIVE! 🎯")
            print("   🔍 Scanning for materials and textures using comprehensive method...")
            
            # Get ALL nodes recursively inside the subnet (like our test script)
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)  # Recurse into children
            
            collect_all_nodes(parent_node)
            
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
            import traceback
            traceback.print_exc()
        
        return texture_info

    def detect_bgeo_sequences_early(self, parent_node):
        """Detect BGEO sequences before any path remapping occurs"""
        bgeo_sequences = {}
        
        try:
            print("      🔍 EARLY BGEO SCAN: Scanning for BGEO sequences with original frame variables...")
            
            # Get ALL nodes recursively
            all_nodes = []
            def collect_all_nodes(parent_node):
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)
            
            collect_all_nodes(parent_node)
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
            import traceback
            traceback.print_exc()
            return {}

    def process_geometry_files(self, parent_node, nodes_to_export, bgeo_sequences=None):
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
            
            # Get ALL nodes recursively inside the subnet
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)  # Recurse into children
            
            collect_all_nodes(parent_node)
            
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
                                    subfolder = 'VDB'
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
            import traceback
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
                    'file_type': f'bgeo/{node.name()}',  # Use the NODE NAME as folder name
                    'extension': Path(seq_file).suffix.lower(),
                    'is_sequence': True,
                    'sequence_pattern': parm_value,
                    'sequence_base_name': node.name(),  # Use node name as base name
                    'sequence_total': len(sequence_files)
                })
            
            # Add a special entry for the sequence pattern mapping (for path remapping)
            library_pattern_path = f"Geometry/bgeo/{node.name()}/{os.path.basename(parm_value)}"
            sequence_info.append({
                'node': node.path(),
                'node_name': node.name(),
                'parameter': parm.name(),
                'file': parm_value,  # Keep original pattern with variables
                'filename': os.path.basename(parm_value),
                'original_path': parm_value,  # Original pattern for remapping
                'library_path': library_pattern_path,  # Library pattern for remapping
                'file_type': f'bgeo/{node.name()}',
                'extension': Path(parm_value).suffix.lower(),
                'is_sequence': True,
                'is_pattern_mapping': True,  # Special flag for pattern remapping
                'sequence_pattern': parm_value,
                'sequence_base_name': node.name(),
                'sequence_total': len(sequence_files)
            })
            
            print(f"            ✅ Created sequence info for {len(sequence_info)} files (including pattern mapping)")
            print(f"            📁 Will be organized under: bgeo/{node.name()}/")
            print(f"            🔗 Pattern mapping: {os.path.basename(parm_value)} → {library_pattern_path}")
            return sequence_info
            
        except Exception as e:
            print(f"            ❌ Error processing BGEO sequence: {e}")
            import traceback
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
                        import copy
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
            import traceback
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
                "id": self.asset_id,  # Full 14-character UID
                "base_uid": self.base_uid,  # 9-character base UID
                "variant_id": self.variant_id,  # 2-character variant ID
                "asset_base_id": self.asset_base_id,  # 11-character asset base ID (base + variant)
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
                "tags": self.tags,
                "created_at": datetime.now().isoformat(),
                "created_by": self._get_artist_name(),
                
                # Frontend hierarchy filtering structure
                "dimension": "3D",  # Always 3D from Houdini
                "hierarchy": {
                    "dimension": "3D",
                    "asset_type": self.asset_type,  # Assets, FX, Materials, HDAs
                    "subcategory": self.subcategory,  # Blacksmith Asset, Megascans, etc.
                    "render_engine": self.render_engine
                },
                
                # Include any structured metadata passed from Houdini
                "export_metadata": self.metadata if isinstance(self.metadata, dict) else {},
                
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
            import json
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
            import json
            from datetime import datetime
            
            print(f"   🔍 COMPREHENSIVE PATH REMAPPING BEFORE EXPORT")
            print(f"   📊 Scanning {len(nodes_to_export)} nodes for file path parameters...")
            
            # DEBUG: Check what we received
            print(f"   🚨 DEBUG: Received for path remapping:")
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
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)  # Recurse into children
            
            collect_all_nodes(parent_node)
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
            import traceback
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
            import traceback
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
            import json
            from datetime import datetime
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
        self.template_file = self.data_folder / "template.hipnc"
    
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
                    import json
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
                    subnet = target_parent.createNode("subnet", asset_name)
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
            import traceback
            traceback.print_exc()
            return False

    def remap_paths_before_export(self, parent_node, nodes_to_export, texture_info, geometry_info):
        """
        Remap all file paths from job locations to library locations BEFORE exporting template.
        This ensures the template contains only library paths when saved.
        """
        try:
            import json
            from datetime import datetime
            
            print(f"   🔍 COMPREHENSIVE PATH REMAPPING BEFORE EXPORT")
            print(f"   📊 Scanning {len(nodes_to_export)} nodes for file path parameters...")
            
            # DEBUG: Check what we received
            print(f"   🚨 DEBUG: Received for path remapping:")
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
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)  # Recurse into children
            
            collect_all_nodes(parent_node)
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
            import traceback
            traceback.print_exc()
            return {}

    def build_path_mappings_from_copied_files(self, texture_info, geometry_info):
        """Build path mappings dictionary from copied texture and geometry file information"""
        mappings = {}
        
        try:
            # Add texture path mappings
            for tex_info in texture_info:
                original_path = tex_info.get('original_path')
                library_path = tex_info.get('library_path')
                
                if original_path and library_path:
                    # Convert library relative path to full path
                    full_library_path = str(self.asset_folder / library_path)
                    mappings[original_path] = full_library_path
                    print(f"      🖼️ Texture mapping: {os.path.basename(original_path)} → {library_path}")
            
            # Add geometry path mappings  
            print(f"      🔍 Processing {len(geometry_info)} geometry entries...")
            
            # DEBUG: Show all pattern mapping entries first
            pattern_count = 0
            regular_count = 0
            
            print(f"      🔍 DETAILED PATTERN MAPPING DEBUG:")
            for i, geo_info in enumerate(geometry_info):
                is_pattern = geo_info.get('is_pattern_mapping', False)
                if is_pattern:
                    pattern_count += 1
                    print(f"         🔗 PATTERN #{pattern_count}: Entry {i}")
                    print(f"            file: {geo_info.get('file', 'MISSING')}")
                    print(f"            original_path: {geo_info.get('original_path', 'MISSING')}")
                    print(f"            library_path: {geo_info.get('library_path', 'MISSING')}")
                    print(f"            is_pattern_mapping: {is_pattern}")
                    print(f"            Keys in entry: {list(geo_info.keys())}")
                else:
                    regular_count += 1
            
            print(f"      📊 Geometry entries breakdown: {pattern_count} patterns, {regular_count} regular files")
            
            # If no patterns found but we expected some, show first few entries
            if pattern_count == 0 and len(geometry_info) > 0:
                print(f"      ⚠️ NO PATTERN MAPPINGS FOUND! Showing first 3 entries:")
                for i in range(min(3, len(geometry_info))):
                    geo_info = geometry_info[i]
                    print(f"         Entry {i}: is_pattern_mapping={geo_info.get('is_pattern_mapping', 'MISSING')}")
                    print(f"            Keys: {list(geo_info.keys())}")
                    print(f"            original_path: {geo_info.get('original_path', 'MISSING')}")
            
            for geo_info in geometry_info:
                original_path = geo_info.get('original_path')
                library_path = geo_info.get('library_path')
                is_pattern = geo_info.get('is_pattern_mapping', False)
                
                print(f"         📄 Geo entry: {os.path.basename(original_path) if original_path else 'NO ORIGINAL_PATH'}")
                print(f"            original_path: {original_path}")
                print(f"            library_path: {library_path}")
                print(f"            is_pattern_mapping: {is_pattern}")
                
                if original_path and library_path:
                    # Convert library relative path to full path
                    full_library_path = str(self.asset_folder / library_path)
                    mappings[original_path] = full_library_path
                    
                    if is_pattern:
                        print(f"            ✅ BGEO Pattern mapping added: {os.path.basename(original_path)} → {library_path}")
                        # Verify frame variables are preserved
                        if "${F4}" in full_library_path or "${F}" in full_library_path:
                            print(f"            🎯 Frame variables preserved in mapping!")
                        else:
                            print(f"            ⚠️ Frame variables NOT found in: {full_library_path}")
                    else:
                        print(f"            ✅ Regular geometry mapping added: {os.path.basename(original_path)} → {library_path}")
                else:
                    if not original_path:
                        print(f"            ❌ Missing original_path")
                    if not library_path:
                        print(f"            ❌ Missing library_path")
            
            print(f"   📝 Built {len(mappings)} path mappings from copied files")
            return mappings
            
        except Exception as e:
            print(f"   ❌ Error building path mappings: {e}")
            return {}

    def discover_all_file_paths(self, all_nodes):
        """Scan all nodes and parameters to discover file path references"""
        discovered_paths = {}  # {parameter_key: path_value}
        
        try:
            # Common file extensions to look for
            file_extensions = [
                # Geometry files
                '.abc', '.fbx', '.obj', '.bgeo', '.geo', '.ply', '.stl', '.usd', '.usda', '.usdc',
                # Texture files  
                '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx',
                # Cache files
                '.sim', '.cache', '.vdb', '.f3d',
                # Other formats
                '.mov', '.mp4', '.avi', '.exr', '.dpx'
            ]
            
            for node in all_nodes:
                node_path = node.path()
                print(f"      🔍 Scanning node: {node_path}")
                
                # Get all parameters
                all_parms = node.parms()
                
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        # Check if this looks like a file path
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            len(parm_value.strip()) > 3 and
                            any(ext in parm_value.lower() for ext in file_extensions)):
                            
                            # Store with unique key
                            param_key = f"{node_path}::{parm.name()}"
                            discovered_paths[param_key] = parm_value.strip()
                            
                            print(f"         📄 Found file path: {parm.name()} = '{parm_value}'")
                            
                    except Exception as e:
                        # Skip parameters that can't be evaluated
                        continue
            
            print(f"   🔍 Discovered {len(discovered_paths)} file path parameters")
            return discovered_paths
            
        except Exception as e:
            print(f"   ❌ Error discovering file paths: {e}")
            return {}

    def create_additional_path_mappings(self, discovered_paths, texture_info, geometry_info):
        """Create additional path mappings for discovered paths that weren't in copied files"""
        additional_mappings = {}
        
        try:
            # Get lists of copied files for matching
            copied_texture_files = [tex['original_path'] for tex in texture_info if 'original_path' in tex]
            copied_geometry_files = [geo['original_path'] for geo in geometry_info if 'original_path' in geo]
            
            for param_key, discovered_path in discovered_paths.items():
                # Skip if we already have a mapping for this exact path
                if discovered_path in additional_mappings:
                    continue
                
                # Try to find this path in our copied files
                if discovered_path in copied_texture_files or discovered_path in copied_geometry_files:
                    # This path was already handled in build_path_mappings_from_copied_files
                    continue
                
                # Try to find a similar file by name matching
                library_path = self._find_matching_library_file(discovered_path, texture_info, geometry_info)
                
                if library_path:
                    full_library_path = str(self.asset_folder / library_path)
                    additional_mappings[discovered_path] = full_library_path
                    print(f"      🔗 Additional mapping: {os.path.basename(discovered_path)} → {library_path}")
                else:
                    print(f"      ⚠️ No library match found for: {discovered_path}")
            
            return additional_mappings
            
        except Exception as e:
            print(f"   ❌ Error creating additional mappings: {e}")
            return {}

    def _find_matching_library_file(self, original_path, texture_info, geometry_info):
        """Find matching library file by filename comparison"""
        try:
            original_filename = os.path.basename(original_path)
            
            # Check texture files
            for tex_info in texture_info:
                tex_original = tex_info.get('original_path', '')
                tex_library = tex_info.get('library_path', '')
                
                if tex_original and tex_library and os.path.basename(tex_original) == original_filename:
                    return tex_library
            
            # Check geometry files
            for geo_info in geometry_info:
                geo_original = geo_info.get('original_path', '')
                geo_library = geo_info.get('library_path', '')
                
                if geo_original and geo_library and os.path.basename(geo_original) == original_filename:
                    return geo_library
            
            return None
            
        except Exception as e:
            print(f"      ❌ Error matching library file: {e}")
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
                            elif current_value in path_mappings:
                                new_path = path_mappings[current_value]
                                
                                print(f"      🔄 Remapping {node_path}::{parm.name()}")
                                print(f"         FROM: {current_value}")
                                print(f"         TO: {new_path}")
                                
                                # Update the parameter
                                parm.set(new_path)
                                remapped_count += 1
                            else:
                                # Debug: Show what wasn't found
                                if unexpanded_value and ("${F4}" in unexpanded_value or "${F}" in unexpanded_value):
                                    print(f"      ❌ BGEO pattern NOT FOUND in mappings:")
                                    print(f"         Unexpanded: {unexpanded_value}")
                                    print(f"         Expanded: {current_value}")
                                    print(f"         Available mappings: {len(path_mappings)} total")
                            
                    except Exception as e:
                        # Skip parameters that can't be updated
                        continue
            
            return remapped_count
            
        except Exception as e:
            print(f"   ❌ Error updating parameters: {e}")
            return 0

    def save_paths_json(self, paths_json_file, path_mappings):
        """Save path mappings to paths.json file"""
        try:
            import json
            from datetime import datetime
            
            paths_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "total_remapped": len(path_mappings),
                    "asset_id": self.asset_id,
                    "asset_name": self.asset_name
                },
                "mappings": path_mappings
            }
            
            with open(paths_json_file, 'w') as f:
                json.dump(paths_data, f, indent=2)
            
            print(f"   💾 Saved {len(path_mappings)} path mappings to paths.json")
            
        except Exception as e:
            print(f"   ❌ Error saving paths.json: {e}")

    def remap_texture_paths(self, imported_subnet):
        """Remap texture paths from original locations to library locations using metadata mapping"""
        try:
            print(f"   🎯 Starting texture path remapping using metadata mapping...")
            
            # Load the texture mapping from metadata
            metadata_file = self.asset_folder / "metadata.json"
            if not metadata_file.exists():
                print(f"   ⚠️ No metadata file found, skipping texture remapping")
                return
            
            import json
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
            import traceback
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
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)  # Recurse into children
            
            collect_all_nodes(imported_subnet)
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
            
            import json
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
            import traceback
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
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)
            
            collect_all_nodes(imported_subnet)
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
                        import fnmatch
                        if fnmatch.fnmatch(geo_basename, original_pattern):
                            # Return the pattern with the correct library path structure
                            library_pattern = geometry_file.replace(geo_basename, os.path.basename(original_path))
                            return library_pattern
        
        return None

    def _ingest_to_database(self, metadata_file, metadata):
        """Automatically ingest the exported asset into the database via API"""
        try:
            print(f"🔴 DEBUG: Starting auto-ingestion process...")
            print(f"🔴 DEBUG: Metadata file: {metadata_file}")
            print(f"🔴 DEBUG: Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
            
            # Import subprocess for curl commands (no external dependencies needed)
            import subprocess
            import json
            
            # Define API endpoint
            api_url = "http://localhost:8000/api/v1/assets"
            print(f"🔴 DEBUG: API URL: {api_url}")
            
            # Prepare asset data for API (match AssetCreateRequest schema)
            # Use ONLY the 12-character UID as database key (no suffix)
            database_key = self.asset_id  # Always use the pure 12-character UID
            print(f"🔴 DEBUG: Using database key: {database_key} (forced to asset_id)")
            print(f"🔴 DEBUG: Metadata id was: {metadata.get('id', 'NOT_FOUND')}")
            
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
            
            print(f"🔴 DEBUG: Asset data prepared:")
            print(f"🔴 DEBUG:   Name: {asset_data['name']}")
            print(f"🔴 DEBUG:   Category: {asset_data['category']}")
            print(f"🔴 DEBUG:   Asset folder: {asset_data['paths']['asset_folder']}")
            print(f"🔴 DEBUG:   Tags: {asset_data['tags']}")
            print(f"🔴 DEBUG: Full asset_data keys: {list(asset_data.keys())}")
            
            # Make API request using curl
            try:
                print(f"🔴 DEBUG: Making POST request to {api_url} via curl")
                print(f"🔴 DEBUG: Request headers: Content-Type: application/json")
                
                # Convert asset_data to JSON for curl
                json_data = json.dumps(asset_data)
                print(f"🔴 DEBUG: JSON data length: {len(json_data)} characters")
                
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
                
                print(f"🔴 DEBUG: Curl return code: {result.returncode}")
                print(f"🔴 DEBUG: Curl stdout (first 500 chars): {result.stdout[:500]}")
                if result.stderr:
                    print(f"🔴 DEBUG: Curl stderr: {result.stderr}")
                
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
                print(f"   💡 Manual ingestion: python /net/dev/alex.parks/scm/int/Blacksmith-Atlas/scripts/utilities/ingest_metadata_curl.py {metadata_file}")
                return False
            
            except Exception as e:
                print(f"🔴 DEBUG: Request exception details: {e}")
                print(f"   ❌ Request failed with error: {e}")
                return False
                
        except Exception as e:
            print(f"🔴 DEBUG: General exception in _ingest_to_database: {e}")
            print(f"   ❌ Error during auto-ingestion: {e}")
            print(f"   💡 Manual ingestion: python /net/dev/alex.parks/scm/int/Blacksmith-Atlas/scripts/utilities/ingest_metadata_curl.py {metadata_file}")
            import traceback
            traceback.print_exc()
            return False
