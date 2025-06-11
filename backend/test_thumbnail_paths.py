# backend/test_thumbnail_paths.py
"""
Test script to find the exact thumbnail file for your PigHead asset
"""

from pathlib import Path
import json


def find_pighead_thumbnail():
    """Find the PigHead thumbnail specifically"""

    print("🐷 Looking for PigHead thumbnail...")

    # Check the JSON database first
    json_path = Path(__file__).parent / "assetlibrary" / "database" / "3DAssets.json"

    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                assets = json.load(f)

            # Find PigHead asset
            pighead_asset = None
            for asset in assets:
                if 'PigHead' in asset.get('name', '') or '5a337cb9' in asset.get('id', ''):
                    pighead_asset = asset
                    break

            if pighead_asset:
                print(f"✅ Found PigHead asset in JSON:")
                print(f"   ID: {pighead_asset.get('id')}")
                print(f"   Name: {pighead_asset.get('name')}")
                print(f"   Folder: {pighead_asset.get('folder')}")

                if 'paths' in pighead_asset and 'thumbnail' in pighead_asset['paths']:
                    json_thumb_path = pighead_asset['paths']['thumbnail']
                    print(f"   JSON Thumbnail Path: {json_thumb_path}")

                    # Check if it exists
                    if Path(json_thumb_path).exists():
                        print(f"✅ JSON thumbnail path EXISTS!")
                        return json_thumb_path
                    else:
                        print(f"❌ JSON thumbnail path does NOT exist")
                else:
                    print(f"⚠️ No thumbnail path in JSON")
            else:
                print(f"❌ PigHead asset not found in JSON database")

        except Exception as e:
            print(f"❌ Error reading JSON: {e}")

    # Manual search in the expected folder
    expected_folder = Path("C:/Users/alexh/Desktop/BlacksmithAtlas_Files/AssetLibrary/3D/5a337cb9_PigHead/Thumbnail")

    print(f"\n📁 Checking expected folder: {expected_folder}")

    if expected_folder.exists():
        print(f"✅ Thumbnail folder EXISTS!")

        # List all files in the folder
        files = list(expected_folder.iterdir())
        print(f"📄 Files in thumbnail folder:")
        for file in files:
            print(f"   - {file.name} (size: {file.stat().st_size} bytes)")

            # Test if this could be the thumbnail
            if file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                print(f"🖼️ Found image file: {file}")
                return str(file)

        if not files:
            print(f"❌ Thumbnail folder is EMPTY!")
    else:
        print(f"❌ Thumbnail folder does NOT exist!")

        # Check if parent folder exists
        parent_folder = expected_folder.parent
        if parent_folder.exists():
            print(f"📁 Parent folder exists: {parent_folder}")
            subfolders = [d for d in parent_folder.iterdir() if d.is_dir()]
            print(f"   Subfolders: {[d.name for d in subfolders]}")
        else:
            print(f"❌ Parent folder also doesn't exist: {parent_folder}")

    return None


def test_api_endpoint():
    """Test the thumbnail API endpoint"""
    import requests

    print(f"\n🌐 Testing API endpoint...")

    asset_id = "5a337cb9_PigHead"
    url = f"http://localhost:8000/thumbnails/{asset_id}"

    try:
        response = requests.get(url)
        print(f"📡 GET {url}")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ Thumbnail API works!")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Length: {response.headers.get('content-length')} bytes")
        else:
            print(f"❌ API failed: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ API request failed: {e}")
        print(f"   Make sure backend is running: python main.py")


def main():
    print("🔍 PigHead Thumbnail Detective")
    print("=" * 50)

    # Find the thumbnail file
    thumbnail_path = find_pighead_thumbnail()

    if thumbnail_path:
        print(f"\n🎉 SUCCESS! Found thumbnail at:")
        print(f"   {thumbnail_path}")

        # Test file access
        try:
            with open(thumbnail_path, 'rb') as f:
                data = f.read(100)  # Read first 100 bytes
            print(f"✅ File is readable (first 100 bytes loaded)")
        except Exception as e:
            print(f"❌ Can't read file: {e}")
    else:
        print(f"\n❌ Could not find PigHead thumbnail")
        print(f"\nTroubleshooting steps:")
        print(f"1. Check if you exported the asset correctly from Houdini")
        print(f"2. Verify the folder structure matches expectations")
        print(f"3. Look for any thumbnail files manually")

    # Test API
    test_api_endpoint()


if __name__ == "__main__":
    main()