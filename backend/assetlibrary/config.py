# backend/assetlibrary/config.py
from pathlib import Path
from typing import Dict, List, Any
import os


class BlacksmithAtlasConfig:
    """Central configuration for Blacksmith Atlas asset management"""

    # Base paths - Docker-friendly with environment variables
    BASE_LIBRARY_PATH = Path(os.getenv('ASSET_LIBRARY_PATH', '/app/assets'))
    USD_LIBRARY_PATH = BASE_LIBRARY_PATH / "3D" / "USD"
    TEXTURE_LIBRARY_PATH = BASE_LIBRARY_PATH / "2D" / "Textures"
    HDRI_LIBRARY_PATH = BASE_LIBRARY_PATH / "2D" / "HDRI"

    # Project paths - Docker-friendly
    PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', '/app'))
    BACKEND_PATH = PROJECT_ROOT / "backend"
    DATABASE_PATH = BACKEND_PATH / "assetlibrary" / "database"
    LOG_PATH = Path(os.getenv('LOG_PATH', '/app/logs'))

    # Database configuration
    DATABASE = {
        'type': 'json',  # Options: 'yaml', 'json', 'arango'
        'yaml_file': DATABASE_PATH / '3DAssets.yaml',
        'json_file': DATABASE_PATH / '3DAssets.json',
        'arango': {
            # Development (local) configuration
            'development': {
                'hosts': [f"http://{os.getenv('ARANGO_HOST', 'localhost')}:{os.getenv('ARANGO_PORT', '8529')}"],
                'database': os.getenv('ARANGO_DATABASE', 'blacksmith_atlas'),
                'username': os.getenv('ARANGO_USER', 'root'),
                'password': os.getenv('ARANGO_PASSWORD', ''),
                'collections': {
                    'assets': '3D_Atlas_Library'
                }
            },
            # Production (shared) configuration
            'production': {
                'hosts': [f"http://{os.getenv('ARANGO_HOST', 'arangodb')}:{os.getenv('ARANGO_PORT', '8529')}"],
                'database': os.getenv('ARANGO_DATABASE', 'blacksmith_atlas'),
                'username': os.getenv('ARANGO_USER', 'root'),
                'password': os.getenv('ARANGO_PASSWORD', 'atlas_password'),
                'collections': {
                    'assets': '3D_Atlas_Library'
                }
            }
        }
    }

    # Asset export settings
    EXPORT_SETTINGS = {
        'formats': {
            'usd': {
                'enabled': True,
                'extension': '.usd',
                'folder': 'USD'
            },
            'fbx': {
                'enabled': True,
                'extension': '.fbx',
                'folder': 'FBX'
            },
            'obj': {
                'enabled': False,
                'extension': '.obj',
                'folder': 'OBJ'
            },
            'abc': {
                'enabled': False,
                'extension': '.abc',
                'folder': 'Alembic'
            }
        },
        'thumbnail': {
            'enabled': True,
            'resolution': (512, 512),
            'format': 'png',
            'folder': 'Thumbnail',
            'renderer': 'opengl'  # Options: 'opengl', 'karma', 'mantra'
        },
        'textures': {
            'copy_mode': 'referenced',  # Options: 'all', 'referenced', 'none'
            'folder': 'Linked_Textures',
            'convert_to_exr': False,
            'resize_large_textures': True,
            'max_texture_size': 4096
        }
    }

    # Metadata collection settings
    METADATA_SETTINGS = {
        'collect_extended': True,
        'track_dependencies': True,
        'track_materials': True,
        'track_animations': True,
        'include_scene_info': True,
        'include_user_info': True,
        'custom_attributes': [
            'project_name',
            'shot_number',
            'asset_version',
            'approval_status'
        ]
    }

    # Asset categories
    ASSET_CATEGORIES = [
        'Characters',
        'Props',
        'Environments',
        'Vehicles',
        'Effects',
        'General',
        'Test',
        'Library'
    ]

    # Asset tags
    DEFAULT_TAGS = [
        'hero',
        'background',
        'highres',
        'lowres',
        'animated',
        'static',
        'procedural',
        'scanned',
        'wip',
        'approved',
        'archived'
    ]

    # Validation rules
    VALIDATION_RULES = {
        'asset_name': {
            'min_length': 3,
            'max_length': 64,
            'allowed_chars': 'alphanumeric_underscore_dash',
            'forbidden_chars': ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' '],
            'required': True
        },
        'geometry': {
            'max_polycount': 10000000,  # 10 million
            'warn_polycount': 1000000,  # 1 million
            'require_uvs': False,
            'require_normals': True
        },
        'textures': {
            'max_size': 8192,
            'allowed_formats': ['.exr', '.png', '.jpg', '.tif', '.tiff', '.tx', '.rat'],
            'require_power_of_two': False
        }
    }

    # Logging settings
    LOGGING = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_rotation': 'daily',
        'keep_days': 30,
        'log_exports': True,
        'log_errors': True,
        'log_performance': True
    }

    # Performance settings
    PERFORMANCE = {
        'lazy_load_assets': True,
        'cache_thumbnails': True,
        'cache_metadata': True,
        'thumbnail_cache_size': 1000,  # Number of thumbnails to keep in memory
        'metadata_cache_ttl': 3600,  # Seconds
        'parallel_exports': False,
        'max_parallel_jobs': 4
    }

    # Integration settings
    INTEGRATIONS = {
        'houdini': {
            'enabled': True,
            'min_version': '19.0',
            'python_version': 3
        },
        'maya': {
            'enabled': False,
            'min_version': '2022'
        },
        'nuke': {
            'enabled': False,
            'min_version': '13.0'
        },
        'flame': {
            'enabled': False,
            'min_version': '2023'
        }
    }

    # API settings
    API_SETTINGS = {
        'host': 'localhost',
        'port': 8000,
        'api_version': 'v1',
        'enable_cors': True,
        'cors_origins': ['http://localhost:3000', 'http://localhost:3011'],
        'rate_limiting': {
            'enabled': True,
            'requests_per_minute': 60
        },
        'authentication': {
            'enabled': False,
            'method': 'jwt',
            'token_expiry': 86400  # 24 hours
        }
    }

    @classmethod
    def get_asset_path(cls, asset_type: str, asset_id: str, filename: str) -> Path:
        """Get the full path for an asset file"""
        if asset_type == '3d':
            return cls.USD_LIBRARY_PATH / f"{asset_id}_{filename}"
        elif asset_type == 'texture':
            return cls.TEXTURE_LIBRARY_PATH / f"{asset_id}_{filename}"
        elif asset_type == 'hdri':
            return cls.HDRI_LIBRARY_PATH / f"{asset_id}_{filename}"
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.BASE_LIBRARY_PATH,
            cls.USD_LIBRARY_PATH,
            cls.TEXTURE_LIBRARY_PATH,
            cls.HDRI_LIBRARY_PATH,
            cls.DATABASE_PATH,
            cls.LOG_PATH
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []

        # Check paths exist
        if not cls.BASE_LIBRARY_PATH.exists():
            issues.append(f"Library path does not exist: {cls.BASE_LIBRARY_PATH}")

        if not cls.PROJECT_ROOT.exists():
            issues.append(f"Project root does not exist: {cls.PROJECT_ROOT}")

        # Check database configuration
        db_type = cls.DATABASE['type']
        if db_type not in ['yaml', 'json', 'arango']:
            issues.append(f"Invalid database type: {db_type}")

        # Check export formats
        if not any(fmt['enabled'] for fmt in cls.EXPORT_SETTINGS['formats'].values()):
            issues.append("No export formats are enabled")

        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

    @classmethod
    def get_database_config(cls, environment: str = 'development') -> dict:
        """Get database configuration for specified environment"""
        # Check for environment variable override
        env = os.getenv('ATLAS_ENV', environment)
        
        if env == 'production':
            return cls.DATABASE['arango']['production']
        else:
            return cls.DATABASE['arango']['development']