# backend/assetlibrary/test_export.py
"""
Test script to verify the asset export system outside of Houdini
Run this to test database connections and export logic
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from assetlibrary.houdini.houdiniae import TemplateAssetExporter
from assetlibrary.config import BlacksmithAtlasConfig
import json
import yaml


def test_config():
    """Test configuration validation"""
    print("Testing configuration...")
    config = BlacksmithAtlasConfig()

    validation = config.validate_config()
    if validation['valid']:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")

    print(f"\nDatabase type: {config.DATABASE['type']}")
    print(f"Base library path: {config.BASE_LIBRARY_PATH}")
    print(f"USD path: {config.USD_LIBRARY_PATH}")


def test_yaml_export():
    """Test YAML database export"""
    print("\n" + "=" * 60)
    print("Testing YAML Export")
    print("=" * 60)

    # Create test exporter
    exporter = TemplateAssetExporter("TestAsset_YAML", "Test")

    # Create test document
    test_doc = {
        'id': exporter.asset_id,
        'name': exporter.name,
        'category': exporter.category,
        'folder': exporter.folder_name,
        'paths': {
            'usd': str(exporter.usd_path),
            'thumbnail': str(exporter.thumbnail_path),
            'textures': str(exporter.textures_folder)
        },
        'metadata': exporter.metadata,
        'test_mode': True
    }

    # Save to YAML
    if exporter.db_handler.save_asset(test_doc):
        print(f"✅ Successfully saved to YAML")
        print(f"   Asset ID: {exporter.asset_id}")
        print(f"   Name: {exporter.name}")

        # Verify by loading
        assets = exporter.db_handler.load_assets()
        found = any(asset['id'] == exporter.asset_id for asset in assets)
        if found:
            print("✅ Verified: Asset found in database")
        else:
            print("❌ Error: Asset not found after save")
    else:
        print("❌ Failed to save to YAML")


def test_json_export():
    """Test JSON database export"""
    print("\n" + "=" * 60)
    print("Testing JSON Export")
    print("=" * 60)

    # Temporarily switch to JSON mode
    original_type = BlacksmithAtlasConfig.DATABASE['type']
    BlacksmithAtlasConfig.DATABASE['type'] = 'json'

    try:
        # Create test exporter
        exporter = TemplateAssetExporter("TestAsset_JSON", "Test")

        # Create test document
        test_doc = {
            'id': exporter.asset_id,
            'name': exporter.name,
            'category': exporter.category,
            'folder': exporter.folder_name,
            'paths': {
                'usd': str(exporter.usd_path),
                'thumbnail': str(exporter.thumbnail_path),
                'textures': str(exporter.textures_folder)
            },
            'metadata': exporter.metadata,
            'test_mode': True
        }

        # Save to JSON
        if exporter.db_handler.save_asset(test_doc):
            print(f"✅ Successfully saved to JSON")
            print(f"   Asset ID: {exporter.asset_id}")
            print(f"   Name: {exporter.name}")

            # Verify file contents
            json_path = exporter.db_handler.json_path
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                print(f"✅ JSON file contains {len(data)} assets")
            else:
                print("❌ JSON file not found")
        else:
            print("❌ Failed to save to JSON")

    finally:
        # Restore original type
        BlacksmithAtlasConfig.DATABASE['type'] = original_type


def test_arango_connection():
    """Test ArangoDB connection (if available)"""
    print("\n" + "=" * 60)
    print("Testing ArangoDB Connection")
    print("=" * 60)

    try:
        from arango import ArangoClient

        config = BlacksmithAtlasConfig.DATABASE['arango']
        client = ArangoClient(hosts=config['hosts'])

        # Try to connect
        sys_db = client.db('_system', username=config['username'], password=config['password'])

        # Check if our database exists
        if config['database'] in sys_db.databases():
            print(f"✅ Database '{config['database']}' exists")

            # Connect to our database
            db = client.db(config['database'], username=config['username'], password=config['password'])

            # Check collections
            collections = db.collections()
            print(f"   Collections: {[c['name'] for c in collections if not c['name'].startswith('_')]}")

        else:
            print(f"⚠️ Database '{config['database']}' does not exist")
            print("   Run this to create it:")
            print(f"   sys_db.create_database('{config['database']}')")

    except ImportError:
        print("⚠️ python-arango not installed")
        print("   Run: pip install python-arango")
    except Exception as e:
        print(f"❌ ArangoDB connection failed: {e}")
        print("   Make sure ArangoDB is running on http://localhost:8529")


def test_folder_creation():
    """Test folder structure creation"""
    print("\n" + "=" * 60)
    print("Testing Folder Creation")
    print("=" * 60)

    # Create test exporter
    exporter = TemplateAssetExporter("TestAsset_Folders", "Test")

    # Don't actually create folders, just show what would be created
    print(f"Would create folder structure:")
    print(f"├── {exporter.asset_folder}/")
    print(f"│   ├── USD/")
    print(f"│   │   └── {exporter.name}.usd")
    print(f"│   ├── Linked_Textures/")
    print(f"│   ├── FBX/")
    print(f"│   │   └── {exporter.name}.fbx")
    print(f"│   └── Thumbnail/")
    print(f"│       └── {exporter.name}_thumbnail.png")


def display_current_assets():
    """Display all assets currently in the database"""
    print("\n" + "=" * 60)
    print("Current Assets in Database")
    print("=" * 60)

    config = BlacksmithAtlasConfig()

    # Load based on current database type
    if config.DATABASE['type'] == 'yaml':
        yaml_path = Path(__file__).parent.parent.parent / config.DATABASE['yaml_file']
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                assets = yaml.safe_load(f) or []
            print(f"YAML Database: {len(assets)} assets")
            for asset in assets:
                print(f"  - {asset.get('name', 'Unknown')} (ID: {asset.get('id', 'Unknown')})")
        else:
            print("YAML database file not found")

    elif config.DATABASE['type'] == 'json':
        json_path = Path(__file__).parent.parent.parent / config.DATABASE['json_file']
        if json_path.exists():
            with open(json_path, 'r') as f:
                assets = json.load(f)
            print(f"JSON Database: {len(assets)} assets")
            for asset in assets:
                print(f"  - {asset.get('name', 'Unknown')} (ID: {asset.get('id', 'Unknown')})")
        else:
            print("JSON database file not found")


def main():
    """Run all tests"""
    print("Blacksmith Atlas Asset Export Test Suite")
    print("========================================\n")

    # Ensure directories exist
    BlacksmithAtlasConfig.ensure_directories()

    # Run tests
    test_config()
    test_yaml_export()
    test_json_export()
    test_arango_connection()
    test_folder_creation()
    display_current_assets()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()