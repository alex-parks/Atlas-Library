#!/usr/bin/env python3
"""
Test Network Configuration for Blacksmith Atlas
==============================================

Simple test script to verify local and network API connectivity.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config_manager import config, network_config, get_local_config, get_network_config
    from api_client import AtlasAPIClient

    print("🧪 TESTING ATLAS NETWORK CONFIGURATION")
    print("=" * 50)

    # Test Local Configuration
    print("\n🏠 TESTING LOCAL CONFIGURATION")
    print("-" * 30)
    local_config = get_local_config()
    print(f"Environment: {local_config.environment}")
    print(f"API URL: {local_config.api_base_url}")
    print(f"Timeout: {local_config.api_timeout}s")
    print(f"SSL: {local_config.use_ssl}")

    try:
        local_client = AtlasAPIClient(use_network=False)
        print("✅ Local client created successfully")
    except Exception as e:
        print(f"❌ Local client failed: {e}")

    # Test Network Configuration
    print("\n🌐 TESTING NETWORK CONFIGURATION")
    print("-" * 30)
    net_config = get_network_config()
    print(f"Environment: {net_config.environment}")
    print(f"API URL: {net_config.api_base_url}")
    print(f"Timeout: {net_config.api_timeout}s")
    print(f"SSL: {net_config.use_ssl}")
    print(f"Verify SSL: {net_config.verify_ssl}")

    try:
        network_client = AtlasAPIClient(use_network=True)
        print("✅ Network client created successfully")
    except Exception as e:
        print(f"❌ Network client failed: {e}")

    print("\n🎯 CONFIGURATION TEST COMPLETE")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the bl-atlas-houdini/python directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()