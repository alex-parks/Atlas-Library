"""
Atlas Database Service - ArangoDB Integration

This module provides database connectivity for storing asset metadata
during the Atlas export process.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import json

# Try to import ArangoDB
try:
    from arango import ArangoClient
    ARANGO_AVAILABLE = True
except ImportError:
    print("⚠️  ArangoDB client not available - database storage disabled")
    ARANGO_AVAILABLE = False

# Import Atlas configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from assetlibrary.config import BlacksmithAtlasConfig
    from assetlibrary.models import Asset3D, Texture, Material
    CONFIG_AVAILABLE = True
except ImportError:
    print("⚠️  Atlas configuration not available - using defaults")
    CONFIG_AVAILABLE = False


class AtlasDatabaseService:
    """Service for storing Atlas assets in ArangoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = {}
        self.connected = False
        
        if ARANGO_AVAILABLE and CONFIG_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """Connect to ArangoDB using Atlas configuration"""
        try:
            # Get database configuration
            env = os.getenv('ATLAS_ENV', 'development')
            db_config = BlacksmithAtlasConfig.get_database_config(env)
            
            print(f"   🔌 Connecting to ArangoDB ({env})...")
            print(f"      Host: {db_config['hosts'][0]}")
            print(f"      Database: {db_config['database']}")
            print(f"      User: {db_config['username']}")
            
            # Create client and connect
            self.client = ArangoClient(hosts=db_config['hosts'])
            self.db = self.client.db(
                db_config['database'],
                username=db_config['username'],
                password=db_config['password']
            )
            
            # Test connection
            server_info = self.db.properties()
            print(f"   ✅ Connected to ArangoDB: {server_info['name']}")
            
            # Get collections
            self.collections = {
                'assets': self.db.collection('Atlas_Library'),
                'relationships': self.db.collection('asset_relationships'),
                'projects': self.db.collection('projects'),
                'tags': self.db.collection('tags'),
                'users': self.db.collection('users')
            }
            
            self.connected = True
            
        except Exception as e:
            print(f"   ❌ Failed to connect to ArangoDB: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.connected and ARANGO_AVAILABLE
    
    def store_asset(self, asset_data):
        """Store an asset in the database"""
        try:
            if not self.is_connected():
                print("Database not connected")
                return None
                
            collection = self.db.collection('Atlas_Library')
            
            # Add default fields if not present
            asset_data.setdefault('created_at', datetime.now().isoformat())
            asset_data.setdefault('updated_at', datetime.now().isoformat())
            asset_data.setdefault('_type', 'Asset3D')
            
            result = collection.insert(asset_data)
            return result['_id'] if result else None
            
        except Exception as e:
            print(f"Error storing asset: {e}")
            return None
    
    def store_texture(self, texture_data):
        """Store a texture in the database"""
        try:
            if not self.is_connected():
                print("Database not connected")
                return None
                
            collection = self.db.collection('Atlas_Library')  # Store textures as assets with type='texture'
            
            # Add default fields
            texture_data.setdefault('created_at', datetime.now().isoformat())
            texture_data.setdefault('updated_at', datetime.now().isoformat())
            texture_data.setdefault('_type', 'Texture')
            
            result = collection.insert(texture_data)
            return result['_id'] if result else None
            
        except Exception as e:
            print(f"Error storing texture: {e}")
            return None
    
    def link_asset_texture(self, asset_id, texture_id, material_name=None):
        """Link an asset to a texture through a relationship"""
        try:
            if not self.is_connected():
                print("Database not connected")
                return None
                
            collection = self.db.collection('asset_relationships')
            
            relationship_data = {
                '_from': f'assets/{asset_id}',
                '_to': f'assets/{texture_id}',
                'relationship_type': 'uses_texture',
                'material_name': material_name,
                'created_at': datetime.now().isoformat()
            }
            
            result = collection.insert(relationship_data)
            return result['_id'] if result else None
            
        except Exception as e:
            print(f"Error linking asset to texture: {e}")
            return None
    
    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset by ID"""
        if not self.is_connected():
            return None
        
        try:
            return self.collections['assets'].get(asset_id)
        except Exception as e:
            print(f"   ❌ Failed to get asset {asset_id}: {e}")
            return None
    
    def search_assets(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for assets matching criteria"""
        if not self.is_connected():
            return []
        
        try:
            # Build AQL query
            aql_query = """
            FOR asset IN Atlas_Library
            FILTER asset.status == "active"
            """
            
            bind_vars = {}
            
            # Add search criteria
            if 'name' in query:
                aql_query += " AND CONTAINS(LOWER(asset.name), LOWER(@name))"
                bind_vars['name'] = query['name']
            
            if 'category' in query:
                aql_query += " AND asset.category == @category"
                bind_vars['category'] = query['category']
            
            if 'tags' in query:
                aql_query += " AND LENGTH(INTERSECTION(asset.tags, @tags)) > 0"
                bind_vars['tags'] = query['tags']
            
            aql_query += " SORT asset.created_at DESC RETURN asset"
            
            cursor = self.db.aql.execute(aql_query, bind_vars=bind_vars)
            return list(cursor)
            
        except Exception as e:
            print(f"   ❌ Asset search failed: {e}")
            return []
    
    def update_asset(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Update asset metadata"""
        if not self.is_connected():
            return False
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            self.collections['assets'].update(asset_id, updates)
            print(f"   ✅ Asset {asset_id} updated")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to update asset {asset_id}: {e}")
            return False
    
    def store_texture(self, texture_data: Dict[str, Any]) -> Optional[str]:
        """Store texture metadata"""
        if not self.is_connected():
            return None
        
        try:
            # Generate texture ID based on file path
            texture_id = self._generate_texture_id(texture_data)
            texture_data['_key'] = texture_id
            texture_data['_type'] = 'Texture'
            
            # Add timestamps
            now = datetime.now().isoformat()
            texture_data['created_at'] = now
            texture_data['updated_at'] = now
            
            # Store in assets collection (textures are also assets)
            result = self.collections['assets'].insert(texture_data, overwrite=True)
            
            print(f"   ✅ Texture stored: {texture_data.get('name', 'Unknown')}")
            return texture_id
            
        except Exception as e:
            print(f"   ❌ Failed to store texture: {e}")
            return None
    
    def link_asset_texture(self, asset_id: str, texture_id: str, material_name: str = None):
        """Create relationship between asset and texture"""
        if not self.is_connected():
            return
        
        try:
            relationship = {
                '_from': f"assets/{asset_id}",
                '_to': f"assets/{texture_id}",
                'type': 'uses_texture',
                'material_name': material_name,
                'created_at': datetime.now().isoformat()
            }
            
            self.collections['relationships'].insert(relationship)
            print(f"   ✅ Linked asset {asset_id} to texture {texture_id}")
            
        except Exception as e:
            print(f"   ❌ Failed to link asset to texture: {e}")
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.is_connected():
            return {'connected': False}
        
        try:
            # Count assets by category
            aql_query = """
            FOR asset IN Atlas_Library
            FILTER asset._type == "Asset3D"
            COLLECT category = asset.category WITH COUNT INTO count
            RETURN {category: category, count: count}
            """
            
            cursor = self.db.aql.execute(aql_query)
            by_category = list(cursor)
            
            # Total count
            total_query = "RETURN LENGTH(FOR asset IN Atlas_Library FILTER asset._type == 'Asset3D' RETURN 1)"
            total_cursor = self.db.aql.execute(total_query)
            total_assets = list(total_cursor)[0]
            
            return {
                'connected': True,
                'total_assets': total_assets,
                'by_category': by_category,
                'database': self.db.properties()
            }
            
        except Exception as e:
            print(f"   ❌ Failed to get statistics: {e}")
            return {'connected': False, 'error': str(e)}
    
    def _generate_asset_id(self, asset_data: Dict[str, Any]) -> str:
        """Generate unique asset ID"""
        name = asset_data.get('name', 'asset')
        category = asset_data.get('category', 'general')
        timestamp = str(datetime.now().timestamp())
        
        # Create hash from name + category + timestamp
        hash_input = f"{name}_{category}_{timestamp}".encode()
        hash_hex = hashlib.md5(hash_input).hexdigest()
        
        return hash_hex[:12].upper()
    
    def _generate_texture_id(self, texture_data: Dict[str, Any]) -> str:
        """Generate unique texture ID based on file path"""
        file_path = texture_data.get('path', texture_data.get('name', 'texture'))
        
        # Create hash from file path
        hash_input = file_path.encode()
        hash_hex = hashlib.md5(hash_input).hexdigest()
        
        return f"tex_{hash_hex[:8]}"


# Global database service instance
_db_service = None

def get_database_service() -> AtlasDatabaseService:
    """Get global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = AtlasDatabaseService()
    return _db_service


def test_database_connection():
    """Test database connection and print status"""
    print("🔍 TESTING ATLAS DATABASE CONNECTION")
    print("=" * 50)
    
    db = get_database_service()
    
    if db.is_connected():
        print("✅ Database connection successful!")
        
        # Get statistics
        stats = db.get_asset_statistics()
        print(f"📊 Total assets: {stats.get('total_assets', 0)}")
        
        if stats.get('by_category'):
            print("📂 Assets by category:")
            for cat_data in stats['by_category']:
                print(f"   - {cat_data['category']}: {cat_data['count']}")
        
        db_info = stats.get('database', {})
        if db_info:
            print(f"🗄️ Database: {db_info.get('name', 'Unknown')}")
            print(f"🔢 Collections: {len(db.collections)}")
    else:
        print("❌ Database connection failed!")
        print("   - Check if ArangoDB is running")
        print("   - Verify credentials in .env file")
        print("   - Check if arango-python package is installed")


if __name__ == "__main__":
    test_database_connection()
