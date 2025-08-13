#!/usr/bin/env python3
"""
Docker Auto-Insert Wrapper
===========================

This script handles auto-insertion from the host system by copying metadata
to the Docker container and processing it there.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def docker_auto_insert(metadata_file_path: str) -> bool:
    """
    Auto-insert asset into ArangoDB via Docker container
    
    Args:
        metadata_file_path: Path to the metadata.json file on host system
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    print("🐳 DOCKER AUTO-INSERT TO ARANGODB")
    print("=" * 40)
    
    try:
        metadata_path = Path(metadata_file_path)
        if not metadata_path.exists():
            print(f"❌ Metadata file not found: {metadata_file_path}")
            return False
        
        # Create temporary file in container
        container_temp_file = f"/tmp/metadata_{metadata_path.stem}_{os.getpid()}.json"
        
        print(f"📄 Copying metadata to container...")
        print(f"   Host: {metadata_file_path}")
        print(f"   Container: {container_temp_file}")
        
        # Copy metadata file to container
        copy_cmd = [
            "docker", "cp", 
            str(metadata_path), 
            f"blacksmith-atlas-backend:{container_temp_file}"
        ]
        
        copy_result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if copy_result.returncode != 0:
            print(f"❌ Failed to copy metadata to container:")
            print(copy_result.stderr)
            return False
        
        print(f"✅ Metadata copied to container")
        
        # Run auto-insert in container
        print(f"🗄️ Running auto-insert in container...")
        
        insert_cmd = [
            "docker", "exec", "blacksmith-atlas-backend",
            "python3", "/app/backend/assetlibrary/_3D/auto_arango_insert.py",
            "--metadata", container_temp_file,
            "--env", "development"
        ]
        
        insert_result = subprocess.run(insert_cmd, capture_output=True, text=True)
        
        # Show output
        if insert_result.stdout:
            print(insert_result.stdout)
        
        if insert_result.stderr:
            print("⚠️ Stderr output:")
            print(insert_result.stderr)
        
        # Cleanup temp file in container
        cleanup_cmd = [
            "docker", "exec", "blacksmith-atlas-backend",
            "rm", "-f", container_temp_file
        ]
        subprocess.run(cleanup_cmd, capture_output=True)
        
        success = insert_result.returncode == 0
        if success:
            print("✅ Docker auto-insert successful!")
        else:
            print("❌ Docker auto-insert failed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Docker auto-insert error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-insert assets via Docker')
    parser.add_argument('--metadata', required=True, help='Path to metadata.json file')
    
    args = parser.parse_args()
    
    success = docker_auto_insert(args.metadata)
    sys.exit(0 if success else 1)