# verify_setup.py - Run this to verify your setup before running npm run dev
"""
Verification script for Blacksmith Atlas ArangoDB setup
Run this before starting your application to ensure everything is configured correctly
"""

import json
import sys
from pathlib import Path


def check_file_structure():
    """Check if all required files exist"""
    print("🔍 Checking file structure...")

    required_files = [
        "backend/assetlibrary/database/setup_arango_database.py",
        "backend/start_database.py",
        "backend/api/assets.py",
        "backend/main.py",
        "package.json"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")

    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False

    return True


def check_json_file():
    """Check if the JSON file exists and is readable"""
    print("\n📄 Checking JSON source file...")

    json_path = r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json"
    json_file = Path(json_path)

    if not json_file.exists():
        print(f"  ❌ JSON file not found: {json_path}")
        print("     Make sure you have assets exported from Houdini first")
        return False

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"  ❌ JSON file is not a list: {type(data)}")
            return False

        print(f"  ✅ JSON file valid: {len(data)} assets found")

        # Check first asset structure
        if data:
            first_asset = data[0]
            required_fields = ['id', 'name', 'category', 'paths']
            missing_fields = [field for field in required_fields if field not in first_asset]

            if missing_fields:
                print(f"  ⚠️ First asset missing fields: {missing_fields}")
            else:
                print(f"  ✅ Asset structure looks good")
                print(f"      Sample: {first_asset['name']} ({first_asset['category']})")

        return True

    except Exception as e:
        print(f"  ❌ Error reading JSON: {e}")
        return False


def check_package_json():
    """Check if package.json has the correct scripts"""
    print("\n📦 Checking package.json scripts...")

    try:
        with open("package.json", 'r') as f:
            package_data = json.load(f)

        scripts = package_data.get('scripts', {})
        required_scripts = {
            'dev': 'npm run kill-atlas && npm run setup-database && concurrently',
            'setup-database': 'cd backend && node ../scripts/py-launcher.js start_database.py'
        }

        for script_name, expected_content in required_scripts.items():
            if script_name not in scripts:
                print(f"  ❌ Missing script: {script_name}")
                return False
            elif expected_content not in scripts[script_name]:
                print(f"  ❌ Script '{script_name}' doesn't contain expected content")
                print(f"      Expected: {expected_content}")
                print(f"      Found: {scripts[script_name]}")
                return False
            else:
                print(f"  ✅ {script_name} script configured correctly")

        return True

    except Exception as e:
        print(f"  ❌ Error reading package.json: {e}")
        return False


def check_python_dependencies():
    """Check if Python dependencies are available"""
    print("\n🐍 Checking Python dependencies...")

    required_modules = [
        'fastapi',
        'uvicorn',
        'arango',
        'requests',
        'aiofiles'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  ❌ {module}")

    if missing_modules:
        print(f"\n  Install missing modules with:")
        print(f"  pip install {' '.join(missing_modules)}")
        return False

    return True


def test_arangodb_connection():
    """Test if ArangoDB connection works"""
    print("\n🗄️ Testing ArangoDB connection...")

    try:
        # Add current directory to path
        sys.path.append(str(Path("backend")))

        from assetlibrary.database.setup_arango_database import test_connection

        # Test connection
        test_connection()
        return True

    except Exception as e:
        print(f"  ❌ ArangoDB connection test failed: {e}")
        print("     Make sure ArangoDB is running on http://localhost:8529")
        return False


def check_frontend_dependencies():
    """Check if frontend dependencies are installed"""
    print("\n⚛️ Checking frontend dependencies...")

    frontend_node_modules = Path("frontend/node_modules")
    if not frontend_node_modules.exists():
        print("  ❌ Frontend node_modules not found")
        print("     Run: cd frontend && npm install")
        return False

    print("  ✅ Frontend dependencies appear to be installed")
    return True


def display_startup_instructions():
    """Display instructions for starting the application"""
    print("\n🚀 Startup Instructions:")
    print("=" * 50)
    print("1. Make sure ArangoDB is running:")
    print("   - Install ArangoDB if not already installed")
    print("   - Start ArangoDB service on http://localhost:8529")
    print()
    print("2. Make sure your JSON file exists and contains assets:")
    print("   C:\\Users\\alexh\\Desktop\\BlacksmithAtlas\\backend\\assetlibrary\\database\\3DAssets.json")
    print()
    print("3. Start the application:")
    print("   npm run dev")
    print()
    print("4. Or test the database manually:")
    print("   cd backend && python assetlibrary/database/setup_arango_database.py test")


def main():
    """Run all verification checks"""
    print("🔍 Blacksmith Atlas Setup Verification")
    print("=" * 60)

    checks = [
        ("File Structure", check_file_structure),
        ("JSON Source File", check_json_file),
        ("Package.json scripts", check_package_json),
        ("Python Dependencies", check_python_dependencies),
        ("Frontend Dependencies", check_frontend_dependencies),
        ("ArangoDB Connection", test_arangodb_connection)
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, check_function in checks:
        print(f"\n{check_name}:")
        if check_function():
            passed_checks += 1
        else:
            print(f"  ⚠️ {check_name} check failed")

    print("\n" + "=" * 60)
    print(f"Verification Results: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("🎉 All checks passed! Your setup is ready.")
        display_startup_instructions()
        return True
    else:
        print("❌ Some checks failed. Please fix the issues above before starting.")
        return False


if __name__ == "__main__":
    main()