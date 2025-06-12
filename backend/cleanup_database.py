# backend/cleanup_database.py
"""
Database cleanup utility for Blacksmith Atlas
Cleans up any locked database files and resets the database state
"""

import os
import time
import glob
from pathlib import Path
import subprocess
import sys


def kill_python_processes():
    """Kill any Python processes that might be holding database locks"""
    print("🔄 Checking for Python processes...")

    try:
        if os.name == 'nt':  # Windows
            # Kill any Python processes related to our project
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'],
                           capture_output=True, text=True)
            subprocess.run(['taskkill', '/f', '/im', 'python3.exe'],
                           capture_output=True, text=True)
        else:  # Unix-like
            subprocess.run(['pkill', '-f', 'python'],
                           capture_output=True, text=True)

        print("   ✅ Python processes cleaned up")
        time.sleep(1)  # Wait for processes to fully terminate

    except Exception as e:
        print(f"   ⚠️ Could not kill processes: {e}")


def cleanup_database_files():
    """Clean up any database files that might be locked"""
    print("🗄️ Cleaning up database files...")

    # Patterns for database files to clean up
    patterns = [
        "backend/database/*.db",
        "backend/database/*.db-wal",
        "backend/database/*.db-shm",
        "test_assets*.db",
        "*.db",
        "*.db-wal",
        "*.db-shm"
    ]

    cleaned_files = 0

    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   🗑️ Removed: {file_path}")
                    cleaned_files += 1
            except Exception as e:
                print(f"   ⚠️ Could not remove {file_path}: {e}")

    if cleaned_files == 0:
        print("   ✅ No database files to clean up")
    else:
        print(f"   ✅ Cleaned up {cleaned_files} database files")


def cleanup_temp_files():
    """Clean up any temporary test files"""
    print("🧹 Cleaning up temporary files...")

    import tempfile
    temp_dir = tempfile.gettempdir()

    # Look for our test database files in temp directory
    atlas_temp_files = glob.glob(os.path.join(temp_dir, "atlas_test_*.db*"))

    cleaned = 0
    for temp_file in atlas_temp_files:
        try:
            os.remove(temp_file)
            print(f"   🗑️ Removed temp file: {os.path.basename(temp_file)}")
            cleaned += 1
        except Exception as e:
            print(f"   ⚠️ Could not remove {temp_file}: {e}")

    if cleaned == 0:
        print("   ✅ No temporary files to clean up")
    else:
        print(f"   ✅ Cleaned up {cleaned} temporary files")


def reset_directories():
    """Reset and recreate necessary directories"""
    print("📁 Resetting directories...")

    directories = [
        "backend/database",
        "backend/logs",
        "config"
    ]

    for dir_path in directories:
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Directory ready: {dir_path}")
        except Exception as e:
            print(f"   ❌ Failed to create {dir_path}: {e}")


def verify_json_file():
    """Verify that the JSON source file is accessible"""
    print("📄 Verifying JSON source file...")

    json_path = Path(r"C:\Users\alexh\Desktop\BlacksmithAtlas\backend\assetlibrary\database\3DAssets.json")

    if not json_path.exists():
        print(f"   ❌ JSON file not found: {json_path}")
        return False

    try:
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"   ✅ JSON file valid: {len(data)} assets available")
        return True

    except Exception as e:
        print(f"   ❌ JSON file error: {e}")
        return False


def main():
    """Main cleanup function"""
    print("🚀 Blacksmith Atlas - Database Cleanup Utility")
    print("=" * 60)
    print()

    # Step 1: Kill any processes that might be holding locks
    kill_python_processes()

    # Step 2: Clean up database files
    cleanup_database_files()

    # Step 3: Clean up temporary files
    cleanup_temp_files()

    # Step 4: Reset directories
    reset_directories()

    # Step 5: Verify JSON source
    json_ok = verify_json_file()

    print()
    print("=" * 60)

    if json_ok:
        print("✅ Cleanup completed successfully!")
        print()
        print("Your database environment has been reset. You can now:")
        print("1. Run the verification script: python verify_database_setup.py")
        print("2. Start the application: npm run dev")
        print("3. Or test the database manually: python setup_sqlite_assets.py")
    else:
        print("⚠️ Cleanup completed but JSON file issues detected.")
        print("Please check your JSON source file path.")

    return json_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)