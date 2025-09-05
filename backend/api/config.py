#!/usr/bin/env python3
"""
Blacksmith Atlas - Configuration API
====================================

Provides configuration endpoints for frontend and other components.

Author: Blacksmith VFX
Version: 1.0
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from backend.core.config_manager import config as atlas_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["configuration"])

@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """
    Get Atlas configuration for frontend use
    
    Returns:
        Configuration object with paths and settings
    """
    try:
        # Return a subset of configuration that's safe for frontend
        config_data = {
            "paths": {
                "asset_library_root": atlas_config.asset_library_root,
                "asset_library_3d": atlas_config.asset_library_3d,
                "asset_library_2d": atlas_config.asset_library_2d,
                "thumbnails": atlas_config.thumbnails_path
            },
            "api": {
                "backend_url": atlas_config.backend_url,
                "frontend_url": atlas_config.frontend_url
            },
            "asset_structure": atlas_config.get('asset_structure', {}),
            "render_settings": atlas_config.get('render_settings', {}),
            "version": atlas_config.get('version', '1.0.0')
        }
        
        logger.info("✅ Configuration retrieved successfully")
        return config_data
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")

@router.get("/config/paths")
async def get_config_paths() -> Dict[str, str]:
    """
    Get just the path configuration
    
    Returns:
        Dictionary of important paths
    """
    try:
        paths = {
            "asset_library_root": atlas_config.asset_library_root,
            "asset_library_3d": atlas_config.asset_library_3d,
            "asset_library_2d": atlas_config.asset_library_2d,
            "thumbnails": atlas_config.thumbnails_path,
            "backend_url": atlas_config.backend_url,
            "frontend_url": atlas_config.frontend_url
        }
        
        logger.info("✅ Path configuration retrieved successfully")
        return paths
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve path configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve path configuration: {str(e)}")

@router.post("/config/reload")
async def reload_config() -> Dict[str, Any]:
    """
    Reload configuration from file
    
    Returns:
        Success status and current configuration
    """
    try:
        success = atlas_config.reload()
        
        if success:
            logger.info("✅ Configuration reloaded successfully")
            return {
                "success": True,
                "message": "Configuration reloaded successfully",
                "config": {
                    "asset_library_root": atlas_config.asset_library_root,
                    "backend_url": atlas_config.backend_url,
                    "version": atlas_config.get('version', '1.0.0')
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload configuration")
            
    except Exception as e:
        logger.error(f"❌ Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")

@router.get("/config/validate")
async def validate_config() -> Dict[str, Any]:
    """
    Validate current configuration
    
    Returns:
        Validation results
    """
    try:
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # Check if asset library paths exist
        import os
        from pathlib import Path
        
        paths_to_check = {
            "asset_library_root": atlas_config.asset_library_root,
            "asset_library_3d": atlas_config.asset_library_3d,
            "asset_library_2d": atlas_config.asset_library_2d
        }
        
        for path_name, path_value in paths_to_check.items():
            if path_value and Path(path_value).exists():
                validation_results["checks"][path_name] = {"exists": True, "path": path_value}
            else:
                validation_results["checks"][path_name] = {"exists": False, "path": path_value}
                validation_results["warnings"].append(f"Path does not exist: {path_name} -> {path_value}")
        
        # Check HDA path
        hda_path = atlas_config.houdini_hda_path
        if hda_path and Path(hda_path).exists():
            validation_results["checks"]["houdini_hda"] = {"exists": True, "path": hda_path}
        else:
            validation_results["checks"]["houdini_hda"] = {"exists": False, "path": hda_path}
            validation_results["warnings"].append(f"Houdini HDA not found: {hda_path}")
        
        # Overall validation status
        if validation_results["errors"]:
            validation_results["valid"] = False
        
        logger.info(f"✅ Configuration validation complete: {len(validation_results['errors'])} errors, {len(validation_results['warnings'])} warnings")
        return validation_results
        
    except Exception as e:
        logger.error(f"❌ Failed to validate configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")