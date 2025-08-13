# backend/assetlibrary/models.py
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import uuid


class AssetBase(BaseModel):
    """Base model for all assets in ArangoDB"""
    _key: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    _type: str = "Asset"
    name: str
    category: str = "General"
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str
    status: str = "active"  # active, archived, deleted

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Asset3D(AssetBase):
    """3D Asset model"""
    _type: str = "Asset3D"

    # File paths
    paths: Dict[str, str] = {
        "usd": None,
        "fbx": None,
        "obj": None,
        "abc": None,
        "thumbnail": None,
        "textures": None
    }

    # Geometry data
    geometry: Dict[str, Any] = {
        "polycount": 0,
        "vertex_count": 0,
        "has_uvs": False,
        "has_normals": True,
        "bounding_box": None
    }

    # Material data
    materials: List[str] = []  # References to material documents

    # Animation data
    animation: Dict[str, Any] = {
        "has_animation": False,
        "frame_range": None,
        "fps": 24
    }

    # Source data
    source: Dict[str, Any] = {
        "application": "Houdini",
        "version": None,
        "file": None,
        "node_path": None
    }

    # File sizes
    file_sizes: Dict[str, int] = {}

    # Dependencies
    dependencies: Dict[str, List[str]] = {
        "textures": [],
        "materials": [],
        "referenced_assets": []
    }


class Texture(AssetBase):
    """Texture asset model"""
    _type: str = "Texture"

    # File info
    path: str
    format: str  # exr, png, jpg, etc.
    resolution: List[int] = [0, 0]  # [width, height]
    channels: int = 3
    bit_depth: int = 8
    color_space: str = "sRGB"

    # Texture specific
    texture_type: str = "diffuse"  # diffuse, normal, roughness, etc.
    is_tileable: bool = False
    has_alpha: bool = False

    # Usage tracking
    used_by_assets: List[str] = []  # Asset IDs that use this texture
    used_by_materials: List[str] = []  # Material IDs


class Material(AssetBase):
    """Material asset model"""
    _type: str = "Material"

    # Material info
    shader_type: str  # principled, redshift, arnold, etc.
    render_engine: str = "redshift"

    # Parameters
    parameters: Dict[str, Any] = {}

    # Texture maps
    texture_maps: Dict[str, str] = {
        "diffuse": None,
        "normal": None,
        "roughness": None,
        "metallic": None,
        "displacement": None,
        "emission": None
    }

    # Usage
    used_by_assets: List[str] = []


class Project(BaseModel):
    """Project model"""
    _key: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    _type: str = "Project"
    name: str
    client: str
    status: str = "active"  # active, completed, archived
    created_at: datetime = Field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Team
    team_members: List[str] = []  # User IDs
    project_lead: Optional[str] = None

    # Assets
    assets: List[str] = []  # Asset IDs

    # Metadata
    metadata: Dict[str, Any] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AssetRelationship(BaseModel):
    """Edge model for asset relationships"""
    _from: str  # Source asset ID (assets/id)
    _to: str  # Target asset ID (assets/id)
    relationship_type: str  # parent, child, dependency, reference
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

    @validator('_from', '_to')
    def validate_asset_reference(cls, v):
        if not v.startswith('assets/'):
            return f'assets/{v}'
        return v


class Tag(BaseModel):
    """Tag model"""
    _key: str
    _type: str = "Tag"
    name: str
    category: str = "general"  # general, technical, artistic, status
    color: str = "#808080"
    description: str = ""
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class User(BaseModel):
    """User model"""
    _key: str
    _type: str = "User"
    username: str
    email: str
    full_name: str
    role: str = "artist"  # artist, lead, producer, admin
    department: str = "general"
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    # Preferences
    preferences: Dict[str, Any] = {
        "default_category": "General",
        "thumbnail_size": "medium",
        "view_mode": "grid"
    }


class ExportJob(BaseModel):
    """Export job tracking model"""
    _key: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    _type: str = "ExportJob"
    asset_id: str
    status: str = "pending"  # pending, processing, completed, failed
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Job details
    export_formats: List[str] = []
    options: Dict[str, Any] = {}

    # Results
    output_files: Dict[str, str] = {}
    errors: List[str] = []
    warnings: List[str] = []

    # Performance
    duration_seconds: Optional[float] = None
    file_sizes: Dict[str, int] = {}


class Todo(BaseModel):
    """Todo/Task model for project management"""
    _key: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    _type: str = "Todo"
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False
    priority: str = "medium"  # low, medium, high, urgent
    category: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None
    user_id: Optional[str] = None  # Assigned user
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Project association
    project_id: Optional[str] = None
    asset_id: Optional[str] = None  # Associated asset if applicable

    # Progress tracking
    progress: int = Field(default=0, ge=0, le=100)  # 0-100%
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(valid_priorities)}')
        return v

    @validator('progress')
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Progress must be between 0 and 100')
        return v


# Query helpers for ArangoDB
class AssetQueries:
    """Helper class for common ArangoDB queries"""

    @staticmethod
    def find_by_name(name: str) -> str:
        """AQL query to find assets by name"""
        return """
        FOR asset IN Asset_Library
            FILTER asset.name == @name
            RETURN asset
        """

    @staticmethod
    def find_by_category(category: str) -> str:
        """AQL query to find assets by category"""
        return """
        FOR asset IN Asset_Library
            FILTER asset.category == @category
            SORT asset.created_at DESC
            RETURN asset
        """

    @staticmethod
    def find_with_dependencies(asset_id: str) -> str:
        """AQL query to find asset with all dependencies"""
        return """
        LET asset = DOCUMENT('assets', @asset_id)
        LET textures = (
            FOR v IN 1..1 OUTBOUND asset asset_relationships
                FILTER v._type == 'Texture'
                RETURN v
        )
        LET materials = (
            FOR v IN 1..1 OUTBOUND asset asset_relationships
                FILTER v._type == 'Material'
                RETURN v
        )
        RETURN {
            asset: asset,
            textures: textures,
            materials: materials
        }
        """

    @staticmethod
    def find_unused_assets() -> str:
        """AQL query to find assets not used in any project"""
        return """
        FOR asset IN Asset_Library
            LET usage = LENGTH(
                FOR v IN 1..1 INBOUND asset asset_relationships
                    RETURN v
            )
            FILTER usage == 0
            RETURN asset
        """

    @staticmethod
    def get_asset_statistics() -> str:
        """AQL query to get asset library statistics"""
        return """
        RETURN {
            total_assets: LENGTH(Asset_Library),
            by_category: (
                FOR asset IN Asset_Library
                    COLLECT category = asset.category WITH COUNT INTO count
                    RETURN {category: category, count: count}
            ),
            by_type: (
                FOR asset IN Asset_Library
                    COLLECT type = asset._type WITH COUNT INTO count
                    RETURN {type: type, count: count}
            ),
            total_size: SUM(
                FOR asset IN Asset_Library
                    RETURN SUM(VALUES(asset.file_sizes))
            )
        }
        """