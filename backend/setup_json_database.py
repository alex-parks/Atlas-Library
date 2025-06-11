# backend/setup_json_database.py
"""
Simple script to set up and verify JSON database for Asset Library
Run this before your presentation to ensure everything works
"""

import json
from pathlib import Path
from datetime import datetime


def setup_json_database():
    """Set up the JSON database with proper structure"""

    # Database path
    db_path = Path(__file__).parent / "assetlibrary" / "database" / "3DAssets.json"

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if database exists
    if db_path.exists():
        print(f"✅ JSON database already exists at: {db_path}")

        # Load and validate existing data
        try:
            with open(db_path, 'r') as f:
                data = json.load(f)

            if isinstance(data, list):
                asset_count = len(data)
            elif isinstance(data, dict) and 'assets' in data:
                asset_count = len(data['assets'])
            else:
                asset_count = 0

            print(f"📦 Found {asset_count} assets in database")

            return True

        except Exception as e:
            print(f"❌ Error reading existing database: {e}")
            print("Creating new database...")

    else:
        print(f"📁 Creating new JSON database at: {db_path}")

    # Create initial structure
    initial_data = []

    # Save initial database
    try:
        with open(db_path, 'w') as f:
            json.dump(initial_data, f, indent=2)

        print(f"✅ JSON database created successfully!")
        print(f"📂 Database location: {db_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def test_database_connection():
    """Test that the database can be read by the API"""

    print("\n🔧 Testing database connection...")

    try:
        # Import and test the load function
        import sys
        sys.path.append(str(Path(__file__).parent))

        from api.assets import load_json_database

        assets = load_json_database()
        print(f"✅ Successfully loaded {len(assets)} assets from database")

        return True

    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


def add_sample_asset():
    """Add a sample asset for testing (optional)"""

    db_path = Path(__file__).parent / "assetlibrary" / "database" / "3DAssets.json"

    if not db_path.exists():
        print("❌ Database doesn't exist. Run setup first.")
        return False

    # Load existing data
    try:
        with open(db_path, 'r') as f:
            assets = json.load(f)

        if not isinstance(assets, list):
            assets = []

        # Check if sample already exists
        if any(asset.get('name') == 'Sample_Asset' for asset in assets):
            print("ℹ️ Sample asset already exists")
            return True

        # Create sample asset
        sample_asset = {
            "id": "sample_001",
            "name": "Sample_Asset",
            "category": "Test",
            "folder": "sample_001_Sample_Asset",
            "paths": {
                "usd": "/path/to/sample.usd",
                "thumbnail": "/path/to/sample_thumbnail.png",
                "textures": "/path/to/textures/"
            },
            "metadata": {
                "houdini_version": "19.5.640",
                "created_by": "Atlas_System",
                "hda_parameters": {
                    "notes": "Sample asset for testing the JSON database"
                }
            },
            "file_sizes": {
                "usd": 1024000,
                "thumbnail": 256000
            },
            "created_at": datetime.now().isoformat(),
            "tags": ["sample", "test"]
        }

        # Add sample asset
        assets.append(sample_asset)

        # Save back to database
        with open(db_path, 'w') as f:
            json.dump(assets, f, indent=2)

        print("✅ Sample asset added successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to add sample asset: {e}")
        return False


def main():
    """Main setup function"""

    print("🚀 Blacksmith Atlas - JSON Database Setup")
    print("=" * 50)

    # Step 1: Set up database
    if not setup_json_database():
        return False

    # Step 2: Test connection
    if not test_database_connection():
        return False

    # Step 3: Optionally add sample data
    print("\n📝 Would you like to add a sample asset for testing? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            add_sample_asset()
    except:
        pass  # Skip if running in non-interactive environment

    print("\n🎉 Setup complete! Your JSON database is ready.")
    print("\nNext steps:")
    print("1. Start your backend: python main.py")
    print("2. Start your frontend: npm run dev")
    print("3. Test the API: http://localhost:8000/docs")
    print("4. Export assets from Houdini to populate the database")

    return True


if __name__ == "__main__":
    main()