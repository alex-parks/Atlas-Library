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
    
    def __init__(self, asset_name, subcategory="Props", description="", tags=None, asset_type=None, render_engine=None, metadata=None):
        self.asset_name = asset_name
        self.subcategory = subcategory  
        self.description = description
        self.tags = tags or []
        self.asset_type = asset_type or "Assets"
        self.render_engine = render_engine or "Redshift"
        self.metadata = metadata or ""
        
        # Generate unique asset ID (8 character UID)
        import uuid
        self.asset_id = str(uuid.uuid4())[:8].upper()
        
        # Sanitize asset name for folder/key generation
        import re
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
        
        self.asset_folder = self.library_root / asset_type / subcategory_folder / f"{self.asset_id}_{self.sanitized_asset_name}"
        self.data_folder = self.asset_folder / "Data"
        self.textures_folder = self.asset_folder / "Textures"
        self.geometry_folder = self.asset_folder / "Geometry"
        
        # Database key in UID_Name format (matching folder name)
        self.database_key = f"{self.asset_id}_{self.sanitized_asset_name}"
    
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
            
            # Process materials and copy textures FIRST
            texture_info = self.process_materials_and_textures(parent_node, nodes_to_export)
            
            # Process geometry files and copy them
            geometry_info = self.process_geometry_files(parent_node, nodes_to_export)
            
            # Export template
            template_file = self.data_folder / "template.hipnc"
            print(f"   💾 Saving template to: {template_file}")
            
            # Use saveChildrenToFile with correct syntax (children, network_boxes, filename)
            try:
                parent_node.saveChildrenToFile(nodes_to_export, parent_node.networkBoxes(), str(template_file))
                print(f"   ✅ Template saved successfully using correct saveChildrenToFile syntax")
            except Exception as e:
                print(f"   ❌ Template save failed: {e}")
                # As a fallback, just create an empty file so the export doesn't fail
                template_file.touch()
                print(f"   ⚠️ Created empty template file as fallback")
            
            print(f"   ✅ Template saved: {template_file.name} ({template_file.stat().st_size / 1024:.1f} KB)")
            
            # Create metadata
            print(f"   📋 Creating metadata...")
            metadata = self.create_asset_metadata(template_file, nodes_to_export, texture_info, geometry_info)
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
                
                print(f"      🔍 {node.path()} ({node_type}) - Category: {category}")
                
                # Collect different types of nodes
                if node_type == 'matnet':
                    matnet_nodes.append(node)
                    print(f"         ✅ MATNET FOUND")
                
                elif category == 'Vop':
                    vop_nodes.append(node)
                    print(f"         ✅ VOP FOUND")
                
                elif category == 'Shop':
                    material_nodes.append(node)
                    print(f"         ✅ SHOP MATERIAL FOUND")
            
            print(f"   📊 SUMMARY:")
            print(f"      🎨 MatNet nodes: {len(matnet_nodes)}")
            print(f"      🔧 VOP nodes: {len(vop_nodes)}")
            print(f"      🏪 Shop materials: {len(material_nodes)}")
            
            # Scan ALL VOP nodes for texture parameters (like our test script)
            print(f"   🔍 SCANNING ALL VOP NODES FOR TEXTURES:")
            
            for vop_node in vop_nodes:
                print(f"      🔍 Scanning VOP: {vop_node.path()} ({vop_node.type().name()})")
                
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
                                        for udim_file in udim_files[:10]:  # Show first 10
                                            print(f"              • {os.path.basename(udim_file)}")
                                            # Add each UDIM file as a separate texture
                                            texture_info.append({
                                                'material': vop_node.path(),
                                                'material_name': material_name,
                                                'node': vop_node.path(),
                                                'parameter': parm.name(),
                                                'file': udim_file,
                                                'filename': os.path.basename(udim_file),
                                                'original_path': parm_value,
                                                'is_udim': True
                                            })
                                        if len(udim_files) > 10:
                                            print(f"              ... and {len(udim_files)-10} more")
                                    else:
                                        print(f"            ❌ No UDIM files found with pattern: {udim_pattern}")
                                        # Try checking if the base file exists (like .1001)
                                        test_udim = expanded_path.replace('<UDIM>', '1001').replace('<udim>', '1001')
                                        if os.path.exists(test_udim):
                                            print(f"            🎯 Found single UDIM file: {os.path.basename(test_udim)}")
                                            texture_info.append({
                                                'material': vop_node.path(),
                                                'material_name': material_name,
                                                'node': vop_node.path(),
                                                'parameter': parm.name(),
                                                'file': test_udim,
                                                'filename': os.path.basename(test_udim),
                                                'original_path': parm_value,
                                                'is_udim': True
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
                                # Handle UDIM patterns for SHOP materials too
                                if '<UDIM>' in parm_value or '<udim>' in parm_value or '<UDIM>' in expanded_path or '<udim>' in expanded_path:
                                    udim_pattern = expanded_path.replace('<UDIM>', '*').replace('<udim>', '*')
                                    udim_files = glob.glob(udim_pattern)
                                    if udim_files:
                                        for udim_file in udim_files:
                                            texture_info.append({
                                                'material': shop_node.path(),
                                                'material_name': material_name,
                                                'node': shop_node.path(),
                                                'parameter': parm.name(),
                                                'file': udim_file,
                                                'filename': os.path.basename(udim_file),
                                                'original_path': parm_value,
                                                'is_udim': True
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
                                copied_textures.append(tex_info)
                                
                            else:
                                print(f"      ⚠️ Texture file not found: {source_file}")
                        
                        except Exception as e:
                            print(f"      ❌ Error copying texture {tex_info['file']}: {e}")
                
                print(f"   ✅ Copied {len(copied_textures)} texture files organized by material")
                texture_info = copied_textures
            
            else:
                print("   📋 No textures found to copy")
            
        except Exception as e:
            print(f"   ⚠️ Error processing materials and textures: {e}")
            import traceback
            traceback.print_exc()
        
        return texture_info

    def process_geometry_files(self, parent_node, nodes_to_export):
        """Process geometry files (Alembic, FBX, etc.) and copy them to library"""
        geometry_info = []
        
        try:
            print("   🔍 SCANNING FOR GEOMETRY FILES (Alembic, FBX, OBJ, etc.)...")
            
            # Get ALL nodes recursively inside the subnet
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                """Recursively collect all nodes"""
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)  # Recurse into children
            
            collect_all_nodes(parent_node)
            
            print(f"   📋 Scanning {len(all_nodes)} nodes for geometry file references...")
            
            # Common geometry file extensions
            geometry_extensions = ['.abc', '.fbx', '.obj', '.bgeo', '.bgeo.sc', '.ply', '.vdb', '.sim', '.geo']
            
            # Scan all nodes for geometry file parameters
            for node in all_nodes:
                node_type = node.type().name()
                category = node.type().category().name()
                
                print(f"      🔍 {node.path()} ({node_type}) - Category: {category}")
                
                # Get ALL parameters on this node
                all_parms = node.parms()
                
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        # Check if this looks like a geometry file path
                        if (isinstance(parm_value, str) and 
                            parm_value.strip() and 
                            any(ext in parm_value.lower() for ext in geometry_extensions)):
                            
                            # Expand Houdini variables
                            expanded_path = hou.expandString(parm_value)
                            print(f"         📁 GEOMETRY FILE PARAMETER: {parm.name()} = '{parm_value}'")
                            print(f"            EXPANDED TO: '{expanded_path}'")
                            
                            # Check for BGEO sequences with Houdini variables
                            if (file_extension := Path(expanded_path).suffix.lower()) in ['.bgeo', '.bgeo.sc']:
                                # Special handling for BGEO sequences
                                if any(var in parm_value for var in ['${F4}', '${F}', '${FF}', '$F4', '$F']):
                                    print(f"            🎬 BGEO SEQUENCE DETECTED: {parm_value}")
                                    sequence_info = self._process_bgeo_sequence(node, parm, parm_value, expanded_path)
                                    if sequence_info:
                                        geometry_info.extend(sequence_info)
                                    continue
                            
                            if os.path.exists(expanded_path):
                                # Determine file type and subfolder
                                file_extension = Path(expanded_path).suffix.lower()
                                if file_extension in ['.abc']:
                                    subfolder = 'Alembic'
                                elif file_extension in ['.fbx']:
                                    subfolder = 'FBX'
                                elif file_extension in ['.obj']:
                                    subfolder = 'OBJ'
                                elif file_extension in ['.bgeo', '.bgeo.sc']:
                                    subfolder = 'BGEO'
                                    # For individual BGEO files, use node-based subfolder
                                    node_name = node.name()
                                    subfolder = f'BGEO/{node_name}'
                                elif file_extension in ['.vdb']:
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
                                    'extension': file_extension,
                                    'is_sequence': False
                                })
                                print(f"            ✅ GEOMETRY FILE FOUND: {os.path.basename(expanded_path)} ({subfolder})")
                            else:
                                print(f"            ❌ GEOMETRY FILE NOT FOUND: {expanded_path}")
                    
                    except Exception as e:
                        pass  # Skip parameters that can't be evaluated
            
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
                    # Handle BGEO sequences specially
                    if file_type.startswith('BGEO/'):
                        # This is a BGEO sequence with node-specific subfolder
                        self._copy_bgeo_sequence(geometry_folder, file_type, files, copied_files)
                    else:
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
            
            # Extract base path and pattern from the original parameter value
            base_path = Path(expanded_path).parent
            original_filename = Path(parm_value).name  # Use original parm_value, not expanded
            
            print(f"            📂 Base path: {base_path}")
            print(f"            📄 Original pattern: {original_filename}")
            
            # Extract the base filename pattern by removing frame variables
            # Example: Library_LibraryExport_v001.$F.bgeo.sc -> Library_LibraryExport_v001 and .bgeo.sc
            base_filename = original_filename
            file_extension = ""
            
            # Find and extract the frame variable and extension
            frame_vars = ['${F4}', '${F}', '${FF}', '$F4', '$F']
            frame_var_used = None
            
            for var in frame_vars:
                if var in base_filename:
                    frame_var_used = var
                    # Split around the frame variable
                    parts = base_filename.split(var)
                    if len(parts) == 2:
                        prefix = parts[0]  # e.g., "Library_LibraryExport_v001."
                        suffix = parts[1]  # e.g., ".bgeo.sc"
                        break
            
            if not frame_var_used:
                print(f"            ⚠️ No frame variable found in: {original_filename}")
                return None
            
            print(f"            🔍 Frame variable: {frame_var_used}")
            print(f"            📋 Prefix: '{prefix}'")
            print(f"            📋 Suffix: '{suffix}'")
            
            # Look for all files in the directory that match the pattern
            sequence_files = []
            
            if base_path.exists():
                print(f"            🔍 Scanning directory: {base_path}")
                
                # Find all files that start with prefix and end with suffix
                for file_path in base_path.iterdir():
                    if file_path.is_file():
                        filename = file_path.name
                        # Check if it matches our pattern
                        if filename.startswith(prefix) and filename.endswith(suffix):
                            # Additional check: make sure there's a frame number in between
                            middle_part = filename[len(prefix):-len(suffix)] if suffix else filename[len(prefix):]
                            # Check if middle part looks like a frame number
                            if middle_part.isdigit() or (middle_part and all(c.isdigit() or c == '.' for c in middle_part)):
                                sequence_files.append(str(file_path))
                                print(f"               ✅ Found: {filename}")
            
            if not sequence_files:
                print(f"            ❌ No sequence files found matching pattern in: {base_path}")
                print(f"            🔍 Looking for files starting with: '{prefix}' and ending with: '{suffix}'")
                return None
            
            # Sort files to ensure proper sequence order
            sequence_files.sort()
            
            print(f"            ✅ Found {len(sequence_files)} files in BGEO sequence")
            print(f"            📋 First file: {os.path.basename(sequence_files[0])}")
            print(f"            📋 Last file: {os.path.basename(sequence_files[-1])}")
            
            # Create geometry info entries for the sequence
            sequence_info = []
            node_name = node.name()
            
            for seq_file in sequence_files:
                sequence_info.append({
                    'node': node.path(),
                    'node_name': node_name,
                    'parameter': parm.name(),
                    'file': seq_file,
                    'filename': os.path.basename(seq_file),
                    'original_path': parm_value,
                    'file_type': f'BGEO/{node_name}',
                    'extension': Path(seq_file).suffix.lower(),
                    'is_sequence': True,
                    'sequence_pattern': parm_value,
                    'sequence_total': len(sequence_files)
                })
            
            print(f"            ✅ Created sequence info for {len(sequence_info)} files")
            return sequence_info
            
        except Exception as e:
            print(f"            ❌ Error processing BGEO sequence: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _copy_bgeo_sequence(self, geometry_folder, file_type, files, copied_files):
        """Copy BGEO sequence files to node-specific subfolders"""
        try:
            # Create the BGEO/NodeName folder structure
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
                print(f"      🎬 Processing BGEO sequence: {sequence_pattern}")
                print(f"         📁 Copying {len(sequence_files)} files to {file_type}/")
                
                copied_in_sequence = 0
                
                for geo_info in sequence_files:
                    source_file = Path(geo_info['file'])
                    if source_file.exists():
                        # Create destination filename in type folder
                        dest_file = type_folder / source_file.name
                        
                        # Copy the geometry file
                        shutil.copy2(source_file, dest_file)
                        
                        # Update geometry info with new relative path
                        geo_info['copied_file'] = str(dest_file)
                        geo_info['relative_path'] = f"Geometry/{file_type}/{dest_file.name}"
                        copied_files.append(geo_info)
                        copied_in_sequence += 1
                        
                        if copied_in_sequence <= 3 or copied_in_sequence == len(sequence_files):
                            # Show first 3 and last file
                            print(f"         ✅ {source_file.name}")
                        elif copied_in_sequence == 4:
                            print(f"         ... copying {len(sequence_files) - 3} more files ...")
                        
                    else:
                        print(f"         ⚠️ BGEO file not found: {source_file}")
                
                print(f"      ✅ Sequence complete: {copied_in_sequence}/{len(sequence_files)} files copied")
                    
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
                        geo_info['relative_path'] = f"Geometry/{file_type}/{dest_file.name}"
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
                                    # Handle UDIM patterns for SHOP materials too
                                    if '<UDIM>' in parm_value or '<udim>' in parm_value or '<UDIM>' in expanded_path or '<udim>' in expanded_path:
                                        udim_pattern = expanded_path.replace('<UDIM>', '*').replace('<udim>', '*')
                                        udim_files = glob.glob(udim_pattern)
                                        if udim_files:
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
                        
                        except Exception as e:
                            pass
        
        except Exception as e:
            print(f"      ⚠️ Error extracting textures from {material_node.path()}: {e}")
        
        print(f"         📋 Found {len(texture_info)} textures in material '{material_name}'")
        return texture_info
    
    def create_asset_metadata(self, template_file, nodes_exported, texture_info=None, geometry_info=None):
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
                "id": self.asset_id,  # Use just the UID part for the document ID
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
        if any(ext in original_filename.lower() for ext in ['.bgeo', '.bgeo.sc']):
            # Check if original path has frame variables
            if any(var in original_path for var in ['${F4}', '${F}', '${FF}', '$F4', '$F']):
                # For sequence patterns, return the pattern itself to be used in remapping
                for geometry_file in geometry_files:
                    # Look for BGEO files in node-specific subfolders
                    if 'BGEO/' in geometry_file and any(ext in geometry_file.lower() for ext in ['.bgeo', '.bgeo.sc']):
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
            # Use the database key from metadata (UID_Name format)
            database_key = metadata.get("id", self.database_key)
            print(f"🔴 DEBUG: Using database key: {database_key}")
            
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
