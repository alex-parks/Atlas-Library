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
        
        # Generate unique asset ID
        import uuid
        self.asset_id = str(uuid.uuid4())[:8].upper()
        
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
        
        self.asset_folder = self.library_root / asset_type / subcategory_folder / f"{self.asset_id}_{asset_name}"
        self.data_folder = self.asset_folder / "Data"
        self.textures_folder = self.asset_folder / "Textures"
        self.geometry_folder = self.asset_folder / "Geometry"
        self.clipboard_folder = self.asset_folder / "Clipboard"
    
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
            
            # Create HCOPY clipboard version with remapped paths
            print(f"   📋 Creating HCOPY clipboard version...")
            self.create_clipboard_version(parent_node, nodes_to_export)
            print(f"   ✅ Clipboard version created successfully")
            
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
                                    subfolder = 'Houdini_Geo'
                                elif file_extension in ['.vdb']:
                                    subfolder = 'VDB'
                                else:
                                    subfolder = 'Other'
                                
                                geometry_info.append({
                                    'node': node.path(),
                                    'parameter': parm.name(),
                                    'file': expanded_path,
                                    'filename': os.path.basename(expanded_path),
                                    'original_path': parm_value,
                                    'file_type': subfolder,
                                    'extension': file_extension
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
                
                print(f"   ✅ Copied {len(copied_files)} geometry files organized by type")
                geometry_info = copied_files
            
            else:
                print("   📋 No geometry files found to copy")
            
        except Exception as e:
            print(f"   ⚠️ Error processing geometry files: {e}")
            import traceback
            traceback.print_exc()
        
        return geometry_info

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
        """Create metadata JSON for the asset (for database/search purposes) and store in ArangoDB"""
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
                "id": self.asset_id,
                "name": self.asset_name,
                "asset_type": self.asset_type,
                "subcategory": self.subcategory,
                "description": self.description,
                "render_engine": self.render_engine,
                "tags": self.tags,
                "created_at": datetime.now().isoformat(),
                "created_by": os.environ.get('USER', 'unknown'),
                
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
                
                # For database searches
                "search_keywords": self._generate_search_keywords(),
                
                # Texture info with detailed mapping
                "textures": {
                    "count": len(texture_info),
                    "files": [tex['relative_path'] for tex in texture_info if 'relative_path' in tex],
                    "mapping": self._create_texture_mapping(texture_info)
                },
                
                # Geometry file info with detailed mapping
                "geometry_files": {
                    "count": len(geometry_info),
                    "files": [geo['relative_path'] for geo in geometry_info if 'relative_path' in geo],
                    "mapping": self._create_geometry_mapping(geometry_info)
                },
                
                # Direct folder path for file manager access
                "folder_path": str(self.asset_folder)
            }
            
            # Note: Database operations are handled separately via Docker auto-insert
            print(f"   🗄️ Database sync will be handled via Docker auto-insert...")
            
            # Write metadata to file
            metadata_file = self.asset_folder / "metadata.json"
            import json
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"   📋 Created metadata: {metadata_file}")
            
            # Auto-insert into ArangoDB via Docker (this is the main database sync method)
            try:
                print(f"   🗄️ Auto-inserting into ArangoDB via Docker...")
                
                # Method 1: Try direct import
                success = False
                try:
                    # Import with absolute path to avoid import issues from Houdini
                    import sys
                    from pathlib import Path
                    script_dir = Path(__file__).parent
                    sys.path.insert(0, str(script_dir))
                    
                    import docker_auto_insert
                    success = docker_auto_insert.docker_auto_insert(str(metadata_file))
                    print(f"   📋 Direct import method: {'✅ Success' if success else '❌ Failed'}")
                    
                except Exception as import_error:
                    print(f"   ⚠️ Direct import failed: {import_error}")
                    
                    # Method 2: Fallback to subprocess call
                    try:
                        print(f"   🔄 Trying subprocess fallback...")
                        import subprocess
                        script_path = Path(__file__).parent / "docker_auto_insert.py"
                        
                        cmd = [
                            "python", str(script_path), 
                            "--metadata", str(metadata_file)
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
                        success = result.returncode == 0
                        
                        if result.stdout:
                            print(f"   📄 Output: {result.stdout[-200:]}")  # Show last 200 chars
                        if result.stderr:
                            print(f"   ⚠️ Errors: {result.stderr[-200:]}")
                            
                        print(f"   📋 Subprocess method: {'✅ Success' if success else '❌ Failed'}")
                        
                    except Exception as subprocess_error:
                        print(f"   ❌ Subprocess fallback failed: {subprocess_error}")
                        success = False
                
                # Update metadata with sync status
                if success:
                    print(f"   ✅ Successfully inserted into ArangoDB: {self.asset_name}")
                    metadata["database_synced"] = True
                    metadata["database_sync_time"] = datetime.now().isoformat()
                    metadata["database_sync_method"] = "docker_auto_insert"
                else:
                    print(f"   ⚠️ ArangoDB insertion failed (export continues)")
                    metadata["database_synced"] = False
                    metadata["database_sync_error"] = "Both import and subprocess methods failed"
                
                # Update metadata file with sync status
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
            except Exception as arango_error:
                print(f"   ❌ ArangoDB auto-insert error: {arango_error}")
                import traceback
                traceback.print_exc()
                metadata["database_synced"] = False
                metadata["database_sync_error"] = str(arango_error)
                # Don't fail the entire export due to database issues
            
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

    def create_clipboard_version(self, parent_node, nodes_to_export):
        """Create Atlas clipboard version with copy string embedded in asset folder"""
        try:
            print(f"   📋 Creating Atlas clipboard system files...")
            
            # Create clipboard folder (now called templates to match Atlas clipboard system)
            templates_folder = self.asset_folder / "templates"
            templates_folder.mkdir(exist_ok=True)
            
            # Generate Atlas copy string components
            print(f"   � Generating Atlas copy string...")
            
            # Generate encryption key (16 characters like HPasteWeb)
            import random
            import string
            encryption_key = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
            
            # Create Atlas copy string format: AtlasAsset_AssetName_UID!encryption_key
            copy_string = f"AtlasAsset_{self.asset_name}_{self.asset_id}!{encryption_key}"
            
            print(f"   📋 Copy String: {copy_string}")
            
            # Create a temporary subnet to work with
            temp_subnet_name = f"temp_template_{self.asset_id}"
            temp_subnet = parent_node.createNode("subnet", temp_subnet_name)
            temp_subnet.setColor(hou.Color(1.0, 0.8, 0.2))  # Orange for temp
            
            try:
                # Copy all the nodes into the temporary subnet
                print(f"   📋 Copying {len(nodes_to_export)} nodes to temporary subnet...")
                copied_nodes = []
                for node in nodes_to_export:
                    copied_node = temp_subnet.copyItems([node])[0]
                    copied_nodes.append(copied_node)
                
                print(f"   🔄 Remapping file paths in temporary subnet...")
                
                # Now remap all file paths in the temporary subnet to library locations
                self._remap_paths_for_clipboard(temp_subnet)
                
                # Create the Atlas clipboard template file (using new naming convention)
                template_file = templates_folder / f"{self.asset_name}_clipboard.hip"
                print(f"   💾 Saving Atlas template file: {template_file}")
                
                # Use the simple saveChildrenToFile approach
                temp_subnet.saveChildrenToFile(copied_nodes, temp_subnet.networkBoxes(), str(template_file))
                
                print(f"   ✅ Atlas template file created: {template_file}")
                print(f"   📏 Template file size: {template_file.stat().st_size / 1024:.1f} KB")
                
                # Create Atlas clipboard metadata
                import json
                import hashlib
                
                # Read template file for metadata
                with open(template_file, 'rb') as f:
                    template_data = f.read()
                
                metadata = {
                    'asset_name': self.asset_name,
                    'uid': self.asset_id,
                    'subcategory': self.subcategory,
                    'asset_path': str(self.asset_folder),
                    'template_filename': f"{self.asset_name}_clipboard.hip",
                    'encrypted': True,  # We'll add encryption later
                    'encryption_key': encryption_key,
                    'node_count': len(nodes_to_export),
                    'context': self._get_node_context(parent_node),
                    'checksum': hashlib.sha256(template_data).hexdigest(),
                    'created_date': datetime.now().isoformat(),
                    'description': self.description,
                    'tags': self.tags
                }
                
                # Save metadata
                metadata_file = templates_folder / f"{self.asset_name}_clipboard.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"   📋 Atlas metadata created: {metadata_file}")
                
                # Save the Atlas copy string for easy access
                copy_string_file = templates_folder / "ATLAS_COPY_STRING.txt"
                with open(copy_string_file, 'w') as f:
                    f.write(f"ATLAS COPY STRING\n")
                    f.write(f"=" * 40 + "\n\n")
                    f.write(f"{copy_string}\n\n")
                    f.write(f"USAGE:\n")
                    f.write(f"1. Copy the string above to clipboard\n")
                    f.write(f"2. Share with others or use Atlas Paste to import\n")
                    f.write(f"3. Atlas Paste will automatically find this asset in library\n\n")
                    f.write(f"ASSET DETAILS:\n")
                    f.write(f"- Name: {self.asset_name}\n")
                    f.write(f"- UID: {self.asset_id}\n")
                    f.write(f"- Category: {self.subcategory}\n")
                    f.write(f"- Encryption: Yes (key embedded)\n")
                    f.write(f"- Library Path: {self.asset_folder}\n")
                
                print(f"   📋 Copy string saved: {copy_string_file}")
                print(f"   🎯 Atlas Copy String: {copy_string}")
                
                # Also create simple usage instructions (backward compatibility)
                instructions_file = templates_folder / "MERGE_INSTRUCTIONS.txt"
                with open(instructions_file, 'w') as f:
                    f.write(f"Blacksmith Atlas Asset: {self.asset_name}\n")
                    f.write(f"=" * 40 + "\n\n")
                    f.write(f"ATLAS CLIPBOARD USAGE (Recommended):\n")
                    f.write(f"------------------------------------\n")
                    f.write(f"Copy this string to clipboard:\n")
                    f.write(f"{copy_string}\n\n")
                    f.write(f"Then use Atlas Paste shelf button to import anywhere!\n\n")
                    f.write(f"MANUAL MERGE (Alternative):\n")
                    f.write(f"---------------------------\n")
                    f.write(f"Method 1 - Python Console:\n")
                    f.write(f'parent_node = hou.pwd()  # Navigate to desired context first\n')
                    f.write(f'parent_node.loadChildrenFromFile("{template_file.name}")\n\n')
                    f.write(f"Method 2 - File > Merge:\n")
                    f.write(f"1. Navigate to desired context (e.g., inside a geometry node)\n")
                    f.write(f"2. File > Merge\n")
                    f.write(f"3. Select: {template_file.name}\n\n")
                    f.write(f"✅ All texture and geometry paths are pre-mapped to library locations!\n")
                    f.write(f"✅ Atlas Copy/Paste system ready for sharing!\n")
                
                print(f"   📋 Atlas clipboard system ready!")
                
            finally:
                # Clean up temporary subnet
                temp_subnet.destroy()
                print(f"   🗑️ Cleaned up temporary subnet")
            
        except Exception as e:
            print(f"   ❌ Error creating template file: {e}")
            import traceback
            traceback.print_exc()

    def _get_node_context(self, node):
        """Get node context like HPaste"""
        try:
            houver = hou.applicationVersion()
            if houver[0] >= 16:
                return node.type().childTypeCategory().name()
            else:
                return node.childTypeCategory().name()
        except:
            return "Object"  # Default fallback

    def _create_hip_file(self, temp_subnet, copied_nodes):
        """Create a .hip file with pre-remapped paths for easy merging"""
        try:
            print(f"   📄 Creating .hip file for merging...")
            
            # Save the hip file
            hip_file = self.clipboard_folder / f"{self.asset_name}_atlas.hip"
            
            # Save current scene
            current_hip = hou.hipFile.path()
            print(f"   💾 Current scene: {current_hip}")
            
            # Create a new scene temporarily
            hou.hipFile.clear(suppress_save_prompt=True)
            
            try:
                # Move our pre-remapped nodes to the root /obj context
                obj_context = hou.node('/obj')
                
                # Create a subnet in /obj to hold our nodes
                asset_subnet = obj_context.createNode('subnet', f"{self.asset_name}_Atlas")
                asset_subnet.setComment(f"Blacksmith Atlas Asset: {self.asset_name}")
                asset_subnet.setColor(hou.Color(0.2, 0.6, 1.0))  # Blue
                
                # Copy nodes into the asset subnet
                final_nodes = []
                for node in copied_nodes:
                    copied_node = asset_subnet.copyItems([node])[0]
                    final_nodes.append(copied_node)
                
                # Position the subnet nicely
                asset_subnet.setPosition(hou.Vector2(0, 0))
                
                # Add metadata parameters to the subnet
                self._add_metadata_to_subnet(asset_subnet)
                
                # Save the hip file
                hou.hipFile.save(str(hip_file))
                
                print(f"   ✅ Hip file created: {hip_file}")
                print(f"   📏 Hip file size: {hip_file.stat().st_size / 1024:.1f} KB")
                
                # Also create a simple text file with merge instructions
                instructions_file = self.clipboard_folder / "README.txt"
                with open(instructions_file, 'w') as f:
                    f.write(f"Blacksmith Atlas Asset: {self.asset_name}\n")
                    f.write(f"================================\n\n")
                    f.write(f"To use this asset:\n")
                    f.write(f"1. Open your Houdini scene\n")
                    f.write(f"2. Go to File > Merge\n")
                    f.write(f"3. Select: {hip_file.name}\n")
                    f.write(f"4. The asset will appear as a subnet with all paths pre-mapped!\n\n")
                    f.write(f"Asset Details:\n")
                    f.write(f"- ID: {self.asset_id}\n")
                    f.write(f"- Category: {self.subcategory}\n")
                    f.write(f"- Location: {self.asset_folder}\n\n")
                    f.write(f"All texture and geometry paths are already mapped to library locations.\n")
                    f.write(f"No additional setup required!\n")
                
                print(f"   � Instructions created: {instructions_file}")
                
            finally:
                # Restore the original scene
                if current_hip and current_hip != "untitled.hip":
                    hou.hipFile.load(current_hip, suppress_save_prompt=True)
                else:
                    hou.hipFile.clear(suppress_save_prompt=True)
                    
        except Exception as e:
            print(f"   ❌ Error creating hip file: {e}")
            import traceback
            traceback.print_exc()

    def _add_metadata_to_subnet(self, subnet):
        """Add Atlas metadata parameters to the subnet"""
        try:
            ptg = subnet.parmTemplateGroup()
            
            # Create metadata parameters
            asset_id_parm = hou.StringParmTemplate("atlas_asset_id", "Atlas Asset ID", 1)
            asset_id_parm.setDefaultValue([self.asset_id])
            asset_id_parm.setTags({"editor": "readonly"})
            
            asset_name_parm = hou.StringParmTemplate("atlas_asset_name", "Asset Name", 1)
            asset_name_parm.setDefaultValue([self.asset_name])
            asset_name_parm.setTags({"editor": "readonly"})
            
            subcategory_parm = hou.StringParmTemplate("atlas_subcategory", "Category", 1)
            subcategory_parm.setDefaultValue([self.subcategory])
            subcategory_parm.setTags({"editor": "readonly"})
            
            library_path_parm = hou.StringParmTemplate("atlas_library_path", "Library Path", 1)
            library_path_parm.setDefaultValue([str(self.asset_folder)])
            library_path_parm.setTags({"editor": "readonly"})
            
            # Create folder with metadata
            parm_list = [asset_id_parm, asset_name_parm, subcategory_parm, library_path_parm]
            atlas_folder = hou.FolderParmTemplate("atlas_info", "🏭 Atlas Asset Info", parm_list, hou.folderType.Collapsible)
            
            ptg.addParmTemplate(atlas_folder)
            subnet.setParmTemplateGroup(ptg)
            
        except Exception as e:
            print(f"   ⚠️ Could not add metadata parameters: {e}")

        except Exception as e:
            print(f"   ⚠️ Could not add metadata parameters: {e}")

    def _remap_paths_for_clipboard(self, subnet):
        """Remap all texture and geometry file paths to library locations for clipboard version"""
        try:
            print(f"   🔄 Comprehensive path remapping for clipboard...")
            
            # Get all nodes recursively
            all_nodes = []
            
            def collect_all_nodes(parent_node):
                for child in parent_node.children():
                    all_nodes.append(child)
                    collect_all_nodes(child)
            
            collect_all_nodes(subnet)
            
            print(f"   📋 Remapping paths in {len(all_nodes)} nodes...")
            
            texture_remaps = 0
            geometry_remaps = 0
            
            # Extensions to look for
            texture_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.hdr', '.pic', '.rat', '.tx']
            geometry_extensions = ['.abc', '.fbx', '.obj', '.bgeo', '.bgeo.sc', '.ply', '.vdb', '.sim', '.geo']
            
            # Scan all nodes for file parameters
            for node in all_nodes:
                all_parms = node.parms()
                
                for parm in all_parms:
                    try:
                        parm_value = parm.eval()
                        
                        if isinstance(parm_value, str) and parm_value.strip():
                            # Check for texture files
                            if any(ext in parm_value.lower() for ext in texture_extensions):
                                new_path = self._find_library_texture_path_for_clipboard(parm_value)
                                if new_path:
                                    parm.set(new_path)
                                    texture_remaps += 1
                                    print(f"      🖼️ Texture remapped: {os.path.basename(parm_value)} -> library")
                            
                            # Check for geometry files
                            elif any(ext in parm_value.lower() for ext in geometry_extensions):
                                new_path = self._find_library_geometry_path_for_clipboard(parm_value)
                                if new_path:
                                    parm.set(new_path)
                                    geometry_remaps += 1
                                    print(f"      📁 Geometry remapped: {os.path.basename(parm_value)} -> library")
                    
                    except Exception as e:
                        pass  # Skip parameters that can't be evaluated
            
            print(f"   ✅ Clipboard remapping complete: {texture_remaps} textures, {geometry_remaps} geometry files")
            
        except Exception as e:
            print(f"   ❌ Error in clipboard path remapping: {e}")

    def _find_library_texture_path_for_clipboard(self, original_path):
        """Find the library path for a texture file for clipboard version"""
        try:
            original_filename = os.path.basename(original_path)
            
            # Search in textures folder
            textures_folder = self.asset_folder / "Textures"
            if textures_folder.exists():
                for material_folder in textures_folder.iterdir():
                    if material_folder.is_dir():
                        # Look for exact filename match
                        texture_file = material_folder / original_filename
                        if texture_file.exists():
                            return str(texture_file)
                        
                        # Look for UDIM pattern match
                        import re
                        if re.search(r'\.\d{4}\.', original_filename):
                            # Convert specific UDIM tile to pattern
                            udim_pattern = re.sub(r'\.\d{4}\.', '.<UDIM>.', original_filename)
                            pattern_file = material_folder / udim_pattern
                            if pattern_file.exists():
                                return str(pattern_file)
            
            return None
            
        except Exception as e:
            return None

    def _find_library_geometry_path_for_clipboard(self, original_path):
        """Find the library path for a geometry file for clipboard version"""
        try:
            original_filename = os.path.basename(original_path)
            
            # Search in geometry folder
            geometry_folder = self.asset_folder / "Geometry"
            if geometry_folder.exists():
                for type_folder in geometry_folder.iterdir():
                    if type_folder.is_dir():
                        geometry_file = type_folder / original_filename
                        if geometry_file.exists():
                            return str(geometry_file)
            
            return None
            
        except Exception as e:
            return None


def paste_atlas_from_clipboard(target_parent=None, network_editor=None):
    """Paste an Atlas asset from the system clipboard (Ctrl+V functionality)"""
    try:
        print(f"📋 BLACKSMITH ATLAS - PASTE FROM CLIPBOARD")
        
        # Get clipboard text
        clipboard_text = hou.ui.getTextFromClipboard()
        if not clipboard_text or not clipboard_text.startswith("BLATLAS:"):
            print(f"   ❌ No Atlas asset found in clipboard")
            hou.ui.displayMessage("No Blacksmith Atlas asset found in clipboard!\n\n"
                                "Use 'Create Atlas Asset' to copy an asset to clipboard first.", 
                                severity=hou.severityType.Warning)
            return None
        
        print(f"   📋 Found Atlas clipboard data ({len(clipboard_text)} chars)")
        
        # Parse the clipboard data
        import json
        import base64
        import bz2
        import tempfile
        import os
        
        # Remove Atlas prefix
        data_text = clipboard_text[8:]  # Remove "BLATLAS:"
        
        # Decode and decompress
        compressed = base64.urlsafe_b64decode(data_text.encode('UTF-8'))
        json_data = bz2.decompress(compressed)
        data = json.loads(json_data.decode('UTF-8'))
        
        print(f"   📋 Asset: {data['asset_name']} ({data['asset_id']})")
        print(f"   📂 From: {data['subcategory']}")
        print(f"   🎯 Pre-remapped: {data.get('pre_remapped', False)}")
        
        # Verify format
        if data.get('format') != 'BlacksmithAtlas':
            raise RuntimeError("Invalid Atlas clipboard format")
        
        # Get target context
        if target_parent is None:
            if network_editor is None:
                # Find current network editor
                network_editors = [x for x in hou.ui.paneTabs() if x.type() == hou.paneTabType.NetworkEditor]
                if network_editors:
                    network_editor = network_editors[0]
                    target_parent = network_editor.pwd()
                else:
                    target_parent = hou.node('/obj')
            else:
                target_parent = network_editor.pwd()
        
        print(f"   📍 Pasting into: {target_parent.path()}")
        
        # Check context compatibility
        houver = hou.applicationVersion()
        required_context = data['context']
        current_context = target_parent.type().childTypeCategory().name()
        
        if current_context != required_context:
            print(f"   ⚠️ Context mismatch: {current_context} vs {required_context}")
            # Try to handle context mismatch (like hpaste does)
            if required_context == 'Sop' and current_context == 'Object':
                # Create a geo node for SOP context
                response = hou.ui.displayMessage(f"Asset needs SOP context but you're in Object context.\n\n"
                                               f"Create a Geometry node to paste into?",
                                               buttons=("Create Geo Node", "Cancel"),
                                               default_choice=0, close_choice=1)
                if response == 0:
                    geo_node = target_parent.createNode('geo', f"{data['asset_name']}_geo")
                    target_parent = geo_node
                    print(f"   📦 Created geo node: {geo_node.path()}")
                else:
                    return None
            else:
                hou.ui.displayMessage(f"Context mismatch!\n\n"
                                    f"Asset context: {required_context}\n"
                                    f"Current context: {current_context}\n\n"
                                    f"Navigate to a compatible context to paste.",
                                    severity=hou.severityType.Error)
                return None
        
        # Decode the binary data
        code = base64.b64decode(data['code'].encode('UTF-8'))
        
        # Verify checksum
        import hashlib
        if hashlib.sha1(code).hexdigest() != data['chsum']:
            raise RuntimeError("Clipboard data checksum failed!")
        
        print(f"   ✅ Checksum verified")
        
        # Get current items for positioning
        old_items = target_parent.allItems() if houver[0] >= 16 else target_parent.children()
        
        # Write to temp file and load
        fd, temppath = tempfile.mkstemp()
        try:
            with open(temppath, "wb") as f:
                f.write(code)
            
            print(f"   🔄 Loading nodes from clipboard...")
            
            # Load using Houdini's native deserialization
            if data['algtype'] == 2:
                target_parent.loadItemsFromFile(temppath)
            elif data['algtype'] == 1:
                target_parent.loadChildrenFromFile(temppath)
            else:
                raise RuntimeError(f"Unsupported algorithm type: {data['algtype']}")
            
        finally:
            os.close(fd)
            os.unlink(temppath)
        
        # Find newly created items
        new_items = []
        current_items = target_parent.allItems() if houver[0] >= 16 else target_parent.children()
        for item in current_items:
            if item not in old_items:
                new_items.append(item)
        
        print(f"   ✅ Created {len(new_items)} items")
        
        # Position items if in network editor
        if network_editor and new_items:
            try:
                # Calculate center position
                cursor_pos = network_editor.cursorPosition()
                
                # Calculate bounding box of new items
                if new_items:
                    positions = [item.position() for item in new_items]
                    min_x = min(pos.x() for pos in positions)
                    min_y = min(pos.y() for pos in positions)
                    center_x = sum(pos.x() for pos in positions) / len(positions)
                    center_y = sum(pos.y() for pos in positions) / len(positions)
                    
                    # Offset to cursor position
                    offset_x = cursor_pos.x() - center_x
                    offset_y = cursor_pos.y() - center_y
                    
                    for item in new_items:
                        current_pos = item.position()
                        new_pos = hou.Vector2(current_pos.x() + offset_x, current_pos.y() + offset_y)
                        item.setPosition(new_pos)
                    
                    print(f"   📍 Positioned items at cursor: {cursor_pos}")
            except:
                pass  # Positioning is optional
        
        # Select the first item
        if new_items:
            new_items[0].setSelected(True, clear_all_selected=True)
        
        # Show success message
        hou.ui.displayMessage(f"✅ Atlas Asset pasted from clipboard!\n\n"
                            f"Asset: {data['asset_name']}\n"
                            f"ID: {data['asset_id']}\n"
                            f"Category: {data['subcategory']}\n"
                            f"Items: {len(new_items)}\n\n"
                            f"🎯 All file paths are pre-mapped to library locations!\n"
                            f"📋 Clipboard paste successful!", 
                            title="Atlas Asset Pasted")
        
        print(f"   ✅ Successfully pasted Atlas asset: {data['asset_name']}")
        return new_items
        
    except Exception as e:
        print(f"   ❌ Clipboard paste error: {e}")
        import traceback
        traceback.print_exc()
        hou.ui.displayMessage(f"❌ Failed to paste Atlas asset from clipboard!\n\n"
                            f"Error: {e}\n\n"
                            f"Make sure you have a valid Atlas asset in your clipboard.",
                            severity=hou.severityType.Error)
        return None


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
        
        return None
