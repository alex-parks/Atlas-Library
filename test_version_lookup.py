#!/usr/bin/env python3

import requests
import json

def test_version_lookup(base_uid):
    """
    Test the version lookup logic directly
    """
    print(f"🧪 Testing version lookup for base UID: {base_uid}")
    
    try:
        # Query the Atlas API to get all assets
        api_url = "http://localhost:8000/api/v1/assets"
        response = requests.get(api_url, params={"limit": 1000})
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            return None
        
        assets_data = response.json()
        all_assets = assets_data.get('items', [])
        
        print(f"🔍 Total assets in database: {len(all_assets)}")
        
        # Print all assets for debugging
        for asset in all_assets:
            asset_id = asset.get('id', '')
            asset_name = asset.get('name', '')
            print(f"   Asset: {asset_id} - {asset_name}")
        
        # Filter assets that match the base UID (first 9 characters)
        matching_assets = []
        
        for asset in all_assets:
            asset_id = asset.get('id', '')
            print(f"🔍 Checking asset: {asset_id}")
            
            if len(asset_id) >= 9 and asset_id[:9].upper() == base_uid.upper():
                matching_assets.append(asset)
                print(f"   ✅ MATCH: {asset_id[:9]} == {base_uid.upper()}")
            else:
                if len(asset_id) >= 9:
                    print(f"   ❌ NO MATCH: {asset_id[:9]} != {base_uid.upper()}")
                else:
                    print(f"   ❌ TOO SHORT: {asset_id} (length: {len(asset_id)})")
        
        print(f"📊 Total matching assets: {len(matching_assets)}")
        
        if not matching_assets:
            print(f"❌ No assets found with base UID: {base_uid}")
            return {
                'base_uid': base_uid,
                'existing_versions': [],
                'next_version': 1,
                'latest_asset': None
            }
        
        # Sort by version number (last 3 characters)
        version_info = []
        print(f"🔍 Processing {len(matching_assets)} matching assets...")
        
        for asset in matching_assets:
            asset_id = asset.get('id', '')
            print(f"🔍 Processing asset ID: {asset_id}")
            
            if len(asset_id) == 12:
                try:
                    version_str = asset_id[-3:]
                    version_num = int(version_str)
                    version_info.append({
                        'version': version_num,
                        'asset_id': asset_id,
                        'asset_data': asset
                    })
                    print(f"   ✅ Parsed version {version_num:03d} from {asset_id}")
                except ValueError:
                    print(f"   ⚠️ Invalid version format in asset ID: {asset_id} (last 3: '{asset_id[-3:]}')")
            else:
                print(f"   ⚠️ Asset ID wrong length: {asset_id} (length: {len(asset_id)})")
        
        # Sort by version number
        version_info.sort(key=lambda x: x['version'])
        print(f"🔍 Sorted version info: {[(v['asset_id'], v['version']) for v in version_info]}")
        
        # Find next version number
        existing_versions = [v['version'] for v in version_info]
        next_version = max(existing_versions) + 1 if existing_versions else 1
        
        print(f"📊 FINAL RESULTS:")
        print(f"   Base UID: {base_uid}")
        print(f"   Existing versions: {existing_versions}")
        print(f"   Next version: {next_version}")
        print(f"   Next full UID: {base_uid}{next_version:03d}")
        
        return {
            'base_uid': base_uid,
            'existing_versions': existing_versions,
            'next_version': next_version,
            'latest_asset': version_info[-1]['asset_data'] if version_info else None,
            'version_info': version_info
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test with the base UID we know exists
    base_uid = "355E1BD69"
    result = test_version_lookup(base_uid)
    
    if result:
        print(f"\n✅ Test completed successfully!")
        print(f"Next version should be: {result['base_uid']}{result['next_version']:03d}")
    else:
        print(f"\n❌ Test failed!")