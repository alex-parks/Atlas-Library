# backend/assetlibrary/database/graph_parser.py
"""
ArangoDB Graph Parser for Blacksmith Atlas
Transforms flat metadata into rich graph relationships
"""

import json
import hashlib
from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AtlasGraphParser:
    """Parse asset metadata into ArangoDB graph structure"""
    
    def __init__(self, arango_db):
        self.db = arango_db
        self.collections = self._ensure_collections()
        
    def _ensure_collections(self):
        """Ensure all required collections exist"""
        collections = {
            # Document collections
            'assets': self.db.collection('assets'),
            'textures': self.db.collection('textures'),
            'materials': self.db.collection('materials'),
            'geometry': self.db.collection('geometry'),
            'projects': self.db.collection('projects'),
            'users': self.db.collection('users'),
            
            # Edge collections
            'asset_uses_texture': self.db.collection('asset_uses_texture'),
            'asset_has_material': self.db.collection('asset_has_material'),
            'material_uses_texture': self.db.collection('material_uses_texture'),
            'asset_uses_geometry': self.db.collection('asset_uses_geometry'),
            'asset_depends_on': self.db.collection('asset_depends_on'),
            'project_contains_asset': self.db.collection('project_contains_asset'),
            'user_created_asset': self.db.collection('user_created_asset'),
        }
        
        # Create collections if they don't exist
        for name, collection in collections.items():
            if not collection:
                # Determine if edge collection
                is_edge = any(edge_type in name for edge_type in ['uses', 'has', 'depends', 'contains', 'created'])
                collections[name] = self.db.create_collection(name, edge=is_edge)
                logger.info(f"Created {'edge' if is_edge else 'document'} collection: {name}")
        
        return collections
    
    def parse_asset_metadata(self, metadata_file: Path) -> Dict[str, List[Dict]]:
        """Parse metadata.json into graph documents and relationships"""
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        results = {
            'documents': [],
            'relationships': []
        }
        
        # Parse main asset document
        asset_doc = self._parse_asset_document(metadata, metadata_file)
        results['documents'].append(('assets', asset_doc))
        
        # Parse textures
        if 'textures' in metadata:
            texture_docs, texture_relationships = self._parse_textures(metadata, asset_doc['_key'])
            results['documents'].extend([('textures', doc) for doc in texture_docs])
            results['relationships'].extend(texture_relationships)
        
        # Parse materials
        if 'textures' in metadata and 'mapping' in metadata['textures']:
            material_docs, material_relationships = self._parse_materials(metadata, asset_doc['_key'])
            results['documents'].extend([('materials', doc) for doc in material_docs])
            results['relationships'].extend(material_relationships)
        
        # Parse geometry
        if 'geometry_files' in metadata:
            geometry_docs, geometry_relationships = self._parse_geometry(metadata, asset_doc['_key'])
            results['documents'].extend([('geometry', doc) for doc in geometry_docs])
            results['relationships'].extend(geometry_relationships)
        
        # Parse user relationship
        if metadata.get('created_by'):
            user_doc, user_relationship = self._parse_user(metadata, asset_doc['_key'])
            results['documents'].append(('users', user_doc))
            results['relationships'].append(user_relationship)
        
        # Parse project relationship (if derivable from source path)
        if 'source_hip_file' in metadata:
            project_relationship = self._parse_project_context(metadata, asset_doc['_key'])
            if project_relationship:
                results['relationships'].append(project_relationship)
        
        return results
    
    def _parse_asset_document(self, metadata: Dict, metadata_file: Path) -> Dict:
        """Create main asset document"""
        asset_id = metadata['id']
        
        # Calculate complexity score based on content
        complexity_score = self._calculate_complexity_score(metadata)
        
        return {
            '_key': asset_id,
            'name': metadata['name'],
            'category': metadata.get('subcategory', 'Unknown'),
            'subcategory': metadata.get('subcategory'),
            'description': metadata.get('description', ''),
            'created_at': metadata.get('created_at'),
            'created_by': metadata.get('created_by'),
            'houdini_version': metadata.get('houdini_version'),
            'export_method': metadata.get('export_method'),
            'export_version': metadata.get('export_version'),
            'node_summary': metadata.get('node_summary', {}),
            'search_keywords': metadata.get('search_keywords', []),
            'library_path': str(metadata_file.parent),
            'template_file': metadata.get('template_file'),
            'template_size': metadata.get('template_size'),
            'source_hip_file': metadata.get('source_hip_file'),
            'status': 'published',
            'version': '1.0',
            'complexity_score': complexity_score,
            'texture_count': metadata.get('textures', {}).get('count', 0),
            'geometry_count': metadata.get('geometry_files', {}).get('count', 0),
            'tags': metadata.get('tags', []) + metadata.get('search_keywords', [])
        }
    
    def _parse_textures(self, metadata: Dict, asset_id: str) -> Tuple[List[Dict], List[Tuple]]:
        """Parse texture documents and relationships"""
        texture_docs = []
        relationships = []
        
        textures_data = metadata.get('textures', {})
        
        # Create texture documents
        for texture_path in textures_data.get('files', []):
            texture_doc = self._create_texture_document(texture_path, metadata)
            texture_docs.append(texture_doc)
            
            # Create asset->texture relationship
            relationships.append((
                'asset_uses_texture',
                {
                    '_from': f'assets/{asset_id}',
                    '_to': f'textures/{texture_doc["_key"]}',
                    'usage_type': texture_doc['texture_type'],
                    'file_path': texture_path,
                    'importance': 'primary'
                }
            ))
        
        # Add detailed mapping relationships
        for node_path, mapping in textures_data.get('mapping', {}).items():
            texture_key = self._generate_texture_key(mapping['library_path'])
            
            relationships.append((
                'asset_uses_texture',
                {
                    '_from': f'assets/{asset_id}',
                    '_to': f'textures/{texture_key}',
                    'node_path': mapping['node_path'],
                    'parameter': mapping['parameter'],
                    'material_name': mapping.get('material_name'),
                    'is_udim_sequence': mapping.get('is_udim_sequence', False),
                    'udim_tiles': mapping.get('udim_tiles', []),
                    'importance': 'primary'
                }
            ))
        
        return texture_docs, relationships
    
    def _parse_materials(self, metadata: Dict, asset_id: str) -> Tuple[List[Dict], List[Tuple]]:
        """Parse material documents and relationships"""
        material_docs = []
        relationships = []
        
        # Extract materials from texture mapping
        materials_found = {}
        for node_path, mapping in metadata.get('textures', {}).get('mapping', {}).items():
            material_name = mapping.get('material_name')
            if material_name and material_name not in materials_found:
                materials_found[material_name] = {
                    'node_path': mapping['node_path'].rsplit('/', 1)[0],  # Remove texture node
                    'textures': []
                }
            
            if material_name:
                materials_found[material_name]['textures'].append(mapping)
        
        # Create material documents
        for material_name, material_data in materials_found.items():
            material_key = f"{asset_id}_{material_name.lower()}_material"
            
            material_doc = {
                '_key': material_key,
                'material_name': material_name,
                'material_type': 'principled_shader',  # Default assumption
                'node_path': material_data['node_path'],
                'shader_type': 'redshift',  # From metadata context
                'texture_count': len(material_data['textures']),
                'complexity': 'medium' if len(material_data['textures']) > 3 else 'simple',
                'created_at': metadata.get('created_at'),
                'asset_context': asset_id
            }
            
            material_docs.append(material_doc)
            
            # Create asset->material relationship
            relationships.append((
                'asset_has_material',
                {
                    '_from': f'assets/{asset_id}',
                    '_to': f'materials/{material_key}',
                    'material_assignment': material_name,
                    'node_path': material_data['node_path']
                }
            ))
            
            # Create material->texture relationships
            for texture_mapping in material_data['textures']:
                texture_key = self._generate_texture_key(texture_mapping['library_path'])
                texture_type = self._infer_texture_type(texture_mapping['library_path'])
                
                relationships.append((
                    'material_uses_texture',
                    {
                        '_from': f'materials/{material_key}',
                        '_to': f'textures/{texture_key}',
                        'channel': texture_type,
                        'parameter': texture_mapping['parameter'],
                        'blend_mode': 'multiply',
                        'influence': 1.0
                    }
                ))
        
        return material_docs, relationships
    
    def _parse_geometry(self, metadata: Dict, asset_id: str) -> Tuple[List[Dict], List[Tuple]]:
        """Parse geometry documents and relationships"""
        geometry_docs = []
        relationships = []
        
        geometry_data = metadata.get('geometry_files', {})
        
        for geo_path in geometry_data.get('files', []):
            geo_key = self._generate_geometry_key(geo_path)
            
            geometry_doc = {
                '_key': geo_key,
                'filename': Path(geo_path).name,
                'file_path': geo_path,
                'file_type': Path(geo_path).suffix[1:].upper(),
                'created_at': metadata.get('created_at'),
                'asset_context': asset_id
            }
            
            # Add detailed mapping info if available
            for node_path, mapping in geometry_data.get('mapping', {}).items():
                if mapping['library_path'] == geo_path:
                    geometry_doc.update({
                        'node_path': mapping['node_path'],
                        'parameter': mapping['parameter'],
                        'original_path': mapping['original_path'],
                        'is_geometry_file': mapping.get('is_geometry_file', True)
                    })
                    break
            
            geometry_docs.append(geometry_doc)
            
            # Create asset->geometry relationship
            relationships.append((
                'asset_uses_geometry',
                {
                    '_from': f'assets/{asset_id}',
                    '_to': f'geometry/{geo_key}',
                    'file_type': geometry_doc['file_type'],
                    'node_path': geometry_doc.get('node_path'),
                    'visibility': True,
                    'lod_level': 0
                }
            ))
        
        return geometry_docs, relationships
    
    def _parse_user(self, metadata: Dict, asset_id: str) -> Tuple[Dict, Tuple]:
        """Parse user document and relationship"""
        username = metadata['created_by']
        user_key = username.replace('.', '_')
        
        user_doc = {
            '_key': user_key,
            'username': username,
            'full_name': username.replace('.', ' ').title(),
            'role': 'artist',  # Default
            'department': '3D',
            'specialties': ['houdini', 'lookdev'],
            'active': True,
            'last_activity': metadata.get('created_at')
        }
        
        user_relationship = (
            'user_created_asset',
            {
                '_from': f'users/{user_key}',
                '_to': f'assets/{asset_id}',
                'role': 'creator',
                'created_at': metadata.get('created_at'),
                'contribution_type': 'full_creation'
            }
        )
        
        return user_doc, user_relationship
    
    def _parse_project_context(self, metadata: Dict, asset_id: str) -> Tuple:
        """Extract project context from source file path"""
        source_path = metadata.get('source_hip_file', '')
        
        # Extract project from path pattern
        # /net/general/250103_under_armour_7v7/vfx/asset/...
        path_parts = Path(source_path).parts
        project_part = None
        
        for part in path_parts:
            if '_' in part and any(char.isdigit() for char in part):
                project_part = part
                break
        
        if project_part:
            project_key = project_part.lower()
            return (
                'project_contains_asset',
                {
                    '_from': f'projects/{project_key}',
                    '_to': f'assets/{asset_id}',
                    'usage_context': 'asset_library',
                    'source_path': source_path,
                    'approval_status': 'approved'
                }
            )
        
        return None
    
    def _create_texture_document(self, texture_path: str, metadata: Dict) -> Dict:
        """Create texture document from path"""
        texture_key = self._generate_texture_key(texture_path)
        path_obj = Path(texture_path)
        
        return {
            '_key': texture_key,
            'filename': path_obj.name,
            'file_path': texture_path,
            'texture_type': self._infer_texture_type(texture_path),
            'format': path_obj.suffix[1:].upper(),
            'created_at': metadata.get('created_at'),
            'asset_context': metadata['id'],
            'udim_tile': self._extract_udim_tile(path_obj.name),
            'is_udim_sequence': '.' in path_obj.stem and any(char.isdigit() for char in path_obj.stem.split('.')[-1])
        }
    
    def _generate_texture_key(self, texture_path: str) -> str:
        """Generate consistent texture key"""
        path_obj = Path(texture_path)
        # Use filename without extension as base, replace dots with underscores
        base_name = path_obj.stem.replace('.', '_').replace(' ', '_').lower()
        return f"tex_{base_name}"
    
    def _generate_geometry_key(self, geo_path: str) -> str:
        """Generate consistent geometry key"""
        path_obj = Path(geo_path)
        base_name = path_obj.stem.replace('.', '_').replace(' ', '_').lower()
        return f"geo_{base_name}"
    
    def _infer_texture_type(self, texture_path: str) -> str:
        """Infer texture type from filename"""
        path_lower = texture_path.lower()
        
        if 'basecolor' in path_lower or 'diffuse' in path_lower:
            return 'basecolor'
        elif 'roughness' in path_lower:
            return 'roughness'
        elif 'normal' in path_lower:
            return 'normal'
        elif 'metallic' in path_lower or 'metal' in path_lower:
            return 'metallic'
        elif 'specular' in path_lower:
            return 'specular'
        elif 'emission' in path_lower or 'emissive' in path_lower:
            return 'emission'
        elif 'opacity' in path_lower or 'alpha' in path_lower:
            return 'opacity'
        elif 'displacement' in path_lower or 'height' in path_lower:
            return 'displacement'
        else:
            return 'unknown'
    
    def _extract_udim_tile(self, filename: str) -> str:
        """Extract UDIM tile number from filename"""
        import re
        udim_match = re.search(r'\.(\d{4})\.', filename)
        if udim_match:
            return udim_match.group(1)
        return None
    
    def _calculate_complexity_score(self, metadata: Dict) -> int:
        """Calculate asset complexity score (1-10)"""
        score = 1
        
        # Add points for content
        texture_count = metadata.get('textures', {}).get('count', 0)
        geometry_count = metadata.get('geometry_files', {}).get('count', 0)
        node_count = metadata.get('node_summary', {}).get('total_nodes', 0)
        
        score += min(texture_count // 3, 3)  # Max 3 points for textures
        score += min(geometry_count, 2)      # Max 2 points for geometry
        score += min(node_count // 5, 2)     # Max 2 points for nodes
        
        # Add points for advanced features
        if metadata.get('textures', {}).get('mapping'):
            score += 1  # Complex texture mapping
        
        if any('udim' in str(v).lower() for v in metadata.get('textures', {}).get('mapping', {}).values()):
            score += 1  # UDIM sequences
        
        return min(score, 10)
    
    def insert_parsed_data(self, parsed_data: Dict) -> Dict:
        """Insert parsed documents and relationships into ArangoDB"""
        stats = {
            'documents_inserted': 0,
            'relationships_inserted': 0,
            'errors': []
        }
        
        # Insert documents first
        for collection_name, document in parsed_data['documents']:
            try:
                collection = self.collections[collection_name]
                # Use upsert to handle duplicates
                collection.insert(document, overwrite=True)
                stats['documents_inserted'] += 1
            except Exception as e:
                stats['errors'].append(f"Document insert error in {collection_name}: {e}")
                logger.error(f"Failed to insert document in {collection_name}: {e}")
        
        # Insert relationships
        for collection_name, relationship in parsed_data['relationships']:
            try:
                collection = self.collections[collection_name]
                collection.insert(relationship, overwrite=True)
                stats['relationships_inserted'] += 1
            except Exception as e:
                stats['errors'].append(f"Relationship insert error in {collection_name}: {e}")
                logger.error(f"Failed to insert relationship in {collection_name}: {e}")
        
        return stats

# Usage example
def parse_and_import_asset(arango_db, metadata_file_path: str):
    """Parse a single asset metadata file and import into ArangoDB graph"""
    parser = AtlasGraphParser(arango_db)
    metadata_file = Path(metadata_file_path)
    
    # Parse metadata into graph structure
    parsed_data = parser.parse_asset_metadata(metadata_file)
    
    # Insert into database
    stats = parser.insert_parsed_data(parsed_data)
    
    logger.info(f"Import complete: {stats['documents_inserted']} documents, "
               f"{stats['relationships_inserted']} relationships inserted")
    
    if stats['errors']:
        logger.warning(f"Errors encountered: {stats['errors']}")
    
    return stats