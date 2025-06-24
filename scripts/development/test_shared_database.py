#!/usr/bin/env python3
"""
Test script to verify shared database access
Run this to test if multiple users can access the same database
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from assetlibrary.config import BlacksmithAtlasConfig
from assetlibrary.database.setup_arango_database import test_connection, setup_database


def test_shared_access():
    """Test if we can connect to the shared database"""
    print("🔍 Testing Shared Database Access")
    print("=" * 50)
    
    # Test development environment
    print("\n1. Testing Development Environment (Local):")
    try:
        test_connection('development')
    except Exception as e:
        print(f"   ❌ Development test failed: {e}")
    
    # Test production environment
    print("\n2. Testing Production Environment (Shared):")
    try:
        test_connection('production')
    except Exception as e:
        print(f"   ❌ Production test failed: {e}")
        print("   💡 Make sure:")
        print("      - ArangoDB server is running")
        print("      - Network access is configured")
        print("      - Credentials are correct")
    
    # Show configuration
    print("\n3. Current Configuration:")
    dev_config = BlacksmithAtlasConfig.get_database_config('development')
    prod_config = BlacksmithAtlasConfig.get_database_config('production')
    
    print(f"   Development: {dev_config['hosts'][0]}")
    print(f"   Production:  {prod_config['hosts'][0]}")
    print(f"   Environment: {os.getenv('ATLAS_ENV', 'development')}")


def setup_shared_database():
    """Set up the shared database"""
    print("\n🗄️ Setting up Shared Database")
    print("=" * 50)
    
    try:
        db = setup_database('production')
        print("✅ Shared database setup complete!")
        return db
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test shared database access")
    parser.add_argument('--setup', action='store_true', help='Set up the shared database')
    parser.add_argument('--test', action='store_true', help='Test database connections')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_shared_database()
    elif args.test:
        test_shared_access()
    else:
        # Default: run both tests
        test_shared_access()
        print("\n" + "=" * 50)
        setup_shared_database() 