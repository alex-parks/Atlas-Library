#!/usr/bin/env python3
"""
Regenerate thumbnails for existing texture assets to ensure they are 1024x1024
"""
import os
import sys
from pathlib import Path
import subprocess
import logging
from PIL import Image
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def resize_image_to_thumbnail(source_path, dest_path, size=1024):
    """Resize an image to 1024x1024 for thumbnail"""
    try:
        # Try oiiotool first if available
        try:
            cmd = [
                'oiiotool',
                str(source_path),
                '--resize', f'{size}x{size}',
                '--colorconvert', 'sRGB', 'sRGB',
                '-o', str(dest_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"✅ Resized with oiiotool: {dest_path}")
                return True
            else:
                logger.warning(f"oiiotool failed: {result.stderr}")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.info("oiiotool not available, falling back to PIL")
        
        # Fallback to PIL
        with Image.open(source_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize to exactly 1024x1024
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG
            img.save(dest_path, 'PNG', optimize=True)
            logger.info(f"✅ Resized with PIL: {dest_path}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to resize {source_path}: {e}")
        return False

def process_texture_asset(asset_folder):
    """Process a single texture asset folder"""
    asset_folder = Path(asset_folder)
    thumbnail_folder = asset_folder / "Thumbnail"
    asset_subfolder = asset_folder / "Asset"
    
    if not thumbnail_folder.exists():
        logger.warning(f"⚠️ No Thumbnail folder in {asset_folder}")
        return
    
    # Get all thumbnail files
    thumbnail_files = list(thumbnail_folder.glob("*_thumbnail.png")) + \
                     list(thumbnail_folder.glob("*_thumbnail.jpg")) + \
                     list(thumbnail_folder.glob("*_thumbnail.jpeg"))
    
    if not thumbnail_files:
        logger.warning(f"⚠️ No thumbnail files found in {thumbnail_folder}")
        return
    
    logger.info(f"\n📁 Processing asset: {asset_folder.name}")
    
    for thumb_file in thumbnail_files:
        # Check current size
        try:
            with Image.open(thumb_file) as img:
                current_size = img.size
                logger.info(f"   📏 Current size of {thumb_file.name}: {current_size[0]}x{current_size[1]}")
                
                # Only resize if not already 1024x1024
                if current_size != (1024, 1024):
                    # Backup original
                    backup_path = thumb_file.with_suffix(f'.original{thumb_file.suffix}')
                    if not backup_path.exists():
                        thumb_file.rename(backup_path)
                        logger.info(f"   💾 Backed up to: {backup_path.name}")
                    else:
                        backup_path = thumb_file
                    
                    # Resize to 1024x1024
                    if resize_image_to_thumbnail(backup_path, thumb_file, 1024):
                        logger.info(f"   ✅ Resized to 1024x1024: {thumb_file.name}")
                    else:
                        logger.error(f"   ❌ Failed to resize: {thumb_file.name}")
                else:
                    logger.info(f"   ✅ Already 1024x1024: {thumb_file.name}")
        except Exception as e:
            logger.error(f"   ❌ Error processing {thumb_file}: {e}")

def main():
    # Check if running in container
    if os.getenv('ASSET_LIBRARY_PATH'):
        base_path = Path(os.getenv('ASSET_LIBRARY_PATH'))
    elif Path('/app/assets').exists():
        # Running in container
        base_path = Path('/app/assets')
    else:
        # Running locally
        base_path = Path('/net/library/atlaslib')
    
    texture_base = base_path / "3D" / "Textures"
    
    if not texture_base.exists():
        logger.error(f"❌ Texture directory not found: {texture_base}")
        sys.exit(1)
    
    logger.info(f"🔍 Scanning texture assets in: {texture_base}")
    
    # Find all texture asset folders
    processed = 0
    for category_folder in texture_base.iterdir():
        if category_folder.is_dir():
            logger.info(f"\n📂 Processing category: {category_folder.name}")
            
            for asset_folder in category_folder.iterdir():
                if asset_folder.is_dir():
                    # Check if this is a texture asset (has metadata.json)
                    metadata_file = asset_folder / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                                if metadata.get('asset_type') == 'Textures':
                                    process_texture_asset(asset_folder)
                                    processed += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Could not read metadata for {asset_folder}: {e}")
    
    logger.info(f"\n✨ Processed {processed} texture assets")

if __name__ == "__main__":
    main()