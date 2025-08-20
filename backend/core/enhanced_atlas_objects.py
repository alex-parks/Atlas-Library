# backend/core/enhanced_atlas_objects.py
"""
Enhanced Atlas Object Hierarchy
==============================

Comprehensive object-oriented foundation implementing full BaseAtlasObject hierarchy
with ArangoDB integration, schema validation, and graph relationships.

This extends the existing base_atlas_object.py with:
- Complete inheritance hierarchy for all Atlas entities
- ArangoDB document/edge collection integration  
- Schema validation with Pydantic
- Graph relationship management
- Migration system for schema updates
"""

import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class AtlasObjectType(str, Enum):
    """Enumeration of all Atlas object types"""
    ASSET = "asset"
    PROJECT = "project" 
    USER = "user"
    AI_TOOL = "ai_tool"
    WORKFLOW = "workflow"
    ASSET_RELATIONSHIP = "asset_relationship"
    PROJECT_ASSET = "project_asset"
    USER_SESSION = "user_session"


class BaseAtlasObject(BaseModel, ABC):
    """
    Enhanced base class for all Atlas objects with ArangoDB integration
    
    Provides:
    - UUID generation and management
    - Timestamp tracking (created_at, updated_at)
    - Metadata management with validation
    - Serialization/deserialization
    - Graph relationship support
    """
    
    # Core identification
    _key: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    object_type: AtlasObjectType
    name: str = Field(..., min_length=1, max_length=200)
    
    # Metadata and tracking
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    # Status tracking
    status: str = Field(default="active")  # active, archived, deleted
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update metadata and refresh timestamp"""
        self.metadata.update(updates)
        self.updated_at = datetime.now()
    
    def add_tags(self, new_tags: List[str]) -> None:
        """Add tags to object"""
        self.tags.extend([tag for tag in new_tags if tag not in self.tags])
        self.updated_at = datetime.now()
    
    def remove_tags(self, tags_to_remove: List[str]) -> None:
        """Remove tags from object"""
        self.tags = [tag for tag in self.tags if tag not in tags_to_remove]
        self.updated_at = datetime.now()
    
    @abstractmethod
    def validate_object_specific(self) -> bool:
        """Object-specific validation logic - implement in subclasses"""
        pass
    
    def validate(self) -> bool:
        """Comprehensive object validation"""
        # Base validation
        if not self.name or len(self.name.strip()) == 0:
            return False
            
        if self.status not in ["active", "archived", "deleted"]:
            return False
            
        # Object-specific validation
        return self.validate_object_specific()
    
    def to_arango_document(self) -> Dict[str, Any]:
        """Convert to ArangoDB document format"""
        doc = self.dict()
        doc["_key"] = self._key
        return doc


class AssetObject(BaseAtlasObject):
    """
    Base class for all asset types in Atlas
    
    Handles common asset functionality:
    - File path management
    - Format support (USD, FBX, OBJ, etc.)
    - Dependency tracking
    - Version control
    """
    
    object_type: AtlasObjectType = AtlasObjectType.ASSET
    
    # Asset classification
    asset_type: str  # geometry, material, texture, light_rig, etc.
    category: str = "General"
    dimension: str = "3D"
    
    # File management
    paths: Dict[str, Optional[str]] = Field(default_factory=dict)
    file_formats: List[str] = Field(default_factory=list)
    file_sizes: Dict[str, int] = Field(default_factory=dict)
    
    # Version control
    version_number: int = 1
    parent_asset_id: Optional[str] = None  # For asset versions
    
    # Processing status
    processing_status: str = "ready"  # ready, processing, error
    preview_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Hierarchy for frontend filtering
    hierarchy: Dict[str, str] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-populate hierarchy for frontend
        self.hierarchy = {
            "dimension": self.dimension,
            "asset_type": self.asset_type,
            "subcategory": self.category
        }
    
    def validate_object_specific(self) -> bool:
        """Asset-specific validation"""
        return bool(self.asset_type and len(self.asset_type.strip()) > 0)
    
    def add_file_path(self, format_type: str, path: str, file_size: int = 0) -> None:
        """Add file path for specific format"""
        self.paths[format_type] = path
        if file_size > 0:
            self.file_sizes[format_type] = file_size
        if format_type not in self.file_formats:
            self.file_formats.append(format_type)
        self.updated_at = datetime.now()
    
    def get_total_file_size(self) -> int:
        """Calculate total file size across all formats"""
        return sum(self.file_sizes.values())


class GeometryAsset(AssetObject):
    """3D Geometry assets (USD, OBJ, FBX)"""
    
    asset_type: str = "geometry"
    
    # Geometry-specific data
    geometry_data: Dict[str, Any] = Field(default_factory=lambda: {
        "polycount": 0,
        "vertex_count": 0,
        "has_uvs": False,
        "has_normals": True,
        "bounding_box": None
    })
    
    # Animation support
    animation_data: Dict[str, Any] = Field(default_factory=lambda: {
        "has_animation": False,
        "frame_range": None,
        "fps": 24
    })
    
    # Source application data
    source_data: Dict[str, Any] = Field(default_factory=lambda: {
        "application": "Houdini",
        "version": None,
        "node_path": None
    })
    
    def validate_object_specific(self) -> bool:
        """Geometry asset validation"""
        return super().validate_object_specific() and self.asset_type == "geometry"


class MaterialAsset(AssetObject):
    """Material assets with shader parameters"""
    
    asset_type: str = "material"
    
    # Material-specific data
    shader_type: str = "principled"  # principled, redshift, arnold, etc.
    render_engine: str = "redshift"
    
    # Shader parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Texture map assignments
    texture_maps: Dict[str, Optional[str]] = Field(default_factory=lambda: {
        "diffuse": None,
        "normal": None,
        "roughness": None,
        "metallic": None,
        "displacement": None,
        "emission": None
    })
    
    def validate_object_specific(self) -> bool:
        """Material asset validation"""
        return super().validate_object_specific() and self.asset_type == "material"


class TextureAsset(AssetObject):
    """Texture assets (EXR, PNG, TIFF)"""
    
    asset_type: str = "texture"
    
    # Image properties
    resolution: List[int] = Field(default_factory=lambda: [0, 0])  # [width, height]
    channels: int = 3
    bit_depth: int = 8
    color_space: str = "sRGB"
    format: str = "png"  # exr, png, jpg, tiff
    
    # Texture-specific properties
    texture_type: str = "diffuse"  # diffuse, normal, roughness, etc.
    is_tileable: bool = False
    has_alpha: bool = False
    
    def validate_object_specific(self) -> bool:
        """Texture asset validation"""
        valid_formats = ["exr", "png", "jpg", "jpeg", "tiff", "tga"]
        return (super().validate_object_specific() and 
                self.asset_type == "texture" and
                self.format.lower() in valid_formats)


class LightRigAsset(AssetObject):
    """Light rig assets"""
    
    asset_type: str = "light_rig"
    
    # Lighting data
    light_count: int = 0
    light_types: List[str] = Field(default_factory=list)  # area, directional, point, etc.
    supports_hdri: bool = True
    
    # Render engine specific settings
    render_settings: Dict[str, Any] = Field(default_factory=dict)
    
    def validate_object_specific(self) -> bool:
        """Light rig asset validation"""
        return super().validate_object_specific() and self.asset_type == "light_rig"


class ProjectObject(BaseAtlasObject):
    """Project management object"""
    
    object_type: AtlasObjectType = AtlasObjectType.PROJECT
    
    # Project details
    client: str
    project_status: str = "active"  # active, completed, cancelled, on_hold
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Team management
    team_members: List[str] = Field(default_factory=list)  # User IDs
    project_lead: Optional[str] = None  # User ID
    
    # Budget and estimation
    budget: Optional[float] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    
    def validate_object_specific(self) -> bool:
        """Project validation"""
        return bool(self.client and len(self.client.strip()) > 0)
    
    def add_team_member(self, user_id: str) -> None:
        """Add team member to project"""
        if user_id not in self.team_members:
            self.team_members.append(user_id)
            self.updated_at = datetime.now()


class UserObject(BaseAtlasObject):
    """User management object"""
    
    object_type: AtlasObjectType = AtlasObjectType.USER
    
    # User details
    email: str
    full_name: str
    role: str = "artist"  # artist, lead, producer, admin
    department: str = "general"
    
    # Authentication
    password_hash: Optional[str] = None
    last_login: Optional[datetime] = None
    
    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "default_category": "General",
        "thumbnail_size": "medium",
        "view_mode": "grid",
        "theme": "dark"
    })
    
    # Permissions
    permissions: List[str] = Field(default_factory=list)
    
    def validate_object_specific(self) -> bool:
        """User validation"""
        valid_roles = ["artist", "lead", "producer", "admin"]
        return (bool(self.email and "@" in self.email) and
                self.role in valid_roles)


class AIToolObject(BaseAtlasObject):
    """AI tool and workflow management"""
    
    object_type: AtlasObjectType = AtlasObjectType.AI_TOOL
    
    # Tool configuration
    tool_type: str  # comfyui, custom, external
    workflow_definition: Dict[str, Any] = Field(default_factory=dict)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    
    # Resource requirements
    gpu_required: bool = True
    memory_required_mb: int = 2048
    estimated_runtime_seconds: Optional[float] = None
    
    # Usage tracking
    execution_count: int = 0
    success_rate: float = 1.0
    
    def validate_object_specific(self) -> bool:
        """AI tool validation"""
        valid_types = ["comfyui", "custom", "external"]
        return self.tool_type in valid_types


class WorkflowObject(BaseAtlasObject):
    """Workflow automation object"""
    
    object_type: AtlasObjectType = AtlasObjectType.WORKFLOW
    
    # Workflow definition
    workflow_type: str  # rendering, compositing, asset_creation
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Execution tracking
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    average_duration_seconds: Optional[float] = None
    
    def validate_object_specific(self) -> bool:
        """Workflow validation"""
        valid_types = ["rendering", "compositing", "asset_creation", "export", "import"]
        return self.workflow_type in valid_types


# Edge Objects for Graph Relationships

class BaseRelationship(BaseModel):
    """Base class for all edge relationships"""
    
    _from: str  # Source document ID
    _to: str    # Target document ID
    relationship_type: str
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AssetDependency(BaseRelationship):
    """Asset dependency relationship (textures, materials, etc.)"""
    
    relationship_type: str = "dependency"
    dependency_type: str  # texture, material, reference, parent
    required: bool = True  # Is this dependency mandatory?
    
    @validator('_from', '_to')
    def validate_asset_references(cls, v):
        """Ensure proper asset document references"""
        if not v.startswith('Atlas_Library/'):
            return f'Atlas_Library/{v}'
        return v


class ProjectAssetRelationship(BaseRelationship):
    """Project to asset relationship"""
    
    relationship_type: str = "project_asset"
    usage_type: str = "primary"  # primary, reference, backup
    assigned_to: Optional[str] = None  # User ID responsible for this asset in project
    
    @validator('_from')
    def validate_project_reference(cls, v):
        """Ensure proper project document reference"""
        if not v.startswith('projects/'):
            return f'projects/{v}'
        return v
    
    @validator('_to')
    def validate_asset_reference(cls, v):
        """Ensure proper asset document reference"""
        if not v.startswith('Atlas_Library/'):
            return f'Atlas_Library/{v}'
        return v


# Factory functions for object creation

def create_asset_object(asset_type: str, name: str, **kwargs) -> AssetObject:
    """Factory function to create appropriate asset object type"""
    
    asset_classes = {
        "geometry": GeometryAsset,
        "material": MaterialAsset,
        "texture": TextureAsset,
        "light_rig": LightRigAsset
    }
    
    asset_class = asset_classes.get(asset_type, AssetObject)
    return asset_class(name=name, **kwargs)


def create_atlas_object(object_type: AtlasObjectType, name: str, **kwargs) -> BaseAtlasObject:
    """Factory function to create appropriate Atlas object"""
    
    object_classes = {
        AtlasObjectType.ASSET: AssetObject,
        AtlasObjectType.PROJECT: ProjectObject,
        AtlasObjectType.USER: UserObject,
        AtlasObjectType.AI_TOOL: AIToolObject,
        AtlasObjectType.WORKFLOW: WorkflowObject
    }
    
    object_class = object_classes.get(object_type, BaseAtlasObject)
    return object_class(name=name, **kwargs)


# Schema validation helpers

def validate_atlas_document(doc: Dict[str, Any], expected_type: AtlasObjectType) -> bool:
    """Validate document against Atlas object schema"""
    try:
        if doc.get("object_type") != expected_type.value:
            return False
            
        # Create object instance to validate
        obj = create_atlas_object(expected_type, doc.get("name", ""), **doc)
        return obj.validate()
        
    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        return False


def get_object_schema(object_type: AtlasObjectType) -> Dict[str, Any]:
    """Get JSON schema for object type"""
    object_classes = {
        AtlasObjectType.ASSET: AssetObject,
        AtlasObjectType.PROJECT: ProjectObject,
        AtlasObjectType.USER: UserObject,
        AtlasObjectType.AI_TOOL: AIToolObject,
        AtlasObjectType.WORKFLOW: WorkflowObject
    }
    
    object_class = object_classes.get(object_type)
    if object_class:
        return object_class.schema()
    return {}