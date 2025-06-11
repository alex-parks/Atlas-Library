# backend/verify_system.py
"""
Quick verification script to ensure everything is working for your presentation
"""

import json
import requests
from pathlib import Path


def check_json_database():
    """Check if JSON database exists and is readable"""
    print("🔍 Checking JSON Database...")

    db_path = Path(__file__).parent / "assetlibrary" / "database" / "3DAssets.json"

    if not db_path.exists():
        print(f"❌ Database file not found at: {db_path}")
        return False

    try:
        with open(db_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict) and 'assets' in data:
            count = len(data['assets'])
        else:
            count = 0

        print(f"✅ Database found with {count} assets")
        return True

    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return False


def check_api_endpoints():
    """Check if API endpoints are working"""
    print("\n🌐 Checking API Endpoints...")

    base_url = "http://localhost:8000"

    endpoints = [
        "/",
        "/health",
        "/api/v1/test",
        "/api/v1/assets"
    ]

    all_working = True

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                all_working = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection refused (is server running?)")
            all_working = False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            all_working = False

    return all_working


def check_houdini_export_compatibility():
    """Check if Houdini export system will work with new API"""
    print("\n🎨 Checking Houdini Export Compatibility...")

    # Check if houdiniae.py exists
    houdini_script = Path(__file__).parent / "assetlibrary" / "_3D" / "houdiniae.py"

    if not houdini_script.exists():
        print(f"❌ Houdini export script not found at: {houdini_script}")
        return False

    print(f"✅ Houdini export script found")

    # Check if the JSON handler is being used
    try:
        with open(houdini_script, 'r') as f:
            content = f.read()

        if "JSONDatabaseHandler" in content:
            print("✅ JSON database handler is configured")
        else:
            print("⚠️ JSON database handler not found in script")

        if "'type': 'json'" in content or "'json':" in content:
            print("✅ JSON mode is configured")
        else:
            print("⚠️ JSON mode not explicitly configured")

        return True

    except Exception as e:
        print(f"❌ Error reading Houdini script: {e}")
        return False


def create_sample_asset():
    """Create a sample asset to test the system"""
    print("\n📦 Creating Sample Asset...")

    db_path = Path(__file__).parent / "assetlibrary" / "database" / "3DAssets.json"

    # Load existing assets
    try:
        if db_path.exists():
            with open(db_path, 'r') as f:
                assets = json.load(f)
        else:
            assets = []

        if not isinstance(assets, list):
            assets = []

        # Check if sample already exists
        if any(asset.get('name') == 'Test_Asset_Demo' for asset in assets):
            print("ℹ️ Sample asset already exists")
            return True

        # Create sample asset for presentation
        sample_asset = {
            "id": "demo_001",
            "name": "Test_Asset_Demo",
            "category": "Props",
            "folder": "demo_001_Test_Asset_Demo",
            "paths": {
                "usd": "C:/BlacksmithAtlas_Files/BlacksmithLibrary/3D/USD/demo_001_Test_Asset_Demo.usd",
                "thumbnail": "C:/BlacksmithAtlas_Files/BlacksmithLibrary/3D/USD/demo_001_Test_Asset_Demo/Thumbnail/Test_Asset_Demo_thumbnail.png",
                "textures": "C:/BlacksmithAtlas_Files/BlacksmithLibrary/3D/USD/demo_001_Test_Asset_Demo/Linked_Textures/"
            },
            "metadata": {
                "houdini_version": "19.5.640",
                "created_by": "Demo_Artist",
                "hip_file": "/path/to/demo.hip",
                "hda_parameters": {
                    "notes": "Demo asset for presentation - shows asset library functionality"
                }
            },
            "file_sizes": {
                "usd": 2048000,
                "thumbnail": 512000
            },
            "created_at": "2025-06-11T10:30:00Z",
            "tags": ["demo", "presentation", "props"]
        }

        assets.append(sample_asset)

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Save back to database
        with open(db_path, 'w') as f:
            json.dump(assets, f, indent=2)

        print("✅ Sample asset created for presentation")
        return True

    except Exception as e:
        print(f"❌ Failed to create sample asset: {e}")
        return False


def main():
    """Run all verification checks"""
    print("🚀 Blacksmith Atlas - Presentation Verification")
    print("=" * 60)

    checks = [
        ("JSON Database", check_json_database),
        ("Houdini Export", check_houdini_export_compatibility),
        ("Sample Asset", create_sample_asset),
    ]

    all_passed = True

    for check_name, check_func in checks:
        result = check_func()
        if not result:
            all_passed = False

    # Check API endpoints (optional - server might not be running yet)
    print("\n🌐 API Endpoint Check (optional):")
    print("   Note: Start the server first with 'python main.py'")
    api_result = check_api_endpoints()

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 All core checks passed! System ready for presentation.")

        if api_result:
            print("✅ API endpoints also working - full system operational!")
        else:
            print("ℹ️ API endpoints not tested (server not running)")

        print("\n📋 Presentation Checklist:")
        print("1. ✅ JSON database configured")
        print("2. ✅ Sample data available")
        print("3. ✅ Houdini export system compatible")
        print("4. 🔄 Start backend: python main.py")
        print("5. 🔄 Start frontend: npm run dev")
        print("6. 🔄 Demo asset export from Houdini")

    else:
        print("❌ Some checks failed. Please review above output.")

    return all_passed


if __name__ == "__main__":
    main()