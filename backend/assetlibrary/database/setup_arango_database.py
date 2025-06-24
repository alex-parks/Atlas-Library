# backend/assetlibrary/database/setup_arango_database.py
from arango.client import ArangoClient
import json
from pathlib import Path
import sys
import os

# Add the assetlibrary directory to the path
current_dir = Path(__file__).parent
assetlibrary_dir = current_dir.parent
sys.path.insert(0, str(assetlibrary_dir))

from config import BlacksmithAtlasConfig


def setup_database(environment: str = 'development'):
    """Set up ArangoDB with all required collections and initial data"""

    # Get database configuration
    db_config = BlacksmithAtlasConfig.get_database_config(environment)
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=db_config['hosts'])

    # Connect to system database
    sys_db = client.db('_system', username=db_config['username'], password=db_config['password'])

    # Create database if it doesn't exist
    db_name = db_config['database']
    if not sys_db.has_database(db_name):
        sys_db.create_database(db_name)
        print(f"✅ Created database: {db_name}")
    else:
        print(f"ℹ️ Database '{db_name}' already exists")

    # Connect to our database
    db = client.db(db_name, username=db_config['username'], password=db_config['password'])

    # Create collections
    collections = {
        'assets': {
            'type': 'document',
            'schema': {
                'rule': {
                    'type': 'object',
                    'properties': {
                        '_key': {'type': 'string'},
                        'name': {'type': 'string'},
                        'category': {'type': 'string'},
                        'asset_type': {'type': 'string'},
                        'paths': {'type': 'object'},
                        'metadata': {'type': 'object'},
                        'tags': {'type': 'array'},
                        'created_at': {'type': 'string'},
                        'updated_at': {'type': 'string'}
                    },
                    'required': ['name', 'category', 'asset_type']
                }
            }
        },
        'asset_relationships': {
            'type': 'edge',
            'schema': None
        },
        'projects': {
            'type': 'document',
            'schema': None
        },
        'tags': {
            'type': 'document',
            'schema': None
        },
        'users': {
            'type': 'document',
            'schema': None
        },
        'export_jobs': {
            'type': 'document',
            'schema': None
        }
    }

    for coll_name, config in collections.items():
        if not db.has_collection(coll_name):
            if config['type'] == 'edge':
                db.create_collection(coll_name, edge=True)
            else:
                collection = db.create_collection(coll_name)
                # Add schema validation if defined
                if config.get('schema'):
                    collection.configure(schema=config['schema'])
            print(f"✅ Created collection: {coll_name}")
        else:
            print(f"ℹ️ Collection '{coll_name}' already exists")

    # Create indexes
    assets = db.collection('assets')

    # Create indexes for better query performance
    indexes = [
        {'fields': ['name'], 'type': 'persistent'},
        {'fields': ['category'], 'type': 'persistent'},
        {'fields': ['created_at'], 'type': 'persistent'},
        {'fields': ['tags[*]'], 'type': 'persistent'},
        {'fields': ['metadata.houdini_version'], 'type': 'persistent', 'sparse': True}
    ]

    for index in indexes:
        try:
            assets.add_index(index)
            print(f"✅ Created index on: {index['fields']}")
        except Exception as e:
            if 'duplicate' not in str(e).lower():
                print(f"⚠️ Failed to create index on {index['fields']}: {e}")

    # Create some initial tags
    tags_collection = db.collection('tags')
    default_tags = [
        {'_key': 'hero', 'name': 'Hero', 'category': 'quality', 'color': '#FF6B6B'},
        {'_key': 'background', 'name': 'Background', 'category': 'usage', 'color': '#4ECDC4'},
        {'_key': 'wip', 'name': 'Work in Progress', 'category': 'status', 'color': '#FFE66D'},
        {'_key': 'approved', 'name': 'Approved', 'category': 'status', 'color': '#95E1D3'},
        {'_key': 'highres', 'name': 'High Resolution', 'category': 'technical', 'color': '#C7CEEA'},
        {'_key': 'lowres', 'name': 'Low Resolution', 'category': 'technical', 'color': '#FECA57'}
    ]

    for tag in default_tags:
        try:
            tags_collection.insert(tag)
            print(f"✅ Created tag: {tag['name']}")
        except Exception as e:
            if 'unique constraint violated' not in str(e).lower():
                print(f"⚠️ Failed to create tag {tag['name']}: {e}")

    print("\n✅ Database setup complete!")
    return db


def migrate_json_to_arango():
    """Migrate existing JSON data to ArangoDB"""

    # Path to your JSON file
    json_path = Path(__file__).parent / "3DAssets.json"

    if not json_path.exists():
        print(f"❌ JSON file not found: {json_path}")
        return

    # Set up database
    db = setup_database()

    # Load JSON data
    with open(json_path, 'r') as f:
        json_assets = json.load(f)

    print(f"\n📦 Migrating {len(json_assets)} assets from JSON to ArangoDB...")

    assets_collection = db.collection('assets')
    migrated = 0
    skipped = 0

    for asset in json_assets:
        try:
            # Prepare document for ArangoDB
            arango_doc = {
                '_key': asset['id'],  # Use existing ID as key
                'name': asset['name'],
                'category': asset['category'],
                'asset_type': '3D',  # All your current assets are 3D
                'folder': asset.get('folder', ''),
                'paths': asset.get('paths', {}),
                'metadata': asset.get('metadata', {}),
                'file_sizes': asset.get('file_sizes', {}),
                'dependencies': asset.get('dependencies', {}),
                'tags': [],  # Start with empty tags
                'created_at': asset.get('created_at', ''),
                'updated_at': asset.get('created_at', ''),  # Use created_at if no updated_at
                'legacy_json': True  # Mark as migrated from JSON
            }

            # Insert into ArangoDB
            assets_collection.insert(arango_doc)
            migrated += 1
            print(f"✅ Migrated: {asset['name']} (ID: {asset['id']})")

        except Exception as e:
            if 'unique constraint violated' in str(e).lower():
                skipped += 1
                print(f"⏭️ Skipped (already exists): {asset['name']}")
            else:
                print(f"❌ Failed to migrate {asset['name']}: {e}")

    print(f"\n📊 Migration complete!")
    print(f"   ✅ Migrated: {migrated}")
    print(f"   ⏭️ Skipped: {skipped}")
    print(f"   📄 Total in ArangoDB: {assets_collection.count()}")


def test_connection(environment: str = 'development'):
    """Test ArangoDB connection and show stats"""
    try:
        # Get database configuration
        db_config = BlacksmithAtlasConfig.get_database_config(environment)
        
        client = ArangoClient(hosts=db_config['hosts'])
        db = client.db(db_config['database'], username=db_config['username'], password=db_config['password'])

        print("✅ Connected to ArangoDB!")
        print(f"   Environment: {environment}")
        print(f"   Host: {db_config['hosts'][0]}")
        print(f"   Database: {db_config['database']}")
        print(f"\n📊 Database Statistics:")

        for coll_name in ['assets', 'projects', 'tags', 'users']:
            if db.has_collection(coll_name):
                count = db.collection(coll_name).count()
                print(f"   {coll_name}: {count} documents")

        # Show some sample assets
        assets = db.collection('assets')
        print(f"\n📦 Sample Assets:")
        for asset in assets.all(limit=5):
            print(f"   - {asset['name']} ({asset['category']}) - ID: {asset['_key']}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Environment: {environment}")
        print(f"   Host: {db_config['hosts'][0]}")
        print("   Make sure ArangoDB is running and accessible")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'migrate':
            migrate_json_to_arango()
        elif sys.argv[1] == 'test':
            test_connection()
        else:
            print("Usage: python setup_arango_database.py [migrate|test]")
    else:
        # Just set up the database
        setup_database()
        print("\nRun with 'migrate' argument to import JSON data")
        print("Run with 'test' argument to test connection")