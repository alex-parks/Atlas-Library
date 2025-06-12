# backend/setup_sqlite_assets.py
"""
Setup script for Blacksmith Atlas SQLite Asset Database
Run this to initialize and populate your SQLite database with JSON data
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from database.sqlite_manager import SQLiteAssetManager
except ImportError:
    print("❌ Error: Could not import SQLiteAssetManager")
    print("   Make sure you've created the database/sqlite_manager.py file")
    sys.exit(1)


def check_json_file(json_path: str) -> bool:
    """Check if JSON file exists and is valid"""
    json_file = Path(json_path)

    if not json_file.exists():
        print(f"❌ JSON file not found: {json_path}")
        return False

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"❌ JSON file is not a list: {type(data)}")
            return False

        print(f"✅ JSON file valid: {len(data)} assets found")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return False


def setup_directories():
    """Create necessary directories"""
    directories = [
        "database",
        "logs"
    ]

    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Directory ensured: {dir_path}")


def test_database_operations(manager: SQLiteAssetManager):
    """Test basic database operations"""
    print("\n🧪 Testing database operations...")

    try:
        # Test getting all assets
        assets = manager.get_all_assets()
        print(f"✅ Retrieved {len(assets)} assets")

        if assets:
            # Test getting specific asset
            first_asset = assets[0]
            asset_id = first_asset['id']
            specific_asset = manager.get_asset_by_id(asset_id)

            if specific_asset:
                print(f"✅ Retrieved specific asset: {specific_asset['name']}")
            else:
                print(f"❌ Could not retrieve asset by ID: {asset_id}")

            # Test search
            search_results = manager.search_assets(search_term=first_asset['name'][:3])
            print(f"✅ Search test: found {len(search_results)} assets")

            # Test statistics
            stats = manager.get_statistics()
            print(f"✅ Statistics: {stats}")

        else:
            print("⚠️ No assets found for testing")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()


def display_asset_summary(manager: SQLiteAssetManager):
    """Display a summary of assets in the database"""
    try:
        assets = manager.get_all_assets()
        stats = manager.get_statistics()

        print("\n📊 Asset Database Summary:")
        print("=" * 50)
        print(f"Total Assets: {len(assets)}")

        if stats.get('by_category'):
            print("\nBy Category:")
            for category, count in stats['by_category'].items():
                print(f"  {category}: {count}")

        if stats.get('by_creator'):
            print("\nBy Creator:")
            for creator, count in stats['by_creator'].items():
                print(f"  {creator}: {count}")

        if assets:
            print("\nSample Assets:")
            for i, asset in enumerate(assets[:3]):
                print(f"  {i + 1}. {asset['name']} ({asset['category']}) - ID: {asset['id']}")

                # Check thumbnail
                thumbnail_path = asset.get('thumbnail_path') or asset.get('paths', {}).get('thumbnail')
                if thumbnail_path and Path(thumbnail_path).exists():
                    print(f"      ✅ Thumbnail: {Path(thumbnail_path).name}")
                else:
                    print(f"      ❌ No thumbnail found")

            if len(assets) > 3:
                print(f"  ... and {len(assets) - 3} more assets")

        print("=" * 50)

    except Exception as e:
        print(f"❌ Error displaying summary: {e}")


def main():
    """Main setup function"""
    print("🚀 Blacksmith Atlas - SQLite Database Setup")
    print("=" * 60)

    # Configuration
    json_path = r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json"
    db_path = "backend/database/assets.db"

    print(f"📁 JSON Source: {json_path}")
    print(f"🗃️ SQLite Database: {db_path}")
    print()

    # Step 1: Check JSON file
    print("Step 1: Checking JSON source file...")
    if not check_json_file(json_path):
        print("\n❌ Setup failed - JSON file issues")
        return False

    # Step 2: Setup directories
    print("\nStep 2: Setting up directories...")
    setup_directories()

    # Step 3: Initialize SQLite manager
    print("\nStep 3: Initializing SQLite database...")
    try:
        manager = SQLiteAssetManager(db_path=db_path, json_path=json_path)
        print("✅ SQLite manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize SQLite manager: {e}")
        return False

    # Step 4: Import JSON data
    print("\nStep 4: Importing JSON data to SQLite...")
    try:
        success = manager.json_to_sqlite()
        if success:
            print("✅ JSON data imported successfully")
        else:
            print("❌ JSON import failed")
            return False
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    # Step 5: Test database operations
    print("\nStep 5: Testing database operations...")
    test_database_operations(manager)

    # Step 6: Display summary
    print("\nStep 6: Database summary...")
    display_asset_summary(manager)

    # Success message
    print("\n🎉 SQLite Database Setup Complete!")
    print("\nNext steps:")
    print("1. Start your backend: python main.py")
    print("2. Start your frontend: cd frontend && npm run dev")
    print("3. Test the API: http://localhost:8000/docs")
    print("4. View Asset Library: http://localhost:3011")
    print("\nAPI Endpoints:")
    print("- GET /api/v1/assets - List all assets")
    print("- GET /api/v1/test - Test database connection")
    print("- POST /admin/sync - Sync SQLite with JSON")
    print("- GET /health - Health check")

    return True


def quick_test():
    """Quick test of the setup"""
    print("🧪 Quick SQLite Test")
    print("=" * 30)

    json_path = r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json"

    try:
        manager = SQLiteAssetManager(json_path=json_path)

        # Import data
        print("Importing JSON data...")
        success = manager.json_to_sqlite()

        if success:
            assets = manager.get_all_assets()
            print(f"✅ Success! {len(assets)} assets in SQLite")

            if assets:
                first_asset = assets[0]
                print(f"Sample asset: {first_asset['name']} (ID: {first_asset['id']})")
        else:
            print("❌ Import failed")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        main()