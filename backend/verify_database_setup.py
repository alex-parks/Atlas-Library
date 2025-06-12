# backend/verify_database_setup.py - Fixed version
"""
Fixed database verification script for Blacksmith Atlas
Handles SQLite connection issues properly
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))


def check_json_source():
    """Check if the JSON source file exists and is valid"""
    print("🔍 Checking JSON source file...")

    json_path = Path(r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json")

    if not json_path.exists():
        print(f"   ❌ JSON file not found: {json_path}")
        return False, f"File not found: {json_path}"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"   ❌ JSON file is not a list: {type(data)}")
            return False, f"Invalid format: {type(data)}"

        print(f"   ✅ JSON file valid: {len(data)} assets found")
        return True, f"{len(data)} assets available"

    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON format: {e}")
        return False, f"JSON decode error: {e}"
    except Exception as e:
        print(f"   ❌ Error reading JSON: {e}")
        return False, f"Read error: {e}"


def check_directories():
    """Check if required directories exist"""
    print("📁 Checking directory structure...")

    required_dirs = [
        "backend/database",
        "backend/logs",
        "config"
    ]

    all_good = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"   ❌ Failed to create {dir_path}: {e}")
                all_good = False
        else:
            print(f"   ✅ Directory exists: {dir_path}")

    return all_good, "All directories ready" if all_good else "Some directories missing"


def check_database_import():
    """Check if SQLiteAssetManager can be imported"""
    print("📦 Checking database module import...")

    try:
        from database.sqlite_manager import SQLiteAssetManager
        print("   ✅ SQLiteAssetManager imported successfully")
        return True, "Module import successful"
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False, f"Import error: {e}"
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False, f"Unexpected error: {e}"


def test_database_creation_safe():
    """Test database creation with proper cleanup"""
    print("🗄️ Testing database creation (safe mode)...")

    try:
        from database.sqlite_manager import SQLiteAssetManager

        # Use a unique temporary database file
        temp_dir = tempfile.gettempdir()
        test_db_name = f"atlas_test_{int(time.time() * 1000)}.db"
        test_db_path = os.path.join(temp_dir, test_db_name)

        print(f"   Using test database: {test_db_path}")

        # Initialize manager with test database
        manager = SQLiteAssetManager(
            db_path=test_db_path,
            json_path=r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json"
        )

        # Test import
        success = manager.json_to_sqlite()
        if not success:
            return False, "JSON import failed"

        # Test retrieval
        assets = manager.get_all_assets()
        asset_count = len(assets)

        # Clean up immediately
        manager.cleanup_connections()

        # Wait for file handles to be released
        time.sleep(0.1)

        # Remove test database
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
                print(f"   🧹 Cleaned up test database")
        except Exception as cleanup_error:
            print(f"   ⚠️ Cleanup warning: {cleanup_error}")

        print(f"   ✅ Database test successful: {asset_count} assets imported")
        return True, f"Database operations successful: {asset_count} assets"

    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False, f"Database test error: {e}"


def check_api_dependencies():
    """Check if API dependencies are available"""
    print("📡 Checking API dependencies...")

    try:
        import fastapi
        import uvicorn
        import sqlite3

        print("   ✅ FastAPI available")
        print("   ✅ Uvicorn available")
        print("   ✅ SQLite3 available")

        return True, "All API dependencies available"

    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        return False, f"Missing dependency: {e}"


def check_frontend_setup():
    """Check if frontend is properly set up"""
    print("🖥️ Checking frontend setup...")

    frontend_path = Path("frontend")
    package_json = frontend_path / "package.json"
    node_modules = frontend_path / "node_modules"

    if not frontend_path.exists():
        print("   ❌ Frontend directory not found")
        return False, "Frontend directory missing"

    if not package_json.exists():
        print("   ❌ package.json not found")
        return False, "package.json missing"

    if not node_modules.exists():
        print("   ❌ node_modules not found - run 'npm install' in frontend directory")
        return False, "node_modules missing - run npm install"

    print("   ✅ Frontend structure looks good")
    return True, "Frontend setup complete"


def main():
    """Main verification function"""
    print("🚀 Blacksmith Atlas - Database Setup Verification (Fixed Version)")
    print("=" * 70)
    print()

    checks = [
        ("JSON Source File", check_json_source),
        ("Directory Structure", check_directories),
        ("Database Module Import", check_database_import),
        ("API Dependencies", check_api_dependencies),
        ("Database Creation (Safe)", test_database_creation_safe),
        ("Frontend Setup", check_frontend_setup),
    ]

    results = []
    passed = 0
    total = len(checks)

    for check_name, check_func in checks:
        try:
            success, message = check_func()
            results.append((check_name, success, message))
            if success:
                passed += 1
            print()  # Add space between checks
        except Exception as e:
            print(f"   ❌ Check failed with exception: {e}")
            results.append((check_name, False, f"Exception: {e}"))
            print()

    # Summary
    print("=" * 70)
    print("Verification Results:")

    for check_name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {check_name}: {message}")

    print("=" * 70)
    print(f"Summary: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All checks passed! Your database setup is ready.")
        print()
        print("Next steps:")
        print("1. Start backend: python main.py")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Or run both: npm run dev (from root directory)")
    else:
        print("❌ Some checks failed. Please fix the issues above before starting.")
        print()
        print("Common fixes:")
        print("- Run 'npm install' in the frontend directory")
        print("- Make sure your JSON file path is correct")
        print("- Check that all required directories exist")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)