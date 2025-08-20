#!/usr/bin/env python3
"""
Test script for the Atlas metadata ingester

This script demonstrates how to use the metadata ingester to process
the example metadata.json file and create an asset in the Atlas API.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path so we can import our modules
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Now import the ingester
from scripts.utilities.ingest_metadata import AtlasMetadataIngester

def main():
    """Test the metadata ingester with the example file"""
    
    # Path to the example metadata file
    example_metadata = Path(__file__).parent.parent.parent / "tests" / "metadata.json"
    
    if not example_metadata.exists():
        print(f"❌ Example metadata file not found: {example_metadata}")
        sys.exit(1)
    
    print("🚀 Testing Atlas Metadata Ingester")
    print(f"📄 Processing file: {example_metadata}")
    print("-" * 50)
    
    try:
        # Initialize the ingester
        ingester = AtlasMetadataIngester("http://localhost:8000")
        
        # Test connection first
        print("✅ Connected to Atlas API")
        
        # Process the metadata file
        result = ingester.ingest_metadata_file(str(example_metadata))
        
        if result:
            print("-" * 50)
            print(f"🎉 SUCCESS! Created asset:")
            print(f"   Name: {result['name']}")
            print(f"   ID: {result['id']}")
            print(f"   Category: {result['category']}")
            print(f"   Tags: {', '.join(result.get('tags', [])[:5])}...")
            print(f"   Created: {result['created_at']}")
            
            # Show some metadata highlights
            metadata = result.get('metadata', {})
            print(f"\n📊 Asset Details:")
            print(f"   Asset Type: {metadata.get('asset_type')}")
            print(f"   Render Engine: {metadata.get('render_engine')}")
            print(f"   Houdini Version: {metadata.get('houdini_version')}")
            print(f"   Texture Count: {metadata.get('textures', {}).get('count', 0)}")
            print(f"   Geometry Count: {metadata.get('geometry_files', {}).get('count', 0)}")
            
            return True
            
        else:
            print("❌ Failed to create asset")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)